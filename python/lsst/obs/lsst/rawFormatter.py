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

"""Gen3 Butler Formatters for LSST raw data.
"""

__all__ = (
    "LsstCamRawFormatter",
    "LatissRawFormatter",
    "LsstCamImSimRawFormatter",
    "LsstCamPhoSimRawFormatter",
    "LsstTS8RawFormatter",
    "LsstTS3RawFormatter",
    "LsstComCamRawFormatter",
    "LsstUCDCamRawFormatter",
)

import numpy as np
from astro_metadata_translator import fix_header, merge_headers

import lsst.afw.fits
from lsst.obs.base import FitsRawFormatterBase
from lsst.obs.base.formatters.fitsExposure import standardizeAmplifierParameters
from lsst.afw.cameraGeom import makeUpdatedDetector

from ._instrument import LsstCam, Latiss, \
    LsstCamImSim, LsstCamPhoSim, LsstTS8, \
    LsstTS3, LsstUCDCam, LsstComCam
from .translators import LatissTranslator, LsstCamTranslator, \
    LsstUCDCamTranslator, LsstTS3Translator, LsstComCamTranslator, \
    LsstCamPhoSimTranslator, LsstTS8Translator, LsstCamImSimTranslator
from .assembly import fixAmpsAndAssemble, fixAmpGeometry, readRawAmps, warn_once


class LsstCamRawFormatter(FitsRawFormatterBase):
    translatorClass = LsstCamTranslator
    filterDefinitions = LsstCam.filterDefinitions
    _instrument = LsstCam

    # These named HDUs' headers will be checked for and added to metadata.
    _extraFitsHeaders = ["REB_COND"]

    def readMetadata(self):
        """Read all header metadata directly into a PropertyList.

        Will merge additional headers if required.

        Returns
        -------
        metadata : `~lsst.daf.base.PropertyList`
            Header metadata.
        """
        file = self.fileDescriptor.location.path

        with lsst.afw.fits.Fits(file, "r") as hdu:
            hdu.setHdu(0)
            base_md = hdu.readMetadata()

            # Any extra HDUs we need to read.
            ehdrs = []
            for hduname in self._extraFitsHeaders:
                try:
                    hdu.setHdu(hduname)
                    ehdr = hdu.readMetadata()
                except lsst.afw.fits.FitsError:
                    # The header doesn't exist in this file. Skip.
                    continue
                else:
                    ehdrs.append(ehdr)

        final_md = merge_headers([base_md] + ehdrs, mode="overwrite")
        fix_header(final_md, translator_class=self.translatorClass)
        return final_md

    def stripMetadata(self):
        """Remove metadata entries that are parsed into components."""
        if "CRVAL1" not in self.metadata:
            # No need to strip WCS since we do not seem to have any WCS.
            return
        super().stripMetadata()

    def getDetector(self, id):
        in_detector = self._instrument.getCamera()[id]
        # The detectors attached to the Camera object represent the on-disk
        # amplifier geometry, not the assembled raw.  But Butler users
        # shouldn't know or care about what's on disk; they want the Detector
        # that's equivalent to `butler.get("raw", ...).getDetector()`, so we
        # adjust it accordingly.  This parallels the logic in
        # fixAmpsAndAssemble, but that function and the ISR AssembleCcdTask it
        # calls aren't set up to handle bare bounding boxes with no pixels.  We
        # also can't remove those without API breakage.  So this is fairly
        # duplicative, and hence fragile.
        # We start by fixing amp bounding boxes based on the size of the amp
        # images themselves, because the camera doesn't have the right overscan
        # regions for all images.
        filename = self.fileDescriptor.location.path
        temp_detector = in_detector.rebuild()
        temp_detector.clear()
        with warn_once(filename) as logCmd:
            for n, in_amp in enumerate(in_detector):
                reader = lsst.afw.image.ImageFitsReader(filename, hdu=(n + 1))
                out_amp, _ = fixAmpGeometry(in_amp,
                                            bbox=reader.readBBox(),
                                            metadata=reader.readMetadata(),
                                            logCmd=logCmd)
                temp_detector.append(out_amp)
        adjusted_detector = temp_detector.finish()
        # Now we need to apply flips and offsets to reflect assembly.  The
        # function call that does this in fixAmpsAndAssemble is down inside
        # ip.isr.AssembleCcdTask.
        return makeUpdatedDetector(adjusted_detector)

    def readImage(self):
        # Docstring inherited.
        return self.readFull().getImage()

    def readFull(self):
        # Docstring inherited.
        rawFile = self.fileDescriptor.location.path
        amplifier, detector, _ = standardizeAmplifierParameters(
            self.checked_parameters,
            self._instrument.getCamera()[self.observationInfo.detector_num],
        )
        if amplifier is not None:
            # LSST raws are already per-amplifier on disk, and in a different
            # assembly state than all of the other images we see in
            # DM-maintained formatters.  And we also need to deal with the
            # on-disk image having different overscans from our nominal
            # detector.  So we can't use afw.cameraGeom.AmplifierIsolator for
            # most of the implementation (as other formatters do), but we can
            # call most of the same underlying code to do the work.

            def findAmpHdu(name):
                """Find the HDU for the amplifier with the given name,
                according to cameraGeom.
                """
                for hdu, amp in enumerate(detector):
                    if amp.getName() == name:
                        return hdu + 1
                raise LookupError(f"Could not find HDU for amp with name {name}.")

            reader = lsst.afw.image.ImageFitsReader(rawFile, hdu=findAmpHdu(amplifier.getName()))
            image = reader.read(dtype=np.dtype(np.int32), allowUnsafe=True)
            with warn_once(rawFile) as logCmd:
                # Extract an amplifier from the on-disk detector and fix its
                # overscan bboxes as necessary to match the on-disk bbox.
                adjusted_amplifier_builder, _ = fixAmpGeometry(
                    detector[amplifier.getName()],
                    bbox=image.getBBox(),
                    metadata=reader.readMetadata(),
                    logCmd=logCmd,
                )
                on_disk_amplifier = adjusted_amplifier_builder.finish()
            # We've now got two Amplifier objects in play:
            # A) 'amplifier' is what the user wants
            # B) 'on_disk_amplifier' represents the subimage we have.
            # The one we want has the orientation/shift state of (A) with
            # the overscan regions of (B).
            comparison = amplifier.compareGeometry(on_disk_amplifier)
            # If the flips or origins differ, we need to modify the image
            # itself.
            if comparison & comparison.FLIPPED:
                from lsst.afw.math import flipImage
                image = flipImage(
                    image,
                    comparison & comparison.FLIPPED_X,
                    comparison & comparison.FLIPPED_Y,
                )
            if comparison & comparison.SHIFTED:
                image.setXY0(amplifier.getRawBBox().getMin())
            # Make a single-amplifier detector that reflects the image we're
            # returning.
            detector_builder = detector.rebuild()
            detector_builder.clear()
            detector_builder.unsetCrosstalk()
            if comparison & comparison.REGIONS_DIFFER:
                # We can't just install the amplifier the user gave us, because
                # that has the wrong overscan regions; instead we transform the
                # on-disk amplifier to have the same orientation and offsets as
                # the given one.
                adjusted_amplifier_builder.transform(
                    outOffset=on_disk_amplifier.getRawXYOffset(),
                    outFlipX=amplifier.getRawFlipX(),
                    outFlipY=amplifier.getRawFlipY(),
                )
                detector_builder.append(adjusted_amplifier_builder)
                detector_builder.setBBox(adjusted_amplifier_builder.getBBox())
            else:
                detector_builder.append(amplifier.rebuild())
                detector_builder.setBBox(amplifier.getBBox())
            exposure = lsst.afw.image.makeExposure(lsst.afw.image.makeMaskedImage(image))
            exposure.setDetector(detector_builder.finish())
        else:
            ampExps = readRawAmps(rawFile, detector)
            exposure = fixAmpsAndAssemble(ampExps, rawFile)
        self.attachComponentsFromMetadata(exposure)
        return exposure


