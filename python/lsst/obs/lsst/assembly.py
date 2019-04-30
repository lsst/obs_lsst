# This file is part of obs_lsst
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

__all__ = ("attachRawWcsFromBoresight", "fixAmpGeometry", "assembleUntrimmedCcd")

import lsst.log
from lsst.obs.base import bboxFromIraf, MakeRawVisitInfoViaObsInfo, createInitialSkyWcs
from lsst.geom import Box2I, Extent2I
from lsst.ip.isr import AssembleCcdTask

logger = lsst.log.Log.getLogger("LsstCamAssembler")


def attachRawWcsFromBoresight(exposure):
    """Attach a WCS by extracting boresight, rotation, and camera geometry from
    an Exposure.

    Parameters
    ----------
    exposure : `lsst.afw.image.Exposure`
        Image object with attached metadata and detector components.

    Return
    ------
    attached : `bool`
        If True, a WCS component was successfully created and attached to
        ``exposure``.
    """
    md = exposure.getMetadata()
    # Use the generic version since we do not have a mapper available to
    # tell us a specific translator to use.
    visitInfo = MakeRawVisitInfoViaObsInfo(logger)(md)
    exposure.getInfo().setVisitInfo(visitInfo)

    if visitInfo.getBoresightRaDec().isFinite():
        exposure.setWcs(createInitialSkyWcs(visitInfo, exposure.getDetector()))
        return True

    return False


def fixAmpGeometry(amp, bbox, metadata, logCmd=None):
    """Make sure a camera geometry amplifier matches an on-disk bounding box.

    Bounding box differences that are consistent with differences in overscan
    regions are assumed to be overscan regions, which gives us enough
    information to correct the camera geometry.

    Parameters
    ----------
    amp : `lsst.afw.table.AmpInfoRecord`
        Amplifier description from camera gemoetry. Will be modified in-place.
    bbox : `lsst.geom.Box2I`
        The on-disk bounding box of the amplifer image.
    metadata : `lsst.daf.base.PropertyList`
        FITS header metadata from the amplifier HDU.
    logCmd : `function`, optional
        Call back to use to issue log messages.  Arguments to this function
        should match arguments to be accepted by normal logging functions.

    Return
    ------
    modified : `bool`
        `True` if ``amp`` was modified; `False` otherwise.

    Raises
    ------
    RuntimeError
        Raised if the bounding boxes differ in a way that is not consistent
        with just a change in overscan.
    """
    if logCmd is None:
        logCmd = lambda x, *args: None  # noqa
    modified = False
    if amp.getRawBBox() != bbox:  # Oh dear. cameraGeom is wrong -- probably overscan
        if amp.getRawDataBBox().getDimensions() != amp.getBBox().getDimensions():
            raise RuntimeError("Active area is the wrong size: %s v. %s" %
                               (amp.getRawDataBBox().getDimensions(), amp.getBBox().getDimensions()))

        logCmd("amp.getRawBBox() != data.getBBox(); patching. (%s v. %s)", amp.getRawBBox(), bbox)

        w, h = bbox.getDimensions()
        ow, oh = amp.getRawBBox().getDimensions()  # "old" (cameraGeom) dimensions
        #
        # We could trust the BIASSEC keyword, or we can just assume that
        # they've changed the number of overscan pixels (serial and/or
        # parallel).  As Jim Chiang points out, the latter is safer
        #
        fromCamGeom = amp.getRawHorizontalOverscanBBox()
        hOverscanBBox = Box2I(fromCamGeom.getBegin(),
                              Extent2I(w - fromCamGeom.getBeginX(), fromCamGeom.getHeight()))
        fromCamGeom = amp.getRawVerticalOverscanBBox()
        vOverscanBBox = Box2I(fromCamGeom.getBegin(),
                              Extent2I(fromCamGeom.getWidth(), h - fromCamGeom.getBeginY()))
        amp.setRawBBox(bbox)
        amp.setRawHorizontalOverscanBBox(hOverscanBBox)
        amp.setRawVerticalOverscanBBox(vOverscanBBox)
        #
        # This gets all the geometry right for the amplifier, but the size
        # of the untrimmed image will be wrong and we'll put the amp sections
        # in the wrong places, i.e.
        #   amp.getRawXYOffset()
        # will be wrong.  So we need to recalculate the offsets.
        #
        xRawExtent, yRawExtent = amp.getRawBBox().getDimensions()

        x0, y0 = amp.getRawXYOffset()
        ix, iy = x0//ow, y0/oh
        x0, y0 = ix*xRawExtent, iy*yRawExtent
        amp.setRawXYOffset(Extent2I(ix*xRawExtent, iy*yRawExtent))

        modified = True

    #
    # Check the "IRAF" keywords, but don't abort if they're wrong
    #
    # Only warn about the first amp, use debug for the others
    #
    d = metadata.toDict()
    detsec = bboxFromIraf(d["DETSEC"]) if "DETSEC" in d else None
    datasec = bboxFromIraf(d["DATASEC"]) if "DATASEC" in d else None
    biassec = bboxFromIraf(d["BIASSEC"]) if "BIASSEC" in d else None

    if detsec and amp.getBBox() != detsec:
        logCmd("DETSEC doesn't match (%s != %s)", amp.getBBox(), detsec)
    if datasec and amp.getRawDataBBox() != datasec:
        logCmd("DATASEC doesn't match for (%s != %s)", amp.getRawDataBBox(), detsec)
    if biassec and amp.getRawHorizontalOverscanBBox() != biassec:
        logCmd("BIASSEC doesn't match for (%s != %s)", amp.getRawHorizontalOverscanBBox(), detsec)

    return modified


def assembleUntrimmedCcd(amps, exposures):
    """Assemble an untrimmmed CCD from per-amp Exposure objects.

    Parameters
    ----------
    amps : sequence of `lsst.afw.table.AmpInfoRecord`.
        A deterministically-ordered container of camera geometry amplifier
        information.  May be a `~lsst.afw.cameraGeom.Detector`, a
        `~lsst.afw.table.AmpInfoCatalog`, a `list`, or any other sequence.
    exposures : sequence of `lsst.afw.image.Exposure`
        Per-amplifier images, in the same order as ``amps``.

    Returns
    -------
    ccd : `lsst.afw.image.Exposure`
        Assembled CCD image.
    """
    ampDict = {}
    for amp, exposure in zip(amps, exposures):
        ampDict[amp.getName()] = exposure
    config = AssembleCcdTask.ConfigClass()
    config.doTrim = False
    assembleTask = AssembleCcdTask(config=config)
    return assembleTask.assembleCcd(ampDict)
