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
from lsst.geom import arcseconds, Extent2I
import lsst.afw.image

from lsst.obs.lsst.testHelper import ObsLsstButlerTests, ObsLsstObsBaseOverrides
from lsst.obs.lsst import LsstComCamSim


class TestLsstCam(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "comCamSim"

    @classmethod
    def getInstrument(cls):
        return LsstComCamSim()

    def setUp(self):
        dataIds = {'raw': {'exposure': 7024032100720, 'name_in_raft': 'S11', 'raft': 'R22'},
                   'bias': unittest.SkipTest,
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest,
                   }
        self.setUp_tests(self._butler, dataIds)

        ccdExposureId_bits = 52
        exposureIds = {'raw': 7024032100720000,
                       }
        filters = {'raw': 'r_03',
                   }
        exptimes = {'raw': 30.0,
                    }
        detectorIds = {'raw': 4,
                       }
        detector_names = {'raw': 'R22_S11',
                          }
        # This name comes from the camera and not from the butler
        detector_serials = {'raw': 'ITL-3800C-283',
                            }
        dimensions = {'raw': Extent2I(4608, 4096),
                      }
        sky_origin = unittest.SkipTest
        raw_subsets = (({}, 1),
                       ({'physical_filter': 'r_03'}, 1),
                       ({'physical_filter': 'foo'}, 0),
                       ({'exposure': 7024032100720}, 1),
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

        self.raw_filename = '7024032100720-R22-S11-det004.fits.fz'

        self.setUp_camera(camera_name='LSSTComCamSim',
                          n_detectors=9,
                          first_detector_name='R22_S00',
                          plate_scale=20.0 * arcseconds,
                          )

        super().setUp()


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
