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

from lsst.obs.lsst.ingest import LsstCamParseTask

config.parse.retarget(LsstCamParseTask)

config.parse.translation = {
    'testType': 'TESTTYPE',
}
config.parse.translators = {
    'expTime': 'translate_expTime',
    'object': 'translate_object',
    'imageType': 'translate_imageType',
    'filter': 'translate_filter',
    'lsstSerial': 'translate_lsstSerial',
    'date': 'translate_date',
    'dateObs': 'translate_dateObs',
    'run': 'translate_run',
    'visit': 'translate_visit',
    'wavelength': 'translate_wavelength',
    'raftName': 'translate_raftName',
    'detectorName': 'translate_detectorName',
    'detector': 'translate_detector',
    'snap': 'translate_snap',
    'controller': 'translate_controller',
    'obsid': 'translate_obsid',
}
config.parse.defaults = {
}
config.parse.hdu = 0

config.register.columns = {
    'run': 'text',
    'visit': 'int',
    'filter': 'text',
    'date': 'text',
    'dateObs': 'text',
    'expTime': 'double',
    'raftName': 'text',
    'detectorName': 'text',
    'detector': 'int',
    'snap': 'int',
    'object': 'text',
    'imageType': 'text',
    'testType': 'text',
    'lsstSerial': 'text',
    'wavelength': 'int',
    'controller': 'text',
    'obsid': 'text',
}
config.register.unique = ["visit", "detector"]
config.register.visit = ['visit', 'filter', 'dateObs', 'expTime']
