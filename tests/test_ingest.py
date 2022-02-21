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

from lsst.afw.math import flipImage
from lsst.afw.cameraGeom import AmplifierGeometryComparison
from lsst.daf.butler import Butler
from lsst.daf.butler.cli.butler import cli as butlerCli
from lsst.daf.butler.cli.utils import LogCliRunner
from lsst.obs.base.ingest_tests import IngestTestBase
from lsst.ip.isr import PhotodiodeCalib
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
        ref = butler.registry.findDataset("raw", self.dataIds[0])
        full_assembled = butler.getDirect(ref)
        unassembled_detector = self.instrumentClass().getCamera()[ref.dataId["detector"]]
        assembled_detector = full_assembled.getDetector()
        for unassembled_amp, assembled_amp in zip(unassembled_detector, assembled_detector):
            # Check that we're testing what we think we're testing: these
            # amps should differ in assembly state (offsets, flips), and they
            # _may_ differ in fundamental geometry if we had to patch the
            # overscan region sizes.
            comparison = unassembled_amp.compareGeometry(assembled_amp)
            self.assertTrue(comparison & AmplifierGeometryComparison.ASSEMBLY_DIFFERS)
            assembled_subimage = butler.getDirect(ref, parameters={"amp": assembled_amp})
            unassembled_subimage = butler.getDirect(ref, parameters={"amp": unassembled_amp.getName()})
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


class LSSTCamIngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):

    curatedCalibrationDatasetTypes = ("camera",)
    instrumentClassName = "lsst.obs.lsst.LsstCam"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "lsstCam", "raw", "2019-03-19",
                        "3019031900001", "3019031900001-R10-S02-det029.fits")
    dataIds = [dict(instrument="LSSTCam", exposure=3019031900001, detector=29)]
    filterLabel = lsst.afw.image.FilterLabel(physical="unknown", band="unknown")


class LSSTCamPhotodiodeIngestTestCase(IngestTestBase, lsst.utils.tests.TestCase):

    curatedCalibrationDatasetTypes = ("camera",)
    instrumentClassName = "lsst.obs.lsst.LsstCam"
    ingestDir = TESTDIR
    file = os.path.join(DATAROOT, "lsstCam", "raw", "2021-12-12",
                        "30211212000310", "30211212000310-R22-S22-det098.fits")
    dataIds = [dict(instrument="LSSTCam", exposure=3021121200310, detector=98)]
    filterLabel = lsst.afw.image.FilterLabel(physical="SDSSi", band="i")
    pdPath = os.path.join(DATAROOT, "lsstCam", "raw")

    def testPhotodiode(self, pdPath=None):
        self._ingestRaws("auto")

        if pdPath is None:
            pdPath = self.pdPath
        runner = LogCliRunner()
        result = runner.invoke(
            butlerCli,
            [
                "ingest-photodiode",
                self.root,
                self.instrumentClassName,
                pdPath,
            ],
        )
        self.assertEqual(result.exit_code, 0, f"output: {result.output} exception: {result.exception}")

        butler = Butler(self.root, run="LSSTCam/calib/photodiode")
        getResult = butler.get('photodiode', dataId=self.dataIds[0])
        self.assertIsInstance(getResult, PhotodiodeCalib)


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
