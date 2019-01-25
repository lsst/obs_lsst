#
# A python script to split out a phoSim "segmentation" file into the per-raft
# datafiles used by generateCamera.py
#
# This is not really part of obs_lsst, but it's useful to keep it here
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

import numpy as np
import re

__all__ = ["writeRaftFile"]


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
    raftData = {}
    with open('segmentation.txt') as fd:
        for line in fd.readlines():
            if re.search(r"^\s*($|#)", line):
                continue

            fields = line.split()
            name = fields[0]
            fields[1:] = [float(_) for _ in fields[1:]]

            nField = len(fields)
            if nField == 4:
                name, nAmp, ncol, nrow = fields
                continue

            fields = fields[:29]
            assert len(fields) == 29

            gain, gainVariation = fields[7], fields[8]
            readNoise, readNoiseVariation = fields[11], fields[12]

            if False:
                gain *= 1 + 0.01*gainVariation*np.random.normal()
                readNoise *= 1 + 0.01*readNoiseVariation*np.random.normal()

            raftName, ccdName, ampName = name.split('_')

            if raftName not in raftData:
                raftData[raftName] = {}
            if ccdName not in raftData[raftName]:
                raftData[raftName][ccdName] = {}

            raftData[raftName][ccdName][ampName] = (gain, readNoise)

    raftId = 0
    for raftName, ccdData in raftData.items():
        raftSerial = "LCA-11021_RTM-%03d" % raftId    # won't be deterministic in reality!
        raftId += 1

        if raftName in ("R00", "R40", "R04", "R44"):
            continue
        with open("%s.yaml" % raftName, "w") as fd:
            writeRaftFile(fd, raftName, "ITL", raftSerial, raftData[raftName])
