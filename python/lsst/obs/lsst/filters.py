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
from .translators.lsst import FILTER_DELIMITER


LSSTCAM_FILTER_DEFINITIONS = FilterDefinitionCollection(
    FilterDefinition(physical_filter="NONE",
                     lambdaEff=0.0,
                     alias={"no_filter", "OPEN"}),
    FilterDefinition(physical_filter="275CutOn",
                     lambdaEff=0.0),
    FilterDefinition(physical_filter="550CutOn",
                     lambdaEff=0.0),
    # Filters for BOT data
    FilterDefinition(physical_filter='480nm+NONE', lambdaEff=0.0),
    FilterDefinition(physical_filter='480nm+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='650nm+NONE', lambdaEff=0.0),
    FilterDefinition(physical_filter='650nm+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='750nm+NONE', lambdaEff=0.0),
    FilterDefinition(physical_filter='750nm+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='870nm+NONE', lambdaEff=0.0),
    FilterDefinition(physical_filter='870nm+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='950nm+NONE', lambdaEff=0.0),
    FilterDefinition(physical_filter='950nm+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='970nm+NONE', lambdaEff=0.0),
    FilterDefinition(physical_filter='970nm+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSu+NONE', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSu+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSu+ND_OD4.0', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSg+NONE', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSg+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSr+NONE', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSr+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSr+ND_OD0.3', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSr+ND_OD0.4', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSr+ND_OD4.0', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSr+ND_OD1.0', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSi+NONE', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSi+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSi+ND_OD0.3', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSi+ND_OD0.5', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSi+ND_OD1.0', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSi+ND_OD2.0', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSi+ND_OD3.0', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSi+ND_OD4.0', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSz+ND_OD3.0', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSz+ND_OD0.1', lambdaEff=0.0),
    FilterDefinition(physical_filter='SDSSY+ND_OD0.1', lambdaEff=0.0),
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

# LATISS filters include a grating in the name so we need to construct
# filters for each combination of filter+grating.
_latiss_filters = (
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
    FilterDefinition(physical_filter="????",
                     lambdaEff=0.0),
    FilterDefinition(physical_filter="BG40",
                     # abstract_filter="g",  # afw only allows one g filter
                     lambdaEff=472.0, lambdaMin=334.5, lambdaMax=609.5),
    FilterDefinition(physical_filter="quadnotch1",
                     lambdaEff=0.0),
    FilterDefinition(physical_filter="RG610",
                     lambdaEff=0.0),
)

# Form a new set of filter definitions from all the explicit filters
_latiss_gratings = ("ronchi90lpmm", "ronchi170lpmm", "EMPTY", "????", "NONE")

# Include the filters without the grating in case someone wants
# to retrieve a filter by an actual filter name
_latiss_filter_and_grating = [f for f in _latiss_filters]

for filter in _latiss_filters:
    for grating in _latiss_gratings:
        # FilterDefinition is a frozen dataclass
        new_name = FILTER_DELIMITER.join([filter.physical_filter, grating])

        # Also need to update aliases
        new_aliases = {FILTER_DELIMITER.join([a, grating]) for a in filter.alias}

        combo = FilterDefinition(physical_filter=new_name,
                                 lambdaEff=filter.lambdaEff,
                                 lambdaMin=filter.lambdaMin,
                                 lambdaMax=filter.lambdaMax,
                                 alias=new_aliases)
        _latiss_filter_and_grating.append(combo)


LATISS_FILTER_DEFINITIONS = FilterDefinitionCollection(*_latiss_filter_and_grating)


LSST_IMSIM_FILTER_DEFINITIONS = FilterDefinitionCollection(
    # These were computed using throughputs 1.4 and
    # lsst.sims.photUtils.BandpassSet.
    FilterDefinition(physical_filter="u_sim_1.4",
                     abstract_filter="u",
                     lambdaEff=367.070, lambdaMin=308.0, lambdaMax=408.6),
    FilterDefinition(physical_filter="g_sim_1.4",
                     abstract_filter="g",
                     lambdaEff=482.685, lambdaMin=386.5, lambdaMax=567.0),
    FilterDefinition(physical_filter="r_sim_1.4",
                     abstract_filter="r",
                     lambdaEff=622.324, lambdaMin=537.0, lambdaMax=706.0),
    FilterDefinition(physical_filter="i_sim_1.4",
                     abstract_filter="i",
                     lambdaEff=754.598, lambdaMin=676.0, lambdaMax=833.0),
    FilterDefinition(physical_filter="z_sim_1.4",
                     abstract_filter="z",
                     lambdaEff=869.090, lambdaMin=803.0, lambdaMax=938.6),
    FilterDefinition(physical_filter="y_sim_1.4",
                     abstract_filter="y",
                     lambdaEff=971.028, lambdaMin=908.4, lambdaMax=1096.3)
)
