# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for the LSST Commissioning Camera"""

__all__ = ("LsstComCamTranslator", )

import logging

from .lsstCam import LsstCamTranslator

log = logging.getLogger(__name__)


class LsstComCamTranslator(LsstCamTranslator):
    """Metadata translation for the LSST Commissioning Camera."""

    name = "LSST-ComCam"
    """Name of this translation class"""

    _const_map = {
        "instrument": "comCam",
    }

    # Use the comCam raft definition
    cameraPolicyFile = "policy/comCam.yaml"

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        Looks for "COMCAM" instrument in case-insensitive manner but
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
            if instrument == "comcam" and telescope == "LSST":
                return True

        return False
