#!/bin/bash

# Reingest all the raw files.
# Run this if there have been registry or translator changes.
#
# Process instruments listed on command line, or everything in $DATADIR if you
# don't specify anything

export DYLD_LIBRARY_PATH=${LSST_LIBRARY_PATH}

set -e
DATADIR=${OBS_LSST_DIR}/data/input
cd ${DATADIR}

instruments="$@"
if [ X"$instruments" = X"" ]; then
    instruments=$(ls)
fi

for instrument in $instruments; do
  echo
  echo $instrument

  rm -f "${instrument}/registry.sqlite3"
  if [ -d "${instrument}/raw" ]; then
      mv "${instrument}/raw" "${instrument}/old"
  fi

  ingest_files=$(find "${instrument}/old" -type f)
  echo ingestImages.py "${instrument}" --mode=copy ${ingest_files}
  ingestImages.py "${instrument}" --mode=copy ${ingest_files}
  rm -rf ${instrument}/old
done
