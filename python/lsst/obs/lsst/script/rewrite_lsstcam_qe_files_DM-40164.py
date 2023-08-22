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
from scipy.interpolate import interp1d
from scipy.optimize import leastsq
import copy

import lsst.utils
from lsst.meas.algorithms.simple_curve import AmpCurve
import lsst.afw.math


class SplineFitter:
    """Simple spline fitter to adjust rafts.

    Parameters
    ----------
    nodes : `np.ndarray`
        Node wavelengths.
    wavelengths : `np.ndarray`
        Wavelengths (nm).
    throughput_obs : `np.ndarray`
        Observed throughput (questionable raft median).
    throughput_ref : `np.ndarray`
        Reference throughput (good raft median).
    """
    def __init__(self, nodes, wavelengths, throughput_obs, throughput_ref):
        self._nodes = nodes
        self._wavelengths = wavelengths
        self._throughput_obs = throughput_obs
        self._throughput_ref = throughput_ref

    @staticmethod
    def compute_ratio_model(nodes, pars, wls, tput_obs, tput_ref, return_spline=False):
        """Compute the ratio between model and observed.

        Parameters
        ----------
        nodes : `np.ndarray`
            Spline nodes.
        pars : `np.ndarray`
            Spline parameters.
        wls : `np.ndarray`
            Wavelengths.
        tput_obs : `np.ndarray`
            Observed throughput.
        tput_ref : `np.ndarray`
            Reference throughput.
        return_spline : `bool`, optional
            Return spline interpolation object?

        Returns
        -------
        ratio_model : `np.ndarray`
            Ratio between model and observed.
        spl : `lsst.afw.math.thing`
            Spline interpolator (returns if return_spline=True).
        """
        spl = lsst.afw.math.makeInterpolate(
            nodes,
            pars,
            lsst.afw.math.stringToInterpStyle("AKIMA_SPLINE"),
        )

        model = spl.interpolate(wls)
        ratio = (tput_obs * model) / tput_ref

        if return_spline:
            return ratio, spl
        else:
            return ratio

    def fit(self, p0):
        """Fit the spline function.

        Parameters
        ----------
        p0 : `np.ndarray`
            Array of starting parameters.

        Returns
        -------
        pars : `np.ndarray`
            Best fit spline parameters.
        """
        params, cov_params, _, msg, ierr = leastsq(
            self,
            p0,
            full_output=True,
            ftol=1e-5,
            maxfev=12000,
        )

        return params

    def __call__(self, pars):
        """Compute the residuals for leastsq.

        Parameters
        ----------
        pars : `np.ndarray`
            Spline parameters.

        Returns
        -------
        residuals : `np.ndarray`
            Fit residuals.
        """
        ratio_model = self.compute_ratio_model(
            self._nodes,
            pars,
            self._wavelengths,
            self._throughput_obs,
            self._throughput_ref,
        )
        return ratio_model - 1.0


data_path = lsst.utils.getPackageDir("obs_lsst_data")
transmission_path = os.path.join(data_path, "lsstCam", "transmission_sensor")
parquet_file = os.path.join(transmission_path, "qe_raft_allvalues_nircorrected_20230725.parquet")
parquet_file_update = os.path.join(
    transmission_path,
    "qe_raft_allvalues_nircorrected_20230725_adjust.parquet",
)

valid_start = "1970-01-01T00:00:00"
valid_date = dateutil.parser.parse(valid_start)
datestr = ''.join(re.split(r'[:-]', valid_date.isoformat()))

data = Table.read(parquet_file)

# Code to do adjustments of questionable rafts.
questionable_rafts = ["R03", "R11", "R21", "R32", "R42"]

e2v_rafts = ["R11", "R12", "R13", "R14",
             "R21", "R22", "R23", "R24",
             "R30", "R31", "R32", "R33", "R34"]
itl_rafts = ["R01", "R02", "R03",
             "R10",
             "R20",
             "R41", "R42", "R43"]

n_amp_per_det = 16
n_det_per_raft = 9

# Nodes chosen to cover the wavelength range of the QE curve data.
nodes = np.linspace(320.0, 1099.0, 20)

# We will do all fitting at a standardized set of wavelengths.
wavelengths = np.linspace(np.min(nodes), np.max(nodes), 1000)

