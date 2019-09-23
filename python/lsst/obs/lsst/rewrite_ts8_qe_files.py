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

import re
import os
import dateutil.parser
import pickle

amp_name_map = {'AMP01': 'C00', 'AMP02': 'C01', 'AMP03': 'C02', 'AMP04': 'C03', 'AMP05': 'C04',
                'AMP06': 'C05', 'AMP07': 'C06', 'AMP08': 'C07', 'AMP09': 'C10', 'AMP10': 'C11',
                'AMP11': 'C12', 'AMP12': 'C13', 'AMP13': 'C14', 'AMP14': 'C15', 'AMP15': 'C16',
                'AMP16': 'C17'}


def rewrite_ts8_files(self, picklefile, out_root='.', valid_start='1970-01-01T00:00:00'):
    file_root = os.path.split(picklefile)[0]

    valid_date = dateutil.parser(valid_start)
    datestr = ''.join(re.split(r'[:-]', valid_date.isoformat()))

    if not file_root:  # no path given
        file_root = '.'
    with open(picklefile, 'rb') as fh:
        raft_name = pickle.load(fh)
        res = pickle.load(fh)  # noqa F841
        detector_list = pickle.load(fh)
        file_list = pickle.load(fh)
        fw = pickle.load(fh)  # noqa F841
        gains = pickle.load(fh)  # noqa F841

    for f in file_list:
        curve_table = convert_qe_curve(os.path.join(file_root, f))
        detector_id = curve_table.meta['detector_id']
        detector_name = None
        for detector_tuple in detector_list:
            if detector_id == detector_tuple[1]:
                detector_name = detector_tuple[2]
        if detector_name is None:
            raise ValueError(f'Could not find detector name for detector id: {detector_id}.')
        outfile = os.path.join(out_root, '_'.join(raft_name, detector_name), datestr+'.ecxv')
        curve_table.writeText(outfile)
