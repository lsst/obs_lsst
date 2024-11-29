# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import sys
import unittest

import lsst.utils.tests
from lsst.geom import arcseconds, Extent2I, PointD, PointI
import lsst.afw.image
from lsst.obs.lsst.cameraTransforms import LsstCameraTransforms

from lsst.obs.lsst.testHelper import ObsLsstButlerTests, ObsLsstObsBaseOverrides
from lsst.obs.lsst import LsstCam


class TestLsstCam(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "lsstCam"

    @classmethod
    def getInstrument(cls):
        return LsstCam()

    def setUp(self):
        dataIds = {'raw': {'exposure': 3019031900001, 'name_in_raft': 'S02', 'raft': 'R10'},
                   'bias': unittest.SkipTest,
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest,
                   }
        self.setUp_tests(self._butler, dataIds)

        ccdExposureId_bits = 52
        exposureIds = {'raw': 3019031900001029,
                       }
        filters = {'raw': 'unknown',
                   }
        exptimes = {'raw': 0.0,
                    }
        detectorIds = {'raw': 29,
                       }
        detector_names = {'raw': 'R10_S02',
                          }
        # This name comes from the camera and not from the butler
        detector_serials = {'raw': 'ITL-3800C-167',
                            }
        dimensions = {'raw': Extent2I(4608, 4096),
                      }
        sky_origin = unittest.SkipTest
        raw_subsets = (({}, 3),
                       ({'physical_filter': 'unknown'}, 2),
                       ({'physical_filter': 'foo'}, 0),
                       ({'exposure': 3019031900001}, 2),
                       ({'exposure': 3019032200002}, 1),
                       ({'exposure': 9999999999999}, 0),
                       ({'physical_filter': 'SDSSi~ND_OD0.5'}, 1),
                       )
        linearizer_type = unittest.SkipTest
        self.setUp_butler_get(ccdExposureId_bits=ccdExposureId_bits,
                              exposureIds=exposureIds,
                              filters=filters,
                              exptimes=exptimes,
                              detectorIds=detectorIds,
                              detector_names=detector_names,
                              detector_serials=detector_serials,
                              dimensions=dimensions,
                              sky_origin=sky_origin,
                              raw_subsets=raw_subsets,
                              linearizer_type=linearizer_type
                              )

        self.raw_filename = '3019031900001-R10-S02-det029.fits'

        self.setUp_camera(camera_name='LSSTCam',
                          n_detectors=205,
                          first_detector_name='R01_S00',
                          plate_scale=20.0 * arcseconds,
                          )

        super().setUp()

    def testObsid(self):
        """Check that we can retrieve data using the obsid."""
        dataId = {'exposure': "MC_C_20190319_000001", 'name_in_raft': 'S02',
                  'raft': 'R10'}
        raw = self.butler.get('raw', dataId)
        self.assertIsNotNone(raw)

        # And that we can get just the header
        md = self.butler.get('raw.metadata', dataId)
        self.assertEqual(md["TELESCOP"], "LSST")

    def testCameraTransforms(self):
        """Test the geometry routines requested by the camera team

        These are found in cameraTransforms.py"""

        camera = self.butler.get('camera', immediate=True)

        raft = 'R22'
        sensor = 'S11'
        ccdid = f"{raft}_{sensor}"

        lct = LsstCameraTransforms(camera)

        # check that we can map ccd pixels to amp pixels
        for cxy, apTrue in [
                ((0,   0), (1, 508, 0)),  # noqa: E241
                ((509, 0), (2, 508, 0)),
        ]:
            ap = lct.ccdPixelToAmpPixel(*cxy, ccdid)
            self.assertEqual(ap, apTrue)

        # check inverse mapping
        for ap, cpTrue in [
                ((508, 0, 1), (0, 0)),
                ((0, 0, 9), (4071, 3999)),
        ]:
            cp = lct.ampPixelToCcdPixel(*ap, ccdid)
            self.assertEqual(cp, PointI(*cpTrue))

        # check round-tripping
        ampX, ampY, channel = 2, 0, 1
        cx, cy = lct.ampPixelToCcdPixel(ampX, ampY, channel, ccdid)
        finalChannel, finalAmpX, finalAmpY = lct.ccdPixelToAmpPixel(cx, cy, ccdid)
        self.assertEqual((finalAmpX, finalAmpY, finalChannel), (ampX, ampY, channel))

        # Check that four amp pixels near the camera's centre are
        # indeed close in focal plane coords
        for ap, fpTrue in [
                ((508, 1999,   5), ( 0.005, -0.005)),  # noqa: E201,E241
                ((0,   1999,   4), (-0.005, -0.005)),  # noqa: E201,E241
                ((0,   1999,  13), (-0.005,  0.005)),  # noqa: E201,E241
                ((508, 1999,  12), ( 0.005,  0.005)),  # noqa: E201,E241
        ]:
            fp = lct.ampPixelToFocalMm(*ap, ccdid)
            self.assertAlmostEqual((fp - PointD(*fpTrue)).computeNorm(), 0.0)

        # and for ccd coordinates:
        for cp, fpTrue in [
                ((2035, 1999), (-0.005, -0.005)),  # noqa: E201,E241
                ((2036, 1999), ( 0.005, -0.005)),  # noqa: E201,E241
                ((2035, 2000), (-0.005,  0.005)),  # noqa: E201,E241
                ((2036, 2000), ( 0.005,  0.005)),  # noqa: E201,E241
        ]:
            fp = lct.ccdPixelToFocalMm(*cp, ccdid)
            self.assertAlmostEqual((fp - PointD(*fpTrue)).computeNorm(), 0.0)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
