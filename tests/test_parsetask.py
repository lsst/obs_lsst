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

import os.path
import unittest

from lsst.pipe.tasks.ingest import IngestConfig

import lsst.obs.lsst.translators  # noqa: F401 -- register the translators
from lsst.obs.lsst.auxTel import AuxTelParseTask
from lsst.obs.lsst.ts8e2v import Ts8e2vParseTask
from lsst.obs.lsst.phosim import PhosimParseTask
from lsst.obs.lsst.imsim import ImsimParseTask
from lsst.obs.lsst.ucd import UcdParseTask

TESTDIR = os.path.abspath(os.path.dirname(__file__))
ROOTDIR = os.path.normpath(os.path.join(TESTDIR, os.path.pardir))
DATADIR = os.path.join(ROOTDIR, "data", "input")
CONFIGDIR = os.path.join(ROOTDIR, "config")


class LsstCamParseTaskTestCase(unittest.TestCase):

    def assertParseCompare(self, datadir, configdir, name, parseTask, testData):
        """Compare parsed output from headers with expected output.

        Parameters
        ----------
        datadir : `str`
            Name of the data directory to use. This directory must include
            a directory of name ``name``.
        configdir : `str`
            Root of the config directory. This directory must include a
            directory of name ``name``.
        name : `str`
            Name of instrument within data directory and config directory.
        parseTask : `lsst.pipe.tasks.ParseTask`
            Class, not instance, to use to extract information from header.
        testData : `tuple` of `tuple` (`str`, `dict`) pairs.
            Each pair in the tuple defines the file name to read from the
            constructed data directory and a `dict` defining the expected
            results from metadata extraction.

        Raises
        ------
        AssertionError
            If the results differ from the expected values.

        """
        ingestConfig = IngestConfig()
        ingestConfig.load(os.path.join(configdir, "ingest.py"))
        ingestConfig.load(os.path.join(configdir, name, "ingest.py"))
        parser = parseTask(ingestConfig.parse, name=name)
        for fileFragment, expected in testData:
            file = os.path.join(DATADIR, name, fileFragment)
            with self.subTest(f"Testing {file}"):
                phuInfo, infoList = parser.getInfo(file)
                print(f"Name: {file}")
                for k, v in phuInfo.items():
                    print(f"{k}: {v!r}")
                self.assertEqual(phuInfo, expected)

    def test_parsetask_auxtel_translator(self):
        """Run the gen 2 metadata extraction code for AuxTel"""
        test_data = (("raw/2018-09-20/05700065-det000.fits",
                      dict(
                          expTime=27.0,
                          object='UNKNOWN',
                          imageType='UNKNOWN',
                          detectorName='S00',
                          dateObs='2018-09-21T06:12:18.210',
                          date='2018-09-21T06:12:18.210',
                          dayObs='2018-09-20',
                          detector=0,
                          filter='NONE',
                          seqNum=65,
                          visit=20180920000065,
                          wavelength=-666,
                          basename='05700065-det000',
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "auxTel", AuxTelParseTask, test_data)

    def test_parsetask_ts8_translator(self):
        """Run the gen 2 metadata extraction code for TS8"""
        test_data = (("raw/6006D/00270095325-S11-det004.fits",
                      dict(
                          expTime=21.913,
                          object='UNKNOWN',
                          imageType='FLAT',
                          testType='LAMBDA',
                          lsstSerial='E2V-CCD250-179',
                          date='2018-07-24T10:28:45.342',
                          dateObs='2018-07-24T10:28:45.342',
                          run='6006D',
                          wavelength=700,
                          detectorName='S11',
                          detector=4,
                          dayObs='2018-07-24',
                          filter='z',
                          visit=201807241028453,
                          testSeqNum=17,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "ts8e2v", Ts8e2vParseTask, test_data)

    def test_parsetask_imsim_translator(self):
        """Run the gen 2 metadata extraction code for Imsim"""
        test_data = (("raw/204595/R11/00204595-R11-S20-det042-000.fits",
                      dict(
                          expTime=30.0,
                          object='UNKNOWN',
                          imageType='SKYEXP',
                          testType='IMSIM',
                          filter='i',
                          lsstSerial='LCA-11021_RTM-000',
                          date='2022-10-05T06:53:26.357',
                          dateObs='2022-10-05T06:53:26.357',
                          run='204595',
                          visit=204595,
                          wavelength=-666,
                          raftName='R11',
                          detectorName='S20',
                          detector=42,
                          snap=0,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "imsim", ImsimParseTask, test_data)

    def test_parsetask_phosim_translator(self):
        """Run the gen 2 metadata extraction code for Phosim"""
        test_data = (("raw/204595/R11/00204595-R11-S20-det042-000.fits",
                      dict(
                          expTime=30.0,
                          object='UNKNOWN',
                          imageType='SKYEXP',
                          testType='PHOSIM',
                          lsstSerial='R11_S20',
                          date='2022-10-05T06:53:11.357',
                          dateObs='2022-10-05T06:53:11.357',
                          run='204595',
                          wavelength=-666,
                          raftName='R11',
                          detectorName='S20',
                          detector=42,
                          snap=0,
                          filter='i',
                          visit=204595,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "phosim", PhosimParseTask, test_data)

    def test_parsetask_ucd_translator(self):
        """Run the gen 2 metadata extraction code for UCDCam"""
        self.maxDiff = None
        test_data = (("raw/2018-12-05/20181205233148-S00-det000.fits",
                      dict(
                          expTime=0.5,
                          object='UNKNOWN',
                          imageType='FLAT',
                          testType='flat',
                          lsstSerial='E2V-CCD250-112-04',
                          date='2018-12-05T23:31:48.288',
                          dateObs='2018-12-05T23:31:48.288',
                          run='2018-12-05',
                          wavelength=-666,
                          raftName='R00',
                          detectorName='S00',
                          detector=0,
                          dayObs='2018-12-05',
                          filter='r',
                          visit=20181205233148,
                          testSeqNum=100,
                      )),
                     ("raw/2018-05-30/20180530150355-S00-det002.fits",
                      dict(
                          expTime=0.5,
                          object='UNKNOWN',
                          imageType='FLAT',
                          testType='flat',
                          lsstSerial='ITL-3800C-002',
                          date='2018-05-30T15:03:55.872',
                          dateObs='2018-05-30T15:03:55.872',
                          run='2018-05-30',
                          wavelength=-666,
                          raftName='R02',
                          detectorName='S00',
                          detector=2,
                          dayObs='2018-05-30',
                          filter='r',
                          visit=20180530150355,
                          testSeqNum=100,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "ucd", UcdParseTask, test_data)


if __name__ == "__main__":
    unittest.main()
