#!/usr/bin/env python
import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
from lsst.obs.lsstCam import SimButlerImage
from lsst.afw.cameraGeom import utils as cgu
from lsst.afw.display.rgb import ZScaleMapping, writeRGB
from lsst.afw.math import rotateImageBy90, flipImage
import lsst.afw.image as afwImage
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
        return [(parsedCmd.id.refList, parsedCmd.butler),]  # two arguments consisting of a list of dataRefs and a butler

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
                dataRefList=dataRefList,
                metadata=task.metadata,
                result=result,
            )

class FocalplaneSummaryConfig(pexConfig.Config):
    binSize = pexConfig.Field(dtype=int, default=50, doc="pixels to bin for the focalplane summary")
    contrast = pexConfig.Field(dtype=float, default=1, doc="contrast factor")
    sensorBinSize = pexConfig.Field(dtype=int, default=4, doc="pixels to bin per sensor")
    putFullSensors = pexConfig.Field(dtype=bool, default=False, doc="persist the full size binned sensor?")


class FocalplaneSummaryTask(pipeBase.CmdLineTask):
    ConfigClass = FocalplaneSummaryConfig
    _DefaultName = "focalplaneSummary"
    RunnerClass = ButlerListRunner

    def __init__(self, *args, **kwargs):
        pipeBase.CmdLineTask.__init__(self, *args, **kwargs)

    def runDataRef(self, expRefList, butler):
        """Make summary plots of full focalplane images.
        """
        sbi = SimButlerImage(butler, type=expRefList[0].butlerSubset.datasetType, visit=expRefList[0].dataId['visit'])

        for expRef in expRefList:
            data_id = expRef.dataId
            ccd = butler.get('calexp_detector', **data_id)
            try:
                binned_im = sbi.getCcdImage(ccd, binSize=self.config.sensorBinSize, as_masked_image=True)[0]
                binned_im = rotateImageBy90(binned_im, ccd.getOrientation().getNQuarter())
                if self.config.putFullSensors:
                    butler.put(binned_im, 'binned_sensor_fits', **data_id)
            except (TypeError, RuntimeError):
                # butler couldn't put the image or there was no image to put
                continue

            (x, y) = binned_im.getDimensions()
            boxes = {'A': afwGeom.Box2I(afwGeom.PointI(0, y/2), afwGeom.ExtentI(x, y/2)),
                     'B': afwGeom.Box2I(afwGeom.PointI(0, 0), afwGeom.ExtentI(x, y/2))}
            for half in ('A', 'B'):
                box = boxes[half]
                butler.put(afwImage.MaskedImageF(binned_im, box), 'binned_sensor_fits_halves', half=half,
                           **data_id)

        im = cgu.showCamera(butler.get('camera'), imageSource=sbi, binSize=self.config.binSize)
        expRef.put(im, 'focalplane_summary_fits')
        im = flipImage(im, False, True)
        zmap = ZScaleMapping(im, contrast=self.config.contrast)
        rgb = zmap.makeRgbImage(im, im, im)
        file_name = expRef.get('focalplane_summary_png_filename')
        writeRGB(file_name[0], rgb)

    @classmethod
    def _makeArgumentParser(cls, *args, **kwargs):
        # Pop doBatch keyword before passing it along to the argument parser
        kwargs.pop("doBatch", False)

        dstype = pipeBase.DatasetArgument('--dstype', default='eimage',
                                          help="dataset type to process from input data repository"
                                               "(i.e., 'eimage', 'calexp')")

        parser = pipeBase.ArgumentParser(name="focalplaneSummary",
                                         *args, **kwargs)
        parser.add_id_argument("--id", datasetType=dstype,
                               help="data ID, e.g. --id visit=12345")
        return parser

    def _getConfigName(self):
        return None

    def _getMetadataName(self):
        return None


if __name__ == "__main__":
    FocalplaneSummaryTask.parseAndRun()
