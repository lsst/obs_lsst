# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np
from astropy.table import Table
import astropy.units as units

from lsst.daf.butler import Butler, DatasetType
import lsst.geom


filter_to_band = {
    "u_02": "u",
    "g_01": "g",
    "r_03": "r",
    "i_06": "i",
    "z_03": "z",
    "y_04": "y",
}

with (
    Butler.from_config(
        "embargo",
        instrument="LSSTComCam",
        collections=[
            "LSSTComCam/runs/DRP/DP1-RC1/w_2025_02/DM-48371",
            "u/erykoff/LSSTComCam/DM-47303/lookuptable",
        ],
    ) as ebutler,
    Butler.from_config(
        "dp1",
        instrument="LSSTComCam",
        writeable=True,
    ) as dbutler,
):
    # Register the new dataset type.
    dataset_type = DatasetType(
        "standard_passband",
        dimensions=["instrument", "band"],
        storageClass="ArrowAstropy",
        universe=dbutler.dimensions,
    )

    _ = dbutler.registry.registerDatasetType(dataset_type)

    # Register the run this will go into.

    output_collection = "LSSTComCam/calib/fgcmcal/DM-48089/standard_passbands"

    _ = dbutler.collections.register(output_collection)

    wavelengths = np.arange(300.0, 1100.5, 0.5)

    for physical_filter, band in filter_to_band.items():
        fsp = ebutler.get("fgcm_standard_passband", physical_filter=physical_filter)

        passband = fsp.sampleAt(lsst.geom.Point2D(0, 0), wavelengths * 10.0)

        passband_table = Table(
            {
                "wavelength": wavelengths * units.nm,
                "throughput": (passband * 100.0) * units.percent,
            },
        )

        print(f"Putting passband for {band} band.")
        dbutler.put(
            passband_table,
            "standard_passband",
            instrument="LSSTComCam",
            band=band,
            run=output_collection,
        )

    # And chain in the collection.
    dbutler.collections.extend_chain(
        "LSSTComCam/calib/fgcmcal",
        output_collection,
    )
