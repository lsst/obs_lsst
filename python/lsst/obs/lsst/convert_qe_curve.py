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

from lsst.meas.algorithms.simple_curve import AmpCurve

amp_name_map = {'AMP01': 'C00', 'AMP02': 'C01', 'AMP03': 'C02', 'AMP04': 'C03', 'AMP05': 'C04',
                'AMP06': 'C05', 'AMP07': 'C06', 'AMP08': 'C07', 'AMP09': 'C10', 'AMP10': 'C11',
                'AMP11': 'C12', 'AMP12': 'C13', 'AMP13': 'C14', 'AMP14': 'C15', 'AMP15': 'C16',
                'AMP16': 'C17'}


def convert_qe_curve(filename):
    """Convert a single QE curve from its native FITS format to an
    an `astropy.table.Table` representation.

    Parameters
    ----------
    filename : `str`
        Full path, including filename for the file to be converted.

    Returns
    -------
    table : `astropy.table.Table`
        A Table object containing the columns that describe this
        QE curve.

    Notes
    -----
    This function is specific to how the ts8 data are formatted
    with a curve per amp.  If ther are other formats, a different
    converter will be necessary.
    """
    hdu_list = fits.open(filename)
    # qe data is in first extension
    data = hdu_list[1].data
    wlength = []
    eff = dict()
    for row in data:
        wlength.append(row['WAVELENGTH'])
        for i in range(16):  # There are 16 amps
            col_name = 'AMP%02d'%(i+1)
            if amp_name_map[col_name] in eff:
                eff[amp_name_map[col_name]].append(row[col_name])
            else:
                eff[amp_name_map[col_name]] = [row[col_name], ]
    out_data = {'amp_name': [], 'wavelength': [], 'efficiency': []}
    for k in eff:
        amp_names = [k for el in range(len(wlength))]
        out_data['amp_name'] += amp_names
        out_data['wavelength'] += wlength
        out_data['efficiency'] += eff[k]

    out_data['amp_name'] = numpy.array(out_data['amp_name'])
    out_data['wavelength'] = numpy.array(out_data['wavelength'])*u.nanometer
    out_data['efficiency'] = numpy.array(out_data['efficiency'])*u.percent
    return Table(out_data)
