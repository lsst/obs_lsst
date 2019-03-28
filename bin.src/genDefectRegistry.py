#!/usr/bin/env python

import glob
import os
import re
try:
    import sqlite3 as sqlite
except ImportError:
    import sqlite
import sys
import argparse
import datetime

from lsst.pipe.base import Struct


class Row(Struct):

    def __init__(self, path, version, validStart, validEnd=None):
        super(Row, self).__init__(path=path, version=version, validStart=validStart, validEnd=validEnd)


parser = argparse.ArgumentParser()
parser.add_argument("--create", action="store_true", help="Create new registry (clobber old)?")
parser.add_argument("--root", default=".", help="Root directory")
parser.add_argument("-v", "--verbose", action="store_true", help="Be chattier")
args = parser.parse_args()

registryName = os.path.join(args.root, "defectRegistry.sqlite3")
if args.create and os.path.exists(registryName):
    os.unlink(registryName)

makeTables = not os.path.exists(registryName)

conn = sqlite.connect(registryName)

if makeTables:
    cmd = "create table defect (id integer primary key autoincrement"
    cmd += ", path text, version text, detector int, detectorName text"
    cmd += ", validStart text, validEnd text)"
    conn.execute(cmd)
    conn.commit()

cmd = "INSERT INTO defect VALUES (NULL, ?, ?, ?, ?, ?, ?)"

rowsPerDetector = {}
for f in glob.glob(os.path.join(args.root, "*", "defects*.fits")):
    m = re.search(r'(\S+)/defects_(\d+)\.fits', f)
    if not m:
        print("Unrecognized file: %s" % (f,), file=sys.stderr)
        continue
    #
    # Convert f to be relative to the location of the registry
    #
    f = os.path.relpath(f, args.root)

    startDate = m.group(1).split('/')[-1]
    version = m.group(1)
    det = m.group(2)
    if det not in rowsPerDetector:
        rowsPerDetector[det] = []
    rowsPerDetector[det].append(Row(f, version, startDate))

# Fix up end dates so there are no collisions.
# Defects files for a detector are valid from the date they are registered
# until the next date. This means that any defects file should carry ALL
# the defects that are present at that time.
for det, rowList in rowsPerDetector.items():
    # ISO-8601 will sort just fine without conversion from str
    rowList.sort(key=lambda row: row.validStart)
    for thisRow, nextRow in zip(rowList[:-1], rowList[1:]):
        thisRow.validEnd = (datetime.datetime.strptime(nextRow.validStart, "%Y-%m-%d") -
                            datetime.timedelta(0, 1)).isoformat()  # 1 sec before: sqlite precision is 1 sec
    rowList[-1].validEnd = "2037-12-31"  # End of UNIX time

    for row in rowList:
        if args.verbose:
            print("Registering %s" % row.path)
        conn.execute(cmd, (row.path, row.version, det, "RXX_S00", row.validStart, row.validEnd))

conn.commit()
conn.close()
