# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.

import os.path

# Load configs from base assembleCoadd
config.load(os.path.join(os.path.dirname(__file__), "assembleCoadd.py"))

# Load configs for the subtasks
config.assembleMeanCoadd.load(os.path.join(os.path.dirname(__file__), "assembleCoadd.py"))
config.assembleMeanCoadd.statistic = 'MEAN'
config.assembleMeanClipCoadd.load(os.path.join(os.path.dirname(__file__), "assembleCoadd.py"))
config.assembleMeanClipCoadd.statistic = 'MEANCLIP'
