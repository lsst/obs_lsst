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

__all__ = ()

from lsst.obs.base import FilterDefinition, FilterDefinitionCollection


LSSTCAM_FILTER_DEFINITIONS = FilterDefinitionCollection(
    FilterDefinition(physical_filter="NONE",
                     lambdaEff=0.0,
                     alias={"no_filter", "OPEN"}),
    FilterDefinition(physical_filter="275CutOn",
                     lambdaEff=0.0),
    FilterDefinition(physical_filter="550CutOn",
                     lambdaEff=0.0),
    # The LSST Filters from L. Jones 04/07/10
    FilterDefinition(physical_filter="u",
                     abstract_filter="u",
                     lambdaEff=364.59, lambdaMin=324.0, lambdaMax=395.0),
    FilterDefinition(physical_filter="g",
                     abstract_filter="g",
                     lambdaEff=476.31, lambdaMin=405.0, lambdaMax=552.0),
    FilterDefinition(physical_filter="r",
                     abstract_filter="r",
                     lambdaEff=619.42, lambdaMin=552.0, lambdaMax=691.0),
    FilterDefinition(physical_filter="i",
                     abstract_filter="i",
                     lambdaEff=752.06, lambdaMin=818.0, lambdaMax=921.0),
    FilterDefinition(physical_filter="z",
                     abstract_filter="z",
                     lambdaEff=866.85, lambdaMin=922.0, lambdaMax=997.0),
    # official y filter
    FilterDefinition(physical_filter="y",
                     abstract_filter="y",
                     lambdaEff=971.68, lambdaMin=975.0, lambdaMax=1075.0, alias=['y4']),
)

LATISS_FILTER_DEFINITIONS = FilterDefinitionCollection(
    FilterDefinition(physical_filter="NONE",
                     lambdaEff=0.0,
                     alias={"no_filter", "OPEN"}),
    FilterDefinition(physical_filter="blank_bk7_wg05",
                     lambdaEff=0.0),
    FilterDefinition(physical_filter="KPNO_1111_436nm",
                     abstract_filter="g",
                     lambdaEff=436.0, lambdaMin=386.0, lambdaMax=486.0),
    FilterDefinition(physical_filter="KPNO_373A_677nm",
                     abstract_filter="r",
                     lambdaEff=677.0, lambdaMin=624.0, lambdaMax=730.0),
    FilterDefinition(physical_filter="KPNO_406_828nm",
                     abstract_filter="z",
                     lambdaEff=828.0, lambdaMin=738.5, lambdaMax=917.5),
    FilterDefinition(physical_filter="diffuser",
                     lambdaEff=0.0),
    FilterDefinition(physical_filter="EMPTY",
                     lambdaEff=0.0),
)
