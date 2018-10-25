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

from lsst.daf.butler.instrument import Instrument

from ..filters import getFilterDefinitions
from ..lsstCam import LsstCam
from ..phosim import PhosimCam
from ..imsim import ImsimCam
from ..auxTel import AuxTelCam
from ..ts8 import Ts8


__all__ = ("LsstCamInstrument", "ImsimInstrument", "PhosimInstrument", "Ts8Instrument",
           "AuxTelInstrument")


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
       the vast majority of Butler use cases, we just use "Detector" even
       though the concept really maps better to "Detector slot".  Ideally in
       the future this distinction between static and time-dependent
       information would be encoded in cameraGeom itself (e.g. by making the
       time-dependent Detector class inherit from a related class that only
       carries static content).

     - The Butler Registry is expected to contain PhysicalFilter entries for
       all filters an instrument has ever had, because we really only care
       about which filters were used for particular observations, not which
       filters were *available* at some point in the past.  And changes in
       individual filters over time will be captured as changes in their
       TransmissionCurve datasets, not changes in the registry content (which
       is really just a label).  While at present Instrument and Registry
       do not provide a way to add new PhysicalFilters, they will in the
       future.
    """

    instrument = "LSST"

    def __init__(self, camera=None, filters=None):
        if camera is None:
            camera = LsstCam()
        self.camera = camera
        if filters is None:
            filters = getFilterDefinitions()
        self.detectors = [self.extractDetectorEntry(camGeomDetector)
                          for camGeomDetector in camera]
        self.physicalFilters = []
        for filterDef in filters:
            # For the standard broadband filters, we use the smae
            # single-letter name for both the PhysicalFilter and the
            # associated AbstractFilter.  For other filters we don't
            # assign an abstract_filter.
            self.physicalFilters.append(
                dict(
                    physical_filter=filterDef.name,
                    abstract_filter=filterDef.name if filterDef.name in "ugrizy" else None
                )
            )

    def extractDetectorEntry(self, camGeomDetector):
        """Create a Gen3 Detector entry dict from a cameraGeom.Detector.
        """
        # All of the LSST instruments have detector names like R??_S??; we'll
        # split them up here, and instruments with only one raft can override
        # to change the group to something else if desired.
        # Long-term, we should get these fields into cameraGeom separately
        # so there's no need to specialize at this stage.
        group, name = camGeomDetector.getName().split("_")

        # getType() returns a pybind11-wrapped enum, which unfortunately
        # has no way to extract the name of just the value (it's always
        # prefixed by the enum type name).
        purpose = str(camGeomDetector.getType()).split(".")[-1]

        return dict(
            detector=camGeomDetector.getId(),
            name=name,
            purpose=purpose,
            group=group,
        )


class ImsimInstrument(LsstCamInstrument):
    """Gen3 Butler specialization for ImSim simulations.
    """

    instrument = "LSST-ImSim"

    def __init__(self):
        super().__init__(camera=ImsimCam())


class PhosimInstrument(LsstCamInstrument):
    """Gen3 Butler specialization for Phosim simulations.
    """

    instrument = "LSST-PhoSim"

    def __init__(self):
        super().__init__(camera=PhosimCam())


class Ts8Instrument(LsstCamInstrument):
    """Gen3 Butler specialization for raft test stand data.
    """

    instrument = "LSST-TS8"

    def __init__(self):
        super().__init__(camera=Ts8())

    def extractDetectorEntry(self, camGeomDetector):
        # Override to remove group (raft) name, because we want to use this
        # same instrument regardless of what raft is on the test stand. Note
        # that the detector name is already just the name of the slot, not
        # something tied to the physical detector.
        entry = super().extractDetectorEntry(camGeomDetector)
        entry["group"] = None
        return entry


class AuxTelInstrument(LsstCamInstrument):
    """Gen3 Butler specialization for raft test stand data.
    """

    instrument = "LSST-AuxTel"

    def __init__(self):
        super().__init__(camera=AuxTelCam())

    def extractDetectorEntry(self, camGeomDetector):
        # Override to remove group (raft) name, because AuxTel only has one
        # detector.
        entry = super().extractDetectorEntry(camGeomDetector)
        entry["group"] = None
        return entry
