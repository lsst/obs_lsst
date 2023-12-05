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
    "GENERIC_FILTER_DEFINITIONS",
)

from lsst.obs.base import FilterDefinition, FilterDefinitionCollection
from .translators.lsst import FILTER_DELIMITER


def addFilter(filter_dict, band, physical_filter):
    """Define a filter in filter_dict, to be converted to a Filter later"""

    # index by band but keep distinct physical filters by band
    # since there can be many physical filters for a single band
    if band not in filter_dict:
        filter_dict[band] = {}

    filter_dict[band][physical_filter] = dict(physical_filter=physical_filter,
                                              band=band, alias=[],
                                              )


# Collection to handle the distinct cases where no filter is being used.
NoFilterCollection = FilterDefinitionCollection(
    # For this case, no filter is being used and the optical path to
    # the focal plane is unoccluded.
    FilterDefinition(physical_filter="empty", band="white",
                     alias={"no_filter", "open"}),
    # For this case, all filters are returned to the carousel and the
    # auto-changer partially occludes the focal plane.  See Tony
    # Johnson's comment at https://jira.lsstcorp.org/browse/DM-41675.
    FilterDefinition(physical_filter="NONE", band="white",
                     alias={"no_filter", "open"}),
)

# Generic filters used by PhoSim and UCDCam
LsstCamFiltersGeneric = FilterDefinitionCollection(
    FilterDefinition(physical_filter="u", band="u"),
    FilterDefinition(physical_filter="g", band="g"),
    FilterDefinition(physical_filter="r", band="r"),
    FilterDefinition(physical_filter="i", band="i"),
    FilterDefinition(physical_filter="z", band="z"),
    FilterDefinition(physical_filter="y", band="y"),
)

# The LSST Filters from Tony Johnson, 05/09/2023, in DM-38882.
LsstCamFiltersBaseline = FilterDefinitionCollection(
    FilterDefinition(physical_filter="ph_5", band="white"),  # pinhole filter
    FilterDefinition(physical_filter="ef_43", band="white"),  # "empty" filter
    FilterDefinition(physical_filter="u_24", band="u"),
    FilterDefinition(physical_filter="g_6", band="g"),
    FilterDefinition(physical_filter="r_57", band="r"),
    FilterDefinition(physical_filter="i_39", band="i"),
    FilterDefinition(physical_filter="z_20", band="z"),
    FilterDefinition(physical_filter="y_10", band="y"),
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

# Update from 2023-11-18:
# in DM-41675 Yousuke notes the following update to the BOT filters:
# SpotProjFWheel:  [grid, spot, sparsegrid, streak, ellipses, empty6]

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
    "sparsegrid": "sparsegrid",
    "streak": "streak",
    "ellipses": "ellipses"
}

BOTFilters_dict = {}
for physical_filter, band in BOT_filter_map.items():
    if physical_filter == "empty":
        pass  # Already defined above
    else:
        addFilter(BOTFilters_dict, band, physical_filter)

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

        addFilter(BOTFilters_dict, band=ndband, physical_filter=phys_plus_nd)

BOTFilters = [
    FilterDefinition(band="unknown", physical_filter="unknown"),
]
for band, physical_filters in BOTFilters_dict.items():
    for physical_filter, filter_defn in physical_filters.items():
        BOTFilters.append(FilterDefinition(**filter_defn))

#
# These are the filters used by the CCOB for both TS8 and LSSTCam.
# For the testing of LSSTCam at SLAC, they will be combined with the
# real LSSTCam filters, so we include those combinations in the CCOB
# filter definitions.
#
CCOB_filter_map = {
    "": "white",
    "HIGH": "white",
    "LOW": "white",
    "uv": "u",
    "blue": "g",
    "red": "r",
    "nm750": "i",
    "nm850": "z",
    "nm960": "y",
}

CCOBFilters = []
for lsst_filter_def in (*NoFilterCollection, *LsstCamFiltersBaseline):
    lsstcam_filter = lsst_filter_def.physical_filter
    if lsstcam_filter == "empty":
        lsstcam_filter = ""
    lsstcam_band = lsst_filter_def.band
    for ccob_filter, ccob_band in CCOB_filter_map.items():
        if lsstcam_band != "white" and ccob_band != "white" and band != ccob_band:
            # Skip disallowed filter combinations based on band values.
            continue
        if ccob_filter == "":
            # This would correspond to an entry already in
            # LSSTCamFilterBaseline
            continue
        filters = lsstcam_filter, ccob_filter
        physical_filter = FILTER_DELIMITER.join(filters).strip(FILTER_DELIMITER)
        if lsstcam_band == "white":
            band = ccob_band
        else:
            band = lsstcam_band
        if physical_filter == "":
            physical_filter = "empty"
        CCOBFilters.append(FilterDefinition(band=band, physical_filter=physical_filter))

