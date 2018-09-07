from lsst.afw.cameraGeom.utils import ButlerImage
import lsst.afw.image as afwImage
from lsst.afw.math import rotateImageBy90
from lsst.daf.persistence.butlerExceptions import NoResults


class SimButlerImage(ButlerImage):

    def getCcdImage(self, ccd, imageFactory=afwImage.ImageF, binSize=1, as_masked_image=False):
        """Return an image of the specified ccd, and also the (possibly updated) ccd

        Parameters
        ----------
        ccd : `afwImage.CameraGeom.Detector`
           Detector for the constructed image
        imageFactory : `afwImage.Image`, optional
           Image like factory for producing default images (`afwImage.ImageF` by default).
        binSize : `int`, optional
           Pixels to bin together.  Symmetric in x and y (1 by default)
        as_masked_image : `bool`, optional
           Return the image as an `afwImage.MaskedImage`? (False by default.  This returns an
           `afwImage.Image`)
        """
        bbox = ccd.getBBox()

        def parse_name_to_dataId(name_str):
            raft, sensor = name_str.split('_')
            return {'raftName': raft, 'detectorName': sensor}

        im = None
        cid = ccd.getName()
        did = parse_name_to_dataId(cid)
        if self.butler is not None and did['raftName'] not in ['R00', 'R04', 'R40', 'R44']:
            self.kwargs.update(did)
            try:
                im = self.butler.get(self.type, **self.kwargs)
                ccd = im.getDetector()  # possibly modified by assembleCcdTask
                if self.type == 'eimage' or self.type == 'calexp':
                    im.setMaskedImage(rotateImageBy90(im.getMaskedImage(), 2))
                else:
                    raise ValueError("Only valid dataset types are 'eimage' and 'calexp'")
            except (NoResults, RuntimeError):
                pass
        else:
            return None, ccd

        if im is None:
            if not as_masked_image:
                im = self._prepareImage(ccd, imageFactory(*bbox.getDimensions()), binSize)
                return rotateImageBy90(im, ccd.getOrientation().getNQuarter()), ccd
            else:
                im = self._prepareImage(ccd, afwImage.makeMaskedImage(imageFactory(*bbox.getDimensions())),
                                          binSize)
                return rotateImageBy90(im, ccd.getOrientation().getNQuarter()), ccd

        if self.type == "raw":
            raise ValueError("This class only handles ccd size images")

        if not as_masked_image:
            return self._prepareImage(ccd, im.getMaskedImage().getImage(), binSize), ccd
        else:
            return self._prepareImage(ccd, im.getMaskedImage(), binSize), ccd
