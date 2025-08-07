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
import tempfile
import lsst.utils.tests

from lsst.afw.math import flipImage
from lsst.afw.cameraGeom import AmplifierGeometryComparison
from lsst.daf.butler import Butler, DataCoordinate
from lsst.daf.butler.cli.butler import cli as butlerCli
from lsst.daf.butler.cli.utils import LogCliRunner
from lsst.obs.base.ingest_tests import IngestTestBase
from lsst.ip.isr import PhotodiodeCalib, ShutterMotionProfile
import lsst.afw.cameraGeom.testUtils  # for injected test asserts
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

    def checkRepo(self, files=None):
        # Test amp parameter implementation for the LSST raw formatter.  This
        # is the same for all instruments, so repeating it in other test cases
        # is wasteful.
        butler = Butler(self.root, run=self.outputRun)
        ref = butler.find_dataset("raw", self.dataIds[0])
        full_assembled = butler.get(ref)
        unassembled_detector = self.instrumentClass().getCamera()[ref.dataId["detector"]]
        assembled_detector = full_assembled.getDetector()
        for unassembled_amp, assembled_amp in zip(unassembled_detector, assembled_detector):
            # Check that we're testing what we think we're testing: these
            # amps should differ in assembly state (offsets, flips), and they
            # _may_ differ in fundamental geometry if we had to patch the
            # overscan region sizes.
            comparison = unassembled_amp.compareGeometry(assembled_amp)
            self.assertTrue(comparison & AmplifierGeometryComparison.ASSEMBLY_DIFFERS)
            assembled_subimage = butler.get(ref, parameters={"amp": assembled_amp})
            unassembled_subimage = butler.get(ref, parameters={"amp": unassembled_amp.getName()})
            self.assertEqual(len(assembled_subimage.getDetector()), 1)
            self.assertEqual(len(unassembled_subimage.getDetector()), 1)
            self.assertEqual(len(assembled_subimage.getDetector()), 1)
            self.assertEqual(len(unassembled_subimage.getDetector()), 1)
            self.assertImagesEqual(assembled_subimage.image, full_assembled.image[assembled_amp.getRawBBox()])
            self.assertImagesEqual(
                unassembled_subimage.image,
                flipImage(
                    full_assembled.image[assembled_amp.getRawBBox()],
                    flipLR=unassembled_amp.getRawFlipX(),
                    flipTB=unassembled_amp.getRawFlipY(),
                ),
            )
            self.assertAmplifiersEqual(assembled_subimage.getDetector()[0], assembled_amp)
            if comparison & comparison.REGIONS_DIFFER:
                # We needed to patch overscans, but unassembled_amp (which
                # comes straight from the camera) won't have those patches, so
                # we can't compare it to the amp attached to
                # unassembled_subimage (which does have those patches).
                comparison2 = unassembled_subimage.getDetector()[0].compareGeometry(unassembled_amp)

                self.assertTrue(comparison2 & AmplifierGeometryComparison.REGIONS_DIFFER)
                # ...and that unassembled_subimage's amp has the same regions
                # (after accounting for assembly/orientation) as assembled_amp.
                comparison3 = unassembled_subimage.getDetector()[0].compareGeometry(assembled_amp)
                self.assertTrue(comparison3 & AmplifierGeometryComparison.ASSEMBLY_DIFFERS)
                self.assertFalse(comparison3 & AmplifierGeometryComparison.REGIONS_DIFFER)
            else:
                self.assertAmplifiersEqual(unassembled_subimage.getDetector()[0], unassembled_amp)


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


class ComCamSimIngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):

    curatedCalibrationDatasetTypes = ("camera",)
    instrumentClassName = "lsst.obs.lsst.LsstComCamSim"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "comCamSim", "raw", "2024-04-04",
                        "7024040400780", "CC_S_20240404_000780_R22_S01.fits")
    dataIds = [dict(instrument="LSSTComCamSim", exposure=7024040400780, detector=1)]
    filterLabel = lsst.afw.image.FilterLabel(physical="r_03", band="r")

    @property
    def visits(self):
        butler = Butler(self.root, collections=[self.outputRun])
        return {
            DataCoordinate.standardize(
                instrument="LSSTComCamSim",
                visit=7024040400780,
                universe=butler.dimensions
            ): [
                DataCoordinate.standardize(
                    instrument="LSSTComCamSim",
                    exposure=7024040400780,
                    universe=butler.dimensions
                )
            ]
        }


class LSSTCamIngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):

    curatedCalibrationDatasetTypes = ("camera",)
    instrumentClassName = "lsst.obs.lsst.LsstCam"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "lsstCam", "raw", "2019-03-19",
                        "3019031900001", "3019031900001-R10-S02-det029.fits")
    dataIds = [dict(instrument="LSSTCam", exposure=3019031900001, detector=29)]
    filterLabel = lsst.afw.image.FilterLabel(physical="unknown", band="unknown")


class LSSTCamSimIngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):

    curatedCalibrationDatasetTypes = ("camera",)
    instrumentClassName = "lsst.obs.lsst.LsstCamSim"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "lsstCamSim", "raw", "2024-03-21",
                        "7024032100720", "7024032100720-R22-S11-det094.fits.fz")
    dataIds = [dict(instrument="LSSTCamSim", exposure=7024032100720, detector=94)]
    filterLabel = lsst.afw.image.FilterLabel(physical="r_57", band="r")

    @property
    def visits(self):
        butler = Butler(self.root, collections=[self.outputRun])
        return {
            DataCoordinate.standardize(
                instrument="LSSTCamSim",
                visit=7024032100720,
                universe=butler.dimensions
            ): [
                DataCoordinate.standardize(
                    instrument="LSSTCamSim",
                    exposure=7024032100720,
                    universe=butler.dimensions
                )
            ]
        }


class LSSTCamPhotodiodeIngestTestCase(lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.lsst.LsstCam"
    rawIngestTask = "lsst.obs.base.RawIngestTask"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "lsstCam", "raw", "2021-12-12",
                        "30211212000310", "30211212000310-R22-S22-det098.fits")
    dataIds = [dict(instrument="LSSTCam", exposure=3021121200310, detector=98)]
    filterLabel = lsst.afw.image.FilterLabel(physical="SDSSi", band="i")
    pdPath = os.path.join(DATAROOT, "lsstCam", "raw")

    def setUp(self):
        """Setup for lightweight photodiode ingest task.

        This will create the repo and register the instrument.
        """
        self.root = tempfile.mkdtemp(dir=self.ingestDir)

        # Create Repo
        runner = LogCliRunner()
        result = runner.invoke(butlerCli, ["create", self.root])
        self.assertEqual(result.exit_code, 0, f"output: {result.output} exception: {result.exception}")

        # Register Instrument
        runner = LogCliRunner()
        result = runner.invoke(butlerCli, ["register-instrument", self.root, self.instrumentClassName])
        self.assertEqual(result.exit_code, 0, f"output: {result.output} exception: {result.exception}")

    def testPhotodiodeFailure(self):
        """Test ingest to a repo missing exposure information will raise.
        """
        runner = LogCliRunner()
        result = runner.invoke(
            butlerCli,
            [
                "ingest-photodiode",
                self.root,
                self.instrumentClassName,
                self.pdPath,
            ],
        )
        self.assertEqual(result.exit_code, 1, f"output: {result.output} exception: {result.exception}")

    def testPhotodiode(self):
        """Test ingest to a repo with the exposure information will not raise.
        """
        # Ingest raw to provide exposure information.
        outputRun = "raw_ingest_" + self.id()
        runner = LogCliRunner()
        result = runner.invoke(
            butlerCli,
            [
                "ingest-raws",
                self.root,
                self.file,
                "--output-run",
                outputRun,
                "--ingest-task",
                self.rawIngestTask,
            ],
        )
        self.assertEqual(result.exit_code, 0, f"output: {result.output} exception: {result.exception}")

        # Ingest photodiode matching this exposure.
        runner = LogCliRunner()
        result = runner.invoke(
            butlerCli,
            [
                "ingest-photodiode",
                self.root,
                self.instrumentClassName,
                self.pdPath,
            ],
        )
        self.assertEqual(result.exit_code, 0, f"output: {result.output} exception: {result.exception}")

        # Confirm that we can retrieve the ingested photodiode, and
        # that it has the correct type.
        butler = Butler(self.root, run="LSSTCam/calib/photodiode")
        getResult = butler.get('photodiode', dataId=self.dataIds[0])
        self.assertIsInstance(getResult, PhotodiodeCalib)


