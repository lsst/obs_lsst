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

"""Test the phosimToRafts.py script in bin.src."""

import unittest
import yaml
import os

import lsst.utils
import lsst.utils.tests

TESTDIR = os.path.abspath(os.path.dirname(__file__))
EXECUTABLEDIR = os.path.normpath(os.path.join(TESTDIR, os.path.pardir, 'bin'))
DATADIR = os.path.normpath(os.path.join(TESTDIR, os.path.pardir, 'data', 'input', 'phosim'))
EXPYAMLDIR = os.path.normpath(os.path.join(TESTDIR, os.path.pardir, 'policy', 'phosim'))


class PhosimToRaftsTestCase(lsst.utils.tests.ExecutablesTestCase):
    """Test the phosimToRafts.py utility script."""
    def testPhosimToRafts(self):
        """Test phosimToRafts.py"""
        self.assertExecutable("phosimToRafts.py",
                              root_dir=EXECUTABLEDIR,
                              args=[DATADIR, "--visit", "204595", "--output_dir", TESTDIR],
                              msg="phosimToRafts.py failed")
        # Read file produced by script above
        with open(os.path.join(TESTDIR, 'R11.yaml')) as fh:
            doc = yaml.load(fh)
        # Read file with expected outputs
        with open(os.path.join(EXPYAMLDIR, 'R11.yaml')) as fh:
            exp_doc = yaml.load(fh)
        # The test data only have the S20 chip
        # Note: as of python 3 the iterator on dicts is not a list, so we need to manually
        # create one since we are deleting entries from the dict.
        for key in list(exp_doc['R11']['amplifiers']):
            if key != 'S20':
                del exp_doc['R11']['amplifiers'][key]
        # Can't compare since the serial depends on how many rafts are in the
        # input repository.  The test repository only has 1.
        for d in (doc, exp_doc):
            del d['R11']['raftSerial']
        self.assertEqual(doc, exp_doc)


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
