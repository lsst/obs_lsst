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

__all__ = ("readRawFitsHeader",)

import re
from astro_metadata_translator import fix_header, merge_headers
import lsst.afw.fits


def readRawFitsHeader(fileName, translator_class=None):
    """Read a FITS header from a raw file and fix it up as required.

    Parameters
    ----------
    fileName : `str`
        Name of the FITS file. Can include a HDU specifier (although 0
        is ignored).
    translator_class : `~astro_metadata_translator.MetadataTranslator`,
                       optional
        Any translator class to use for fixing up the header.

    Returns
    -------
    md : `PropertyList`
        Metadata from file. We also merge the contents with the
        next HDU if an ``INHERIT`` key is not specified. If an explicit
        HDU is encoded with the file name and it is greater than 0 then
        no merging will occur.
    """
    mat = re.search(r"\[(\d+)\]$", fileName)
    hdu = None
    if mat:
        # Treat 0 as a special case
        # For some instruments the primary header is empty
        requested = int(mat.group(1))
        if requested > 0:
            hdu = requested

    if hdu is not None:
        md = lsst.afw.fits.readMetadata(fileName, hdu=hdu)
    else:
        # For raw some of these files need the second header to be
        # read as well. Not all instruments want the double read
        # but for now it's easiest to always merge.
        phdu = lsst.afw.fits.readMetadata(fileName, 0)
        md = lsst.afw.fits.readMetadata(fileName)
        md = merge_headers([phdu, md], mode="overwrite")

    fix_header(md, translator_class=translator_class)
    return md