for det_type in ["e2v", "itl"]:
    if det_type == "e2v":
        rafts = e2v_rafts
    else:
        rafts = itl_rafts

    tput_amps = np.zeros((len(wavelengths), n_amp_per_det*n_det_per_raft*len(rafts)))
    tput_amps[:, :] = np.nan

    counter = 0

    for raft in rafts:
        if raft in questionable_rafts:
            continue

        raft_use, = np.where((data["bay"] == raft) & (data["seg"] != "Ave"))

        det_amps = []
        for row in data[raft_use]:
            det_amps.append(row["bay"] + row["slot"] + row["seg"])
        det_amps = np.array(det_amps)
        unique_det_amps = np.unique(det_amps)

        for i, det_amp in enumerate(unique_det_amps):
            amp_use, = np.where(det_amps == det_amp)

            interp = interp1d(
                data["wl"][raft_use][amp_use],
                data["qecorr"][raft_use][amp_use],
                bounds_error=False,
                fill_value=0.0,
            )
            tput_amps[:, counter] = interp(wavelengths)

            counter += 1

    if det_type == "e2v":
        tput_e2v_median = np.nanmedian(tput_amps, axis=1)
    else:
        tput_itl_median = np.nanmedian(tput_amps, axis=1)

# Compute the median for each questionable raft.
questionable_throughputs = {}

for raft in questionable_rafts:
    counter = 0

    tput_amps = np.zeros((len(wavelengths), n_amp_per_det*n_det_per_raft))

    raft_use, = np.where((data["bay"] == raft) & (data["seg"] != "Ave"))

    det_amps = []
    for row in data[raft_use]:
        det_amps.append(row["bay"] + row["slot"] + row["seg"])
    det_amps = np.array(det_amps)
    unique_det_amps = np.unique(det_amps)

    for i, det_amp in enumerate(unique_det_amps):
        amp_use, = np.where(det_amps == det_amp)

        interp = interp1d(
            data["wl"][raft_use][amp_use],
            data["qecorr"][raft_use][amp_use],
            bounds_error=False,
            fill_value=0.0,
        )
        tput_amps[:, counter] = interp(wavelengths)

        counter += 1

    questionable_throughputs[raft] = np.nanmedian(tput_amps, axis=1)

# For each questionable raft, we want to fit some spline nodes.
questionable_spline_correctors = {}
for raft in questionable_rafts:

    if raft in e2v_rafts:
        throughput_ref = tput_e2v_median
    else:
        throughput_ref = tput_itl_median

    fitter = SplineFitter(nodes, wavelengths, questionable_throughputs[raft], throughput_ref)
    pars = fitter.fit(np.ones(len(nodes)))

    _, spl = fitter.compute_ratio_model(
        nodes,
        pars,
        wavelengths,
        questionable_throughputs[raft],
        throughput_ref,
        return_spline=True,
    )

    questionable_spline_correctors[raft] = spl

det_nums = np.unique(data["idet"])

data_update = copy.copy(data)

for det_num in det_nums:
    det_use, = np.where((data["idet"] == det_num) & (data["seg"] != "Ave"))
    slot = data["slot"][det_use[0]]
    bay = data["bay"][det_use[0]]

    wavelength = np.array(data["wl"][det_use])
    efficiency = np.array(data["qecorr"][det_use])
    if bay in questionable_rafts:
        # Fix this up with spline.
        spl = questionable_spline_correctors[bay]
        efficiency *= spl.interpolate(wavelength)

    data_update["qecorr"][det_use][:] = efficiency

    curve_table = QTable(
        {
            "amp_name": np.array(data["seg"][det_use]),
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

    # And update the average.
    det_use_ave, = np.where((data["idet"] == det_num) & (data["seg"] == "Ave"))
    wavelength_ave = np.array(data["wl"][det_use_ave])
    efficiency_ave = np.array(data["qecorr"][det_use_ave])
    if bay in questionable_rafts:
        spl = questionable_spline_correctors[bay]
        efficiency_ave *= spl.interpolate(wavelength_ave)

    data_update["qecorr"][det_use_ave][:] = efficiency_ave

data_update.write(parquet_file_update, overwrite=True)
