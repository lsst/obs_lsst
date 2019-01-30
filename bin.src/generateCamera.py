#!/usr/bin/env python
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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
import os
import sys
import shutil
import yaml


def findYamlOnPath(fileName, searchPath):
    """Find and return a file somewhere in the directories listed in searchPath"""
    for d in searchPath:
        f = os.path.join(d, fileName)
        if os.path.exists(f):
            return f

    raise FileNotFoundError("Unable to find %s on path %s" % (fileName, ":".join(searchPath)))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="""
    Generate a camera.yaml file for a camera by assembling descriptions of rafts, sensors, etc.

    Because we have many similar cameras, the assembly uses a :-separated search path of directories
    to find desired information.  The _first_ occurrence of a filename is used.
    """)

    parser.add_argument('outputFile', type=str, help="Name of generated file")
    parser.add_argument('--path', type=str, help="List of directories to search for components",
                        default=False)
    parser.add_argument('--verbose', action="store_true", help="How chatty should I be?", default=False)

    args = parser.parse_args()

    cameraFile = args.outputFile
    cameraFileDir = os.path.dirname(cameraFile)

    searchPath = []
    for d in args.path.split(":"):
        searchPath.append(os.path.join(cameraFileDir, d))

    cameraSklFile = findYamlOnPath("cameraHeader.yaml", searchPath)
    with open(cameraSklFile) as fd:
        cameraSkl = yaml.load(fd, Loader=yaml.CLoader)

    cameraTransformsFile = findYamlOnPath("cameraTransforms.yaml", searchPath)
    with open(cameraTransformsFile) as fd:
        cameraTransforms = yaml.load(fd, Loader=yaml.CLoader)

    with open(findYamlOnPath("rafts.yaml", searchPath)) as fd:
        raftData = yaml.load(fd, Loader=yaml.CLoader)

    with open(findYamlOnPath("ccdData.yaml", searchPath)) as fd:
        ccdData = yaml.load(fd, Loader=yaml.CLoader)

    shutil.copyfile(cameraSklFile, cameraFile)

    nindent = 0        # current number of indents

    def indent():
        """Return the current indent string"""
        dindent = 2    # number of spaces per indent
        return(nindent*dindent - 1)*" "   # print will add the extra " "

    with open(cameraFile, "a") as fd:
        print("""
#
# Specify the geometrical transformations relevant to the camera in all appropriate
# (and known!) coordinate systems
#""", file=fd)
        for k, v in cameraTransforms.items():
            print("%s : %s" % (k, v), file=fd)

        print("""
#
# Define our specific devices
#
# All the CCDs present in this file
#
CCDs :\
""", file=fd)

        for raftName, perRaftData in raftData["rafts"].items():
            try:
                with open(findYamlOnPath("%s.yaml" % raftName, searchPath)) as yfd:
                    raftCcdData = yaml.load(yfd, Loader=yaml.CLoader)[raftName]
            except FileNotFoundError:
                print("Unable to load CCD descriptions for raft %s" % raftName, file=sys.stderr)
                continue

            try:
                detectorType = raftCcdData["detectorType"]
                _ccds = cameraSkl['RAFT_%s' % detectorType]["ccds"]        # describe this *type* of raft

                try:
                    sensorTypes = raftCcdData["sensorTypes"]
                except KeyError:
                    sensorTypes = None

                # only include CCDs in the raft for which we have a serial
                # (the value isn't checked)
                ccds = {}
                for ccdName in raftCcdData["ccdSerials"]:
                    ccds[ccdName] = _ccds[ccdName]
                del _ccds

                amps = cameraSkl['CCD_%s' % detectorType]["amplifiers"]  # describe this *type* of ccd
            except KeyError:
                raise RuntimeError("Unknown detector type %s" % detectorType)

            try:
                crosstalkCoeffs = ccdData["crosstalk"][detectorType]
            except KeyError:
                crosstalkCoeffs = None

            nindent += 1

            raftOffset = perRaftData["offset"]
            id0 = perRaftData['id0']
            for ccdName, ccdLayout in ccds.items():
                print(indent(), "%s_%s : " % (raftName, ccdName), file=fd)
                nindent += 1
                print(indent(), "<< : *%s_%s" % (ccdName, detectorType), file=fd)
                if sensorTypes is not None:
                    print(indent(), "detectorType : %i" % (sensorTypes[ccdName]), file=fd)
                print(indent(), "id : %s" % (id0 + ccdLayout['id']), file=fd)
                print(indent(), "serial : %s" % (raftCcdData['ccdSerials'][ccdName]), file=fd)
                print(indent(), "refpos : %s" % (ccdLayout['refpos']), file=fd)
                print(indent(), "offset : [%g, %g]" % (ccdLayout['offset'][0] + raftOffset[0],
                                                       ccdLayout['offset'][1] + raftOffset[1]), file=fd)

                if crosstalkCoeffs is not None:
                    namp = len(amps)
                    print(indent(), "crosstalk : [", file=fd)
                    nindent += 1
                    print(indent(), file=fd, end="")
                    for iAmp in amps:
                        for jAmp in amps:
                            print("%11.3e," % crosstalkCoeffs[iAmp][jAmp], file=fd, end='')
                        print(file=fd, end="\n" + indent())
                    nindent -= 1
                    print("]", file=fd)

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
