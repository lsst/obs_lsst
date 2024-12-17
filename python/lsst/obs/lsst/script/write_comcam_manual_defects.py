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
from lsst.ip.isr import Defects
from lsst.geom import Box2I, Point2I, Extent2I
import lsst.utils
from lsst.obs.lsst import LsstComCam


camera = LsstComCam().getCamera()

data_root = lsst.utils.getPackageDir("obs_lsst_data")

valid_start = "2024-10-20T00:00:00"
valid_date = dateutil.parser.parse(valid_start)
datestr = "".join(re.split(r"[:-]", valid_date.isoformat()))

for det in camera:
    print("Building manual defects from detector ", det.getName(), det.getId())
    name = det.getName()
    raft, sensor = name.split("_")

    out_path = os.path.join(data_root, "comCam", "manual_defects", name.lower())
    os.makedirs(out_path, exist_ok=True)
    out_file = os.path.join(out_path, f"{datestr}.ecsv")

    if os.path.isfile(out_file):
        os.remove(out_file)

    box_xywh = []

    # Define the manual defects from DM-47365.
    if det.getId() == 1:
        # Phosphorescence.
        box_xywh.extend(
            (
                (0, 1300, 350, 2695),
                (3650, 3600, 417, 395),
            ),
        )
    elif det.getId() == 4:
        # Unmasked dark column.
        box_xywh.extend(
            (
                (3400, 2000, 15, 2000),
            ),
        )
    elif det.getId() == 5:
        # High CTI amp edges.
        box_xywh.extend(
            (
                (500, 0, 10, 2000),
                (1008, 0, 15, 2000),
                (1522, 0, 10, 2000),
                (2031, 0, 10, 2000),
            ),
        )

    bboxes = [
        Box2I(corner=Point2I(x, y), dimensions=Extent2I(w, h))
        for x, y, w, h in box_xywh
    ]

    defects = Defects(bboxes)

    defects.updateMetadata(
        OBSTYPE="manual_defects",
        camera=camera,
        detector=det,
        setCalibId=True,
        setCalibInfo=True,
        CALIBDATE=valid_start,
        INSTRUME="ComCam",
        CALIB_ID=(f"raftName={raft} detectorName={name} "
                  f"detector={det.getId()} calibDate={valid_start}"),
    )

    defects.writeText(out_file)
