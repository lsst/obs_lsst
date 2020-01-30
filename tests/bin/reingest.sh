#!/bin/bash

# Reingest all the raw files.
# Run this if there have been registry or translator changes.

export DYLD_LIBRARY_PATH=${LSST_LIBRARY_PATH}

set -e
DATADIR=${OBS_LSST_DIR}/data/input
cd ${DATADIR}

for instrument in *; do
  echo
  echo $instrument

  rm "${instrument}/registry.sqlite3"
  mv "${instrument}/raw" "${instrument}/old"

  ingest_files=$(find "${instrument}/old" -type f)
  echo ingestImages.py "${instrument}" --mode=copy ${ingest_files}
  ingestImages.py "${instrument}" --mode=copy ${ingest_files}
  rm -rf ${instrument}/old
done
