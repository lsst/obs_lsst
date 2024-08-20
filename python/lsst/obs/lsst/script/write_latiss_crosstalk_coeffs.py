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
from lsst.daf.butler import Butler
import lsst.utils


butler = Butler("/repo/embargo")
camera = butler.get("camera", instrument="LATISS", collections=["LATISS/calib"])
crosstalk = butler.get("crosstalk", instrument="LATISS", detector=0, collections=["LATISS/calib"])

det = camera[0]
name = det.getName()

# Make this valid for all time.
valid_start = "1970-01-01T00:00:00"
valid_date = dateutil.parser.parse(valid_start)
datestr = "".join(re.split(r"[:-]", valid_date.isoformat()))
directory = lsst.utils.getPackageDir("obs_lsst_data")
out_path = os.path.join(directory, "latiss", "crosstalk", name.lower())
os.makedirs(out_path, exist_ok=True)
out_file = os.path.join(out_path, datestr + ".ecsv")

crosstalk.updateMetadata(
    camera=camera,
    detector=det,
    setCalibId=True,
    setCalibInfo=True,
    CALIBDATE=valid_start,
)

crosstalk.writeText(out_file)
