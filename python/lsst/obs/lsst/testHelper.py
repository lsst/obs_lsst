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

"""Test support classes for obs_lsst"""
__all__ = ("ObsLsstButlerTests",)

import os.path
import unittest
import lsst.utils.tests
from lsst.utils import getPackageDir

# Define the data location relative to this package
DATAROOT = os.path.join(getPackageDir("obs_lsst"), "data", "input")


class ObsLsstButlerTests(lsst.utils.tests.TestCase):
    """Base class shared by all tests of the butler and mapper.

    This class can not inherit from `~lsst.obs.base.tests.ObsTests` since
    that will trigger tests in this class directly that will fail.

    This class defines a butler and a mapper for each test subclass.
    They are stored in the ``_mapper`` and ``_butler`` class attributes
    to distinguish them from the ``mapper`` and ``butler`` instance
    attributes used by `~lsst.obs.base.tests.ObsTests`.
    """

    instrumentDir = "TBD"  # Override in subclass
    """Name of instrument directory within data/input."""

    _mapper = None
    _butler = None

    @classmethod
    def tearDownClass(cls):
        del cls._mapper
        del cls._butler

    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.normpath(os.path.join(DATAROOT, cls.instrumentDir))
        # Protection against the base class values being used
        if not os.path.exists(cls.data_dir):
            raise unittest.SkipTest(f"Data directory {cls.data_dir} does not exist.")

        cls._butler = lsst.daf.persistence.Butler(root=cls.data_dir)
        mapper_class = cls._butler.getMapperClass(root=cls.data_dir)
        cls._mapper = mapper_class(root=cls.data_dir)
