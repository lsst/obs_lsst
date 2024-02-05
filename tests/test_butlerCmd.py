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
    instrumentClassName = "lsst.obs.lsst.LsstComCam"


class TestButlerCmdLsstComCamSim(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.lsst.LsstComCamSim"


class TestButlerCmdLsstCamImSim(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.lsst.LsstCamImSim"


class TestButlerCmdLsstCamPhoSim(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.lsst.LsstCamPhoSim"


class TestButlerCmdLsstTS8(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.lsst.LsstTS8"


class TestButlerCmdLsstUCDCam(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.lsst.LsstUCDCam"


class TestButlerCmdLsstTS3(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.lsst.LsstTS3"


class TestButlerCmdLatiss(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.lsst.Latiss"


class TestMultiple(ButlerCmdTestBase, lsst.utils.tests.TestCase):
    instrumentClassName = "lsst.obs.lsst.Latiss"
    secondInstrumentClassName = "lsst.obs.lsst.LsstTS3"


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    lsst.utils.tests.init()
    unittest.main()
