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

__all__ = (
    "LSSTCAM_FILTER_DEFINITIONS",
    "LATISS_FILTER_DEFINITIONS",
    "LSSTCAM_IMSIM_FILTER_DEFINITIONS",
    "TS3_FILTER_DEFINITIONS",
    "TS8_FILTER_DEFINITIONS",
    "COMCAM_FILTER_DEFINITIONS",
)

import re
from lsst.obs.base import FilterDefinition, FilterDefinitionCollection
from .translators.lsst import FILTER_DELIMITER


def addFilter(filter_dict, band, physical_filter, lambdaEff=0.0):
    """Define a filter in filter_dict, to be converted to a Filter later"""

    # index by band but keep distinct physical filters by band
    # since there can be many physical filters for a single band
    if band not in filter_dict:
        filter_dict[band] = {}

    filter_dict[band][physical_filter] = dict(physical_filter=physical_filter,
                                              band=band, lambdaEff=lambdaEff, alias=[],
                                              )


# The LSST Filters from L. Jones 05/14/2020 - "Edges" = 5% of peak throughput
# See https://github.com/rhiannonlynne/notebooks/blob/master/Filter%20Characteristics.ipynb # noqa: W505
#
# N.b. DM-26623 requests that these physical names be updated once
# the camera team has decided upon the final values (CAP-617)

LsstCamFiltersBaseline = FilterDefinitionCollection(
    FilterDefinition(physical_filter="empty", band="white",
                     lambdaEff=0.0,
                     alias={"no_filter", "open"}),
    FilterDefinition(physical_filter="u", band="u",
                     lambdaEff=368.48, lambdaMin=320.00, lambdaMax=408.60),
    FilterDefinition(physical_filter="g", band="g",
                     lambdaEff=480.20, lambdaMin=386.40, lambdaMax=567.00),
    FilterDefinition(physical_filter="r", band="r",
                     lambdaEff=623.12, lambdaMin=537.00, lambdaMax=706.00),
    FilterDefinition(physical_filter="i", band="i",
                     lambdaEff=754.17, lambdaMin=676.00, lambdaMax=833.00),
    FilterDefinition(physical_filter="z", band="z",
                     lambdaEff=869.05, lambdaMin=803.00, lambdaMax=938.60),
    FilterDefinition(physical_filter="y", band="y",
                     lambdaEff=973.64, lambdaMin=908.40, lambdaMax=1099.00),
)

#
# Define the filters present in the BOT.
# According to Tony Johnson the possible physical filters are
#   ColorFWheel    [SDSSu,SDSSg,SDSSr,SDSSi,SDSSz,SDSSY,
#                   480nm,650nm,750nm,870nm,950nm,970nm]
#   SpotProjFWheel [grid,spot,empty3,empty4,empty5,empty6]
#   NeutralFWheel  [ND_OD1.0,ND_OD0.5,ND_OD0.3,empty,ND_OD2.0,ND_OD0.7]
# where:
#   ColorFWheel and SpotProjFWheel are mutually exclusive and
#                                            both appear in FILTER,
#   NeutralFWheel appears in FILTER2
#
# Experimentally we also see FILTER2 values of:
#    ['ND_OD0.01', 'ND_OD0.05', 'ND_OD0.4', 'ND_OD3.0', 'ND_OD4.0']
#
# The band names are not yet defined, so I'm going to invent them

# Map the BOT filters to corresponding band explicitly
BOT_filter_map = {
    "empty": "white",
    "SDSSu": "u",
    "SDSSg": "g",
    "SDSSr": "r",
    "SDSSi": "i",
    "SDSSz": "z",
    "SDSSY": "y",
    "480nm": "g",
    "650nm": "r",
    "750nm": "i",
    "870nm": "z",
    "950nm": "y",
    "970nm": "y",
    "grid": "grid",
    "spot": "spot",
}

