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

# This script is a record of a one-time run for DM-49283.
# See obs_lsst_data lsstCam/transmission_sensor/README.md
# for details.

import astropy.units as u
from astropy.table import Table, QTable
import os
import numpy as np

import lsst.utils
from lsst.meas.algorithms.simple_curve import AmpCurve
import lsst.afw.math

from ..utils import valid_start_to_file_root

data_path = lsst.utils.getPackageDir("obs_lsst_data")
transmission_path = os.path.join(data_path, "lsstCam", "transmission_sensor")

# This is the "updated" transmissions from DM-40164.
parquet_file_update = os.path.join(
    transmission_path,
    "qe_raft_allvalues_nircorrected_20230725_adjust.parquet",
)

parquet_file_corr_factors = os.path.join(
    transmission_path,
    "qe_corr_factor_bydetnum.parquet",
)

valid_start = "1970-01-01T00:00:00"
datestr = valid_start_to_file_root(valid_start)

data_update = Table.read(parquet_file_update)

corr_factors = Table.read(parquet_file_corr_factors)

det_nums = np.unique(data_update["idet"])

for det_num in det_nums:
    det_use, = np.where((data_update["idet"] == det_num) & (data_update["seg"] != "Ave"))
    slot = data_update["slot"][det_use[0]]
    # bay is the same as raft.
    bay = data_update["bay"][det_use[0]]

    wavelength = np.asarray(data_update["wl"][det_use])
    efficiency = np.asarray(data_update["qecorr"][det_use])

    corr_factor_index, = np.where(corr_factors["det_num"] == det_num)
    corr_factor = corr_factors["qe_corr_factor"][corr_factor_index[0]]
    efficiency *= corr_factor

    curve_table = QTable(
        {
            "amp_name": np.asarray(data_update["seg"][det_use]),
            "wavelength": wavelength * u.nanometer,
            "efficiency": efficiency * u.percent,
        }
    )
    curve = AmpCurve.fromTable(curve_table)

    out_path = os.path.join(transmission_path, bay.lower() + "_" + slot.lower())
    os.makedirs(out_path, exist_ok=True)

    out_file = os.path.join(out_path, datestr + ".ecsv")

    curve_table.meta.update(
        {
            "CALIBDATE": valid_start,
            "INSTRUME": "LSSTCam",
            "OBSTYPE": "transmission_sensor",
            "TYPE": "transmission_sensor",
            "DETECTOR": det_num,
            "PARQUETFILE": os.path.basename(parquet_file_update),
            "CORRFILE": os.path.basename(parquet_file_corr_factors),
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
