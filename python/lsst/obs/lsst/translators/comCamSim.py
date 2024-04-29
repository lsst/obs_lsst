# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for the Simulated LSST Commissioning Camera"""

__all__ = ("LsstComCamSimTranslator", )

import logging
import warnings

import astropy
import astropy.utils.exceptions
from astropy.coordinates import AltAz
from astro_metadata_translator import cache_translation

from .lsstCam import LsstCamTranslator
from .lsst import SIMONYI_TELESCOPE

log = logging.getLogger(__name__)


class LsstComCamSimTranslator(LsstCamTranslator):
    """Metadata translation for the LSST Commissioning Camera."""

    name = "LSSTComCamSim"
    """Name of this translation class"""

    _const_map = {
        "instrument": "LSSTComCamSim",
    }

    cameraPolicyFile = 'policy/comCamSim.yaml'

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        Looks for "COMCAMSIM" instrument in case-insensitive manner but
        must be on LSST telescope.  This avoids confusion with other
        telescopes using commissioning cameras.

        Parameters
        ----------
        header : `dict`-like
            Header to convert to standardized form.
        filename : `str`, optional
            Name of file being translated.

        Returns
        -------
        can : `bool`
            `True` if the header is recognized by this class. `False`
            otherwise.
        """
        if "INSTRUME" in header and "TELESCOP" in header:
            telescope = header["TELESCOP"]
            instrument = header["INSTRUME"].lower()
            if instrument == "comcamsim" and telescope in (SIMONYI_TELESCOPE, "LSST"):
                return True

        return False

    @classmethod
    def fix_header(cls, header, instrument, obsid, filename=None):
        """Fix Simulated ComCam headers.

        Notes
        -----
        Content will be added as needed.

        Corrections are reported as debug level log messages.

        See `~astro_metadata_translator.fix_header` for details of the general
        process.
        """
        modified = False

        # Calculate the standard label to use for log messages
        log_label = cls._construct_log_prefix(obsid, filename)

        # Some simulated files lack RASTART/DECSTART etc headers. Since these
        # are simulated they can be populated directly from the RA/DEC headers.
        synced_radec = False
        for key in ("RA", "DEC"):
            for time in ("START", "END"):
                time_key = f"{key}{time}"
                if not header.get(time_key):
                    if (value := header.get(key)):
                        header[time_key] = value
                        synced_radec = True
        if synced_radec:
            modified = True
            log.debug("%s: Synced RASTART/RAEND/DECSTART/DECEND headers with RA/DEC headers", log_label)

        if not header.get("RADESYS") and header.get("RA") and header.get("DEC"):
            header["RADESYS"] = "ICRS"
            log.debug("%s: Forcing undefined RADESYS to '%s'", log_label, header["RADESYS"])
            modified = True

        if not header.get("TELCODE"):
            if camcode := header.get("CAMCODE"):
                header["TELCODE"] = camcode
                modified = True
                log.debug("%s: Setting TELCODE header from CAMCODE header", log_label)
            else:
                # Get the code from the OBSID.
                code, _ = obsid.split("_", 1)
                header["TELCODE"] = code
                modified = True
                log.debug("%s: Determining telescope code of %s from OBSID", log_label, code)

        return modified

    def _is_on_mountain(self):
        """Indicate whether these data are coming from the instrument
        installed on the mountain.
        Returns
        -------
        is : `bool`
            `True` if instrument is on the mountain.

        Notes
        -----
        TODO: DM-33387 This is currently a terrible hack and MUST be removed
        once CAP-807 and CAP-808 are done.
        Until then, ALL non-calib ComCam data will look like it is on sky.
        """
        return True

    @cache_translation
    def to_altaz_begin(self):
        # Tries to calculate the value. Simulated files for ops-rehearsal 3
        # did not have the AZ/EL headers defined.
        if self.are_keys_ok(["ELSTART", "AZSTART"]):
            return super().to_altaz_begin()

        # Calculate it from the RA/Dec and time.
        # The time is not consistent with the HASTART/AMSTART values.
        # This means that the elevation may well come out negative.
        if self.are_keys_ok(["RA", "DEC"]):
            # Derive from RADec in absence of any other information
            radec = self.to_tracking_radec()
            if radec is not None:
                # This can trigger warnings because of the future dates
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=astropy.utils.exceptions.AstropyWarning)
                    altaz = radec.transform_to(AltAz())
                return altaz

        return None

    @classmethod
    def observing_date_to_offset(cls, observing_date: astropy.time.Time) -> astropy.time.TimeDelta | None:
        # Always use the 12 hour offset.
        return cls._ROLLOVER_TIME
