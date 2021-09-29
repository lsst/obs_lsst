# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
__all__ = ("main", )


import argparse
import glob
import os
import sys

from astropy.table import Table

from lsst.ip.isr import PhotodiodeCalib
from lsst.daf.butler import Butler


def build_argparser():
    """Construct an argument parser for the ``prepare_photodiode.py`` script.

    Returns
    -------
    parser : `argparse.ArgumentParser`
        The argument parser that defines the ``prepare_photodiode.py``
        command line interface.
    """
    parser = argparse.ArgumentParser(description="Reformat photodiode data and include metadata for ingest.")
    parser.add_argument("repository", help="Repository containing raw data to use to construct metadata.")
    parser.add_argument("input_directory", help="Directory to scan for photodiode data.")
    parser.add_argument("output_directory", help="Directory to write the reformatted photodiode data.")
    parser.add_argument("--file_extension", type=str, default=".txt",
                        help="File extension matching photodiode data.")
    parser.add_argument("--reformat", type=bool, default=True, help="Should photodiode data be reformatted?")
    parser.add_argument("--instrument", type=str, default='LSSTCam',
                        help="Instrument to use for these photodiode data.")
    return parser


def main():
    args = build_argparser().parse_args()

    # Create output directory or stop.
    if os.path.exists(args.output_directory):
        print(f"Output directory {args.output_directory} exists.  Exiting.")
        sys.exit(1)
    else:
        print(f"Creating output directory {args.output_directory}")
        os.makedirs(args.output_directory)

    # Determine what files we have to work on.
    globPath = os.path.join(args.input_directory, "*" + args.file_extension)
    inputFiles = glob.glob(globPath)
    print(globPath, len(inputFiles))

    butler = Butler(args.repository)

    ingestFilenames = []
    ingestInstrument = []
    ingestExposureId = []
    for rawPhotodiode in inputFiles:
        photodiode = PhotodiodeCalib.readSummitPhotodiode(rawPhotodiode)
        day_obs = photodiode.getMetadata()['day_obs']
        seq_num = photodiode.getMetadata()['seq_num']

        records = [rec for rec in
                   butler.registry.queryDimensionRecords("exposure", instrument=args.instrument,
                                                         where=f"exposure.day_obs={day_obs} AND "
                                                         f"exposure.seq_num={seq_num}")]
        if len(records) != 1:
            print(f"Found {len(records)} for day_obs {day_obs} seq_num {seq_num}! Skipping!")
            continue
        exposureId = records[0].id
        photodiode.updateMetadata(camera=None, detector=None, filterName=None,
                                  setCalibId=False, setCalibInfo=True, setDate=True,
                                  EXPOSURE=exposureId, INSTRUME=args.instrument)

        photodiodeSubDirectory = os.path.join(args.output_directory, args.instrument,
                                              "photodiode", f"{day_obs}")
        if not os.path.exists(photodiodeSubDirectory):
            os.makedirs(photodiodeSubDirectory)

        outputFilename = os.path.join(photodiodeSubDirectory,
                                      f"photodiode_{args.instrument}_{exposureId}.fits")
        photodiode.writeFits(outputFilename)

        ingestFilenames.append(outputFilename)
        ingestInstrument.append(args.instrument)
        ingestExposureId.append(exposureId)

    ingestTable = Table({"uri": ingestFilenames,
                         "instrument": ingestInstrument,
                         "exposure": ingestExposureId})

    ingestOutputFilename = os.path.join(args.output_directory, "ingestTable.fits")
    ingestTable.write(ingestOutputFilename)
