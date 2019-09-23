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

import astropy.units as u
from astropy.io import fits
from astropy.table import Table
import numpy


def convert_qe_curve(filename):
    hdu_list = fits.open(filename)
    # qe data is in first extension
    data = hdu_list[1].data
    wlength = []
    eff = dict()
    for row in data:
        for i in range(18):  # There are 16 amps
            wlength.append(row['WAVELENGTH'])
            col_name = 'AMP%2i'%(i)
            if col_name in eff:
                eff[col_name].append(row[col_name])
            else:
                eff[col_name] = [row[col_name], ]
    out_data = {'amp_name': [], 'wavelength': [], 'efficiency': []}
    for k in eff:
        amp_names = numpy.fill(wlength.shape, k)
        out_data['amp_name'] = numpy.concatenate(out_data['amp_name'], amp_names)
        out_data['wavelength'] = numpy.concatenate(out_data['wavelength'], wlength)
        out_data['efficiency'] = numpy.concatenate(out_data['efficiency'], eff[k])

    out_data['wavelength'] = out_data['wavelength']*u.nanometer
    out_data['efficiency'] = out_data['efficiency']*u.percent
    metadata = {'detector_id': hdu_list[0].header['LSST_NUM']}
    return Table(out_data, meta = metadata)
