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

__all__ = ("LsstCam", "LsstCamImSim", "LsstCamPhoSim", "LsstTS8",
           "Latiss", "LsstTS3", "LsstUCDCam", "LsstComCam", "LsstComCamSim",
           "LsstCamSim")

import datetime
import hashlib
import importlib.resources

import lsst.obs.base.yamlCamera as yamlCamera
from lsst.utils.introspection import get_full_type_name
from lsst.obs.base import Instrument, VisitSystem
from .filters import (LSSTCAM_FILTER_DEFINITIONS, LATISS_FILTER_DEFINITIONS,
                      LSSTCAM_IMSIM_FILTER_DEFINITIONS, TS3_FILTER_DEFINITIONS,
                      TS8_FILTER_DEFINITIONS, COMCAM_FILTER_DEFINITIONS,
                      GENERIC_FILTER_DEFINITIONS, UCD_FILTER_DEFINITIONS,
                      )

from .translators import LatissTranslator, LsstCamTranslator, \
    LsstUCDCamTranslator, LsstTS3Translator, LsstComCamTranslator, \
    LsstCamPhoSimTranslator, LsstTS8Translator, LsstCamImSimTranslator, \
    LsstComCamSimTranslator, LsstCamSimTranslator

from .translators.lsst import GROUP_RE, TZERO_DATETIME


