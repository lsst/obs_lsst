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

import os
import unittest

import lsst.utils.tests
from lsst.obs.base.gen2to3 import convertTests

testDataPackage = "obs_lsst"
try:
    testDataDirectory = lsst.utils.getPackageDir(testDataPackage)
except LookupError:
    testDataDirectory = None


class ConvertGen2To3TestCase(convertTests.ConvertGen2To3TestCase):
    detectorKey = "detector"
    exposureKey = "expId"
    config = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                          "config", "convert2to3Config.py")

    def setUp(self):
        rawpath = os.path.join(testDataDirectory, f"data/input/{self.instrumentDir}")
        calibpath = os.path.join(testDataDirectory, f"{rawpath}/CALIB")

        self.gen2root = rawpath
        if os.path.exists(calibpath):
            self.gen2calib = calibpath

        super().setUp()
        self.collections.add(f"calib/{self.instrumentName}")


class LatissGen2To3TestCase(ConvertGen2To3TestCase, lsst.utils.tests.TestCase):
    instrumentName = "LATISS"
    instrumentDir = "latiss"
    instrumentClass = "lsst.obs.lsst.Latiss"
    biases = [{"detector": 0, "calibration_label": "gen2/bias_2018-09-21_000",
               "instrument": instrumentName}]


class TS8Gen2To3TestCase(ConvertGen2To3TestCase, lsst.utils.tests.TestCase):

    instrumentName = "LSST-TS8"
    instrumentDir = "ts8"
    instrumentClass = "lsst.obs.lsst.LsstTS8"
    biases = [{"detector": 67, "calibration_label": "gen2/bias_2018-07-24_067",
               "instrument": instrumentName}]


class TS3Gen2To3TestCase(ConvertGen2To3TestCase, lsst.utils.tests.TestCase):

    instrumentName = "LSST-TS3"
    instrumentDir = "ts3"
    instrumentClass = "lsst.obs.lsst.LsstTS3"


class UCDCamGen2To3TestCase(ConvertGen2To3TestCase, lsst.utils.tests.TestCase):

    instrumentName = "LSST-UCDCam"
    instrumentDir = "ucd"
    instrumentClass = "lsst.obs.lsst.LsstUCDCam"


class PhoSimGen2To3TestCase(ConvertGen2To3TestCase, lsst.utils.tests.TestCase):

    instrumentName = "LSST-PhoSim"
    instrumentDir = "phosim"
    instrumentClass = "lsst.obs.lsst.LsstPhoSim"


class ImSimGen2To3TestCase(ConvertGen2To3TestCase, lsst.utils.tests.TestCase):

    instrumentName = "LSST-ImSim"
    instrumentDir = "imsim"
    instrumentClass = "lsst.obs.lsst.LsstImSim"
    biases = [{"detector": 42, "calibration_label": "gen2/bias_2022-01-01_042",
               "instrument": instrumentName}]
    darks = [{"detector": 42, "calibration_label": "gen2/dark_2022-01-01_042",
              "instrument": instrumentName}]
    flats = [{"detector": 42, "calibration_label": "gen2/flat_2022-08-06_042_i",
              "instrument": instrumentName, "physical_filter": "i"}]


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
