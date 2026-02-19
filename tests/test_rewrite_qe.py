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

"""Test the rewrite_ts8_qe_files.py script in bin.src."""

import unittest
import os
import shutil
import tempfile
import glob

from lsst.obs.lsst.script.rewrite_ts8_qe_files import rewrite_ts8_files
from lsst.ip.isr import IntermediateSensorTransmissionCurve
from lsst.resources import ResourcePath

TESTDIR = os.path.abspath(os.path.dirname(__file__))


class RewriteQeTestCase(unittest.TestCase):
    """Test the rewrite_ts8_qe_files.py utility script."""

    def testRewriteQe(self):
        failed = False
        root = tempfile.mkdtemp(dir=TESTDIR)
        try:
            rewrite_ts8_files(os.path.join(TESTDIR, 'data/qe_test/RaftRun10517.p'),
                              root, '1970-01-01T00:00:00')
            files = glob.glob(os.path.join(root, '*', '19700101T000000.ecsv'))
            self.assertEqual(len(files), 9)
            for f in files:
                curve1 = IntermediateSensorTransmissionCurve.readText(f)

                rel_path = os.path.relpath(f, root)
                with ResourcePath(
                    f"resource://lsst.obs_lsst_data/resources/ts8/transmission_sensor/{rel_path}",
                    forceDirectory=False,
                ).as_local() as expect_file:
                    curve2 = IntermediateSensorTransmissionCurve.readText(expect_file.ospath)

                # These fields are created every time, and therefore
                # differ between the test data and the references.
                curve1.getMetadata().pop('DATE')
                curve1.getMetadata().pop('CALIB_CREATION_DATE')
                curve1.getMetadata().pop('CALIB_CREATION_TIME')

                curve2.getMetadata().pop('DATE')
                curve2.getMetadata().pop('CALIB_CREATION_DATE')
                curve2.getMetadata().pop('CALIB_CREATION_TIME')

                self.assertEqual(curve1, curve2)
        except Exception:
            failed = True
            raise
        finally:
            if failed:
                print(f"Output test data located in {root}")
            else:
                shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