class LSSTCamShutterMotionIngestTestCase(lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.lsst.LsstCam"
    rawIngestTask = "lsst.obs.base.RawIngestTask"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "lsstCam", "raw", "2021-12-12",
                        "30211212000310", "30211212000310-R22-S22-det098.fits")
    dataIds = [dict(instrument="LSSTCam", exposure=3021121200310, detector=98)]
    filterLabel = lsst.afw.image.FilterLabel(physical="SDSSi", band="i")
    smpPath = os.path.join(DATAROOT, "lsstCam", "raw")

    def setUp(self):
        """Setup for lightweight shutter motion ingest task.

        This will create the repo and register the instrument.
        """
        self.root = tempfile.mkdtemp(dir=self.ingestDir)

        # Create Repo
        runner = LogCliRunner()
        result = runner.invoke(butlerCli, ["create", self.root])
        self.assertEqual(result.exit_code, 0, f"output: {result.output} exception: {result.exception}")

        # Register Instrument
        runner = LogCliRunner()
        result = runner.invoke(butlerCli, ["register-instrument", self.root, self.instrumentClassName])
        self.assertEqual(result.exit_code, 0, f"output: {result.output} exception: {result.exception}")

    def testShutterMotionFailure(self):
        """Test ingest to a repo missing exposure information will raise.
        """
        runner = LogCliRunner()
        result = runner.invoke(
            butlerCli,
            [
                "ingest-shuttermotion",
                self.root,
                self.instrumentClassName,
                self.smpPath,
                "-c",
                "doRaiseOnMissingExposure=True",
            ],
        )
        self.assertEqual(result.exit_code, 1, f"output: {result.output} exception: {result.exception}")

    def testShutterMotion(self):
        """Test ingest to a repo with the exposure information will not raise.
        """
        # Ingest raw to provide exposure information.
        outputRun = "raw_ingest_" + self.id()
        runner = LogCliRunner()
        result = runner.invoke(
            butlerCli,
            [
                "ingest-raws",
                self.root,
                self.file,
                "--output-run",
                outputRun,
                "--ingest-task",
                self.rawIngestTask,
            ],
        )
        self.assertEqual(result.exit_code, 0, f"output: {result.output} exception: {result.exception}")

        # Ingest photodiode matching this exposure.
        runner = LogCliRunner()
        result = runner.invoke(
            butlerCli,
            [
                "ingest-shuttermotion",
                self.root,
                self.instrumentClassName,
                self.smpPath,
                "-c",
                "doRaiseOnMissingExposure=True",
            ],
        )
        self.assertEqual(result.exit_code, 0, f"output: {result.output} exception: {result.exception}")

        # Confirm that we can retrieve the ingested photodiode, and
        # that it has the correct type.
        butler = Butler(self.root, run="LSSTCam/calib/shutterMotion")
        getResult = butler.get('shutterMotionProfileOpen', dataId=self.dataIds[0])
        self.assertIsInstance(getResult, ShutterMotionProfile)


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
