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

"""
A python script to read phoSim's headers and write the per-raft datafiles
used by generateCamera.py

This is not really part of obs_lsst, but it's useful to keep it here.
"""

__all__ = ("main",)

import argparse
import re
import sys
import os

import lsst.log
import lsst.daf.persistence as dafPersist

logger = lsst.log.getLogger(__name__)


def writeRaftFile(fd, raftName, detectorType, raftSerial, ccdData):
    print(f"""\
{raftName} :
  detectorType : {detectorType}
  raftSerial : {raftSerial}

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
""", file=fd)
    for ccdName in ccdData:
        print(f"    {ccdName} :", file=fd)

        for ampName, (gain, readNoise) in ccdData[ccdName].items():
            print(f"      {ampName} : {{ gain : {gain:5.3f}, readNoise : {readNoise:4.2f} }}", file=fd)


def build_argparser():
    """Construct an argument parser for the ``generateCamera.py`` script.

    Returns
    -------
    argparser : `argparse.ArgumentParser`
        The argument parser that defines the ``translate_header.py``
        command-line interface.
    """
    parser = argparse.ArgumentParser(description="Read phoSim headers and write the per-raft datafiles")

    parser.add_argument('input', type=str, help="Path to input data repository")
    parser.add_argument('--id', type=str, help="ID for data (visit=XXX)", default=None)
    parser.add_argument('--visit', type=int, help="visit to read", default=None)
    parser.add_argument('--log', type=str, help="Specify logging level to use", default="WARN")
    parser.add_argument('--output_dir', type=str,
                        help="Path to output data directory (must exist)", default=None)

    return parser


def processPhosimData(ids, visit, inputDir, outputDir):
    """Process the specified data.

    Parameters
    ----------
    ids : `str`
        DataId to be used to access the data. Can only be given as
        ``visit=NNN`` form. ``visit`` is used if this is `None`.
        ``expId`` is assumed to be an alias for ``visit`` in PhoSim.
    visit : `int`
        Explicit visit number to read from repository. Only used if
        ``ids`` is `None` or to check that it is consistent with the value
        in ``ids``.
    inputDir : `str`
        Location of input butler repository.
    outputDir : `str`
        Location to write raft files. Will use current directory if `None`.

    Notes
    -----
    If no visit is specified in the ``ids`` or ``visit`` arguments the
    repository is queried and the first visit found is used.

    Raises
    ------
    RuntimeError:
        Raised if there is an inconsistency with the visit specification.
        Other exceptions may be raised by butler usage.
    """
    if ids is not None:
        mat = re.search(r"visit=(\d+)", ids)
        if not mat:
            raise RuntimeError("Please specify an integer visit in the id string")
        idvisit = int(mat.group(1))

        # Only allowed to specify a visit and id if they happen to be the same
        if visit is None:
            visit = idvisit
        elif idvisit != visit:
            raise RuntimeError("Please specify either --id or --visit (or be consistent)")

    butler = dafPersist.Butler(inputDir)
    #
    # Lookup the amp names
    #
    camera = butler.get("camera")
    det = list(camera)[0]
    ampNames = [a.getName() for a in det]

    if visit is None:
        rawData = butler.queryMetadata("raw", ["visit"])
        if not rawData:
            raise RuntimeError(f"No raw data found in butler repository at {inputDir}")
        visit = rawData[0]

    # For phosim we declare that visit==expId
    dataId = dict(expId=visit)
    #
    # Due to butler stupidity it can't/won't lookup things when you also
    # specify a channel.  Sigh
    #
    queryResults = butler.queryMetadata("raw", ["run", "snap"], dataId)
    if not queryResults:
        raise RuntimeError(f"Unable to find any data to match dataId {dataId}")

    dataId["run"], dataId["snap"] = queryResults[0]

    logger.info("DataId = %s", dataId)

    raftData = {}
    for raftName, detectorName, detector in \
            butler.queryMetadata("raw", ["raftName", "detectorName", "detector"], dataId):

        dataId["detector"] = detector   # more of the butler stupidity

        logger.warn("Processing data from detector %s_%s", raftName, detectorName)

        if raftName not in raftData:
            raftData[raftName] = {}
        if detectorName not in raftData[raftName]:
            raftData[raftName][detectorName] = {}

        for i, ampName in enumerate(ampNames, 1):
            md = butler.get("raw_amp_md", dataId,
                            raftName=raftName, detectorName=detectorName, channel=i)
            gain = md["GAIN"]
            readNoise = md["RDNOISE"]
            assert(ampName[-2:] == md["EXTNAME"][-2:])

            raftData[raftName][detectorName][ampName] = (gain, readNoise)

    raftId = 0
    for raftName, ccdData in raftData.items():
        raftSerial = f"LCA-11021_RTM-{raftId:03d}"  # won't be deterministic in reality!
        raftId += 1

        if raftName in ("R00", "R40", "R04", "R44"):
            continue
        if outputDir:
            prefix = outputDir
        else:
            prefix = os.path.curdir
        outfile = os.path.join(prefix, f"{raftName}.yaml")
        logger.debug("Writing raft information to %s", outfile)
        with open(outfile, "w") as fd:
            writeRaftFile(fd, raftName, "ITL", raftSerial, raftData[raftName])

    return


def main():
    args = build_argparser().parse_args()

    logLevel = args.log.upper()
    logger.setLevel(getattr(logger, logLevel))

    try:
        processPhosimData(args.id, args.visit, args.input, args.output_dir)
    except Exception as e:
        print(f"{e}", file=sys.stderr)
        return 1
    return 0
