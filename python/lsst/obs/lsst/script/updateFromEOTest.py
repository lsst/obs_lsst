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

__all__ = ("main", "writeRXXFile")

import argparse
import glob
import os
import shutil
import sys
import json
import yaml

import lsst.utils


def writeRXXFile(fileName, raftName, raftNameData, gains=None, readNoises=None, saturations=None, indent=2):

    dindent = indent

    with open(fileName, "w") as fd:   # can't use `with` because of the sys.stdout workaround
        indent = 0

        def iprint(*args):
            """Print with the proper indentation"""
            if len(args) > 0:
                print(indent*dindent*" ", end='', file=fd)
            print(*args, file=fd)

        iprint(f"{raftName} :")

        ccdNames = list(raftNameData["ccdSerials"])

        indent += 1
        iprint(f"detectorType : {raftNameData['detectorType']}")
        iprint(f"raftSerial : {raftNameData['raftSerial']}")

        iprint()
        iprint("ccdSerials :")
        indent += 1
        for ccdName in ccdNames:
            iprint(f"{ccdName} : {raftNameData['ccdSerials'][ccdName]}")
        indent -= 1

        iprint()
        iprint("geometryWithinRaft :")
        indent += 1
        for ccdName in ccdNames:
            offset, yaw = raftNameData['geometryWithinRaft'][ccdName].values()
            iprint(f"{ccdName} : " "{")
            indent += 1
            iprint(f"offset : {offset},")
            iprint(f"yaw : {yaw},")

            indent -= 1
            iprint("}")

        indent -= 1

        if 'sensorTypes' in raftNameData:
            iprint()
            iprint("sensorTypes :")
            indent += 1
            for ccdName in ccdNames:
                iprint(f"{ccdName} : {raftNameData['sensorTypes'][ccdName]}")
            indent -= 1

        iprint()
        iprint("amplifiers :")

        # The yaml files treat e.g. R00 and R00W separately for technical
        # reasons but cameraGeom/EOTest itself has no such constraint.
        raftName_real = raftName[:3] if raftName.endswith("W") else raftName
        indent += 1
        for ccdName in ccdNames:
            fullCcdName = f'{raftName_real}_{ccdName}'
            iprint(f"{ccdName} :")

            indent += 1
            for ampName in raftNameData["amplifiers"][ccdName]:
                iprint(f"{ampName} : " "{")

                indent += 1
                gain = raftNameData["amplifiers"][ccdName][ampName]["gain"] if \
                    gains is None else gains[fullCcdName][ampName]
                iprint(f"gain : {gain:.5f},")

                readNoise = raftNameData["amplifiers"][ccdName][ampName]["readNoise"] if \
                    readNoises is None else readNoises[fullCcdName][ampName]
                iprint(f"readNoise : {readNoise:.3f},")

                try:
                    saturation = raftNameData["amplifiers"][ccdName][ampName]["saturation"] if \
                        saturations is None else saturations[fullCcdName][ampName]
                    iprint(f"saturation : {saturation:.0f},")
                except KeyError:
                    pass

                indent -= 1
                iprint("}")

            indent -= 1


def updateFromEOTest(RXXDir, raftNames, updatedData):
    for raftName in raftNames:
        #
        # Read the old values
        #
        RXXFile = os.path.join(RXXDir, f"{raftName}.yaml")
        with open(RXXFile) as fd:
            raftNameData = yaml.load(fd, yaml.CSafeLoader)

        shutil.copyfile(RXXFile, RXXFile + "~")  # make a backup, although we also have git

        # the corner rafts are a nuisance, and we have to handle them as two
        # .yaml files, e.g. R00.yaml and R00W.yaml, whereas the raft names
        # don't need to worry about this.  Consequently, we may need to remove
        # a "W" to be able to look up values
        if raftName in ["R00W", "R04W", "R40W", "R44W"]:
            raftNameData[raftName] = raftNameData[raftName[:3]]

        writeRXXFile(RXXFile, raftName, raftNameData[raftName],
                     gains=updatedData["gain"],
                     readNoises=updatedData["readNoise"],
                     saturations=updatedData["saturation"])


def main():
    parser = argparse.ArgumentParser(description="""
    Regenerate the RXX.yaml files describing rafts in a camera

    Values that aren't provided are read from e.g. RXXDir/RYY.yaml;
    all rafts are processed until you specify a list of rafts

    The JSON files are as written by EOTest, a dict indexed by CCD name (e.g. R01_S00)
    each of whose values is indexed by amp name (e.g. C00)
    E.g.
       {'R01_S00': {'C10': 1.4449166059494019, ... },
        'R01_S01': {'C10': 1.3959081172943115, ... },
        ...
       }
    """)

    parser.add_argument('raftNames', nargs='*', type=str, help="Name rafts to process (default: all)")
    parser.add_argument('--RXXDir', type=str, help="Directory containing RXX.yaml files")
    parser.add_argument('--gainFile', help="JSON file of gains")
    parser.add_argument('--readNoiseFile', help="JSON file of readNoise")
    parser.add_argument('--saturationFile', help="JSON file of saturation levels")
    parser.add_argument('--doraise', action="store_true", help="Raise an exception on error", default=False)

    args = parser.parse_args()

    if args.RXXDir is None:
        args.RXXDir = os.path.join(lsst.utils.getPackageDir("OBS_LSST"), "policy", "lsstCam")

    if len(args.raftNames) == 0:
        RXXFiles = glob.glob(os.path.join(args.RXXDir, "R*.yaml"))
        args.raftNames = sorted([os.path.splitext(os.path.basename(RXX))[0] for RXX in RXXFiles])

    updatedData = {}

    for dtype, fileName in [
            ("gain", args.gainFile),
            ("readNoise", args.readNoiseFile),
            ("saturation", args.saturationFile),
    ]:
        if fileName is None:
            updatedData[dtype] = None
        else:
            with open(fileName) as fd:
                updatedData[dtype] = json.load(fd)

    try:
        updateFromEOTest(args.RXXDir, args.raftNames, updatedData)
    except Exception as e:
        if args.doraise:
            raise
        print(f"{e}", file=sys.stderr)
        return 1
    return 0
