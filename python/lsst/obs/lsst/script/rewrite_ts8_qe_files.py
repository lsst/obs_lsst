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
__all__ = ("main", )

from lsst.obs.lsst.ts8 import Ts8Mapper

import astropy.units as u
from astropy.io import fits
from astropy.table import QTable
import argparse
import sys
import re
import os
import dateutil.parser
import pickle
import numpy

from lsst.meas.algorithms.simple_curve import AmpCurve

amp_name_map = {'AMP01': 'C00', 'AMP02': 'C01', 'AMP03': 'C02', 'AMP04': 'C03', 'AMP05': 'C04',
                'AMP06': 'C05', 'AMP07': 'C06', 'AMP08': 'C07', 'AMP09': 'C10', 'AMP10': 'C11',
                'AMP11': 'C12', 'AMP12': 'C13', 'AMP13': 'C14', 'AMP14': 'C15', 'AMP15': 'C16',
                'AMP16': 'C17'}


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


def rewrite_ts8_files(picklefile, out_root='.', valid_start='1970-01-01T00:00:00'):
    """Write the QE curves out to the specified location.

    Parameters
    ----------
    picklefile : `str`
        Path to the pickle file that describes a set of QE curves.
    out_root : `str`, optional
        Path to the output location.  If the path doesn't exist,
        it will be created.
    valid_start : `str`, optional
        A string indicating the valid start time for these QE curves.
        Any ISO compliant string will work.
    """

    cam = Ts8Mapper().camera
    file_root = os.path.dirname(picklefile)

    valid_date = dateutil.parser.parse(valid_start)
    datestr = ''.join(re.split(r'[:-]', valid_date.isoformat()))

    if not file_root:  # no path given
        file_root = os.path.curdir()
    with open(picklefile, 'rb') as fh:
        full_raft_name = pickle.load(fh)
        # The pickle file was written with sequential dumps,
        # so it needs to be read sequentially as well.
        _ = pickle.load(fh)  # res
        _ = pickle.load(fh)  # Detector list
        file_list = pickle.load(fh)

    for detector_name, f in file_list.items():
        f = os.path.basename(f[0])
        curve_table = convert_qe_curve(os.path.join(file_root, f))
        curve = AmpCurve.fromTable(curve_table)
        raft_name = full_raft_name.split('_')[1]  # Select just the RTM part.
        outpath = os.path.join(out_root, '_'.join([raft_name, detector_name]).lower())
        outfile = os.path.join(outpath, datestr+'.ecsv')
        os.makedirs(outpath, exist_ok=True)
        full_detector_name = '_'.join([raft_name, detector_name])
        detector_id = cam[full_detector_name].getId()
        curve_table.meta.update({'CALIBDATE': valid_start, 'INSTRUME': 'TS8', 'OBSTYPE': 'qe_curve',
                                 'DETECTOR': detector_id, 'PICKLEFILE': os.path.split(picklefile)[1]})
        curve_table.meta['CALIB_ID'] = (f'raftName={raft_name} detectorName={detector_name} '
                                        f'detector={detector_id} calibDate={valid_start} '
                                        f'ccd={detector_id} ccdnum={detector_id} filter=None')
        curve.writeText(outfile)


def build_argparser():
    """Construct an argument parser for the ``rewrite_ts8_qe_files.py`` script.

    Returns
    -------
    argparser : `argparse.ArgumentParser`
        The argument parser that defines the ``rewrite_ts8_qe_files.py``
        command-line interface.
    """
    parser = argparse.ArgumentParser(description = 'Rewrite native FITS files from the test '
                                                   'stand to a standard format')
    parser.add_argument('picklefile', help = "Pickle file to read.")
    parser.add_argument('--out_root', type = str,
                        help = "Root directory to which to write outputs", default = '.')
    parser.add_argument('--valid_start', type = str,
                        help = "ISO format date string stating the start of the validity range.",
                        default = '1970-01-01T00:00:00')

    return parser


def main():
    args = build_argparser().parse_args()

    try:
        rewrite_ts8_files(args.picklefile, args.out_root, args.valid_start)
    except Exception as e:
        print(f"{e}", file=sys.stderr)
        return 1
    return 0
