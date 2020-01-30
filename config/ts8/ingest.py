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

from lsst.obs.lsst.ts8 import Ts8ParseTask

config.parse.retarget(Ts8ParseTask)

# what used to be config.parse.translators = {
del config.parse.translators['snap']
config.parse.translators['dayObs'] = 'translate_dayObs'
config.parse.translators['testSeqNum'] = 'translate_testSeqNum'

# what used to be config.parse.defaults = {

config.parse.hdu = 0

# what used to be config.register.columns = {
del config.register.columns['snap']
config.register.columns['dayObs'] = 'text'
config.register.columns['testSeqNum'] = 'int'

config.register.unique = ["expId", "detector", "visit"]
config.register.visit = list(config.register.columns.keys())
