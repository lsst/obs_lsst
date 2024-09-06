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
import re
import os
import dateutil.parser
import numpy as np
from lsst.daf.butler import Butler
from lsst.ip.isr import CrosstalkCalib
import lsst.utils

repo = "/sdf/group/rubin/repo/main"
butler = Butler(repo)
registry = butler.registry
camera = butler.get("camera", instrument="LSSTCam", collections=["LSSTCam/calib"])

# PTC RUN collection found via
# butler query-collections /sdf/group/rubin/repo/main
#  u/snyder18/*crosstalk_analysis*

# PTC for the crosstalk coefficients persisted in the
# u/snyder18/13199/crosstalk_analysis/20240406T213728Z and
# u/snyder18/13198/crosstalk_analysis/20240406T214205Z
# collections used below.
butlerPtc = Butler(repo, collections="u/lsstccs/ptc_13144_w_2023_22/20230607T013806Z")

# Use a dictionary keyed by detector id to store raw crosstalks.
crosstalk_dict = {}

for detector in camera:
    det_id = detector.getId()
    det_name = detector.getName()

    print("Working on ", det_id, det_name)

    nAmp = len(detector)

    cc = CrosstalkCalib(nAmp=nAmp)
    # The coefficients are in two collections
    if det_id < 99:
        run_num = 13198
        run_col = "20240406T214205Z"
    else:
        run_num = 13199
        run_col = "20240406T213728Z"

    # Crosstalk from A. Snyder (UCDavis, 2024)
    collections = f"u/snyder18/{run_num}/crosstalk_analysis/{run_col}"
    where = "instrument='LSSTCam'" + f" and detector={det_id}"

    data_refs = list(
        registry.queryDatasets("crosstalkResults", collections=collections, where=where)
    )
    # When we take these images the projector illuminates 1/4 of the sensor,
    # but we can only limit the readout to a single raft.
    # So we take 5 images at a specific position, 4 positions to cover
    # the entire sensor and then 9 different sensors.
    # So 180 images, but only 20 are relevant for each sensors,
    # and only 5 are relevant per amplifier.  The rest are filled with NaN.
    c0_matrix_in = np.full((nAmp, nAmp, 180), np.nan)
    c1_matrix_in = np.full((nAmp, nAmp, 180), np.nan)
    c0_error_in = np.full((nAmp, nAmp, 180), np.nan)
    c1_error_in = np.full((nAmp, nAmp, 180), np.nan)

    for i, ref in enumerate(data_refs):
        crosstalk_results = butler.get(ref)
        for j in range(nAmp):
            target_segment = detector[j].getName()
            for k in range(nAmp):
                source_segment = detector[k].getName()
                if j == k:
                    c0_matrix_in[k, j, i] = 0.0
                    c1_matrix_in[k, j, i] = 0.0
                    continue
                try:
                    this_ct_result = crosstalk_results[det_name][det_name]
                    c0_matrix_in[k, j, i] = this_ct_result[target_segment][source_segment]["c0"]
                    c1_matrix_in[k, j, i] = this_ct_result[target_segment][source_segment]["c1"]
                    c0_error_in[k, j, i] = this_ct_result[target_segment][source_segment]["c0Error"]
                    c1_error_in[k, j, i] = this_ct_result[target_segment][source_segment]["c1Error"]
                except KeyError:
                    continue

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        c0_matrix = np.nanmedian(c0_matrix_in, axis=2)
        c1_matrix = np.nanmedian(c1_matrix_in, axis=2)
        c0_error_matrix = np.nanmedian(c0_error_in, axis=2)
        c1_error_matrix = np.nanmedian(c1_error_in, axis=2)

    coeff_valid_matrix = (
        np.isfinite(c0_matrix)
        & np.isfinite(c1_matrix)
        & np.isfinite(c0_error_matrix)
        & np.isfinite(c1_error_matrix)
    )

    # Set the nans to 0.
    c0_matrix[~coeff_valid_matrix] = 0.0
    c0_error_matrix[~coeff_valid_matrix] = 0.0
    c1_matrix[~coeff_valid_matrix] = 0.0
    c1_error_matrix[~coeff_valid_matrix] = 0.0

    cc.coeffs[:, :] = c0_matrix
    cc.coeffErr[:, :] = c0_error_matrix
    cc.coeffsSqr[:, :] = c1_matrix
    cc.coeffErrSqr[:, :] = c1_error_matrix

    # PTC gains, to save matrix of gain ratios
    ptc = butlerPtc.get("ptc", instrument="LSSTCam", detector=det_id)
    gain_ratios_matrix = np.full((nAmp, nAmp), np.nan)
    # Use this same loop to set the diagonal of the
    # crosstalk matrices to invalid
    coeff_valid_matrix = np.full((nAmp, nAmp), True)
    for i in range(nAmp):
        target_segment = detector[i].getName()
        for j in range(nAmp):
            source_segment = detector[j].getName()
            if i == j:
                gain_ratios_matrix[j, i] = 1.0
                coeff_valid_matrix[j, i] = False
                continue
            gain_source = ptc.gain[source_segment]
            gain_target = ptc.gain[target_segment]
            gain_ratios_matrix[j, i] = gain_target / gain_source

    fit_gains = np.full(nAmp, np.nan)
    for i in range(nAmp):
        fit_gains[i] = ptc.gain[detector[i].getName()]

    # Units are e-/e-.
    cc.crosstalkRatiosUnits = 'electron'
    cc.ampGainRatios[:, :] = gain_ratios_matrix
    cc.coeffValid[:, :] = coeff_valid_matrix
    cc.fitGains[:] = fit_gains

    crosstalk_dict[det_id] = cc


    # Save the ecsv files
    valid_start = "1970-01-01T00:00:00"
    valid_date = dateutil.parser.parse(valid_start)
    datestr = "".join(re.split(r"[:-]", valid_date.isoformat()))
    directory = lsst.utils.getPackageDir("obs_lsst_data")
    out_path = os.path.join(directory, "lsstCam", "crosstalk", det_name.lower())
    os.makedirs(out_path, exist_ok=True)
    out_file = os.path.join(out_path, datestr + ".ecsv")

    cc = crosstalk_dict[det_id]
    cc.hasCrosstalk = True

    cc.updateMetadata(
        camera=camera,
        detector=detector,
        setCalibId=True,
        setCalibInfo=True,
        setDate=True,
    )
    cc.writeText(out_file)
