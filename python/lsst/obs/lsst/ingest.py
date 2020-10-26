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

import re
from lsst.pipe.tasks.ingest import ParseTask
from lsst.pipe.tasks.ingestCalibs import CalibsParseTask
from astro_metadata_translator import ObservationInfo
import lsst.log as lsstLog
from .translators import LsstCamTranslator
from .lsstCamMapper import LsstCamMapper
from ._fitsHeader import readRawFitsHeader

EXTENSIONS = ["fits", "gz", "fz"]  # Filename extensions to strip off

__all__ = ["LsstCamParseTask"]


class LsstCamParseTask(ParseTask):
    """Parser suitable for lsstCam data.

    See `LCA-13501 <https://ls.st/LCA-13501>`_ and
    `LSE-400 <https://ls.st/LSE-400>`_.
    """

    _mapperClass = LsstCamMapper
    _translatorClass = LsstCamTranslator

    def __init__(self, config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)

        self.observationInfo = None

    def getInfo(self, filename):
        """Get information about the image from the filename and its contents

        Here, we open the image and parse the header.

        Parameters
        ----------
        filename : `str`
            Name of file to inspect

        Returns
        -------
        info : `dict`
            File properties
        linfo : `list` of `dict`
            List of file properties. Always contains the same as ``info``
            because no extensions are read.
        """
        md = readRawFitsHeader(filename, translator_class=self._translatorClass)
        phuInfo = self.getInfoFromMetadata(md)
        # No extensions to worry about
        return phuInfo, [phuInfo]

    def getInfoFromMetadata(self, md, info=None):
        """Attempt to pull the desired information out of the header.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList`
            FITS header.
        info : `dict`, optional
            File properties, to be updated by this routine. If `None`
            it will be created.

        Returns
        -------
        info : `dict`
            Translated information from the metadata. Updated form of the
            input parameter.

        Notes
        -----

        This is done through two mechanisms:

        * translation: a property is set directly from the relevant header
                       keyword.
        * translator: a property is set with the result of calling a method.

        The translator methods receive the header metadata and should return
        the appropriate value, or None if the value cannot be determined.

        This implementation constructs an
        `~astro_metadata_translator.ObservationInfo` object prior to calling
        each translator method, making the translated information available
        through the ``observationInfo`` attribute.

        """
        # Always calculate a new ObservationInfo since getInfo calls
        # this method repeatedly for each header.
        self.observationInfo = ObservationInfo(md, translator_class=self._translatorClass,
                                               pedantic=False)

        info = super().getInfoFromMetadata(md, info)

        # Ensure that the translated ObservationInfo is cleared.
        # This avoids possible confusion.
        self.observationInfo = None
        return info

    def translate_wavelength(self, md):
        """Translate wavelength provided by teststand readout.

        The teststand driving script asks for a wavelength, and then reads the
        value back to ensure that the correct position was moved to. This
        number is therefore read back with sub-nm precision.  Typically the
        position is within 0.005nm of the desired position, so we warn if it's
        not very close to an integer value.

        Future users should be aware that the ``HIERARCH MONOCH-WAVELENG`` key
        is NOT the requested value, and therefore cannot be used as a
        cross-check that the wavelength was close to the one requested.
        The only record of the wavelength that was set is in the original
        filename.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            Image metadata.

        Returns
        -------
        wavelength : `int`
            The recorded wavelength in nanometers as an `int`.
        """
        bad_wl = -666  # Bad value for wavelength
        if "MONOWL" not in md:
            return bad_wl

        raw_wl = float(md.getScalar("MONOWL"))

        # Negative wavelengths are bad so normalize the bad value
        if raw_wl < 0:
            return bad_wl

        wl = int(round(raw_wl))
        if abs(raw_wl-wl) >= 0.1:
            logger = lsstLog.Log.getLogger('obs.lsst.ingest')
            logger.warn(
                'Translated significantly non-integer wavelength; '
                '%s is more than 0.1nm from an integer value', raw_wl)
        return wl

    def translate_dateObs(self, md):
        """Retrieve the date of observation as an ISO format string.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            Image metadata.

        Returns
        -------
        dateObs : `str`
            The date that the data was taken in FITS ISO format,
            e.g. ``2018-08-20T21:56:24.608``.
        """
        dateObs = self.observationInfo.datetime_begin
        dateObs.format = "isot"
        return str(dateObs)

    translate_date = translate_dateObs

    def translate_dayObs(self, md):
        """Generate the day that the observation was taken.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            image metadata

        Returns
        -------
        dayObs : `str`
            The day that the data was taken, e.g. ``1958-02-05``.
        """
        dayObs = str(self.observationInfo.observing_day)
        return "-".join([dayObs[:4], dayObs[4:6], dayObs[6:]])

    def translate_snap(self, md):
        """Extract snap number from metadata.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            Image metadata.

        Returns
        -------
        snap : `int`
            Snap number (default: 0).
        """
        try:
            return int(md.getScalar("SNAP"))
        except KeyError:
            return 0

    def translate_detectorName(self, md):
        """Extract ccd ID from CHIPID.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            Image metadata.

        Returns
        -------
        ccdID : `str`
            Name of ccd, e.g. ``S01``.
        """
        return self.observationInfo.detector_name

    def translate_raftName(self, md):
        """Extract raft ID from CHIPID.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            Image metadata.

        Returns
        -------
        raftID : `str`
            Name of raft, e.g. ``R21``.
        """
        return self.observationInfo.detector_group

    def translate_detector(self, md):
        """Extract detector ID from metadata

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            Image metadata.

        Returns
        -------
        detID : `int`
            Detector ID, e.g. ``4``.
        """
        return self.observationInfo.detector_num

    def translate_expTime(self, md):
        return self.observationInfo.exposure_time.value

    def translate_object(self, md):
        return self.observationInfo.object

    def translate_imageType(self, md):
        obstype = self.observationInfo.observation_type.upper()
        # Dictionary for obstype values is not yet clear
        if obstype == "SCIENCE":
            obstype = "SKYEXP"
        return obstype

    def translate_filter(self, md):
        return self.observationInfo.physical_filter

    def translate_lsstSerial(self, md):
        return self.observationInfo.detector_serial

    def translate_run(self, md):
        return self.observationInfo.science_program

    def translate_visit(self, md):
        return self.observationInfo.visit_id

    def translate_obsid(self, md):
        return self.observationInfo.observation_id

    def translate_testType(self, md):
        # Gen2 prefers upper case
        return self.observationInfo.observation_reason.upper()

    def translate_expGroup(self, md):
        return self.observationInfo.exposure_group

    def translate_expId(self, md):
        return self.observationInfo.exposure_id

    def translate_controller(self, md):
        if "CONTRLLR" in md:
            if md["CONTRLLR"]:
                return md["CONTRLLR"]
            else:
                # Was undefined, sometimes it is in fact in the OBSID
                obsid = self.translate_obsid(md)
                components = obsid.split("_")
                if len(components) >= 2 and len(components[1]) == 1:
                    # AT_C_20190319_00001
                    return components[1]
                # Assume OCS control
                return "O"
        else:
            # Assume it is under camera control
            return "C"


class LsstCamCalibsParseTask(CalibsParseTask):
    """Parser for calibs."""

    def _translateFromCalibId(self, field, md):
        """Get a value from the CALIB_ID written by ``constructCalibs``."""
        data = md.getScalar("CALIB_ID")
        match = re.search(r".*%s=(\S+)" % field, data)
        return match.groups()[0]

    def translate_raftName(self, md):
        return self._translateFromCalibId("raftName", md)

    def translate_detectorName(self, md):
        return self._translateFromCalibId("detectorName", md)

    def translate_detector(self, md):
        # this is not a _great_ fix, but this obs_package is enforcing that
        # detectors be integers and there's not an elegant way of ensuring
        # this is the right type really
        return int(self._translateFromCalibId("detector", md))

    def translate_filter(self, md):
        return self._translateFromCalibId("filter", md)

    def translate_calibDate(self, md):
        return self._translateFromCalibId("calibDate", md)
