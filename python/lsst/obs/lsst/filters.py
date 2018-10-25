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

import numpy as np

from lsst.afw.image.utils import defineFilter


__all__ = ("FilterDefinition", "getFilterDefinitions")


class FilterDefinition:
    """A temporary stand-in for the afw.image Filter classes used to
    share initialization between Gen2 Mappers and Gen3 Instruments.
    """

    def __init__(self, name, lambdaEff, lambdaMin=np.nan, lambdaMax=np.nan, alias=()):
        self.name = name
        self.lambdaEff = lambdaEff
        self.lambdaMin = lambdaMin
        self.lambdaMax = lambdaMax
        self.alias = alias

    def declare(self):
        """Declare the filter to via afw.image.Filter.
        """
        defineFilter(self.name, lambdaEff=self.lambdaEff,
                     lambdaMin=self.lambdaMin, lambdaMax=self.lambdaMax,
                     alias=self.alias)

    def __str__(self):
        return self.name


def getFilterDefinitions():
    """Return a list of FilterDefinition objects for the main LSST camera.

    The order of the filters matters as their IDs are used to generate at
    least some object IDs (e.g. on coadds) and changing the order will
    invalidate old IDs.
    """
    return [
        FilterDefinition('NONE', 0.0, alias=['no_filter', "OPEN"]),
        FilterDefinition('275CutOn', 0.0, alias=[]),
        FilterDefinition('550CutOn', 0.0, alias=[]),
        # The LSST Filters from L. Jones 04/07/10
        FilterDefinition('u', lambdaEff=364.59, lambdaMin=324.0, lambdaMax=395.0),
        FilterDefinition('g', lambdaEff=476.31, lambdaMin=405.0, lambdaMax=552.0),
        FilterDefinition('r', lambdaEff=619.42, lambdaMin=552.0, lambdaMax=691.0),
        FilterDefinition('i', lambdaEff=752.06, lambdaMin=818.0, lambdaMax=921.0),
        FilterDefinition('z', lambdaEff=866.85, lambdaMin=922.0, lambdaMax=997.0),
        # official y filter
        FilterDefinition('y', lambdaEff=971.68, lambdaMin=975.0, lambdaMax=1075.0, alias=['y4']),
    ]