class LsstCam(Instrument):
    """Gen3 Butler specialization for the LSST Main Camera.

    Parameters
    ----------
    camera : `lsst.cameraGeom.Camera`
        Camera object from which to extract detector information.
    filters : `list` of `FilterDefinition`
        An ordered list of filters to define the set of PhysicalFilters
        associated with this instrument in the registry.

    While both the camera geometry and the set of filters associated with a
    camera are expected to change with time in general, their Butler Registry
    representations defined by an Instrument do not.  Instead:

     - We only extract names, IDs, and purposes from the detectors in the
       camera, which should be static information that actually reflects
       detector "slots" rather than the physical sensors themselves.  Because
       the distinction between physical sensors and slots is unimportant in
       the vast majority of Butler use cases, we just use "detector" even
       though the concept really maps better to "detector slot".  Ideally in
       the future this distinction between static and time-dependent
       information would be encoded in cameraGeom itself (e.g. by making the
       time-dependent Detector class inherit from a related class that only
       carries static content).

     - The Butler Registry is expected to contain physical_filter entries for
       all filters an instrument has ever had, because we really only care
       about which filters were used for particular observations, not which
       filters were *available* at some point in the past.  And changes in
       individual filters over time will be captured as changes in their
       TransmissionCurve datasets, not changes in the registry content (which
       is really just a label).  While at present Instrument and Registry
       do not provide a way to add new physical_filters, they will in the
       future.
    """
    filterDefinitions = LSSTCAM_FILTER_DEFINITIONS
    instrument = "LSSTCam"
    policyName = "lsstCam"
    translatorClass = LsstCamTranslator
    obsDataPackage = "obs_lsst_data"
    visitSystem = VisitSystem.BY_SEQ_START_END

    @property
    def configPaths(self):
        return ["resource://lsst.obs.lsst/resources/config",
                f"resource://lsst.obs.lsst/resources/config/{self.policyName}"]

    @classmethod
    def getName(cls):
        # Docstring inherited from Instrument.getName
        return cls.instrument

    @classmethod
    def getCamera(cls):
        # Constructing a YAML camera takes a long time but we rely on
        # yamlCamera to cache for us.
        with importlib.resources.path(
            "lsst.obs.lsst", f"resources/policy/{cls.policyName}.yaml"
        ) as cameraYamlFile:
            camera = yamlCamera.makeCamera(cameraYamlFile)
        if camera.getName() != cls.getName():
            raise RuntimeError(f"Expected to read camera geometry for {cls.instrument}"
                               f" but instead got geometry for {camera.getName()}")
        return camera

    def _make_default_dimension_packer(
        self,
        config_attr,
        data_id,
        is_exposure=None,
        default="rubin",
    ):
        # Docstring inherited from Instrument._make_default_dimension_packer.
        # Only difference is the change to default above.
        return super()._make_default_dimension_packer(
            config_attr,
            data_id,
            is_exposure=is_exposure,
            default=default,
        )

    def getRawFormatter(self, dataId):
        # Docstring inherited from Instrument.getRawFormatter
        # local import to prevent circular dependency
        from .rawFormatter import LsstCamRawFormatter
        return LsstCamRawFormatter

    def register(self, registry, update=False):
        # Docstring inherited from Instrument.register
        # The maximum values below make Gen3's ObservationDataIdPacker produce
        # outputs that match Gen2's ccdExposureId.
        obsMax = self.translatorClass.max_exposure_id()
        # Make sure this is at least 1 to avoid non-uniqueness issues (e.g.
        # for data ids that also get used in indexing).
        detectorMax = max(self.translatorClass.DETECTOR_MAX, 1)
        with registry.transaction():
            registry.syncDimensionData(
                "instrument",
                {
                    "name": self.getName(),
                    "detector_max": detectorMax,
                    "visit_max": obsMax,
                    "exposure_max": obsMax,
                    "class_name": get_full_type_name(self),
                    "visit_system": None if self.visitSystem is None else self.visitSystem.value,
                },
                update=update
            )
            for detector in self.getCamera():
                registry.syncDimensionData("detector", self.extractDetectorRecord(detector), update=update)

            self._registerFilters(registry, update=update)

    def extractDetectorRecord(self, camGeomDetector):
        """Create a Gen3 Detector entry dict from a cameraGeom.Detector.
        """
        # All of the LSST instruments have detector names like R??_S??; we'll
        # split them up here, and instruments with only one raft can override
        # to change the group to something else if desired.
        # Long-term, we should get these fields into cameraGeom separately
        # so there's no need to specialize at this stage.
        # They are separate in ObservationInfo
        group, name = camGeomDetector.getName().split("_")

        # getType() returns a pybind11-wrapped enum, which unfortunately
        # has no way to extract the name of just the value (it's always
        # prefixed by the enum type name).
        purpose = str(camGeomDetector.getType()).split(".")[-1]

        return dict(
            instrument=self.getName(),
            id=camGeomDetector.getId(),
            full_name=camGeomDetector.getName(),
            name_in_raft=name,
            purpose=purpose,
            raft=group,
        )

    @classmethod
    def group_name_to_group_id(cls, group_name: str) -> int:
        """Translate the exposure group name to an integer.

        Parameters
        ----------
        group_name : `str`
            The name of the exposure group.

        Returns
        -------
        id : `int`
            The exposure group name in integer form. This integer might be
            used as an ID to uniquely identify the group in contexts where
            a string can not be used.

        Notes
        -----
        If given a group name that can be directly cast to an integer it
        returns the integer. If the group name looks like an ISO date the ID
        returned is seconds since an arbitrary recent epoch. Otherwise
        the group name is hashed and the first 14 digits of the hash is
        returned along with the length of the group name.
        """
        # If the group is an int we return it
        try:
            group_id = int(group_name)
            return group_id
        except ValueError:
            pass

        # A Group is defined as ISO date with an extension
        # The integer must be the same for a given group so we can never
        # use datetime_begin.
        # Nominally a GROUPID looks like "ISODATE+N" where the +N is
        # optional.  This can be converted to seconds since epoch with
        # N being zero-padded to 4 digits and appended (defaulting to 0).
        # For early data lacking that form we hash the group and return
        # the int.
        matches_date = GROUP_RE.match(group_name)
        if matches_date:
            iso_str = matches_date.group(1)
            fraction = matches_date.group(2)
            n = matches_date.group(3)
            if n is not None:
                n = int(n)
            else:
                n = 0
            iso = datetime.datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S")

            tdelta = iso - TZERO_DATETIME
            epoch = int(tdelta.total_seconds())

            # Form the integer from EPOCH + 3 DIGIT FRAC + 0-pad N
            group_id = int(f"{epoch}{fraction}{n:04d}")
        else:
            # Non-standard string so convert to numbers
            # using a hash function. Use the first N hex digits
            group_bytes = group_name.encode("us-ascii")
            hasher = hashlib.blake2b(group_bytes)
            # Need to be big enough it does not possibly clash with the
            # date-based version above
            digest = hasher.hexdigest()[:14]
            group_id = int(digest, base=16)

            # To help with hash collision, append the string length
            group_id = int(f"{group_id}{len(group_name):02d}")

        return group_id


class LsstComCam(LsstCam):
    """Gen3 Butler specialization for ComCam data.
    """

    filterDefinitions = COMCAM_FILTER_DEFINITIONS
    instrument = "LSSTComCam"
    policyName = "comCam"
    translatorClass = LsstComCamTranslator

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstComCamRawFormatter
        return LsstComCamRawFormatter


class LsstComCamSim(LsstCam):
    """Gen3 Butler specialization for ComCamSim data.
    """

    filterDefinitions = COMCAM_FILTER_DEFINITIONS
    instrument = "LSSTComCamSim"
    policyName = "comCamSim"
    translatorClass = LsstComCamSimTranslator

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstComCamSimRawFormatter
        return LsstComCamSimRawFormatter


class LsstCamSim(LsstCam):
    """Gen3 Butler specialization for LSSTCamSim data.
    """

    filterDefinitions = LSSTCAM_FILTER_DEFINITIONS
    instrument = "LSSTCamSim"
    policyName = "lsstCamSim"
    translatorClass = LsstCamSimTranslator

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstCamSimRawFormatter
        return LsstCamSimRawFormatter


