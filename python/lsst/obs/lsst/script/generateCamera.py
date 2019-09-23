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

__all__ = ("main",)

import argparse
import os
import sys
import shutil
import yaml
import numpy as np


def findYamlOnPath(fileName, searchPath):
    """Find and return a file somewhere in the directories listed in
    searchPath"""
    for d in searchPath:
        f = os.path.join(d, fileName)
        if os.path.exists(f):
            return f

    raise FileNotFoundError("Unable to find %s on path %s" % (fileName, ":".join(searchPath)))


def parseYamlOnPath(fileName, searchPath):
    """Find the named file in search path, parse the YAML, and return contents.
    """
    yamlFile = findYamlOnPath(fileName, searchPath)
    with open(yamlFile) as fd:
        content = yaml.load(fd, Loader=yaml.CSafeLoader)
    return content


def build_argparser():
    """Construct an argument parser for the ``generateCamera.py`` script.

    Returns
    -------
    argparser : `argparse.ArgumentParser`
        The argument parser that defines the ``translate_header.py``
        command-line interface.
    """

    parser = argparse.ArgumentParser(description="""
    Generate a camera.yaml file for a camera by assembling descriptions of
    rafts, sensors, etc.

    Because we have many similar cameras, the assembly uses a :-separated
    search path of directories to find desired information.  The _first_
    occurrence of a filename is used.
    """)

    parser.add_argument('outputFile', type=str, help="Name of generated file")
    parser.add_argument('--path', type=str, help="List of directories to search for components",
                        default=False)
    parser.add_argument('--verbose', action="store_true", help="How chatty should I be?", default=False)

    return parser


def applyRaftYaw(ccdLayout, raftYaw):
    """Apply raft yaw angle to internal offsets of the CCDs.

    Parameters
    ----------
    ccdLayout : `dict`
        Dictionary containing CCD layout information.
    raftYaw : `float`
        Raft yaw angle in degrees.

    Returns
    -------
    2-item sequence of floats containing the rotated offsets.
    """
    if raftYaw == 0.:
        return ccdLayout['offset']
    new_offset = np.zeros(2, dtype=np.float)
    sinTheta = np.sin(np.radians(raftYaw))
    cosTheta = np.cos(np.radians(raftYaw))
    new_offset[0] = cosTheta*ccdLayout['offset'][0] - sinTheta*ccdLayout['offset'][1]
    new_offset[1] = sinTheta*ccdLayout['offset'][0] + cosTheta*ccdLayout['offset'][1]
    return new_offset


def generateCamera(cameraFile, path):
    """Generate a combined camera YAML definition from component parts.

    Parameters
    ----------
    cameraFile : `str`
        Path to output YAML file.
    path : `str` or `list` of `str`
        List of directories to search for component YAML files or a
        colon-separated path string.  If relative paths are given they will be
        converted to absolute path by combining with  directory specified with
        the output ``cameraFile``.
    """
    cameraFileDir = os.path.dirname(cameraFile)

    if not cameraFile.endswith(".yaml"):
        raise RuntimeError(f"Output file name ({cameraFile}) does not end with .yaml")

    if isinstance(path, str):
        path = path.split(":")
    searchPath = [os.path.join(cameraFileDir, d) for d in path]

    cameraSkl = parseYamlOnPath("cameraHeader.yaml", searchPath)
    cameraTransforms = parseYamlOnPath("cameraTransforms.yaml", searchPath)
    raftData = parseYamlOnPath("rafts.yaml", searchPath)
    ccdData = parseYamlOnPath("ccdData.yaml", searchPath)

    # See if we have an override of the name
    try:
        nameYaml = parseYamlOnPath("name.yaml", searchPath)
    except FileNotFoundError:
        nameOverride = None
    else:
        nameOverride = nameYaml["name"]

    # Copy the camera header, replacing the name if needed.  We can not
    # write out the cameraSkl dataset because that will expand all the
    # YAML references.  We must edit the file itself.
    inputHeader = findYamlOnPath("cameraHeader.yaml", searchPath)
    if nameOverride:
        with open(inputHeader) as infd:
            with open(cameraFile, "w") as outfd:
                replaced = False
                for line in infd:
                    if not replaced and line.startswith("name :") or line.startswith("name:"):
                        line = f"name : {nameOverride}\n"
                        replaced = True
                    print(line, file=outfd, end="")
                if not replaced:
                    raise RuntimeError(f"Override name {nameOverride} specified but no name"
                                       f" to replace in {inputHeader}")
    else:
        shutil.copyfile(inputHeader, cameraFile)

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
                raftCcdData = parseYamlOnPath(f"{raftName}.yaml", searchPath)[raftName]
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
            try:
                raftYaw = perRaftData['yaw']
            except KeyError:
                raftYaw = 0.
            geometryWithinRaft = raftCcdData['geometryWithinRaft'] \
                                 if 'geometryWithinRaft' in raftCcdData else {} # noqa E127

            for ccdName, ccdLayout in ccds.items():
                if ccdName in geometryWithinRaft:
                    doffset = geometryWithinRaft[ccdName]['offset']
                    yaw = geometryWithinRaft[ccdName]['yaw'] + raftYaw
                else:
                    doffset = (0.0, 0.0,)
                    yaw = None

                print(indent(), "%s_%s : " % (raftName[:3], ccdName), file=fd)
                nindent += 1
                print(indent(), "<< : *%s_%s" % (ccdName, detectorType), file=fd)
                if sensorTypes is not None:
                    print(indent(), "detectorType : %i" % (sensorTypes[ccdName]), file=fd)
                print(indent(), "id : %s" % (id0 + ccdLayout['id']), file=fd)
                print(indent(), "serial : %s" % (raftCcdData['ccdSerials'][ccdName]), file=fd)
                print(indent(), "physicalType : %s" % (detectorType), file=fd)
                print(indent(), "refpos : %s" % (ccdLayout['refpos']), file=fd)
                ccdLayoutOffset = applyRaftYaw(ccdLayout, raftYaw)
                print(indent(), "offset : [%g, %g]" % (ccdLayoutOffset[0] + raftOffset[0] + doffset[0],
                                                       ccdLayoutOffset[1] + raftOffset[1] + doffset[1]),
                      file=fd)
                if yaw is not None:
                    print(indent(), "yaw : %g" % (yaw), file=fd)

                if crosstalkCoeffs is not None:
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


def main():
    args = build_argparser().parse_args()

    try:
        generateCamera(args.outputFile, args.path)
    except Exception as e:
        print(f"{e}", file=sys.stderr)
        return 1
    return 0
