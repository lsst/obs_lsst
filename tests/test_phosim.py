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
import os
import sys
import unittest
import unittest.mock

import lsst.utils.tests
from lsst.geom import arcseconds, Extent2I
import lsst.afw.image

from lsst.obs.lsst.testHelper import ObsLsstButlerTests, ObsLsstObsBaseOverrides
from lsst.obs.lsst import LsstCamPhoSim

TESTDIR = os.path.abspath(os.path.dirname(__file__))


def _clean_metadata_provenance(hdr):
    """Remove metadata fix up provenance."""
    for k in hdr:
        if k.startswith("HIERARCH ASTRO METADATA"):
            del hdr[k]


class TestPhosim(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "phosim"

    @classmethod
    def getInstrument(cls):
        return LsstCamPhoSim()

    def setUp(self):
        dataIds = {'raw': {'exposure': 204595, 'name_in_raft': 'S20', 'raft': 'R11'},
                   'bias': unittest.SkipTest,
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest
                   }
        self.setUp_tests(self._butler, dataIds)

        ccdExposureId_bits = 34
        exposureIds = {'raw': 204595042}
        filters = {'raw': 'i'}
        exptimes = {'raw': 30.0}
        detectorIds = {'raw': 42}
        detector_names = {'raw': 'R11_S20'}
        detector_serials = {'raw': 'ITL-3800C-102-Dev'}
        dimensions = {'raw': Extent2I(4176, 4020)}
        sky_origin = (55.67759886, -30.44239357)
        raw_subsets = (({}, 1),
                       ({'physical_filter': 'i'}, 1),
                       ({'physical_filter': 'foo'}, 0),
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

        self.setUp_camera(camera_name='LSSTCam-PhoSim',
                          n_detectors=201,
                          first_detector_name='R01_S00',
                          plate_scale=20.0 * arcseconds,
                          )

        super().setUp()

    def testMetadata(self):
        """Check that we can read headers properly"""
        dataId = {'exposure': 204595, 'name_in_raft': 'S20', 'raft': 'R11'}
        md = self.butler.get("raw.metadata", dataId)

        # This header comes from amp header
        self.assertEqual(md["PRESS"], 520.0)

        # This header is in HDU0
        self.assertEqual(md["TESTTYPE"], "PHOSIM")

        visitInfo = self.butler.get("raw.visitInfo", dataId)
        weather = visitInfo.getWeather()
        self.assertEqual(weather.getAirTemperature(), 20.0)

        # Check that corrections are being applied
        with unittest.mock.patch.dict(os.environ,
                                      {"METADATA_CORRECTIONS_PATH": os.path.join(TESTDIR, "data")}):
            # Check that corrections are applied during simple md get
            md_md = self.butler.get("raw.metadata", dataId)
            self.assertEqual(md_md["NEWHDR"], "corrected")

            # Check that corrections are applied if we do assembly
            raw = self.butler.get("raw", dataId)
            raw_md = raw.getMetadata()

            _clean_metadata_provenance(raw_md)
            _clean_metadata_provenance(md_md)

            self.assertEqual(raw_md, md_md)

            # And finally ensure that visitInfo gets corrections
            visitInfo = self.butler.get("raw.visitInfo", dataId)
            weather = visitInfo.getWeather()
            self.assertEqual(weather.getAirTemperature(), 10.0)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
