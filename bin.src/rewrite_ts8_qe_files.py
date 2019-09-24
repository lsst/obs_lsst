#!/usr/bin/env python
#
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

import argparse
import sys

from lsst.obs.lsst.rewrite_ts8_qe_files import rewrite_ts8_files

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Rewrite native FITS files from the test ' +
                                                   'stand to a standard format')
    parser.add_argument('picklefile', help = "Pickle file to read.")
    parser.add_argument('--out_root', type = str,
                        help = "Root directory to which to write outputs", default = '.')
    parser.add_argument('--valid_start', type = str,
                        help = "ISO format date string stating the stgart of the validity range.",
                        default = '1970-01-01T00:00:00')

    args = parser.parse_args()
    sys.exit(rewrite_ts8_files(args.picklefile, args.out_root, args.valid_start))
