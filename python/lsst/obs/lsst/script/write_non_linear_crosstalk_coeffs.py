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
import warnings
from scipy.stats import median_abs_deviation

repo = "/sdf/group/rubin/repo/main"
butler = Butler(repo)
registry = butler.registry
camera = butler.get("camera", instrument="LSSTCam", collections=["LSSTCam/calib"])

nsigma_outlier_coeff = 10.0
nsigma_outlier_coeff_sqr = 20.0

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

n_itl = 0
n_e2v = 0
for det in camera:
    if len(det) != len(camera[0]):
        # Skip nAmp=8 detectors which fortunately look fine.
        continue

    if det.getPhysicalType() == "ITL":
        n_itl += 1
    else:
        n_e2v += 1

# Now we aggregate the ITL and E2V crosstalk terms.
itl_matrices = np.zeros((n_itl, 16, 16))
itl_matrices_sqr = np.zeros_like(itl_matrices)
e2v_matrices = np.zeros((n_e2v, 16, 16))
e2v_matrices_sqr = np.zeros_like(e2v_matrices)
itl_det_nums = np.zeros(n_itl, dtype=np.int32)
e2v_det_nums = np.zeros(n_e2v, dtype=np.int32)

itl_index = 0
e2v_index = 0

for det in camera:
    if len(det) != len(camera[0]):
        # Skip nAmp=8 detectors which fortunately look fine.
        continue

    crosstalk = crosstalk_dict[det.getId()]

    if det.getPhysicalType() == "ITL":
        itl_matrices[itl_index, :, :] = crosstalk.coeffs
        itl_matrices_sqr[itl_index, :, :] = crosstalk.coeffsSqr
        # Flag bad values with nans.
        itl_matrices[itl_index, :, :][~crosstalk.coeffValid] = np.nan
        itl_matrices_sqr[itl_index, :, :][~crosstalk.coeffValid] = np.nan
        itl_det_nums[itl_index] = det.getId()
        itl_index += 1
    else:
        e2v_matrices[e2v_index, :, :] = crosstalk.coeffs
        e2v_matrices_sqr[e2v_index, :, :] = crosstalk.coeffsSqr
        e2v_matrices[e2v_index, :, :][~crosstalk.coeffValid] = np.nan
        e2v_matrices_sqr[e2v_index, :, :][~crosstalk.coeffValid] = np.nan
        e2v_det_nums[e2v_index] = det.getId()
        e2v_index += 1

# Compute the median ITL and E2V matrices for "fixups".
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    median_itl_matrix = np.nanmedian(itl_matrices, axis=0)
    median_itl_matrix_sqr = np.nanmedian(itl_matrices_sqr, axis=0)
    median_e2v_matrix = np.nanmedian(e2v_matrices, axis=0)
    median_e2v_matrix_sqr = np.nanmedian(e2v_matrices_sqr, axis=0)

# Fix up any large outliers for the ITL detectors.
nAmp = len(camera[itl_det_nums[0]])
for i in range(nAmp):
    for j in range(nAmp):
        if i == j:
            continue

        med_coeff = median_itl_matrix[i, j]
        sigma_mad_coeff = median_abs_deviation(itl_matrices[:, i, j], scale="normal", nan_policy="omit")

        min_coeff = med_coeff - nsigma_outlier_coeff*sigma_mad_coeff
        max_coeff = med_coeff + nsigma_outlier_coeff*sigma_mad_coeff

        med_coeff_sqr = median_itl_matrix_sqr[i, j]
        sigma_mad_coeff_sqr = median_abs_deviation(
            itl_matrices_sqr[:, i, j],
            scale="normal",
            nan_policy="omit",
        )

        min_coeff_sqr = med_coeff_sqr - nsigma_outlier_coeff_sqr*sigma_mad_coeff_sqr
        max_coeff_sqr = med_coeff_sqr + nsigma_outlier_coeff_sqr*sigma_mad_coeff_sqr

        bad, = np.where(
            (itl_matrices[:, i, j] < min_coeff)
            | (itl_matrices[:, i, j] > max_coeff)
            | (itl_matrices_sqr[:, i, j] < min_coeff_sqr)
            | (itl_matrices_sqr[:, i, j] > max_coeff_sqr)
        )

        if len(bad) > 0:
            for b in itl_det_nums[bad]:
                print(f"Found bad coefficient for detector {b} ({camera[b].getName()}), position ({i}, {j}).")

                crosstalk_dict[b].coeffs[i, j] = med_coeff
                crosstalk_dict[b].coeffsSqr[i, j] = med_coeff_sqr

nAmp = len(camera[e2v_det_nums[0]])
for i in range(nAmp):
    for j in range(nAmp):
        if i == j:
            continue

        med_coeff = median_e2v_matrix[i, j]
        sigma_mad_coeff = median_abs_deviation(e2v_matrices[:, i, j], scale="normal", nan_policy="omit")

        min_coeff = med_coeff - nsigma_outlier_coeff*sigma_mad_coeff
        max_coeff = med_coeff + nsigma_outlier_coeff*sigma_mad_coeff

        med_coeff_sqr = median_e2v_matrix_sqr[i, j]
        sigma_mad_coeff_sqr = median_abs_deviation(
            e2v_matrices_sqr[:, i, j],
            scale="normal",
            nan_policy="omit",
        )

        min_coeff_sqr = med_coeff_sqr - nsigma_outlier_coeff_sqr*sigma_mad_coeff_sqr
        max_coeff_sqr = med_coeff_sqr + nsigma_outlier_coeff_sqr*sigma_mad_coeff_sqr

        bad, = np.where(
            (e2v_matrices[:, i, j] < min_coeff)
            | (e2v_matrices[:, i, j] > max_coeff)
            | (e2v_matrices_sqr[:, i, j] < min_coeff_sqr)
            | (e2v_matrices_sqr[:, i, j] > max_coeff_sqr)
        )

        if len(bad) > 0:
            for b in e2v_det_nums[bad]:
                print(f"Found bad coefficient for detector {b} ({camera[b].getName()}), position ({i}, {j}).")

                crosstalk_dict[b].coeffs[i, j] = med_coeff
                crosstalk_dict[b].coeffsSqr[i, j] = med_coeff_sqr

for detector in camera:
    det_id = detector.getId()
    det_name = detector.getName()

    print("Serializing ", det_id, det_name)

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
