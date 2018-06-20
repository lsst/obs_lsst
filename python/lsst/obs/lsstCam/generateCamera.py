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
import shutil
import yaml

if __name__ == "__main__":
    cameraFile = "camera.yaml"

    cameraSklFile = "camera.skl.yaml"
    cameraDataFile = "cameraData.yaml"

    with open(cameraSklFile) as fd:
        cameraSkl = yaml.load(fd, Loader=yaml.Loader)

    with open(cameraDataFile) as fd:
        cameraData = yaml.load(fd, Loader=yaml.Loader)

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

        for raftName, raftData in cameraData.items():
            try:
                detectorType = raftData["detectorType"]
                ccds = cameraSkl['RAFT_%s' % detectorType]["ccds"]
                amps = cameraSkl['CCD_%s'  % detectorType]["amplifiers"]

            except KeyError:
                raise RuntimeError("Unknown detector type %s" % detectorType)

            nindent += 1

            raftOffset = raftData["offset"]
            id = raftData['id0']
            for ccdName, ccdData in ccds.items():
                print(indent(), "%s_%s : " % (raftName, ccdName), file=fd)
                nindent += 1
                print(indent(), "<< : *%s_%s" % (ccdName, detectorType), file=fd)
                print(indent(), "id : %s" % (id), file=fd); id += 1
                print(indent(), "serial : %s" % (cameraData[raftName]['ccdSerials'][ccdName]), file=fd)
                print(indent(), "refpos : %s" % (ccdData['refpos']), file=fd)
                print(indent(), "offset : [%g, %g]" % (ccdData['offset'][0] + raftOffset[0],
                                                       ccdData['offset'][1] + raftOffset[1]), file=fd)

                print(indent(), "amplifiers :", file=fd)
                nindent += 1
                for ampName, ampData in amps.items():
                    print(indent(), "\"%s\" :" % ampName, file=fd)

                    nindent += 1
                    print(indent(), "<< : *A%s_%s" % (ampName, detectorType), file=fd)
                    print(indent(), "gain : %g" % (cameraData[raftName]['gain'][ccdName][ampName]), file=fd)
                    print(indent(), "readNoise : %g" % (cameraData[raftName]['readNoise'][ccdName][ampName]), file=fd)
                    nindent -= 1
                nindent -= 1

                nindent -= 1

            nindent -= 1
