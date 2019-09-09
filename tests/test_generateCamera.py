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

"""Test the generateCamera.py script"""

import unittest
import os
import shutil
from tempfile import mkdtemp

import lsst.utils
import lsst.utils.tests

from lsst.obs.lsst.script.generateCamera import generateCamera, parseYamlOnPath

TESTDIR = os.path.abspath(os.path.dirname(__file__))
POLICYDIR = os.path.normpath(os.path.join(TESTDIR, os.path.pardir, 'policy'))


class PhosimToRaftsTestCase(lsst.utils.tests.ExecutablesTestCase):
    """Test the phosimToRafts.py utility script."""

    def setUp(self):
        self.testdir = mkdtemp(dir=TESTDIR)

    def tearDown(self):
        shutil.rmtree(self.testdir, ignore_errors=True)

    def testGenerateCamera(self):
        """Test with LATISS in a test directory."""
        camera = "testCamera"
        cameraYamlFile = f"{camera}.yaml"
        outfile = os.path.join(self.testdir, cameraYamlFile)
        searchPath = ":".join(os.path.join(POLICYDIR, f) for f in ("latiss", "lsstCam", os.path.curdir))
        generateCamera(outfile, searchPath)
        self.assertTrue(os.path.exists(outfile))

        content = parseYamlOnPath(cameraYamlFile, [self.testdir])
        self.assertEqual(content["name"], "lsstCam")
        self.assertEqual(content["plateScale"], 20.0)

        # Check that some top level keys exist
        for k in ("CCDs", "AMP_E2V", "AMP_ITL", "CCD_ITL", "CCD_E2V", "RAFT_ITL", "RAFT_E2V",
                  "transforms"):
            self.assertIn(k, content)

        with self.assertRaises(RuntimeError):
            generateCamera("test", searchPath)

        with self.assertRaises(FileNotFoundError):
            generateCamera("test.yaml", "latiss:lsstCam:.")


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
