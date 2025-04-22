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
from lsst.afw.cameraGeom import DetectorType
from lsst.meas.algorithms.simple_curve import AmpCurve
from astropy.table import QTable

import lsst.utils
from lsst.obs.lsst import LsstComCam, LsstCam

from ..utils import valid_start_to_file_root

comcam_instr = LsstComCam()
comcam_camera = comcam_instr.getCamera()
lsst_camera = LsstCam().getCamera()

data_root = lsst.utils.getPackageDir("obs_lsst_data")

valid_start = "1970-01-01T00:00:00"
datestr = valid_start_to_file_root(valid_start)

# The LSSTComCam focal plane is a raft of ITL sensors, while the LSSTCam
# focal plane is a mix of ITL and E2V sensors. While there are chromatic
# QE variations from sensor to sensor, these are not as large as the
# overall difference between the ITL family and the E2V family of
# sensors. See, e.g., DM-40164. Therefore, the estimated LSSTComCam
# transmission is taken as the average of all of the ITL amplifiers.
transmission_sensor_files = []
for det in lsst_camera:
    if det.getType() != DetectorType.SCIENCE:
        continue
    if det.getPhysicalType() != "ITL":
        # Skip non-ITL detectors.
        continue

    name = det.getName()

    transmission_sensor_files.append(
        os.path.join(data_root, "lsstCam", "transmission_sensor", name.lower(), f"{datestr}.ecsv"),
    )

# Read in the first one to get the size/shape of things.
transmission_sensor0 = AmpCurve.readText(transmission_sensor_files[0])

amp_names = sorted([amp.getName() for amp in comcam_camera[0]])

wavelengths = transmission_sensor0.data[amp_names[0]][0]
efficiencies = np.zeros((len(wavelengths), len(amp_names) * len(transmission_sensor_files)))

counter = 0
for transmission_sensor_file in transmission_sensor_files:
    transmission_sensor = AmpCurve.readText(transmission_sensor_file)
    for amp_name in amp_names:
        wave, eff = transmission_sensor.data[amp_name]
        if len(wave) != len(wavelengths):
            # Ignore this amp which has fewer samples.
            print(f"Skipping file {transmission_sensor_file} amplifier {amp_name}")
            continue
        np.testing.assert_array_almost_equal(np.asarray(wave), np.asarray(wavelengths))

        efficiencies[:, counter] = eff
        counter += 1

print(f"Taking median of transmission from {counter} ITL amplifiers.")

efficiency = np.median(efficiencies[:, : counter], axis=1)*transmission_sensor0.data[amp_names[0]][1].unit

for det in comcam_camera:
    name = det.getName()
    raft, sensor = name.split("_")
    det_num = det.getId()

    curve_table = QTable(
        {
            "amp_name": np.repeat(amp_names, len(wavelengths)),
            "wavelength": np.tile(wavelengths, len(amp_names)),
            "efficiency": np.tile(efficiency, len(amp_names)),
        }
    )

    curve = AmpCurve.fromTable(curve_table)

    out_path = os.path.join(
        comcam_instr.getObsDataPackageDir(),
        comcam_instr.policyName,
        "transmission_sensor",
        name.lower(),
    )
    os.makedirs(out_path, exist_ok=True)
    out_file = os.path.join(out_path, f"{datestr}.ecsv")

    curve_table.meta.update(
        {
            "CALIBDATE": valid_start,
            "INSTRUME": "ComCam",
            "OBSTYPE": "transmission_sensor",
            "TYPE": "transmission_sensor",
            "DETECTOR": det_num,
            "CALIBCLS": "lsst.ip.isr.IntermediateSensorTransmissionCurve",
            "SOURCE": "Median of LSSTCam ITL sensor QE from DM-40164",
        }
    )
    curve_table.meta["CALIB_ID"] = (
        f"raftName={raft} detectorName={name} "
        f"detector={det.getId()} calibDate={valid_start}"
    )

    # We need to remove any previous file if it is there.
    if os.path.isfile(out_file):
        os.remove(out_file)

    curve.writeText(out_file)
