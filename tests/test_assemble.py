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

import numpy
import os
import sys
import unittest

import lsst.utils.tests
from lsst.utils import getPackageDir
from lsst.daf.butler import Butler
from lsst.afw.cameraGeom import Detector
from lsst.afw.image import ImageFitsReader
import lsst.obs.base.yamlCamera as yamlCamera
from lsst.ip.isr import AssembleCcdTask

from lsst.obs.lsst.utils import readRawFile

PACKAGE_DIR = getPackageDir("obs_lsst")
TESTDIR = os.path.dirname(__file__)
LATISS_DATA_ROOT = os.path.join(PACKAGE_DIR, 'data', 'input', 'latiss')
BOT_DATA_ROOT = os.path.join(TESTDIR, 'data', 'input')
E2V_DATA_ID = {'raft': 'R22', 'name_in_raft': 'S11', 'exposure': 3019103101985, 'instrument': 'LSSTCam'}
ITL_DATA_ID = {'raft': 'R02', 'name_in_raft': 'S02', 'exposure': 3019110102212, 'instrument': 'LSSTCam'}
TESTDATA_ROOT = os.path.join(TESTDIR, "data")


class RawAssemblyTestCase(lsst.utils.tests.TestCase):
    """Test assembly of each of data from each of the two
       manufacturers.  Data come from BOT spot data runs.
       """

    def setUp(self):
        # E2V and ITL detecotrs and expected assembled images
        self.e2v = {'detector': Detector.readFits(os.path.join(TESTDATA_ROOT, 'e2v_detector.fits')),
                    'expected': ImageFitsReader(os.path.join(TESTDATA_ROOT,
                                                             'e2v_expected_assembled.fits.gz'))}
        self.itl = {'detector': Detector.readFits(os.path.join(TESTDATA_ROOT, 'itl_detector.fits')),
                    'expected': ImageFitsReader(os.path.join(TESTDATA_ROOT,
                                                             'itl_expected_assembled.fits.gz'))}
        self.roots = [BOT_DATA_ROOT, BOT_DATA_ROOT]
        self.ids = [E2V_DATA_ID, ITL_DATA_ID]
        self.expecteds = [self.e2v, self.itl]

    def assertAmpRawBBoxesEqual(self, amp1, amp2):
        """Check that Raw bounding boxes match between amps.

        Parameters
        ----------
        amp1 : `~lsst.afw.cameraGeom.Amplifier`
            First amplifier.
        amp2 : `~lsst.afw.cameraGeom.Amplifier`
            Second amplifier.
        """
        self.assertEqual(amp1.getRawBBox(), amp2.getRawBBox())
        self.assertEqual(amp1.getRawHorizontalOverscanBBox(), amp2.getRawHorizontalOverscanBBox())
        self.assertEqual(amp1.getRawVerticalOverscanBBox(), amp2.getRawVerticalOverscanBBox())

    def assertAmpRawBBoxesFlippablyEqual(self, amp1, amp2):
        """Check that amp1 can be self-consistently transformed to match amp2.

        This method compares amplifier bounding boxes by confirming
        that they represent the same segment of the detector image.
        If the offsets or amplifier flips differ between the
        amplifiers, this method will pass even if the raw bounding
        boxes returned by the amplifier accessors are not equal.

        Parameters
        ----------
        amp1 : `~lsst.afw.cameraGeom.Amplifier`
            Amplifier to transform.
        amp2 : `~lsst.afw.cameraGeom.Amplifier`
            Reference amplifier.

        """
        xFlip = amp1.getRawFlipX() ^ amp2.getRawFlipX()
        yFlip = amp1.getRawFlipY() ^ amp2.getRawFlipY()
        XYOffset = amp1.getRawXYOffset() - amp2.getRawXYOffset()

        testRawBox = amp1.getRawBBox()
        testHOSBox = amp1.getRawHorizontalOverscanBBox()
        testVOSBox = amp1.getRawVerticalOverscanBBox()

        if xFlip:
            size = amp1.getRawBBox().getWidth()
            testRawBox.flipLR(size)
            testHOSBox.flipLR(size)
            testVOSBox.flipLR(size)
        if yFlip:
            size = amp1.getRawBBox().getHeight()
            testRawBox.flipTB(size)
            testHOSBox.flipTB(size)
            testVOSBox.flipTB(size)

        testRawBox.shift(XYOffset)
        testHOSBox.shift(XYOffset)
        testVOSBox.shift(XYOffset)

        self.assertEqual(testRawBox, amp2.getRawBBox())
        self.assertEqual(testHOSBox, amp2.getRawHorizontalOverscanBBox())
        self.assertEqual(testVOSBox, amp2.getRawVerticalOverscanBBox())

    def testDetectors(self):
        """Test that the detector returned by the butler is the same
        as the expected one.
        """
        for root, did, expected in zip(self.roots, self.ids, self.expecteds):
            with Butler.from_config(root) as butler:
                raw = butler.get("raw", dataId=did, collections="LSSTCam/raw/all")
                for amp1, amp2 in zip(expected['detector'], raw.getDetector()):
                    with self.subTest(amp=amp1.getName()):
                        self.assertEqual(amp1.getName(), amp2.getName())
                        self.assertAmpRawBBoxesEqual(amp1, amp2)

    def testAssemble(self):
        """Test the assembly of E2V and ITL sensors
        """
        task = AssembleCcdTask()
        # exclude LATISS for this test since we don't have an expected output
        for root, did, expected in zip(self.roots, self.ids, self.expecteds):
            with Butler.from_config(root) as butler:
                raw = butler.get("raw", dataId=did, collections="LSSTCam/raw/all")
                assembled = task.assembleCcd(raw)
                count = numpy.sum(expected['expected'].read().array - assembled.getImage().array)
                self.assertEqual(count, 0)


class ReadRawFileTestCase(lsst.utils.tests.TestCase):
    def testReadRawLatissFile(self):
        fileName = os.path.join(LATISS_DATA_ROOT, "raw/2018-09-20/3018092000065-det000.fits")
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
