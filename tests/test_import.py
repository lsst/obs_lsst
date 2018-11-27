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

"""Test that the code in this package can be imported."""

import unittest
import lsst.obs.lsst
import lsst.obs.lsst.auxTel
import lsst.obs.lsst.ts8
import lsst.obs.lsst.ucd
import lsst.obs.lsst.phosim
import lsst.obs.lsst.imsim


class ImportTest(unittest.TestCase):
    def testImport(self):
        self.assertTrue(hasattr(lsst.obs.lsst, "__version__"))


if __name__ == "__main__":
    unittest.main()