class LatissRawFormatter(LsstCamRawFormatter):
    translatorClass = LatissTranslator
    _instrument = Latiss
    filterDefinitions = Latiss.filterDefinitions
    wcsFlipX = True


class LsstCamImSimRawFormatter(LsstCamRawFormatter):
    translatorClass = LsstCamImSimTranslator
    _instrument = LsstCamImSim
    filterDefinitions = LsstCamImSim.filterDefinitions


class LsstCamPhoSimRawFormatter(LsstCamRawFormatter):
    translatorClass = LsstCamPhoSimTranslator
    _instrument = LsstCamPhoSim
    filterDefinitions = LsstCamPhoSim.filterDefinitions
    _extraFitsHeaders = [1]


class LsstTS8RawFormatter(LsstCamRawFormatter):
    translatorClass = LsstTS8Translator
    _instrument = LsstTS8
    filterDefinitions = LsstTS8.filterDefinitions


class LsstTS3RawFormatter(LsstCamRawFormatter):
    translatorClass = LsstTS3Translator
    _instrument = LsstTS3
    filterDefinitions = LsstTS3.filterDefinitions


class LsstComCamRawFormatter(LsstCamRawFormatter):
    translatorClass = LsstComCamTranslator
    _instrument = LsstComCam
    filterDefinitions = LsstComCam.filterDefinitions


class LsstUCDCamRawFormatter(LsstCamRawFormatter):
    translatorClass = LsstUCDCamTranslator
    _instrument = LsstUCDCam
    filterDefinitions = LsstUCDCam.filterDefinitions
