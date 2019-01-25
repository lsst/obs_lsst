#!/usr/bin/env python
#
# A python script to read phoSim's headers and write the per-raft datafiles
# used by generateCamera.py
#
# This is not really part of obs_lsst, but it's useful to keep it here
#
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import re
import sys
import os

import lsst.daf.persistence as dafPersist


def writeRaftFile(fd, raftName, detectorType, raftSerial, ccdData):
    print("""\
%s :
  detectorType : %s
  raftSerial : %s

  ccdSerials :
    S00 : ITL-3800C-145-Dev
    S01 : ITL-3800C-022-Dev
    S02 : ITL-3800C-041-Dev
    S10 : ITL-3800C-100-Dev
    S11 : ITL-3800C-017-Dev
    S12 : ITL-3800C-018-Dev
    S20 : ITL-3800C-102-Dev
    S21 : ITL-3800C-146-Dev
    S22 : ITL-3800C-103-Dev

  amplifiers :\
""" % (raftName, detectorType, raftSerial), file=fd)
    for ccdName in ccdData:
        print("    %s :" % (ccdName), file=fd)

        for ampName, (gain, readNoise) in ccdData[ccdName].items():
            print("      %s : { gain : %5.3f, readNoise : %4.2f }" % (ampName, gain, readNoise), file=fd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read phoSim headers and write the per-raft datafiles")

    parser.add_argument('input', type=str, help="Path to input data repository")
    parser.add_argument('--id', type=str, help="ID for data (visit=XXX)", default=None)
    parser.add_argument('--visit', type=int, help="visit to read", default=None)
    parser.add_argument('-v', '--verbose', action="store_true", help="How chatty should I be?", default=False)
    parser.add_argument('--output_dir', type=str,
                        help="Path to output data directory (must exist)", default=None)

    args = parser.parse_args()
    ids = args.id
    verbose = args.verbose
    visit = args.visit

    if ids is not None:
        mat = re.search(r"visit=(\d+)", ids)
        if not mat:
            print("Please specify a visit", file=sys.stderr)
            sys.exit(1)
        visit = int(mat.group(1))

        if args.visit is not None and visit != args.visit:
            print("Please specify either --id or --visit (or be consistent)", file=sys.stderr)
            sys.exit(1)

    butler = dafPersist.Butler(args.input)
    #
    # Lookup the amp names
    #
    camera = butler.get("camera")
    det = list(camera)[0]
    ampNames = [a.getName() for a in det]

    if visit is None:
        visit = butler.queryMetadata("raw", ["visit"])[0]

    dataId = dict(visit=visit)
    #
    # Due to butler stupidity it can't/won't lookup things when you also
    # specify a channel.  Sigh
    #
    dataId["run"], dataId["snap"] = butler.queryMetadata("raw", ["run", "snap"], dataId)[0]

    if verbose:
        print("DataId = %s" % dataId)

    raftData = {}
    for raftName, detectorName, detector in \
            butler.queryMetadata("raw", ["raftName", "detectorName", "detector"], dataId):

        dataId["detector"] = detector   # more of the butler stupidity

        print(raftName, detectorName)

        if raftName not in raftData:
            raftData[raftName] = {}
        if detectorName not in raftData[raftName]:
            raftData[raftName][detectorName] = {}

        for i, ampName in enumerate(ampNames, 1):
            md = butler.get("raw_amp_md", dataId,
                            raftName=raftName, detectorName=detectorName, channel=i)
            gain = md.get("GAIN")
            readNoise = md.get("RDNOISE")
            assert(ampName[-2:] == md.get("EXTNAME")[-2:])

            raftData[raftName][detectorName][ampName] = (gain, readNoise)

    raftId = 0
    for raftName, ccdData in raftData.items():
        raftSerial = "LCA-11021_RTM-%03d" % raftId    # won't be deterministic in reality!
        raftId += 1

        if raftName in ("R00", "R40", "R04", "R44"):
            continue
        if args.output_dir:
            prefix = args.output_dir
        else:
            prefix = ""
        with open(os.path.join(prefix, "%s.yaml") % raftName, "w") as fd:
            writeRaftFile(fd, raftName, "ITL", raftSerial, raftData[raftName])
