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

__all__ = ("LsstCamInstrument", "ImsimInstrument", "PhosimInstrument", "Ts8Instrument",
           "LatissInstrument", "Ts3Instrument", "UcdCamInstrument", "LsstComCamInstrument")

import os.path
from dateutil import parser

from lsst.utils import getPackageDir
from lsst.daf.butler.instrument import Instrument, addUnboundedCalibrationLabel
from lsst.daf.butler import DatasetType, DataId
from lsst.pipe.tasks.read_defects import read_all_defects
from ..filters import LSSTCAM_FILTER_DEFINITIONS
from ..lsstCamMapper import LsstCamMapper
from ..comCam import LsstComCamMapper
from ..phosim import PhosimMapper
from ..imsim import ImsimMapper
from ..latiss import LatissMapper
from ..ts8 import Ts8Mapper
from ..ts3 import Ts3Mapper
from ..ucd import UcdMapper

PACKAGE_DIR = getPackageDir("obs_lsst")


class LsstCamInstrument(Instrument):
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
    instrument = "lsstCam"
    policyName = "lsstCam"
    _mapperClass = LsstCamMapper
    _camera = None

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
        if cls._camera is None:
            cls._camera = cls._mapperClass().camera
        return cls._camera

    def getRawFormatter(self, dataId):
        # Docstring inherited from Instrument.getRawFormatter
        raise NotImplementedError()

    def register(self, registry):
        # Docstring inherited from Instrument.register
        dataId = {"instrument": self.getName()}
        # The maximum values below make Gen3's ObservationDataIdPacker produce
        # outputs that match Gen2's ccdExposureId.
        obsMax = 2050121299999250
        registry.addDimensionEntry("instrument", dataId,
                                   entries={"detector_max": 200,
                                            "visit_max": obsMax,
                                            "exposure_max": obsMax})

        for detector in self.getCamera():
            detInfo = self.extractDetectorEntry(detector)
            registry.addDimensionEntry(
                "detector", dataId, **detInfo
            )

        self._registerFilters(registry)

    def extractDetectorEntry(self, camGeomDetector):
        """Create a Gen3 Detector entry dict from a cameraGeom.Detector.
        """
        # All of the LSST instruments have detector names like R??_S??; we'll
        # split them up here, and instruments with only one raft can override
        # to change the group to something else if desired.
        # Long-term, we should get these fields into cameraGeom separately
        # so there's no need to specialize at this stage.
        print(f"Name: {camGeomDetector.getName()}")
        group, name = camGeomDetector.getName().split("_")

        # getType() returns a pybind11-wrapped enum, which unfortunately
        # has no way to extract the name of just the value (it's always
        # prefixed by the enum type name).
        purpose = str(camGeomDetector.getType()).split(".")[-1]

        return dict(
            detector=camGeomDetector.getId(),
            name=name,
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

        # Write defects with validity ranges taken from
        # obs_lsst_data/{name}/defects (along with the defects themselves).
        datasetType = DatasetType("defects", ("instrument", "detector", "calibration_label"), "DefectsList",
                                  universe=butler.registry.dimensions)
        butler.registry.registerDatasetType(datasetType)
        defectPath = os.path.join(getPackageDir("obs_lsst"), self.policyName, "defects")

        if os.path.exists(defectPath):
            camera = self.getCamera()
            defectsDict = read_all_defects(defectPath, camera)
            endOfTime = '20380119T031407'
            with butler.transaction():
                for det in defectsDict:
                    detector = camera[det]
                    times = sorted([k for k in defectsDict[det]])
                    defects = [defectsDict[det][time] for time in times]
                    times = times + [parser.parse(endOfTime), ]
                    for defect, beginTime, endTime in zip(defects, times[:-1], times[1:]):
                        md = defect.getMetadata()
                        dataId = DataId(universe=butler.registry.dimensions,
                                        instrument=self.getName(),
                                        calibration_label=f"defect/{md['CALIBDATE']}/{md['DETECTOR']}")
                        dataId.entries["calibration_label"]["valid_first"] = beginTime
                        dataId.entries["calibration_label"]["valid_last"] = endTime
                        butler.registry.addDimensionEntry("calibration_label", dataId)
                        butler.put(defect, datasetType, dataId, detector=detector.getId())


class LsstComCamInstrument(LsstCamInstrument):
    """Gen3 Butler specialization for ComCam data.
    """

    instrument = "LSST-ComCam"
    policyName = "comCam"
    _mapperClass = LsstComCamMapper


class ImsimInstrument(LsstCamInstrument):
    """Gen3 Butler specialization for ImSim simulations.
    """

    instrument = "LSST-ImSim"
    policyName = "imsim"
    _mapperClass = ImsimMapper


class PhosimInstrument(LsstCamInstrument):
    """Gen3 Butler specialization for Phosim simulations.
    """

    instrument = "LSST-PhoSim"
    policyName = "phosim"
    _mapperClass = PhosimMapper


class Ts8Instrument(LsstCamInstrument):
    """Gen3 Butler specialization for raft test stand data.
    """

    instrument = "LSST-TS8"
    policyName = "ts8"
    _mapperClass = Ts8Mapper


class UcdCamInstrument(LsstCamInstrument):
    """Gen3 Butler specialization for UCDCam test stand data.
    """

    instrument = "UCDCam"
    policyName = "ucd"
    _mapperClass = UcdMapper


class Ts3Instrument(LsstCamInstrument):
    """Gen3 Butler specialization for TS3 test stand data.
    """

    instrument = "LSST-TS3"
    policyName = "ts3"
    _mapperClass = Ts3Mapper


class LatissInstrument(LsstCamInstrument):
    """Gen3 Butler specialization for AuxTel LATISS data.
    """

    instrument = "LATISS"
    policyName = "latiss"
    _mapperClass = LatissMapper

    def extractDetectorEntry(self, camGeomDetector):
        # Override to remove group (raft) name, because LATISS only has one
        # detector.
        entry = super().extractDetectorEntry(camGeomDetector)
        entry["raft"] = None
        return entry
