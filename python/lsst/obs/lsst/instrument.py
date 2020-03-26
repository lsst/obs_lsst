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

__all__ = ("LsstCam", "LsstImSim", "LsstPhoSim", "LsstTS8",
           "Latiss", "LsstTS3", "LsstUCDCam", "LsstComCam")

import os.path
from dateutil import parser

import lsst.obs.base.yamlCamera as yamlCamera
from lsst.utils import getPackageDir
from lsst.obs.base.instrument import Instrument, addUnboundedCalibrationLabel
from lsst.daf.butler import DatasetType, DataCoordinate
from lsst.pipe.tasks.read_curated_calibs import read_all
from .filters import LSSTCAM_FILTER_DEFINITIONS, LATISS_FILTER_DEFINITIONS

from .translators import LatissTranslator, LsstCamTranslator, \
    LsstUCDCamTranslator, LsstTS3Translator, LsstComCamTranslator, \
    LsstPhoSimTranslator, LsstTS8Translator, LsstImSimTranslator

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
    _camera = None
    _cameraCachedClass = None
    translatorClass = LsstCamTranslator
    obsDataPackageDir = getPackageDir("obs_lsst_data")

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
        # Constructing a YAML camera takes a long time so cache the result
        # We have to be careful to ensure we cache at the subclass level
        # since LsstCam base class will look like a cache to the subclasses
        if cls._camera is None or cls._cameraCachedClass != cls:
            cameraYamlFile = os.path.join(PACKAGE_DIR, "policy", f"{cls.policyName}.yaml")
            cls._camera = yamlCamera.makeCamera(cameraYamlFile)
            cls._cameraCachedClass = cls
        return cls._camera

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
        registry.insertDimensionData("instrument",
                                     {"name": self.getName(),
                                      "detector_max": self.translatorClass.DETECTOR_MAX,
                                      "visit_max": obsMax,
                                      "exposure_max": obsMax})

        records = [self.extractDetectorRecord(detector) for detector in self.getCamera()]
        registry.insertDimensionData("detector", *records)

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

    def writeCuratedCalibrations(self, butler):
        """Write human-curated calibration Datasets to the given Butler with
        the appropriate validity ranges.

        This is a temporary API that should go away once obs_ packages have
        a standardized approach to this problem.
        """

        # Write cameraGeom.Camera, with an infinite validity range.
        datasetType = DatasetType("camera", ("instrument", "calibration_label"), "Camera",
                                  universe=butler.registry.dimensions)
        butler.registry.registerDatasetType(datasetType)
        unboundedDataId = addUnboundedCalibrationLabel(butler.registry, self.getName())
        camera = self.getCamera()
        butler.put(camera, datasetType, unboundedDataId)

        # Write calibrations from obs_lsst_data

        curatedCalibrations = {
            "defects": {"dimensions": ("instrument", "detector", "calibration_label"),
                        "storageClass": "Defects"},
            "qe_curve": {"dimensions": ("instrument", "detector", "calibration_label"),
                         "storageClass": "QECurve"},
        }

        for typeName, definition in curatedCalibrations.items():
            # We need to define the dataset types.
            datasetType = DatasetType(typeName, definition["dimensions"],
                                      definition["storageClass"],
                                      universe=butler.registry.dimensions)
            butler.registry.registerDatasetType(datasetType)
            self._writeCuratedCalibrationDataset(butler, datasetType)

    def _writeCuratedCalibrationDataset(self, butler, datasetType):
        """Write a standardized curated calibration dataset from an obs data
        package.

        Parameters
        ----------
        butler : `lsst.daf.butler.Butler`
            Gen3 butler in which to put the calibrations.
        datasetType : `lsst.daf.butler.DatasetType`
            Dataset type to be put.

        Notes
        -----
        This method scans the location defined in the ``obsDataPackageDir``
        class attribute for curated calibrations corresponding to the
        supplied dataset type.  The directory name in the data package much
        match the name of the dataset type. They are assumed to use the
        standard layout and can be read by
        `~lsst.pipe.tasks.read_curated_calibs.read_all` and provide standard
        metadata.
        """
        calibPath = os.path.join(self.obsDataPackageDir, self.policyName,
                                 datasetType.name)

        if not os.path.exists(calibPath):
            return

        camera = self.getCamera()
        calibsDict = read_all(calibPath, camera)[0]  # second return is calib type
        endOfTime = '20380119T031407'
        dimensionRecords = []
        datasetRecords = []
        for det in calibsDict:
            times = sorted([k for k in calibsDict[det]])
            calibs = [calibsDict[det][time] for time in times]
            times = times + [parser.parse(endOfTime), ]
            for calib, beginTime, endTime in zip(calibs, times[:-1], times[1:]):
                md = calib.getMetadata()
                calibrationLabel = f"{datasetType.name}/{md['CALIBDATE']}/{md['DETECTOR']}"
                dataId = DataCoordinate.standardize(
                    universe=butler.registry.dimensions,
                    instrument=self.getName(),
                    calibration_label=calibrationLabel,
                    detector=md["DETECTOR"],
                )
                datasetRecords.append((calib, dataId))
                dimensionRecords.append({
                    "instrument": self.getName(),
                    "name": calibrationLabel,
                    "datetime_begin": beginTime,
                    "datetime_end": endTime,
                })

        # Second loop actually does the inserts and filesystem writes.
        with butler.transaction():
            butler.registry.insertDimensionData("calibration_label", *dimensionRecords)
            # TODO: vectorize these puts, once butler APIs for that become
            # available.
            for calib, dataId in datasetRecords:
                butler.put(calib, datasetType, dataId)


class LsstComCam(LsstCam):
    """Gen3 Butler specialization for ComCam data.
    """

    instrument = "LSSTComCam"
    policyName = "comCam"
    translatorClass = LsstComCamTranslator

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstComCamRawFormatter
        return LsstComCamRawFormatter


class LsstImSim(LsstCam):
    """Gen3 Butler specialization for ImSim simulations.
    """

    instrument = "LSST-ImSim"
    policyName = "imsim"
    translatorClass = LsstImSimTranslator

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstImSimRawFormatter
        return LsstImSimRawFormatter


class LsstPhoSim(LsstCam):
    """Gen3 Butler specialization for Phosim simulations.
    """

    instrument = "LSST-PhoSim"
    policyName = "phosim"
    translatorClass = LsstPhoSimTranslator

    def getRawFormatter(self, dataId):
        # local import to prevent circular dependency
        from .rawFormatter import LsstPhoSimRawFormatter
        return LsstPhoSimRawFormatter


class LsstTS8(LsstCam):
    """Gen3 Butler specialization for raft test stand data.
    """

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
