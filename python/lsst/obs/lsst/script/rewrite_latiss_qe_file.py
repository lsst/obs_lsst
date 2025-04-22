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
from astropy.table import QTable
import os
import numpy

import lsst.utils
from lsst.meas.algorithms.simple_curve import AmpCurve

from ..utils import valid_start_to_file_root

amp_name_map = {'AMP01': 'C10', 'AMP02': 'C11', 'AMP03': 'C12', 'AMP04': 'C13', 'AMP05': 'C14',
                'AMP06': 'C15', 'AMP07': 'C16', 'AMP08': 'C17', 'AMP09': 'C07', 'AMP10': 'C06',
                'AMP11': 'C05', 'AMP12': 'C04', 'AMP13': 'C03', 'AMP14': 'C02', 'AMP15': 'C01',
                'AMP16': 'C00'}


def convert_qe_curve(filename):
    """Convert a single QE curve from its native FITS format to an
    an `astropy.table.QTable` representation.

    Parameters
    ----------
    filename : `str`
        Full path, including filename for the file to be converted.

    Returns
    -------
    table : `astropy.table.QTable`
        A QTable object containing the columns that describe this
        QE curve.

    Notes
    -----
    This function is specific to how the ts8 data are formatted
    with a curve per amp.  If ther are other formats, a different
    converter will be necessary.
    """
    with fits.open(filename) as hdu_list:
        # qe data is in first extension
        data = hdu_list[1].data
    wlength = []
    eff = dict()
    for row in data:
        wlength.append(row['WAVELENGTH'])
        for i in range(16):  # There are 16 amps
            col_name = f'AMP{i+1:02d}'
            eff.setdefault(amp_name_map[col_name], []).append(row[col_name])
    out_data = {'amp_name': [], 'wavelength': [], 'efficiency': []}
    for k in eff:
        amp_names = [k]*len(wlength)
        out_data['amp_name'] += amp_names
        out_data['wavelength'] += wlength
        out_data['efficiency'] += eff[k]

    out_data['amp_name'] = numpy.array(out_data['amp_name'])
    out_data['wavelength'] = numpy.array(out_data['wavelength'])*u.nanometer
    out_data['efficiency'] = numpy.array(out_data['efficiency'])*u.percent

    return QTable(out_data)


data_dir = lsst.utils.getPackageDir("obs_lsst_data")
raft_name = "rxx"
detector_name = "s00"
raft_detector = raft_name + "_" + detector_name
detector_id = 0
fits_file = "ITL-3800C-068_QE.fits"
valid_start = "1970-01-01T00:00:00"

filename = os.path.join(data_dir, "latiss", "transmission_sensor", raft_detector, fits_file)

curve_table = convert_qe_curve(filename)
curve = AmpCurve.fromTable(curve_table)

datestr = valid_start_to_file_root(valid_start)

outfile = os.path.join(data_dir, "latiss", "transmission_sensor", raft_detector, datestr + ".ecsv")

curve_table.meta.update(
    {
        "CALIBDATE": valid_start,
        "INSTRUME": "LATISS",
        "OBSTYPE": "transmission_sensor",
        "TYPE": "transmission_sensor",
        "DETECTOR": detector_id,
        "CALIBCLS": "lsst.ip.isr.IntermediateSensorTransmissionCurve",
        "SOURCE": fits_file,
    }
)

curve_table.meta["CALIB_ID"] = (
    f"raftName={raft_name} detectorName={detector_name} "
    f"detector={detector_id} calibDate={valid_start} "
    f"ccd={detector_id} ccdnum={detector_id} filter=None")

curve.writeText(outfile)
