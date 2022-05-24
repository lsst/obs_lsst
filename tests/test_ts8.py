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
from lsst.obs.lsst import LsstTS8


class TestTs8(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "ts8"

    @classmethod
    def getInstrument(cls):
        return LsstTS8()

    def setUp(self):
        dataIds = {'raw': {'exposure': 201807241028453, 'name_in_raft': 'S11', 'raft': 'RTM-010'},
                   'bias': {'name_in_raft': 'S11', 'raft': 'RTM-010',
                            'day_obs': 20180724, 'seq_num': 17},
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest
                   }
        self.setUp_tests(self._butler, None, dataIds)

        ccdExposureId_bits = 58
        exposureIds = {'raw': 201807241028453067, 'bias': 201807241028453067}
        filters = {'raw': 'z', 'bias': '_unknown_'}
        exptimes = {'raw': 21.913, 'bias': 0}
        detectorIds = {'raw': 67, 'bias': 67}
        detector_names = {'raw': 'RTM-010_S11', 'bias': 'RTM-010_S11'}
        detector_serials = {'raw': 'E2V-CCD250-179', 'bias': 'E2V-CCD250-179'}
        dimensions = {'raw': Extent2I(4608, 4096),
                      'bias': Extent2I(4096, 4004)}
        sky_origin = unittest.SkipTest
        raw_subsets = (({}, 1),
                       ({'physical_filter': 'z'}, 1),
                       ({'physical_filter': 'foo'}, 0),
                       ({'exposure': 201807241028453}, 1),
                       ({'exposure': 201807241028454}, 0),
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

        self.raw_filename = '201807241028453-RTM-010-S11-det067.fits'

        self.setUp_camera(camera_name='LSST-TS8',
                          n_detectors=225,
                          first_detector_name='RTM-002_S00',
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