BOTFilters_dict = {}
for physical_filter, band in BOT_filter_map.items():
    lambdaEff = 0.0
    lsstCamFilterMatches = [f for f in LsstCamFiltersBaseline if f.band == band]
    if lsstCamFilterMatches:
        lambdaEff = lsstCamFilterMatches[0].lambdaEff

    if mat := re.match(r"(\d+)nm$", physical_filter):
        lambdaEff = float(mat.group(1))

    if physical_filter == "empty":
        pass  # Already defined above
    else:
        addFilter(BOTFilters_dict, band, physical_filter, lambdaEff=lambdaEff)

    # Empty ND is removed by metadata translator so is not needed here
    ndFilters = ["ND_OD0.1", "ND_OD0.3", "ND_OD0.5", "ND_OD0.7", "ND_OD1.0", "ND_OD2.0"]
    # We found these additional filters in BOT data files:
    ndFilters += ['ND_OD0.01', 'ND_OD0.05', 'ND_OD0.4', 'ND_OD3.0', 'ND_OD4.0']

    for nd in ndFilters:
        # fully qualified physical filter
        phys_plus_nd = f"{physical_filter}{FILTER_DELIMITER}{nd}"

        # When one of the filters is empty we can just use the real filter
        # (e.g. "u" not "u~empty");  but we always need at least one "empty"
        if band == "white":
            # Use the ND on its own
            phys_plus_nd = nd

        # Use a generic ND modifier for the band
        ndband = f"{band}{FILTER_DELIMITER}nd"

        addFilter(BOTFilters_dict, band=ndband, physical_filter=phys_plus_nd, lambdaEff=lambdaEff)

BOTFilters = [
    FilterDefinition(band="unknown", physical_filter="unknown", lambdaEff=0.0),
]
for band, physical_filters in BOTFilters_dict.items():
    for physical_filter, filter_defn in physical_filters.items():
        BOTFilters.append(FilterDefinition(**filter_defn))

#
# The filters that we might see in the real LSSTCam (including in SLAC)
#
# Note that the filters we'll use on the sky, LsstCamFiltersBaseline, must
# come first as we're not allocating enough bits in _computeCoaddExposureId
# for all the BOT composite filters (i.e. "u~ND_OD1.0")
#
LSSTCAM_FILTER_DEFINITIONS = FilterDefinitionCollection(
    *LsstCamFiltersBaseline,
    *BOTFilters,
)

#
# Filters in SLAC's Test Stand 3
#
TS3Filters = [
    FilterDefinition(band="unknown", physical_filter="unknown", lambdaEff=0.0),
    FilterDefinition(physical_filter="275CutOn", lambdaEff=0.0),
    FilterDefinition(physical_filter="550CutOn", lambdaEff=0.0)]

TS3_FILTER_DEFINITIONS = FilterDefinitionCollection(
    *LsstCamFiltersBaseline,
    *TS3Filters,
)
#
# Filters in SLAC's Test Stand 8
#
TS8Filters = [
    FilterDefinition(band="unknown", physical_filter="unknown", lambdaEff=0.0),
    FilterDefinition(physical_filter="275CutOn", lambdaEff=0.0),
    FilterDefinition(physical_filter="550CutOn", lambdaEff=0.0)]

TS8_FILTER_DEFINITIONS = FilterDefinitionCollection(
    *LsstCamFiltersBaseline,
    *TS8Filters,
)


# LATISS filters include a grating in the name so we need to construct
# filters for each combination of filter+grating.
_latiss_filters = (
    FilterDefinition(physical_filter="empty",
                     band="white",
                     lambdaEff=0.0,
                     alias={"no_filter", "open"}),
    FilterDefinition(physical_filter="blank_bk7_wg05",
                     band="white",
                     lambdaEff=0.0),
    FilterDefinition(physical_filter="KPNO_1111_436nm",
                     band="g",
                     lambdaEff=436.0, lambdaMin=386.0, lambdaMax=486.0),
    FilterDefinition(physical_filter="KPNO_373A_677nm",
                     band="r",
                     lambdaEff=677.0, lambdaMin=624.0, lambdaMax=730.0),
    FilterDefinition(physical_filter="KPNO_406_828nm",
                     band="z",
                     lambdaEff=828.0, lambdaMin=738.5, lambdaMax=917.5),
    FilterDefinition(physical_filter="diffuser",
                     band="diffuser",
                     lambdaEff=0.0),
    FilterDefinition(physical_filter="unknown",
                     band="unknown",
                     lambdaEff=0.0),
    FilterDefinition(physical_filter="BG40",
                     band="g",
                     afw_name="bg",
                     lambdaEff=472.0, lambdaMin=334.5, lambdaMax=609.5),
    FilterDefinition(physical_filter="quadnotch1",
                     lambdaEff=0.0,
                     band="notch"),
    FilterDefinition(physical_filter="RG610",
                     lambdaEff=0.0,
                     band="r",
                     afw_name="rg"),
)

