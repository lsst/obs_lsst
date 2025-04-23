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
import warnings
from lsst.afw.cameraGeom import DetectorType
from lsst.ip.isr import CrosstalkCalib
import lsst.utils
from lsst.obs.lsst import LsstComCam, LsstCam

from lsst.obs.base.utils import iso_date_to_curated_calib_file_root

comcam_camera = LsstComCam().getCamera()
lsst_camera = LsstCam().getCamera()

data_root = lsst.utils.getPackageDir("obs_lsst_data")

valid_start = "1970-01-01T00:00:00"
datestr = iso_date_to_curated_calib_file_root(valid_start)

# Get the crosstalk filenames of every ITL detector.
crosstalk_files = []
for det in lsst_camera:
    if det.getType() != DetectorType.SCIENCE:
        continue
    if det.getPhysicalType() != "ITL":
        continue

    name = det.getName()

    crosstalk_files.append(
        os.path.join(data_root, "lsstCam", "crosstalk", name.lower(), f"{datestr}.ecsv"),
    )

# Read in the first one to get the size/shape of things.
crosstalk0 = CrosstalkCalib.readText(crosstalk_files[0])

n_amp = crosstalk0.nAmp

c0_matrices = np.zeros((n_amp, n_amp, len(crosstalk_files)))
c1_matrices = np.zeros_like(c0_matrices)
c0_error_matrices = np.zeros_like(c0_matrices)
c1_error_matrices = np.zeros_like(c0_matrices)
gain_ratio_matrices = np.zeros_like(c0_matrices)

for i, crosstalk_file in enumerate(crosstalk_files):
    crosstalk = CrosstalkCalib.readText(crosstalk_file)

    c0_matrices[:, :, i] = crosstalk.coeffs
    c1_matrices[:, :, i] = crosstalk.coeffsSqr
    c0_error_matrices[:, :, i] = crosstalk.coeffErr
    c1_error_matrices[:, :, i] = crosstalk.coeffErrSqr
    gain_ratio_matrices[:, :, i] = crosstalk.ampGainRatios

c0_matrix = np.nanmedian(c0_matrices, axis=2)
c1_matrix = np.nanmedian(c1_matrices, axis=2)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    c0_error_matrix = np.nanmedian(c0_error_matrices, axis=2)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    c1_error_matrix = np.nanmedian(c1_error_matrices, axis=2)
gain_ratio_matrix = np.nanmedian(gain_ratio_matrices, axis=2)

# The diagonal elements have no error.
c0_error_matrix[np.diag_indices(n_amp)] = 0.0
c1_error_matrix[np.diag_indices(n_amp)] = 0.0

for det in comcam_camera:
    name = det.getName()
    raft, sensor = name.split("_")

    comcam_crosstalk = CrosstalkCalib(nAmp=n_amp)
    comcam_crosstalk.coeffs = c0_matrix
    comcam_crosstalk.coeffErr = c0_error_matrix
    comcam_crosstalk.coeffsSqr = c1_matrix
    comcam_crosstalk.coeffErrSqr = c1_error_matrix
    comcam_crosstalk.ampGainRatios = gain_ratio_matrix
    comcam_crosstalk.crosstalkRatiosUnits = "electron"
    comcam_crosstalk.coeffValid = np.ones((n_amp, n_amp), dtype=np.bool_)
    comcam_crosstalk.hasCrosstalk = True

    out_path = os.path.join(data_root, "comCam", "crosstalk", name.lower())
    os.makedirs(out_path, exist_ok=True)
    out_file = os.path.join(out_path, f"{datestr}.ecsv")

    comcam_crosstalk.updateMetadata(
        camera=comcam_camera,
        detector=det,
        setCalibId=True,
        setCalibInfo=True,
        CALIBDATE=valid_start,
    )

    # Update with the full ID.
    metadata = comcam_crosstalk.getMetadata()
    metadata["CALIB_ID"] = (
        f"raftName={raft} detectorName={name} "
        f"detector={det.getId()} calibDate={valid_start}"
    )

    comcam_crosstalk.writeText(out_file)
