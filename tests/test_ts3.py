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
import os.path
import sys
import unittest

import lsst.utils.tests
from lsst.geom import arcseconds, Extent2I
import lsst.afw.image

from lsst.obs.lsst.testHelper import ObsLsstButlerTests, ObsLsstObsBaseOverrides
from lsst.obs.lsst import LsstTS3

TESTDIR = os.path.abspath(os.path.dirname(__file__))


class TestTs3(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "ts3"
    DATAROOT = os.path.join(TESTDIR, "data", "input")

    @classmethod
    def getInstrument(cls):
        return LsstTS3()

    def setUp(self):
        dataIds = {'raw': {'exposure': 201607220607067, 'name_in_raft': 'S00', 'raft': 'R071'},
                   'bias': unittest.SkipTest,
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest
                   }
        self.setUp_tests(self._butler, dataIds)

        ccdExposureId_bits = 58
        exposureIds = {'raw': 201607220607067071}
        filters = {'raw': '550CutOn'}
        exptimes = {'raw': 30.611}
        detectorIds = {'raw': 71}
        detector_names = {'raw': 'R071_S00'}
        detector_serials = {'raw': 'ITL-3800C-098'}
        dimensions = {'raw': Extent2I(4352, 4096),
                      }
        sky_origin = unittest.SkipTest
        raw_subsets = (({}, 2),
                       ({'physical_filter': '550CutOn'}, 2),
                       ({'detector': 71}, 1),
                       ({'detector.raft': 'R433'}, 1),
                       ({'detector.raft': 'R999'}, 0),
                       ({'exposure': 201607220607067}, 1),
                       ({'exposure': 201607220607068}, 0),
                       ({'physical_filter': '550CutOn'}, 2),
                       ({'physical_filter': 'foo'}, 0)
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

        self.raw_filename = '201607220607067-R071-S00-det071.fits'

        self.setUp_camera(camera_name='LSST-TS3',
                          n_detectors=435,
                          first_detector_name='R000_S00',
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
