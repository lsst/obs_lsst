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
import fitsio

import astropy.units as u
from astropy.table import QTable
import galsim

import lsst.utils
from lsst.meas.algorithms.simple_curve import DetectorCurve
from lsst.obs.lsst import LsstCam

from lsst.obs.base.utils import iso_date_to_curated_calib_file_root

valid_start = "1970-01-01T00:00:00"
datestr = iso_date_to_curated_calib_file_root(valid_start)

lsstcam_instr = LsstCam()
camera = lsstcam_instr.getCamera()

data_path = lsst.utils.getPackageDir("obs_lsst_data")
filter_path = os.path.join(data_path, "lsstCam", "transmission_filter_detector")

# Band to filter name, from lsst.obs.lsst.filters
filter_dict = {
    "u": "u_24",
    "g": "g_6",
    "r": "r_57",
    "i": "i_39",
    "z": "z_20",
    "y": "y_10",
}

for band, physical_filter in filter_dict.items():
    print("Working on ", band)

    # Read in all the filter curves for the science detectors.
    filter_file = os.path.join(filter_path, f"integrated_transmission_materion_{band}band.fits")

    wavelengths = None
    filter_tput_dict = {}
    filter_tput_tot = None
    filter_tput_n = 0

    for detector in camera:
        if detector.getType() != lsst.afw.cameraGeom.DetectorType.SCIENCE:
            continue
        data = fitsio.read(
            filter_file,
            ext=f"filter {band} sensor {detector.getName()}",
        )
        if wavelengths is None:
            wavelengths = data[0]["wavelength"]
            filter_tput_tot = np.zeros_like(wavelengths)

        filter_tput_dict[detector.getName()] = data[0]["integ_transmission"]
        filter_tput_tot += filter_tput_dict[detector.getName()]
        filter_tput_n += 1

    filter_tput_mean = filter_tput_tot / filter_tput_n

    for detector in camera:
        if detector.getName() in filter_tput_dict:
            filter_tput = filter_tput_dict[detector.getName()]
        else:
            # Get a nearby neighbor for the corner rafts.
            raft, _ = detector.getName().split("_")
            if raft == "R00":
                filter_tput = filter_tput_dict["R01_S20"]
            elif raft == "R04":
                filter_tput = filter_tput_dict["R03_S22"]
            elif raft == "R40":
                filter_tput = filter_tput_dict["R41_S00"]
            elif raft == "R44":
                filter_tput = filter_tput_dict["R43_S02"]
            else:
                print("Unknown raft/name ", detector.getName())
                # Put in the average just so there is something there.
                filter_tput = filter_tput_mean

        # Use a GalSim.Bandpass object to truncate the curves at low
        # relative throughput.
        bp = galsim.Bandpass(
            galsim.LookupTable(wavelengths, filter_tput, interpolant="linear"),
            wave_type="nm",
        )
        bp = bp.truncate(relative_throughput=0.0)

        filter_table = QTable(
            {
                "wavelength": wavelengths * u.nanometer,
                "efficiency": bp(wavelengths) * 100.0 * u.percent,
            }
        )

        curve = DetectorCurve.fromTable(filter_table)

        # Set metadata values.
        filter_table.meta.update(
            {
                "CALIBDATE": valid_start,
                "INSTRUME": "LSSTCam",
                "OBSTYPE": "transmission_filter_detector",
                "TYPE": "transmission_filter_detector",
                "CALIBCLS": "lsst.ip.isr.IntermediateFilterDetectorTransmissionCurve",
                "SOURCE": "Materion (DM-46256)",
                "DETECTOR": detector.getId(),
                "FILTER": physical_filter,
            }
        )

        calib_id = f"calibDate={valid_start} filter={physical_filter} detector={detector.getId()}"
        filter_table.meta["CALIB_ID"] = calib_id

        # Write the file.
        out_path = os.path.join(
            lsstcam_instr.getObsDataPackageDir(),
            lsstcam_instr.policyName,
            "transmission_filter_detector",
            detector.getName().lower(),
            physical_filter,
        )
        os.makedirs(out_path, exist_ok=True)
        out_file = os.path.join(out_path, f"{datestr}.ecsv")

        curve.writeText(out_file)
