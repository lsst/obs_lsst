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

from lsst.ip.isr import Defects
from lsst.geom import Box2I, Point2I, Extent2I
import lsst.utils
from lsst.obs.lsst import LsstCam

from lsst.obs.base.utils import iso_date_to_curated_calib_file_root

camera = LsstCam().getCamera()

data_root = lsst.utils.getPackageDir("obs_lsst_data")

valid_start = "1970-01-01T00:00:00"
datestr = iso_date_to_curated_calib_file_root(valid_start)

total_masked_pixels = 0

for det in camera:
    print("Building manual defects from detector ", det.getName(), det.getId())
    name = det.getName()
    raft, sensor = name.split("_")

    out_path = os.path.join(data_root, "lsstCam", "manual_defects", name.lower())
    os.makedirs(out_path, exist_ok=True)
    out_file = os.path.join(out_path, f"{datestr}.ecsv")

    if os.path.isfile(out_file):
        os.remove(out_file)

    box_xywh = []

    if det.getId() == 0:
        box_xywh.extend(
            (
                # Scratch on detector.
                (2300, 0, 200, 4000),
                # Edge bleed regions.
                (2036, 0, 509, 100),
                (2036, 3900, 509, 100),
            ),
        )
    elif det.getId() == 9:
        box_xywh.extend(
            (
                # Ardenti negans imperfecta
                (2900, 2000, 10, 1142),
                (3071, 2000, 7, 690),
            ),
        )
    elif det.getId() == 15:
        box_xywh.extend(
            (
                # Arcanum columnae
                (2086, 2000, 12, 2000),
            ),
        )
    elif det.getId() == 24:
        box_xywh.extend(
            (
                # Ardenti negans
                (1097, 2000, 15, 2000),
            ),
        )
    elif det.getId() == 25:
        box_xywh.extend(
            (
                # Negativa affirmativa
                (1241, 0, 2, 2000),
            ),
        )
    elif det.getId() == 34:
        box_xywh.extend(
            (
                # Arcanum columnae
                (3026, 0, 11, 3355),
            ),
        )
    elif det.getId() == 52:
        box_xywh.extend(
            (
                # Ardenti negans imperfecta
                (1329, 2000, 9, 1590),
            ),
        )
    elif det.getId() == 67:
        box_xywh.extend(
            (
                # Ardenti negans
                (3753, 2000, 30, 2000),
                # Ardenti negans imperfecta
                (407, 1480, 11, 520),
            ),
        )
    elif det.getId() == 76:
        box_xywh.extend(
            (
                # Negativa affirmativa
                (3346, 2000, 4, 2000),
            ),
        )
    elif det.getId() == 83:
        box_xywh.extend(
            (
                # Negativa affirmativa
                (1425, 0, 2, 2000),
            ),
        )
    elif det.getId() == 90:
        box_xywh.extend(
            (
                # Ardenti negans
                (3031, 0, 21, 2000),
            ),
        )
    elif det.getId() == 105:
        box_xywh.extend(
            (
                # Ardenti negans
                (629, 2000, 21, 2000),
            ),
        )
    elif det.getId() == 116:
        box_xywh.extend(
            (
                # Thermometrum vestigium
                (2380, 0, 4, 2000),
                (2374, 450, 15, 15),
                (2397, 0, 2, 2000),
            ),
        )
    elif det.getId() == 117:
        box_xywh.extend(
            (
                # Ardenti negans imperfecta
                (2585, 1640, 10, 360),
                (2590, 0, 1, 2000),
            ),
        )
    elif det.getId() == 127:
        box_xywh.extend(
            (
                # Ardenti negans imperfecta
                (2840, 482, 13, 1518),
            ),
        )
    elif det.getId() == 128:
        box_xywh.extend(
            (
                # Ardenti negans imperfecta
                (2974, 2000, 14, 1700),
            ),
        )
    elif det.getId() == 132:
        box_xywh.extend(
            (
                # Ardenti negans imperfecta
                (2970, 2000, 13, 1086),
            ),
        )
    elif det.getId() == 134:
        box_xywh.extend(
            (
                # Ardenti negans imperfecta
                (383, 2000, 11, 1468),
            ),
        )
    elif det.getId() == 139:
        box_xywh.extend(
            (
                # Ardenti negans imperfecta
                (3574, 2000, 13, 402),
            ),
        )
    elif det.getId() == 145:
        box_xywh.extend(
            (
                # Ardenti negans
                (978, 18, 19, 2000),
            ),
        )
    elif det.getId() == 154:
        box_xywh.extend(
            (
                # Ardenti negans imperfecta
                (2049, 225, 10, 1775),
            ),
        )
    elif det.getId() == 155:
        box_xywh.extend(
            (
                # Ardenti negans imperfecta
                (1447, 2000, 15, 700),
            ),
        )

    bboxes = [
        Box2I(corner=Point2I(x, y), dimensions=Extent2I(w, h))
        for x, y, w, h in box_xywh
    ]

    for x, y, w, h in box_xywh:
        total_masked_pixels += w*h

    defects = Defects(bboxes)

    defects.updateMetadata(
        OBSTYPE="manual_defects",
        camera=camera,
        detector=det,
        setCalibId=True,
        setCalibInfo=True,
        CALIBDATE=valid_start,
        INSTRUME="LSSTCam",
        CALIB_ID=(f"raftName={raft} detectorName={name} "
                  f"detector={det.getId()} calibDate={valid_start}"),
    )

    defects.writeText(out_file)

print("Total number of manually masked pixels masked will be ", total_masked_pixels)
