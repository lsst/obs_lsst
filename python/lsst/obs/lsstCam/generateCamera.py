#
# LSST Data Management System
# Copyright 2017 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
import os
import sys
import shutil
import yaml

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="")
    
    parser.add_argument('outputFile', type=str, help="Name of generated file")
    parser.add_argument('--verbose', action="store_true", help="How chatty should I be?", default=False)
    
    args = parser.parse_args()

    cameraFile = args.outputFile
    cameraFileDir = os.path.dirname(cameraFile)

    cameraSklFile = os.path.join(cameraFileDir, "cameraHeader.yaml")
    raftsFile = os.path.join(cameraFileDir, "rafts.yaml")

    with open(cameraSklFile) as fd:
        cameraSkl = yaml.load(fd, Loader=yaml.Loader)

    with open(raftsFile) as fd:
        raftData = yaml.load(fd, Loader=yaml.Loader)

    shutil.copyfile(cameraSklFile, cameraFile)

    nindent = 0        # current number of indents
    def indent():
        """Return the current indent string"""
        dindent = 2    # number of spaces per indent
        return(nindent*dindent - 1)*" "   # print will add the extra " "

    with open(cameraFile, "a") as fd:
        print("""
#
# Define our specific devices
#
# All the CCDs present in this file
#
CCDs :\
""", file=fd)

        for raftName, raftData in raftData["rafts"].items():
            try:
                with open(os.path.join(cameraFileDir, "%s.yaml" % raftName)) as yfd:
                    raftCcdData = yaml.load(yfd, Loader=yaml.Loader)[raftName]
            except FileNotFoundError:
                print("Unable to load CCD descriptions for raft %s" % raftName, file=sys.stderr)
                continue

            try:
                detectorType = raftCcdData["detectorType"]
                ccds = cameraSkl['RAFT_%s' % detectorType]["ccds"]        # describe this *type* of raft
                amps = cameraSkl['CCD_%s'  % detectorType]["amplifiers"]  # describe this *type* of ccd

            except KeyError:
                raise RuntimeError("Unknown detector type %s" % detectorType)

            nindent += 1

            raftOffset = raftData["offset"]
            id0 = raftData['id0']
            for ccdName, ccdData in ccds.items():
                print(indent(), "%s_%s : " % (raftName, ccdName), file=fd)
                nindent += 1
                print(indent(), "<< : *%s_%s" % (ccdName, detectorType), file=fd)
                print(indent(), "id : %s" % (id0 + ccdData['id']), file=fd)
                print(indent(), "serial : %s" % (raftCcdData['ccdSerials'][ccdName]), file=fd)
                print(indent(), "refpos : %s" % (ccdData['refpos']), file=fd)
                print(indent(), "offset : [%g, %g]" % (ccdData['offset'][0] + raftOffset[0],
                                                       ccdData['offset'][1] + raftOffset[1]), file=fd)

                print(indent(), "amplifiers :", file=fd)
                nindent += 1
                for ampName, ampData in amps.items():
                    amplifierData = raftCcdData['amplifiers'][ccdName]

                    print(indent(), "%s :" % ampName, file=fd)

                    nindent += 1
                    print(indent(), "<< : *%s_%s" % (ampName, detectorType), file=fd)
                    print(indent(), "gain : %g" % (amplifierData[ampName]['gain']), file=fd)
                    print(indent(), "readNoise : %g" % (amplifierData[ampName]['readNoise']), file=fd)
                    nindent -= 1
                nindent -= 1

                nindent -= 1

            nindent -= 1
