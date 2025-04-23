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
from astropy.table import Table, QTable

import lsst.utils
from lsst.meas.algorithms.simple_curve import DetectorCurve

from lsst.obs.base.utils import iso_date_to_curated_calib_file_root

data_dir = lsst.utils.getPackageDir("obs_lsst_data")
subaru_file = "subaru_m1_r_20200219.txt"
valid_start = "1970-01-01T00:00:00"

filename = os.path.join(data_dir, "latiss", "transmission_optics", subaru_file)

subaru_data = Table.read(filename, format="ascii")

wavelength = subaru_data["col1"]
ref = np.mean(
    np.array(subaru_data[["col2", "col3", "col4", "col5", "col6"]]).view("f8").reshape((len(subaru_data), 5)),
    axis=1,
)

# Make sure it's sorted by wavelength.
st = np.argsort(wavelength)

optics_table = QTable(
    {
        "wavelength": np.array(wavelength[st], dtype=np.float64)*u.nanometer,
        "efficiency": ref[st]*u.percent,
    }
)

# Adjust the overall normalization to match AuxTel scans.
optics_table["efficiency"] += 3.5*u.percent

curve = DetectorCurve.fromTable(optics_table)

datestr = iso_date_to_curated_calib_file_root(valid_start)

outfile = os.path.join(data_dir, "latiss", "transmission_optics", datestr + ".ecsv")

optics_table.meta.update(
    {
        "CALIBDATE": valid_start,
        "INSTRUME": "LATISS",
        "OBSTYPE": "transmission_optics",
        "TYPE": "transmission_optics",
        "CALIBCLS": "lsst.ip.isr.IntermediateOpticsTransmissionCurve",
        "SOURCE": subaru_file,
    }
)

optics_table.meta["CALIB_ID"] = (
    f"calibDate={valid_start} filter=None"
)

curve.writeText(outfile)
