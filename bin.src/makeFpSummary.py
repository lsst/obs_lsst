#!/usr/bin/env python
import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
from lsst.afw.cameraGeom import utils as cgu
from lsst.afw.display.rgb import ZScaleMapping, writeRGB
from lsst.afw.math import rotateImageBy90, flipImage
import lsst.afw.geom as afwGeom
import lsst.afw.fits
lsst.afw.fits.setAllowImageCompression(False)


class ButlerListRunner(pipeBase.TaskRunner):
    """A task runner that calls run with a list of data references
    Differs from the default TaskRunner by providing all data references at once,
    instead of iterating over them one at a time. It also passes a butler to the
    call method.
    """
    @staticmethod
    def getTargetList(parsedCmd):
        """Return a list of targets (arguments for __call__); one entry per invocation
        """
        return [(parsedCmd.id.refList, parsedCmd.butler)]  # two arguments; a list of dataRefs and a butler

    def __call__(self, args):
        """Run task.runDataRef on a single target
        @param args: tuple of arguments to unpack and send to the task
        @return:
        - None if doReturnResults false
        - A pipe_base Struct containing these fields if doReturnResults true:
            - dataRefList: the argument dict sent to runDataRef
            - metadata: task metadata after execution of runDataRef
            - result: result returned by task runDataRef
        """
        dataRefList, butler = args
        task = self.TaskClass(config=self.config, log=self.log)
        result = task.runDataRef(dataRefList, butler=butler)

        if self.doReturnResults:
            return pipeBase.Struct(
                exitStatus=result.exitStatus,
                dataRefList=dataRefList,
                metadata=task.metadata,
                result=result,
            )
        else:
            return pipeBase.Struct(
                exitStatus=result.exitStatus,
            )


class FocalplaneSummaryConfig(pexConfig.Config):
    binSize = pexConfig.Field(dtype=int, default=64, doc="pixels to bin for the focalplane summary")
    contrast = pexConfig.Field(dtype=float, default=1, doc="contrast factor")
    sensorBinSize = pexConfig.Field(dtype=int, default=4, doc="pixels to bin per sensor")
    putFullSensors = pexConfig.Field(dtype=bool, default=False, doc="persist the full size binned sensor?")
    doSensorImages = pexConfig.Field(dtype=bool, default=True, doc="Make images of the individual sensors")

    def validate(self):
        if self.putFullSensors and not self.doSensorImages:
            raise ValueError("You may not set putFullSensors == True if doSensorImages == False")


class FocalplaneSummaryTask(pipeBase.CmdLineTask):
    ConfigClass = FocalplaneSummaryConfig
    _DefaultName = "focalplaneSummary"
    RunnerClass = ButlerListRunner

    def __init__(self, *args, **kwargs):
        pipeBase.CmdLineTask.__init__(self, *args, **kwargs)

    def runDataRef(self, expRefList, butler):
        """Make summary plots of full focalplane images.
        """
        if len(expRefList) == 0:
            return pipeBase.Struct(exitStatus=1)

        dstype = expRefList[0].butlerSubset.datasetType

        if dstype == "raw":
            def callback(im, ccd, imageSource):
                return cgu.rawCallback(im, ccd, imageSource, correctGain=True, subtractBias=True)
        elif dstype == "eimage":
            callback = eimageCallback
        else:
            callback = None

        for visit in set([er.dataId["visit"] for er in expRefList]):
            self.log.info("Processing visit %d", visit)
            expRefListForVisit = [er for er in expRefList if er.dataId["visit"] == visit]

            dataId = expRefListForVisit[0].dataId
            bi = cgu.ButlerImage(butler, dstype, visit=visit, callback=callback, verbose=True)

            if self.config.doSensorImages:
                for dataId in (er.dataId for er in expRefListForVisit):
                    ccd = butler.get('calexp_detector', **dataId)
                    try:
                        binned_im = bi.getCcdImage(ccd, binSize=self.config.sensorBinSize)[0]
                        binned_im = rotateImageBy90(binned_im, ccd.getOrientation().getNQuarter())
                        if self.config.putFullSensors:
                            butler.put(binned_im, 'binned_sensor_fits', **dataId)
                    except (TypeError, RuntimeError) as e:
                        # butler couldn't put the image or there was no image to put
                        self.log.warn("Unable to make binned image: %s", e)
                        continue

                    (x, y) = binned_im.getDimensions()
                    boxes = {'A': afwGeom.Box2I(afwGeom.PointI(0, y/2), afwGeom.ExtentI(x, y/2)),
                             'B': afwGeom.Box2I(afwGeom.PointI(0, 0), afwGeom.ExtentI(x, y/2))}
                    for half in ('A', 'B'):
                        box = boxes[half]
                        butler.put(binned_im[box], 'binned_sensor_fits_halves', half=half, **dataId)

            detectorNameList = ["%s_%s" % (er.dataId["raftName"], er.dataId["detectorName"])
                                for er in expRefListForVisit]

            im = cgu.showCamera(butler.get('camera'), imageSource=bi, binSize=self.config.binSize,
                                detectorNameList=detectorNameList)

            # filter is needed for butler.put() (but may not be available for eimages)
            if "filter" in dataId:
                filter = dataId["filter"]
            else:
                filter = butler.queryMetadata("raw", ["filter"], visit=visit)[0]

            butler.put(im, 'focalplane_summary_fits', visit=visit, filter=filter)
            zmap = ZScaleMapping(im, contrast=self.config.contrast)
            rgb = zmap.makeRgbImage(im, im, im)
            file_name = butler.get('focalplane_summary_png_filename', visit=visit, filter=filter)
            writeRGB(file_name[0], rgb)

        return pipeBase.Struct(exitStatus=0)

    @classmethod
    def _makeArgumentParser(cls, *args, **kwargs):
        # Pop doBatch keyword before passing it along to the argument parser
        kwargs.pop("doBatch", False)

        dstype = pipeBase.DatasetArgument('--dstype', default='calexp',
                                          help="dataset type to process from input data repository"
                                               "(e.g. eimage, postISRCCD, or calexp)")

        parser = pipeBase.ArgumentParser(name="focalplaneSummary",
                                         *args, **kwargs)
        parser.add_id_argument("--id", datasetType=dstype,
                               help="data ID, e.g. --id visit=12345")
        return parser

    def _getConfigName(self):
        return None

    def _getMetadataName(self):
        return None


def eimageCallback(im, ccd=None, imageSource=None):
    """A callback to handle eimages"""

    im = im.convertF()

    nQuarter = 1
    im = rotateImageBy90(im, nQuarter)
    im = flipImage(im, True, False)

    return im


if __name__ == "__main__":
    FocalplaneSummaryTask.parseAndRun()
