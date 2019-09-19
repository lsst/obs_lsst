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
import sys
import unittest

import lsst.utils.tests
from lsst.utils import getPackageDir
from lsst.daf.persistence import Butler
from lsst.afw.cameraGeom import Camera, Detector
from lsst.afw.image import ImageFitsReader
import lsst.obs.base.yamlCamera as yamlCamera

from lsst.obs.lsst.assembly import fixAmpGeometry
from lsst.obs.lsst.utils import readRawFile

PACKAGE_DIR = getPackageDir("obs_lsst")
TESTDIR = os.path.dirname(__file__)
LATISS_DATA_ROOT = os.path.join(PACKAGE_DIR, "data", "input", "latiss")
BAD_OVERSCAN_GEN2_DATA_ID = {'dayObs': '2018-09-20', 'seqNum': 65, 'detector': 0}
BAD_OVERSCAN_FILENAME = "raw/2018-09-20/2018092000065-det000.fits"
LOCAL_DATA_ROOT = os.path.join(TESTDIR, "data")


class RawAssemblyTestCase(lsst.utils.tests.TestCase):

    def setUp(self):
        # A snapshot of LATISS that has incorrect overscan regions for this
        # data ID
        self.cameraBroken = Camera.readFits(os.path.join(LOCAL_DATA_ROOT, "camera-bad-overscan.fits"))
        # A snapshot of the Detector for this file after we've read it in with
        # code that fixes the overscans.
        self.detectorFixed = Detector.readFits(os.path.join(LOCAL_DATA_ROOT, "detector-fixed-assembled.fits"))
        self.assertEqual(self.cameraBroken[0].getName(), self.detectorFixed.getName())

    def assertAmpRawBBoxesEqual(self, amp1, amp2):
        self.assertEqual(amp1.getRawBBox(), amp2.getRawBBox())
        self.assertEqual(amp1.getRawHorizontalOverscanBBox(), amp2.getRawHorizontalOverscanBBox())
        self.assertEqual(amp1.getRawVerticalOverscanBBox(), amp2.getRawVerticalOverscanBBox())

    def testGen2GetBadOverscan(self):
        """Test that we can use the Gen2 Butler to read a file with overscan
        regions that disagree with cameraGeom, and that the detector attached
        to it has its overscan regions corrected.

        This is essentially just a regression test, and an incomplete one at
        that: the fixed Detector snapshot that we're comparing to was generated
        by the same code we're calling here.  And because the LATISS
        associated by the Butler we use in this test may in the future be
        corrected to have the right overscan regions, we may end up just
        testing a simpler case than we intended.  We'll use a snapshot of
        the incorrect Camera in other tests to get coverage of that case.
        """
        butler = Butler(LATISS_DATA_ROOT)
        raw = butler.get("raw", dataId=BAD_OVERSCAN_GEN2_DATA_ID)
        for amp1, amp2 in zip(self.detectorFixed, raw.getDetector()):
            with self.subTest(amp=amp1.getName()):
                self.assertEqual(amp1.getName(), amp2.getName())
                self.assertAmpRawBBoxesEqual(amp1, amp2)

    @unittest.expectedFailure
    def testFixBadOverscans(self):
        """Test the low-level code for repairing cameraGeom overscan regions
        that disagree with raw files.
        """
        testFile = os.path.join(LATISS_DATA_ROOT, BAD_OVERSCAN_FILENAME)
        for i, (ampBad, ampGood) in enumerate(zip(self.cameraBroken[0], self.detectorFixed)):
            with self.subTest(amp=ampBad.getName()):
                self.assertEqual(ampBad.getName(), ampGood.getName())
                hdu = i + 1
                self.assertEqual(ampBad.get("hdu"), hdu)
                reader = ImageFitsReader(testFile, hdu=hdu)
                metadata = reader.readMetadata()
                image = reader.read()
                self.assertEqual(ampGood.getRawBBox(), image.getBBox())
                self.assertNotEqual(ampBad.getRawBBox(), image.getBBox())
                modified = fixAmpGeometry(ampBad, image.getBBox(), metadata)
                self.assertTrue(modified)
                # self.assertAmpRawBBoxesEqual(ampBad, ampGood)


class ReadRawFileTestCase(lsst.utils.tests.TestCase):
    def testReadRawLatissFile(self):
        fileName = os.path.join(LATISS_DATA_ROOT, BAD_OVERSCAN_FILENAME)
        policy = os.path.join(PACKAGE_DIR, "policy", "latiss.yaml")
        camera = yamlCamera.makeCamera(policy)
        exposure = readRawFile(fileName, camera[0], dataId={"file": fileName})
        self.assertIsInstance(exposure, lsst.afw.image.Exposure)
        md = exposure.getMetadata()
        self.assertIn("INSTRUME", md)


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    setup_module(sys.modules[__name__])
    unittest.main()
