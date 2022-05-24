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
from lsst.obs.lsst import LsstUCDCam


class TestUcdCam(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "ucd"

    @classmethod
    def getInstrument(cls):
        return LsstUCDCam()

    def setUp(self):
        dataIds = {'raw': {'exposure': 20180530150355, 'name_in_raft': 'S00', 'raft': 'R02'},
                   'bias': unittest.SkipTest,
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest
                   }
        self.setUp_tests(self._butler, None, dataIds)

        ccdExposureId_bits = 48
        exposureIds = {'raw': 201805301503552}
        filters = {'raw': 'r'}
        exptimes = {'raw': 0.5}
        detectorIds = {'raw': 2}
        detector_names = {'raw': 'R02_S00'}
        detector_serials = {'raw': 'ITL-3800C-002'}
        dimensions = {'raw': Extent2I(0, 0)}
        sky_origin = unittest.SkipTest
        raw_subsets = (({}, 2),
                       ({'physical_filter': 'r'}, 2),
                       ({'physical_filter': 'foo'}, 0),
                       ({'exposure': 20180530150355}, 1),
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

        self.raw_filename = '20180530150355-S00-det002.fits'

        self.setUp_camera(camera_name='LSST-UCDCam',
                          n_detectors=4,
                          first_detector_name='R00_S00',
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
