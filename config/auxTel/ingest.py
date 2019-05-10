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

from lsst.obs.lsst.auxTel import AuxTelParseTask

config.parse.retarget(AuxTelParseTask)

del config.parse.translation['testType']

del config.parse.translators['run']
del config.parse.translators['lsstSerial']
del config.parse.translators['snap']

config.parse.translators['raftName'] = "set_raftName_to_RXX"
config.parse.translators['dayObs'] = 'translate_dayObs'
config.parse.translators['seqNum'] = 'translate_seqNum'

config.parse.hdu = 0

config.register.columns = {
    #'run': 'text',
    'dayObs': 'text',
    'seqNum': 'int',
    'visit': 'int',
    'detector': 'int',
    'raftName': 'text',
    'detectorName': 'text',
    'filter': 'text',
    'dateObs': 'text',
    'date': 'text',
    'expTime': 'double',
    'object': 'text',
    'imageType': 'text',
    'wavelength': 'int',
}
config.register.unique = ["visit", "detector"]
config.register.visit = list(config.register.columns.keys())