class LsstCamImSim(LsstCam):
    """Gen3 Butler specialization for ImSim simulations.
    """

    instrument = "LSSTCam-imSim"
    policyName = "imsim"
    translatorClass = LsstCamImSimTranslator
    filterDefinitions = LSSTCAM_IMSIM_FILTER_DEFINITIONS
    visitSystem = VisitSystem.ONE_TO_ONE

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstCamImSimRawFormatter
        return LsstCamImSimRawFormatter

    def _make_default_dimension_packer(
        self,
        config_attr,
        data_id,
        is_exposure=None,
        default="observation",
    ):
        # Docstring inherited from Instrument._make_default_dimension_packer.
        # Only difference is the change to default above (which reverts back
        # the default in lsst.pipe.base.Instrument).
        return super()._make_default_dimension_packer(
            config_attr,
            data_id,
            is_exposure=is_exposure,
            default=default,
        )


class LsstCamPhoSim(LsstCam):
    """Gen3 Butler specialization for Phosim simulations.
    """

    instrument = "LSSTCam-PhoSim"
    policyName = "phosim"
    translatorClass = LsstCamPhoSimTranslator
    filterDefinitions = GENERIC_FILTER_DEFINITIONS
    visitSystem = VisitSystem.ONE_TO_ONE

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstCamPhoSimRawFormatter
        return LsstCamPhoSimRawFormatter

    def _make_default_dimension_packer(
        self,
        config_attr,
        data_id,
        is_exposure=None,
        default="observation",
    ):
        # Docstring inherited from Instrument._make_default_dimension_packer.
        # Only difference is the change to default above (which reverts back
        # the default in lsst.pipe.base.Instrument).
        return super()._make_default_dimension_packer(
            config_attr,
            data_id,
            is_exposure=is_exposure,
            default=default,
        )


class LsstTS8(LsstCam):
    """Gen3 Butler specialization for raft test stand data.
    """

    filterDefinitions = TS8_FILTER_DEFINITIONS
    instrument = "LSST-TS8"
    policyName = "ts8"
    translatorClass = LsstTS8Translator
    visitSystem = VisitSystem.ONE_TO_ONE

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstTS8RawFormatter
        return LsstTS8RawFormatter

    def _make_default_dimension_packer(
        self,
        config_attr,
        data_id,
        is_exposure=None,
        default="observation",
    ):
        # Docstring inherited from Instrument._make_default_dimension_packer.
        # Only difference is the change to default above (which reverts back
        # the default in lsst.pipe.base.Instrument).
        return super()._make_default_dimension_packer(
            config_attr,
            data_id,
            is_exposure=is_exposure,
            default=default,
        )


class LsstUCDCam(LsstCam):
    """Gen3 Butler specialization for UCDCam test stand data.
    """
    filterDefinitions = UCD_FILTER_DEFINITIONS
    instrument = "LSST-UCDCam"
    policyName = "ucd"
    translatorClass = LsstUCDCamTranslator
    visitSystem = VisitSystem.ONE_TO_ONE

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstUCDCamRawFormatter
        return LsstUCDCamRawFormatter

    def _make_default_dimension_packer(
        self,
        config_attr,
        data_id,
        is_exposure=None,
        default="observation",
    ):
        # Docstring inherited from Instrument._make_default_dimension_packer.
        # Only difference is the change to default above (which reverts back
        # the default in lsst.pipe.base.Instrument).
        return super()._make_default_dimension_packer(
            config_attr,
            data_id,
            is_exposure=is_exposure,
            default=default,
        )


class LsstTS3(LsstCam):
    """Gen3 Butler specialization for TS3 test stand data.
    """

    filterDefinitions = TS3_FILTER_DEFINITIONS
    instrument = "LSST-TS3"
    policyName = "ts3"
    translatorClass = LsstTS3Translator
    visitSystem = VisitSystem.ONE_TO_ONE

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstTS3RawFormatter
        return LsstTS3RawFormatter

    def _make_default_dimension_packer(
        self,
        config_attr,
        data_id,
        is_exposure=None,
        default="observation",
    ):
        # Docstring inherited from Instrument._make_default_dimension_packer.
        # Only difference is the change to default above (which reverts back
        # the default in lsst.pipe.base.Instrument).
        return super()._make_default_dimension_packer(
            config_attr,
            data_id,
            is_exposure=is_exposure,
            default=default,
        )


class Latiss(LsstCam):
    """Gen3 Butler specialization for AuxTel LATISS data.
    """
    filterDefinitions = LATISS_FILTER_DEFINITIONS
    instrument = "LATISS"
    policyName = "latiss"
    translatorClass = LatissTranslator

    def extractDetectorRecord(self, camGeomDetector):
        # Override to remove group (raft) name, because LATISS only has one
        # detector.
        record = super().extractDetectorRecord(camGeomDetector)
        record["raft"] = None
        record["name_in_raft"] = record["full_name"]
        return record

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LatissRawFormatter
        return LatissRawFormatter
