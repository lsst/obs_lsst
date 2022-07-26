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
from lsst.obs.lsst import LsstCamImSim


class TestImsim(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "imsim"

    @classmethod
    def getInstrument(cls):
        return LsstCamImSim()

    def setUp(self):
        dataIds = {'raw': {'exposure': 204595, 'name_in_raft': 'S20', 'raft': 'R11'},
                   'bias': {'exposure': 204595, 'name_in_raft': 'S20', 'raft': 'R11'},
                   'flat': {'exposure': 204595, 'name_in_raft': 'S20', 'raft': 'R11',
                            'physical_filter': 'i_sim_1.4'},
                   'dark': {'exposure': 204595, 'name_in_raft': 'S20', 'raft': 'R11'}
                   }
        self.setUp_tests(self._butler, dataIds)

        ccdExposureId_bits = 34
        exposureIds = {'raw': 204595042,
                       'bias': 204595042,
                       'dark': 204595042,
                       'flat': 204595042
                       }
        filters = {'raw': 'i_sim_1.4',
                   'bias': '_unknown_',
                   'dark': '_unknown_',
                   'flat': 'i_sim_1.4'
                   }
        exptimes = {'raw': 30.0,
                    'bias': 0.0,
                    'dark': 1.0,
                    'flat': 1.0
                    }
        detectorIds = {'raw': 42,
                       'bias': 42,
                       'dark': 42,
                       'flat': 42
                       }
        detector_names = {'raw': 'R11_S20',
                          'bias': 'R11_S20',
                          'dark': 'R11_S20',
                          'flat': 'R11_S20'
                          }
        detector_serials = {'raw': 'ITL-3800C-102-Dev',
                            'bias': 'ITL-3800C-102-Dev',
                            'dark': 'ITL-3800C-102-Dev',
                            'flat': 'ITL-3800C-102-Dev'
                            }
        dimensions = {'raw': Extent2I(4352, 4096),
                      'bias': Extent2I(4072, 4000),
                      'dark': Extent2I(4072, 4000),
                      'flat': Extent2I(4072, 4000),
                      }
        sky_origin = (55.67759886, -30.44239357)
        raw_subsets = (({}, 1),
                       ({'physical_filter': 'i_sim_1.4'}, 1),
                       ({'physical_filter': 'foo'}, 0),
                       ({'exposure': 204595}, 1),
                       ({'exposure': 204595}, 1),
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

        self.raw_filename = '00204595-R11-S20-det042.fits'

        self.setUp_camera(camera_name='LSSTCam-imSim',
                          n_detectors=189,
                          first_detector_name='R01_S00',
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
