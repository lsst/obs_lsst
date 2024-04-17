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

# PTC in butler query-collections /sdf/group/rubin/repo/main
#  u/snyder18/*crosstalk_analysis*
# PTC for the crosstalk coefficients persisted in the
# u/snyder18/*crosstalk_analysis* collections used below.
butlerPtc = Butler(repo, collections="u/lsstccs/ptc_13144_w_2023_22/20230607T013806Z")

for det_id, detector in enumerate(camera):
    det_name = detector.getName()
    if det_name in [
        "R00_SW0",
        "R00_SW1",
        "R04_SW0",
        "R04_SW1",
        "R40_SW0",
        "R40_SW1",
        "R44_SW0",
        "R44_SW1",
    ]:
        nAmp = 8
        AMP2SEG = {
            1: "C10",
            2: "C11",
            3: "C12",
            4: "C13",
            5: "C14",
            6: "C15",
            7: "C16",
            8: "C17",
        }
    else:
        nAmp = 16
        AMP2SEG = {
            1: "C10",
            2: "C11",
            3: "C12",
            4: "C13",
            5: "C14",
            6: "C15",
            7: "C16",
            8: "C17",
            9: "C07",
            10: "C06",
            11: "C05",
            12: "C04",
            13: "C03",
            14: "C02",
            15: "C01",
            16: "C00",
        }

    cc = CrosstalkCalib(detector=detector, nAmp=nAmp)
    # The coefficients are in two collections
    if det_id < 99:
        run_num = 13198
    else:
        run_num = 13199

    # Crosstalk from A. Snyder (UCDavis, 2024)
    collections = "u/snyder18/{0}/crosstalk_analysis".format(run_num)
    where = "instrument='LSSTCam'" + " and detector={0}".format(det_id)

    data_refs = list(
        registry.queryDatasets("crosstalkResults", collections=collections, where=where)
    )
    # When we take these images the projector illuminates 1/4 of the sensor,
    # but we can only limit the readout to a single raft.
    # So we take 5 images at a specific position, 4 positions to cover
    # the entire sensor and then 9 different sensors.
    # So 180 images, but only 20 are relevant for each sensors,
    # and only 5 are relevant per amplifier.  The rest are filled with NaN.
    c0_matrix = np.full((nAmp, nAmp, 180), np.nan)
    c1_matrix = np.full((nAmp, nAmp, 180), np.nan)
    c0_error = np.full((nAmp, nAmp, 180), np.nan)
    c1_error = np.full((nAmp, nAmp, 180), np.nan)

    for i, ref in enumerate(data_refs):
        crosstalk_results = butler.get(ref)
        for j in range(nAmp):
            target_segment = AMP2SEG[j + 1]
            for k in range(nAmp):
                source_segment = AMP2SEG[k + 1]
                if j == k:
                    c0_matrix[k, j, i] = 0.0
                    c1_matrix[k, j, i] = 0.0
                    continue
                try:
                    this_ct_result = crosstalk_results[det_name][det_name]
                    c0_matrix[k, j, i] = this_ct_result[target_segment][source_segment]["c0"]
                    c1_matrix[k, j, i] = this_ct_result[target_segment][source_segment]["c1"]
                    c0_error[k, j, i] = this_ct_result[target_segment][source_segment]["c0Error"]
                    c1_error[k, j, i] = this_ct_result[target_segment][source_segment]["c1Error"]
                except KeyError:
                    continue

    c0_matrix = np.nanmedian(c0_matrix, axis=2)
    c1_matrix = np.nanmedian(c1_matrix, axis=2)
    c0_error_matrix = np.nanmedian(c0_error, axis=2)
    c1_error_matrix = np.nanmedian(c1_error, axis=2)

    cc.coeffs = c0_matrix
    cc.coeffErr = c0_error_matrix
    cc.coeffsSqr = c1_matrix
    cc.coeffErrSqr = c1_error_matrix

    # PTC gains, to save matrix of gain ratios
    ptc = butlerPtc.get("ptc", instrument="LSSTCam", detector=det_id)
    gain_ratios_matrix = np.full((nAmp, nAmp), np.nan)

    for i in range(nAmp):
        target_segment = AMP2SEG[i + 1]
        for j in range(nAmp):
            source_segment = AMP2SEG[j + 1]
            if i == j:
                gain_ratios_matrix[j, i] = 1.0
                continue
            gain_source = ptc.gain[source_segment]
            gain_target = ptc.gain[target_segment]
            gain_ratios_matrix[j, i] = gain_target / gain_source

    # Units are e-/e-. "e" is the default in crosstalk calib class
    # of ip_isr.
    cc.ampGainRatios = gain_ratios_matrix

    # Save the ecsv files
    valid_start = "1970-01-01T00:00:00"
    valid_date = dateutil.parser.parse(valid_start)
    datestr = "".join(re.split(r"[:-]", valid_date.isoformat()))
    directory = lsst.utils.getPackageDir("obs_lsst_data")
    out_path = os.path.join(directory, "lsstCam", "crosstalk", det_name.lower())
    os.makedirs(out_path, exist_ok=True)
    out_file = os.path.join(out_path, datestr + ".ecsv")

    cc.updateMetadata(
        camera=camera,
        detector=detector,
        setCalibId=True,
        setCalibInfo=True,
        setDate=True,
    )
    cc.writeText(out_file)
