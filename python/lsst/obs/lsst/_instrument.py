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
           "Latiss", "LsstTS3", "LsstUCDCam", "LsstComCam")

import os.path

import lsst.obs.base.yamlCamera as yamlCamera
from lsst.daf.butler.core.utils import getFullTypeName
from lsst.utils import getPackageDir
from lsst.obs.base import Instrument
from lsst.obs.base.gen2to3 import TranslatorFactory
from .filters import (LSSTCAM_FILTER_DEFINITIONS, LATISS_FILTER_DEFINITIONS,
                      LSSTCAM_IMSIM_FILTER_DEFINITIONS, TS3_FILTER_DEFINITIONS,
                      TS8_FILTER_DEFINITIONS, COMCAM_FILTER_DEFINITIONS,
                      )

from .translators import LatissTranslator, LsstCamTranslator, \
    LsstUCDCamTranslator, LsstTS3Translator, LsstComCamTranslator, \
    LsstCamPhoSimTranslator, LsstTS8Translator, LsstCamImSimTranslator

PACKAGE_DIR = getPackageDir("obs_lsst")


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

    @property
    def configPaths(self):
        return [os.path.join(PACKAGE_DIR, "config"),
                os.path.join(PACKAGE_DIR, "config", self.policyName)]

    @classmethod
    def getName(cls):
        # Docstring inherited from Instrument.getName
        return cls.instrument

    @classmethod
    def getCamera(cls):
        # Constructing a YAML camera takes a long time but we rely on
        # yamlCamera to cache for us.
        cameraYamlFile = os.path.join(PACKAGE_DIR, "policy", f"{cls.policyName}.yaml")
        camera = yamlCamera.makeCamera(cameraYamlFile)
        if camera.getName() != cls.getName():
            raise RuntimeError(f"Expected to read camera geometry for {cls.instrument}"
                               f" but instead got geometry for {camera.getName()}")
        return camera

    def getRawFormatter(self, dataId):
        # Docstring inherited from Instrument.getRawFormatter
        # local import to prevent circular dependency
        from .rawFormatter import LsstCamRawFormatter
        return LsstCamRawFormatter

    def register(self, registry):
        # Docstring inherited from Instrument.register
        # The maximum values below make Gen3's ObservationDataIdPacker produce
        # outputs that match Gen2's ccdExposureId.
        obsMax = self.translatorClass.max_detector_exposure_id()
        with registry.transaction():
            registry.syncDimensionData(
                "instrument",
                {
                    "name": self.getName(),
                    "detector_max": self.translatorClass.DETECTOR_MAX,
                    "visit_max": obsMax,
                    "exposure_max": obsMax,
                    "class_name": getFullTypeName(self),
                }
            )
            for detector in self.getCamera():
                registry.syncDimensionData("detector", self.extractDetectorRecord(detector))

            self._registerFilters(registry)

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

    def makeDataIdTranslatorFactory(self) -> TranslatorFactory:
        # Docstring inherited from lsst.obs.base.Instrument.
        factory = TranslatorFactory()
        factory.addGenericInstrumentRules(self.getName(), detectorKey="detector", exposureKey="expId")
        return factory


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


class LsstCamImSim(LsstCam):
    """Gen3 Butler specialization for ImSim simulations.
    """

    instrument = "LSSTCam-imSim"
    policyName = "imsim"
    translatorClass = LsstCamImSimTranslator
    filterDefinitions = LSSTCAM_IMSIM_FILTER_DEFINITIONS

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstCamImSimRawFormatter
        return LsstCamImSimRawFormatter


class LsstCamPhoSim(LsstCam):
    """Gen3 Butler specialization for Phosim simulations.
    """

    instrument = "LSSTCam-PhoSim"
    policyName = "phosim"
    translatorClass = LsstCamPhoSimTranslator

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstCamPhoSimRawFormatter
        return LsstCamPhoSimRawFormatter


class LsstTS8(LsstCam):
    """Gen3 Butler specialization for raft test stand data.
    """

    filterDefinitions = TS8_FILTER_DEFINITIONS
    instrument = "LSST-TS8"
    policyName = "ts8"
    translatorClass = LsstTS8Translator

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstTS8RawFormatter
        return LsstTS8RawFormatter


class LsstUCDCam(LsstCam):
    """Gen3 Butler specialization for UCDCam test stand data.
    """

    instrument = "LSST-UCDCam"
    policyName = "ucd"
    translatorClass = LsstUCDCamTranslator

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstUCDCamRawFormatter
        return LsstUCDCamRawFormatter


class LsstTS3(LsstCam):
    """Gen3 Butler specialization for TS3 test stand data.
    """

    filterDefinitions = TS3_FILTER_DEFINITIONS
    instrument = "LSST-TS3"
    policyName = "ts3"
    translatorClass = LsstTS3Translator

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstTS3RawFormatter
        return LsstTS3RawFormatter


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