#
# The filters that we might see in the real LSSTCam (including in SLAC)
#
# Note that the filters we'll use on the sky, LsstCamFiltersBaseline, must
# come first as we're not allocating enough bits in _computeCoaddExposureId
# for all the BOT composite filters (i.e. "u~ND_OD1.0")
#
LSSTCAM_FILTER_DEFINITIONS = FilterDefinitionCollection(
    *NoFilterCollection,
    *LsstCamFiltersBaseline,
    *BOTFilters,
    *CCOBFilters,
)

GENERIC_FILTER_DEFINITIONS = FilterDefinitionCollection(
    *NoFilterCollection,
    *LsstCamFiltersGeneric,
)

#
# Filters in SLAC's Test Stand 3
#
TS3Filters = [
    FilterDefinition(band="unknown", physical_filter="unknown"),
    FilterDefinition(physical_filter="275CutOn"),
    FilterDefinition(physical_filter="550CutOn")]

TS3_FILTER_DEFINITIONS = FilterDefinitionCollection(
    *NoFilterCollection,
    *LsstCamFiltersGeneric,
    *TS3Filters,
)
#
# Filters in SLAC's Test Stand 8
#
TS8Filters = [
    FilterDefinition(band="unknown", physical_filter="unknown"),
    FilterDefinition(physical_filter="275CutOn"),
    FilterDefinition(physical_filter="550CutOn")]

TS8_FILTER_DEFINITIONS = FilterDefinitionCollection(
    *NoFilterCollection,
    *LsstCamFiltersGeneric,
    *LsstCamFiltersBaseline,
    *TS8Filters,
    *BOTFilters,
    *CCOBFilters,
)


# LATISS filters include a grating in the name so we need to construct
# filters for each combination of filter+grating.

# This set of filters can be installed in either the grating or filter wheel,
# so we define them here to avoid duplication.
sdss65mm_filters = [FilterDefinition(physical_filter="SDSSu_65mm",
                                     band="u"),
                    FilterDefinition(physical_filter="SDSSg_65mm",
                                     band="g"),
                    FilterDefinition(physical_filter="SDSSr_65mm",
                                     band="r"),
                    FilterDefinition(physical_filter="SDSSi_65mm",
                                     band="i"),
                    FilterDefinition(physical_filter="SDSSz_65mm",
                                     band="z"),
                    FilterDefinition(physical_filter="SDSSy_65mm",
                                     band="y"),
                    ]

_latiss_filters = (
    FilterDefinition(physical_filter="empty",
                     band="white",
                     alias={"no_filter", "open"}),
    FilterDefinition(physical_filter="blank_bk7_wg05",
                     band="white"),
    FilterDefinition(physical_filter="KPNO_1111_436nm",
                     band="g"),
    FilterDefinition(physical_filter="KPNO_373A_677nm",
                     band="r"),
    FilterDefinition(physical_filter="KPNO_406_828nm",
                     band="z"),
    FilterDefinition(physical_filter="diffuser",
                     band="diffuser"),
    FilterDefinition(physical_filter="unknown",
                     band="unknown"),
    FilterDefinition(physical_filter="BG40",
                     band="g",
                     afw_name="bg"),
    FilterDefinition(physical_filter="BG40_65mm_1",
                     band="g",
                     afw_name="bg"),
    FilterDefinition(physical_filter="BG40_65mm_2",
                     band="g",
                     afw_name="bg"),
    FilterDefinition(physical_filter="quadnotch1",
                     band="notch"),
    FilterDefinition(physical_filter="RG610",
                     band="r",
                     afw_name="rg"),
    FilterDefinition(physical_filter="OG550_65mm_1",
                     band="g",
                     afw_name="bg"),
    FilterDefinition(physical_filter="OG550_65mm_2",
                     band="g",
                     afw_name="bg"),
    FilterDefinition(physical_filter="FELH0600",
                     band="r",
                     afw_name="rg"),
    FilterDefinition(physical_filter="SDSSg",
                     band="g"),
    FilterDefinition(physical_filter="SDSSr",
                     band="r"),
    FilterDefinition(physical_filter="SDSSi",
                     band="i"),
    FilterDefinition(physical_filter="collimator",
                     band="white"),
    FilterDefinition(physical_filter="cyl_lens",
                     band="white"),
    *sdss65mm_filters,
)

