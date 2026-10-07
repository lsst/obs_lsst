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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Shutter-corrected per-source mid-exposure times (lsst.ip.isr.shutterTiming),
# from the shutter Hall-fit cards in the exposure metadata and the
# shutter-plane beam table shipped with obs_lsst.
config.doShutterTiming = True
config.shutterTiming.beamFile = (
    "resource://lsst.obs.lsst/resources/shutter/beam_at_L3S1_z9.618_rot0_evaluated.tnt"
)
