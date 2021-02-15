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

    curatedCalibrationDatasetTypes = ("camera", "defects")
    instrumentClassName = "lsst.obs.lsst.Latiss"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "latiss", "raw", "2018-09-20", "3018092000065-det000.fits")
    dataIds = [dict(instrument="LATISS", exposure=3018092000065, detector=0)]
    filterLabel = lsst.afw.image.FilterLabel(band="unknown", physical="unknown~unknown")


class Ts3IngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):

    curatedCalibrationDatasetTypes = ("camera",)
    instrumentClassName = "lsst.obs.lsst.LsstTS3"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "ts3", "raw", "2018-11-15", "201811151255111-R433-S00-det433.fits")
    dataIds = [dict(instrument="LSST-TS3", exposure=201811151255111, detector=433)]
    filterLabel = lsst.afw.image.FilterLabel(physical="550CutOn")


class ComCamIngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):

    curatedCalibrationDatasetTypes = ("camera",)
    instrumentClassName = "lsst.obs.lsst.LsstComCam"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "comCam", "raw", "2019-05-30",
                        "3019053000001", "3019053000001-R22-S00-det000.fits")
    dataIds = [dict(instrument="LSSTComCam", exposure=3019053000001, detector=0)]
    filterLabel = lsst.afw.image.FilterLabel(physical="unknown", band="unknown")


class LSSTCamIngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):

    curatedCalibrationDatasetTypes = ("camera",)
    instrumentClassName = "lsst.obs.lsst.LsstCam"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "lsstCam", "raw", "2019-03-19",
                        "3019031900001", "3019031900001-R10-S02-det029.fits")
    dataIds = [dict(instrument="LSSTCam", exposure=3019031900001, detector=29)]
    filterLabel = lsst.afw.image.FilterLabel(physical="unknown", band="unknown")


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
