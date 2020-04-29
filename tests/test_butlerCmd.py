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

"""Tests of the butler cli subcommands LSST instrument classes.
"""

import unittest

import lsst.utils.tests
from lsst.obs.base.cli.butler_cmd_test import ButlerCmdTestBase


class TestButlerCmdLsstComCam(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    def setUp(self):
        self.instrument_class = "lsst.obs.lsst.LsstComCam"
        self.instrument_name = "LSSTComCam"


class TestButlerCmdLsstImSim(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    def setUp(self):
        self.instrument_class = "lsst.obs.lsst.LsstImSim"
        self.instrument_name = "LSST-ImSim"


class TestButlerCmdLsstPhoSim(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    def setUp(self):
        self.instrument_class = "lsst.obs.lsst.LsstPhoSim"
        self.instrument_name = "LSST-PhoSim"


class TestButlerCmdLsstTS8(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    def setUp(self):
        self.instrument_class = "lsst.obs.lsst.LsstTS8"
        self.instrument_name = "LSST-TS8"


class TestButlerCmdLsstUCDCam(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    def setUp(self):
        self.instrument_class = "lsst.obs.lsst.LsstUCDCam"
        self.instrument_name = "LSST-UCDCam"


class TestButlerCmdLsstTS3(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    def setUp(self):
        self.instrument_class = "lsst.obs.lsst.LsstTS3"
        self.instrument_name = "LSST-TS3"


class TestButlerCmdLatiss(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    def setUp(self):
        self.instrument_class = "lsst.obs.lsst.Latiss"
        self.instrument_name = "LATISS"


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    lsst.utils.tests.init()
    unittest.main()
