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
import astropy.units as u
from astropy.table import Table, QTable
import re
import os
import dateutil.parser
import numpy as np

import lsst.utils
from lsst.meas.algorithms.simple_curve import AmpCurve


data_path = lsst.utils.getPackageDir("obs_lsst_data")
transmission_path = os.path.join(data_path, "lsstCam", "transmission_sensor")
parquet_file = os.path.join(transmission_path, "qe_raft_allvalues_nircorrected_20230725.parquet")

valid_start = "1970-01-01T00:00:00"
valid_date = dateutil.parser.parse(valid_start)
datestr = ''.join(re.split(r'[:-]', valid_date.isoformat()))

data = Table.read(parquet_file)

det_nums = np.unique(data["idet"])

for det_num in det_nums:
    det_use, = np.where((data["idet"] == det_num) & (data["seg"] != "Ave"))
    slot = data["slot"][det_use[0]]
    bay = data["bay"][det_use[0]]

    curve_table = QTable(
        {
            "amp_name": np.array(data["seg"][det_use]),
            "wavelength": np.array(data["wl"][det_use]) * u.nanometer,
            "efficiency": np.array(data["qecorr"][det_use]) * u.percent,
        }
    )
    curve = AmpCurve.fromTable(curve_table)

    out_path = os.path.join(transmission_path, bay.lower() + "_" + slot.lower())
    os.makedirs(out_path, exist_ok=True)

    out_file = os.path.join(out_path, datestr + ".ecsv")

    curve_table.meta.update(
        {
            "CALIBDATE": valid_start,
            "INSTRUME": "LSSTCAM",
            "OBSTYPE": "transmission_sensor",
            "TYPE": "transmission_sensor",
            "DETECTOR": det_num,
            "PARQUETFILE": os.path.basename(parquet_file),
            "CALIBCLS": "lsst.ip.isr.IntermediateSensorTransmissionCurve",
        }
    )
    curve_table.meta["CALIB_ID"] = (
        f"raftName={bay} detectorName={slot} "
        f"detector={det_num} calibDate={valid_start} "
        f"ccd={det_num} ccdnum={det_num} filter=None"
    )

    # We need to remove any previous file if it is there.
    if os.path.isfile(out_file):
        os.remove(out_file)

    curve.writeText(out_file)
