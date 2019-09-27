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

from .convert_qe_curve import convert_qe_curve
from .ts8 import Ts8Mapper

import re
import os
import dateutil.parser
import pickle

from lsst.meas.algorithms.simple_curve import AmpCurve

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
    file_root = os.path.split(picklefile)[0]

    valid_date = dateutil.parser.parse(valid_start)
    datestr = ''.join(re.split(r'[:-]', valid_date.isoformat()))

    if not file_root:  # no path given
        file_root = '.'
    with open(picklefile, 'rb') as fh:
        full_raft_name = pickle.load(fh)
        res = pickle.load(fh)  # noqa F841
        detector_list = pickle.load(fh)
        file_list = pickle.load(fh)
        fw = pickle.load(fh)  # noqa F841
        gains = pickle.load(fh)  # noqa F841

    for k, f in file_list.items():
        detector_name = k
        # for some reason the path to the file is in 
        f = os.path.split(f[0])[1]  # The path is absolute, so grab file name only
        curve_table = convert_qe_curve(os.path.join(file_root, f))
        curve = AmpCurve.fromTable(curve_table)
        raft_name = full_raft_name.split('_')[1]  # Select just the RTM part.
        outpath = os.path.join(out_root, '_'.join([raft_name, detector_name]).lower())
        outfile = os.path.join(outpath, datestr+'.ecxv')
        os.makedirs(outpath, exist_ok=True)
        full_detector_name = '_'.join([raft_name, detector_name])
        detector_id = cam[full_detector_name].getId()
        curve_table.meta.update({'CALIBDATE': valid_start, 'INSTRUME': 'ts8', 'OBSTYPE': 'qe_curve',
                                 'DETECTOR': cam['_'.join([raft_name, detector_name])].getId(),
                                 'PICKLEFILE': os.path.split(picklefile)[1]})
        curve_table.meta['CALIB_ID'] = (f'raftName={raft_name} detectorName={full_detector_name} ' +
                                        f'detector={detector_id} calibDate={valid_start} ' +
                                        f'ccd={detector_id} ccdnum={detector_id} filter=None')
        curve.writeText(outfile)
