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

import lsst.log
import lsst.utils.tests
from lsst.geom import arcseconds, Extent2I
import lsst.afw.image

from lsst.obs.lsst.testHelper import ObsLsstButlerTests, ObsLsstObsBaseOverrides
from lsst.obs.lsst import Latiss


class TestLatiss(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "latiss"

    @classmethod
    def getInstrument(cls):
        return Latiss()

    def setUp(self):
        dataIds = {'raw': {'exposure': 3018092000065, 'detector': 0},
                   'bias': {'detector': 0, 'exposure': 3018092000065},
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest
                   }
        self.setUp_tests(self._butler, None, dataIds)

        ccdExposureId_bits = 52
        exposureIds = {'raw': 3018092000065, 'bias': 3018092000065}
        filters = {'raw': 'unknown~unknown', 'bias': '_unknown_'}
        exptimes = {'raw': 27.0, 'bias': 0}
        detectorIds = {'raw': 0, 'bias': 0}
        detector_names = {'raw': 'RXX_S00', 'bias': 'RXX_S00'}
        detector_serials = {'raw': 'ITL-3800C-068', 'bias': 'ITL-3800C-098'}
        dimensions = {'raw': Extent2I(4608, 4096),
                      'bias': Extent2I(4072, 4000)}
        sky_origin = unittest.SkipTest
        raw_subsets = (({}, 1),
                       ({'physical_filter': 'unknown~unknown'}, 1),
                       ({'physical_filter': 'SDSSg'}, 0),
                       ({'exposure.day_obs': 20180920}, 1),
                       ({'exposure': 3018092000065}, 1),
                       ({'exposure': 9999999999999}, 0),
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

        self.raw_filename = '3018092000065-det000.fits'

        self.setUp_camera(camera_name='LATISS',
                          n_detectors=1,
                          first_detector_name='RXX_S00',
                          plate_scale=9.5695 * arcseconds,
                          )

        super().setUp()


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
