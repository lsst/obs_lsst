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
"""Tests of the LSSTCam shutter-timing configuration."""

import unittest

import lsst.utils.tests

BEAM_URI = "resource://lsst.obs.lsst/resources/shutter/beam_at_L3S1_z9.618_rot0_evaluated.tnt"


class ShutterBeamTestCase(lsst.utils.tests.TestCase):
    """The LSSTCam shutter-timing configuration."""

    def testConfigOverrides(self):
        """The LSSTCam overrides turn the timing on with the packaged beam."""
        try:
            from lsst.ap.association import DiaPipelineConfig, TransformDiaSourceCatalogConfig
        except ImportError:
            raise unittest.SkipTest("ap_association is not set up")
        from lsst.obs.lsst import LsstCam

        for configClass, name in ((TransformDiaSourceCatalogConfig, "transformDiaSourceCatalog"),
                                  (DiaPipelineConfig, "diaPipe")):
            config = configClass()
            LsstCam().applyConfigOverrides(name, config)
            self.assertTrue(config.doShutterTiming)
            self.assertEqual(config.shutterTiming.beamFile, BEAM_URI)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