# Form a new set of filter definitions from all the explicit gratings, and add
# sdss65mm_filter set.
_latiss_gratings = ("ronchi90lpmm",
                    "ronchi170lpmm",
                    "empty",
                    "unknown",
                    "holo4_003",
                    "blue300lpmm_qn1",
                    "holo4_001",
                    "pinhole_1_1000",
                    "pinhole_1_0500",
                    "pinhole_1_0200",
                    "pinhole_1_0100",
                    "pinhole_2_1_1000",
                    "pinhole_2_1_0500",
                    "pinhole_2_1_0200",
                    "pinhole_2_1_0100",
                    "pinhole_2_2_1000",
                    "pinhole_2_2_0500",
                    "pinhole_2_2_0200",
                    "pinhole_2_2_0100",
                    "pinhole_2_3_1000",
                    "pinhole_2_3_0500",
                    "pinhole_2_3_0200",
                    "pinhole_2_3_0100",
                    "pinhole_2_4_1000",
                    "pinhole_2_4_0500",
                    "pinhole_2_4_0200",
                    "pinhole_2_4_0100",
                    *sdss65mm_filters,
                    )

# Include the filters without the grating in case someone wants
# to retrieve a filter by an actual filter name
_latiss_filter_and_grating = [f for f in _latiss_filters]

for filter in _latiss_filters:
    for grating in _latiss_gratings:
        # The diffuser "filter" was never used with gratings
        # so skip it
        if filter.physical_filter == "diffuser":
            continue

        # If the grating is a FilterDefinition, use the band and alias
        # attributes defined in the grating for the new, combined
        # FilterDefinition. In addition, filter out any combinations that do
        # not use the "empty" filter in combination with a grating that is a
        # FitlerDefintion as we should never combine multiple filters in real
        # observations.
        if isinstance(grating, FilterDefinition):
            if filter.physical_filter != "empty":
                continue

            new_name = FILTER_DELIMITER.join([filter.physical_filter, grating.physical_filter])
            new_aliases = {FILTER_DELIMITER.join([filter.physical_filter, a]) for a in grating.alias}

            combo = FilterDefinition(physical_filter=new_name,
                                     band=grating.band,
                                     afw_name=grating.afw_name,
                                     alias=new_aliases)
        else:
            new_name = FILTER_DELIMITER.join([filter.physical_filter, grating])
            new_aliases = {FILTER_DELIMITER.join([a, grating]) for a in filter.alias}

            combo = FilterDefinition(physical_filter=new_name,
                                     band=filter.band,
                                     afw_name=filter.afw_name,
                                     alias=new_aliases)

        _latiss_filter_and_grating.append(combo)


LATISS_FILTER_DEFINITIONS = FilterDefinitionCollection(*_latiss_filter_and_grating)


LSSTCAM_IMSIM_FILTER_DEFINITIONS = FilterDefinitionCollection(
    # These were computed using throughputs 1.4 and
    # lsst.sims.photUtils.BandpassSet.
    FilterDefinition(physical_filter="u_sim_1.4",
                     band="u"),
    FilterDefinition(physical_filter="g_sim_1.4",
                     band="g"),
    FilterDefinition(physical_filter="r_sim_1.4",
                     band="r"),
    FilterDefinition(physical_filter="i_sim_1.4",
                     band="i"),
    FilterDefinition(physical_filter="z_sim_1.4",
                     band="z"),
    FilterDefinition(physical_filter="y_sim_1.4",
                     band="y"),
    *LsstCamFiltersGeneric,
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

    addFilter(ComCamFilters_dict, band, physical_filter)


ComCamFilters = [
    FilterDefinition(band="white", physical_filter="empty"),
    FilterDefinition(band="unknown", physical_filter="unknown"),
]
for band, physical_filters in ComCamFilters_dict.items():
    for physical_filter, filter_defn in physical_filters.items():
        ComCamFilters.append(FilterDefinition(**filter_defn))

COMCAM_FILTER_DEFINITIONS = FilterDefinitionCollection(
    *ComCamFilters,
)
