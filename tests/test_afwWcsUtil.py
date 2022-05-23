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

import sys
import unittest
import itertools
import numpy as np

import lsst.utils.tests

import lsst.afw.image
from lsst.obs.base import createInitialSkyWcsFromBoresight
from lsst.obs.lsst import Latiss


class WcsRotationTestCase(lsst.utils.tests.TestCase):
    """A test case for checking angles between wcses."""

    def setUp(self):

        camera = Latiss.getCamera()
        self.assertTrue(len(camera) == 1)
        self.detector = camera[0]

    def test_getAngleBetweenWcs(self):
        ras = [0, 0.1, 1, np.pi/2, np.pi]
        decs = [0, 1, np.pi/2]
        rotAngles1 = [0, 0.01, 45, 90, 180, 270, -10]
        epsilon = 0.5
        rotAngles2 = [r + epsilon for r in rotAngles1]
        flips = [True, False]

        nomPosition = lsst.geom.SpherePoint(1.2, 1.1, lsst.geom.radians)
        for ra, dec, rot1, rot2, flip in itertools.product(ras, decs, rotAngles1, rotAngles2, flips):
            nomRotation = lsst.geom.Angle(rot2, lsst.geom.degrees)
            nominalWcs = createInitialSkyWcsFromBoresight(nomPosition, nomRotation, self.detector, flipX=flip)

            testPoint = lsst.geom.SpherePoint(ra, dec, lsst.geom.radians)
            testRot = lsst.geom.Angle(rot1, lsst.geom.degrees)
            testWcs = createInitialSkyWcsFromBoresight(testPoint, testRot, self.detector, flipX=flip)

            result = nominalWcs.getRelativeRotationToWcs(testWcs).asDegrees()
            test = (rot2 - rot1) % 360
            self.assertAlmostEqual(result, test, 6)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
