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
import re
import numpy as np

import astropy.units as u
from astropy.table import QTable
import dateutil.parser
import galsim

import lsst.utils
from lsst.meas.algorithms.simple_curve import DetectorCurve

# Obtain the throughputs of the individual optical components from
# the throughputs package.
throughputs_dir = lsst.utils.getPackageDir("throughputs")

component_files = [
    os.path.join(throughputs_dir, "baseline", _)
    for _ in ("m1.dat", "m2.dat", "m3.dat", "lens1.dat", "lens2.dat", "lens3.dat")
]

# Combine, i.e., multiply, the component contributions to get the
# total optical throughput.
total = np.genfromtxt(component_files[0], names=["wl", "throughput"])
for component_file in component_files[1:]:
    component = np.genfromtxt(component_file, names=["wl", "throughput"])
    total["throughput"] *= component["throughput"]

# Use a GalSim.Bandpass object to truncate the curves at low
# relative throughput and thin the number of wavelength points.
bp = galsim.Bandpass(
    galsim.LookupTable(total["wl"], total["throughput"], interpolant="linear"),
    wave_type="nm",
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
        "OBSTYPE": "transmission_optics",
        "TYPE": "transmission_optics",
        "CALIBCLS": "lsst.ip.isr.IntermediateOpticsTransmissionCurve",
        "SOURCE": "https://github.com/lsst/throughputs",
        "VERSION": 1.9,
    }
)

optics_table.meta["CALIB_ID"] = f"calibDate={valid_start} filter=None"

# Write output transmission_optics file.
valid_date = dateutil.parser.parse(valid_start)
datestr = "".join(re.split(r"[:-]", valid_date.isoformat()))

data_dir = lsst.utils.getPackageDir("obs_lsst_data")
outfile = os.path.join(data_dir, "comCamSim", "transmission_optics", datestr + ".ecsv")
os.makedirs(os.path.dirname(outfile), exist_ok=True)

curve.writeText(outfile)
