#
# A python script to split out a phoSim "segmentation" file into the per-raft datafiles
# used by generateCamera.py
#
# This is not really part of obs_lsstCam, but it's useful to keep it here
# 
import re

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
        
        gain, readNoise = fields[7], fields[11]
        raftName, ccdName, ampName = name.split('_')

        if raftName not in raftData:
            raftData[raftName] = {}
        if ccdName not in raftData[raftName]:
            raftData[raftName][ccdName] = {}

        raftData[raftName][ccdName][ampName] = (gain, readNoise)

import sys
fd = sys.stdout


def writeRaftFile(fd, raftName, detectorType, ccdData):
    print("""\
%s :
  detectorType : %s

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
""" % (raftName, detectorType), file=fd)
    for ccdName in ccdData:
        print("    %s :" % (ccdName), file=fd)

        for ampName, (gain, readNoise) in ccdData[ccdName].items():
            print("      %s : { gain : %5.3f, readNoise : %4.2f }" % (ampName, gain, readNoise), file=fd)

for raftName, ccdData in raftData.items():
    if raftName in ("R00", "R40", "R04", "R44"):
        continue
    with open("%s.yaml" % raftName, "w") as fd:
        writeRaftFile(fd, raftName, "ITL", raftData[raftName])
