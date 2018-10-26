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
from lsst.daf.persistence import Butler
from lsst.afw.cameraGeom import Camera, Detector
from lsst.afw.image import ImageFitsReader

from lsst.obs.lsst.assembly import fixAmpGeometry

# This should obviously be replaced by something like
# getPackageDir("testdata_auxTel") once we actually have such a package.
AUXTEL_DATA_ROOT = "/project/rhl/Data/ci_lsst/auxTel"
BAD_OVERSCAN_GEN2_DATA_ID = {'dayObs': '2018-09-20', 'seqNum': 49, 'detector': 0}
BAD_OVERSCAN_FILENAME = "raw/2018-09-20/05700049-det000.fits"
LOCAL_DATA_ROOT = os.path.join(os.path.dirname(__file__), "data")


@unittest.skipUnless(os.path.exists(AUXTEL_DATA_ROOT), "{} does not exist".format(AUXTEL_DATA_ROOT))
class RawAssemblyTestCase(lsst.utils.tests.TestCase):

    def setUp(self):
        # A snapshot of AuxTelCam that has incorrect overscan regions for this data ID
        self.cameraBroken = Camera.readFits(os.path.join(LOCAL_DATA_ROOT, "camera-bad-overscan.fits"))
        # A snapshot of the Detector for this file after we've read it in with code that fixes
        # the overscans.
        self.detectorFixed = Detector.readFits(os.path.join(LOCAL_DATA_ROOT, "detector-fixed.fits"))
        self.assertEqual(self.cameraBroken[0].getName(), self.detectorFixed.getName())

    def assertAmpRawBBoxesEqual(self, amp1, amp2):
        self.assertEqual(amp1.getRawBBox(), amp2.getRawBBox())
        self.assertEqual(amp1.getRawHorizontalOverscanBBox(), amp2.getRawHorizontalOverscanBBox())
        self.assertEqual(amp1.getRawVerticalOverscanBBox(), amp2.getRawVerticalOverscanBBox())

    def testGen2GetBadOverscan(self):
        """Test that we can use the Gen2 Butler to rea a file with overscan
        regions that disagree with cameraGeom, and that the detector attached
        to it has its overscan regions corrected.

        This is essentially just a regression test, and an incomplete one at
        that: the fixed Detector snapshot that we're comparing to was generated
        by the same code we're calling here.  And because the AuxTelCam
        associated by the Butler we use in this test may in the future be
        corrected to have the right overscan regions, we may end up just
        testing a simpler case than we intended.  We'll use a snapshot of
        the incorrect Camera in other tests to get coverage of that case.
        """
        butler = Butler(AUXTEL_DATA_ROOT)
        raw = butler.get("raw", dataId=BAD_OVERSCAN_GEN2_DATA_ID)
        for amp1, amp2 in zip(self.detectorFixed, raw.getDetector()):
            with self.subTest(amp=amp1.getName()):
                self.assertEqual(amp1.getName(), amp2.getName())
                self.assertAmpRawBBoxesEqual(amp1, amp2)

    def testFixBadOverscans(self):
        """Test the low-level code for repairing cameraGeom overscan regions
        that disagree with raw files.
        """
        for i, (ampBad, ampGood) in enumerate(zip(self.cameraBroken[0], self.detectorFixed)):
            with self.subTest(amp=ampBad.getName()):
                self.assertEqual(ampBad.getName(), ampGood.getName())
                hdu = i + 1
                self.assertEqual(ampBad.get("hdu"), hdu)
                reader = ImageFitsReader(os.path.join(AUXTEL_DATA_ROOT, BAD_OVERSCAN_FILENAME), hdu=hdu)
                metadata = reader.readMetadata()
                image = reader.read()
                self.assertEqual(ampGood.getRawBBox(), image.getBBox())
                self.assertNotEqual(ampBad.getRawBBox(), image.getBBox())
                modified = fixAmpGeometry(ampBad, image.getBBox(), metadata)
                self.assertTrue(modified)
                #self.assertAmpRawBBoxesEqual(ampBad, ampGood)


if __name__ == "__main__":
    unittest.main()
