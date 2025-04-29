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
import os
import numpy as np

import astropy.units as u
from astropy.table import QTable
import galsim

import lsst.utils
from lsst.meas.algorithms.simple_curve import DetectorCurve

from lsst.obs.base.utils import iso_date_to_curated_calib_file_root

# Write transmission_filter files for the g, r, i band used
# by LSSTComCamSim.  These are the baseline/filter_[gri].dat
# files in the throughputs package.
throughputs_dir = lsst.utils.getPackageDir("throughputs")
filter_files = [
    os.path.join(throughputs_dir, "baseline", _)
    for _ in ("filter_g.dat", "filter_r.dat", "filter_i.dat")
]
physical_filters = ("g_01", "r_03", "i_06")

for physical_filter, filter_file in zip(physical_filters, filter_files):
    throughput = np.genfromtxt(filter_file).transpose()
    # Use a GalSim.Bandpass object to truncate the curves at low
    # relative throughput and thin the number of wavelength points.
    bp = galsim.Bandpass(
        galsim.LookupTable(*throughput, interpolant="linear"), wave_type="nm"
    )
    bp = bp.truncate(relative_throughput=1e-4)
    bp = bp.thin()

    # Package as a DetectorCurve object.
    optics_table = QTable(
        {
            "wavelength": bp.wave_list * u.nanometer,
            "efficiency": bp(bp.wave_list) * 100.0 * u.percent,
        }
    )
    curve = DetectorCurve.fromTable(optics_table)

    # Set metadata values.
    valid_start = "1970-01-01T00:00:00"
    optics_table.meta.update(
        {
            "CALIBDATE": valid_start,
            "INSTRUME": "comCamSim",
            "OBSTYPE": "transmission_filter",
            "TYPE": "transmission_filter",
            "CALIBCLS": "lsst.ip.isr.IntermediateFilterTransmissionCurve",
            "SOURCE": "https://github.com/lsst/throughputs",
            "FILTER": physical_filter,
            "VERSION": 1.9,
        }
    )

    optics_table.meta["CALIB_ID"] = f"calibDate={valid_start} filter={physical_filter}"

    # Write output transmission_filter file.
    datestr = iso_date_to_curated_calib_file_root(valid_start)

    data_dir = lsst.utils.getPackageDir("obs_lsst_data")
    outfile = os.path.join(
        data_dir, "comCamSim", "transmission_filter", physical_filter, datestr + ".ecsv"
    )
    os.makedirs(os.path.dirname(outfile), exist_ok=True)

    curve.writeText(outfile)