# Form a new set of filter definitions from all the explicit filters
_latiss_gratings = ("ronchi90lpmm", "ronchi170lpmm", "empty", "unknown")

# Include the filters without the grating in case someone wants
# to retrieve a filter by an actual filter name
_latiss_filter_and_grating = [f for f in _latiss_filters]

for filter in _latiss_filters:
    for grating in _latiss_gratings:
        # The diffuser "filter" was never used with gratings
        # so skip it
        if filter.physical_filter == "diffuser":
            continue

        # FilterDefinition is a frozen dataclass
        new_name = FILTER_DELIMITER.join([filter.physical_filter, grating])

        # Also need to update aliases
        new_aliases = {FILTER_DELIMITER.join([a, grating]) for a in filter.alias}

        # For gratings set the band to the band of the filter
        combo = FilterDefinition(physical_filter=new_name,
                                 band=filter.band,
                                 lambdaEff=filter.lambdaEff,
                                 lambdaMin=filter.lambdaMin,
                                 lambdaMax=filter.lambdaMax,
                                 afw_name=filter.afw_name,
                                 alias=new_aliases)
        _latiss_filter_and_grating.append(combo)


LATISS_FILTER_DEFINITIONS = FilterDefinitionCollection(*_latiss_filter_and_grating)


LSSTCAM_IMSIM_FILTER_DEFINITIONS = FilterDefinitionCollection(
    # These were computed using throughputs 1.4 and
    # lsst.sims.photUtils.BandpassSet.
    FilterDefinition(physical_filter="u_sim_1.4",
                     band="u",
                     lambdaEff=367.070, lambdaMin=308.0, lambdaMax=408.6),
    FilterDefinition(physical_filter="g_sim_1.4",
                     band="g",
                     lambdaEff=482.685, lambdaMin=386.5, lambdaMax=567.0),
    FilterDefinition(physical_filter="r_sim_1.4",
                     band="r",
                     lambdaEff=622.324, lambdaMin=537.0, lambdaMax=706.0),
    FilterDefinition(physical_filter="i_sim_1.4",
                     band="i",
                     lambdaEff=754.598, lambdaMin=676.0, lambdaMax=833.0),
    FilterDefinition(physical_filter="z_sim_1.4",
                     band="z",
                     lambdaEff=869.090, lambdaMin=803.0, lambdaMax=938.6),
    FilterDefinition(physical_filter="y_sim_1.4",
                     band="y",
                     lambdaEff=971.028, lambdaMin=908.4, lambdaMax=1096.3)
)

# ###########################################################################
#
# ComCam
#
# See https://jira.lsstcorp.org/browse/DM-21706

ComCamFilters_dict = {}
for band, sn in [("u", "SN-05"),  # incorrect sub thickness
                 ("u", "SN-02"),  # not yet coated
                 ("u", "SN-06"),  # not yet coated
                 ("g", "SN-07"),  # bad cosmetics
                 ("g", "SN-01"),
                 ("r", "SN-03"),
                 ("i", "SN-06"),
                 ("z", "SN-03"),
                 ("z", "SN-02"),  # failed specs
                 ("y", "SN-04"),
                 ]:
    physical_filter = f"{band}_{sn[3:]}"
    lsstCamFilter = [f for f in LsstCamFiltersBaseline if f.band == band][0]
    lambdaEff = lsstCamFilter.lambdaEff

    addFilter(ComCamFilters_dict, band, physical_filter, lambdaEff=lambdaEff)


ComCamFilters = [
    FilterDefinition(band="white", physical_filter="empty", lambdaEff=0.0),
    FilterDefinition(band="unknown", physical_filter="unknown", lambdaEff=0.0),
]
for band, physical_filters in ComCamFilters_dict.items():
    for physical_filter, filter_defn in physical_filters.items():
        ComCamFilters.append(FilterDefinition(**filter_defn))

COMCAM_FILTER_DEFINITIONS = FilterDefinitionCollection(
    *ComCamFilters,
)
