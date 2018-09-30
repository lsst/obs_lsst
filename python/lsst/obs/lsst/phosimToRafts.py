#
# A python script to read phoSim's headers and write the per-raft datafiles
# used by generateCamera.py
#
# This is not really part of obs_lsst, but it's useful to keep it here
#
import argparse
import re
import sys

import lsst.daf.persistence as dafPersist

from segmentationToRafts import writeRaftFile

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read phoSim headers and write the per-raft datafiles")

    parser.add_argument('input', type=str, help="Path to input data repository")
    parser.add_argument('--id', type=str, help="ID for data (visit=XXX)", default=None)
    parser.add_argument('--visit', type=int, help="visit to read", default=None)
    parser.add_argument('-v', '--verbose', action="store_true", help="How chatty should I be?", default=False)

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
    # Due to butler stupidity it can't/won't lookup things when you also specify a channel.  Sigh
    #
    dataId["run"], dataId["snap"] = butler.queryMetadata("raw", ["run", "snap"], dataId)[0]

    if verbose:
        print("DataId = %s" % dataId)

    raftData = {}
    for raftName, detectorName, detector in \
        butler.queryMetadata("raw", ["raftName", "detectorName", "detector"], dataId): # noqa E125

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
        with open("%s.yaml" % raftName, "w") as fd:
            writeRaftFile(fd, raftName, "ITL", raftSerial, raftData[raftName])
