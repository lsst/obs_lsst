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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
#    N.b. This will be superseded when Butler Gen3 versions camera data.
#
from .ts8 import Ts8Mapper, Ts8ParseTask

__all__ = ["Ts8itlMapper", "Ts8itlParseTask"]


class Ts8itlMapper(Ts8Mapper):
    """The Mapper for the ts8 ITL camera."""
    _cameraName = "ts8itl"


class Ts8itlParseTask(Ts8ParseTask):
    """Parser suitable for ts8 ITL data.
    """

    _mapperClass = Ts8itlMapper
