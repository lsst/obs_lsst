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

"""Unit tests for LSST raw data ingest.
"""

import unittest
import os
import lsst.utils.tests

from lsst.obs.base.ingest_tests import IngestTestBase
import lsst.obs.lsst

TESTDIR = os.path.abspath(os.path.dirname(__file__))
DATAROOT = os.path.join(TESTDIR, os.path.pardir, "data", "input")


class LatissIngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):
    def setUp(self):
        self.ingestDir = TESTDIR
        self.instrument = lsst.obs.lsst.LatissInstrument()
        self.file = os.path.join(DATAROOT, "latiss", "raw", "2018-09-20",
                                 "3018092000065-det000.fits")
        self.dataIds = [dict(instrument="LATISS", exposure=3018092000065, detector=0)]

        super().setUp()


class Ts3IngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):
    def setUp(self):
        self.ingestDir = TESTDIR
        self.instrument = lsst.obs.lsst.Ts3Instrument()
        self.file = os.path.join(DATAROOT, "ts3", "raw", "2018-11-15",
                                 "201811151255111-R433-S00-det433.fits")
        self.dataIds = [dict(instrument="LSST-TS3", exposure=201811151255111, detector=433)]

        super().setUp()


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
