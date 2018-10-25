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

import os
import unittest
from tempfile import TemporaryDirectory
from cProfile import Profile
from pstats import Stats

import numpy as np

import lsst.utils.tests
from lsst.obs.lsst.gen3 import (LsstCamInstrument, ImsimInstrument, PhosimInstrument,
                                Ts8Instrument, AuxTelInstrument)

try:
    from lsst.daf.butler import Butler, DatasetType, StorageClassFactory
    haveGen3 = True
except ImportError:
    haveGen3 = False


# This test is unfortunately slow; leave a profiling option in in case we want
# to improve it later.  Initial version is about 60% YamlCamera construction
# (!) and 40% SQLite operations inside Butler.
PRINT_PROFILE = False


@unittest.skipUnless(haveGen3, "daf_butler not setup")
class TestInstruments(lsst.utils.tests.TestCase):

    def setUp(self):
        self.rng = np.random.RandomState(50)  # arbitrary deterministic seed
        if PRINT_PROFILE:
            self.profile = Profile()
            self.profile.enable()

    def tearDown(self):
        if PRINT_PROFILE:
            stats = Stats(self.profile)
            stats.strip_dirs()
            stats.sort_stats("cumtime")
            stats.print_stats()

    def checkInstrumentWithRegistry(self, cls):
        base = os.path.dirname(__file__)
        with TemporaryDirectory(prefix=cls.__name__, dir=base) as root:
            Butler.makeRepo(root)
            butler = Butler(root, run="tests")
            instrument = cls()
            scFactory = StorageClassFactory()

            # Add Instrument, Detector, and PhysicalFilter entries to the
            # Butler Registry.
            instrument.register(butler.registry)

            # Define a DatasetType for the cameraGeom.Camera, which can be accessed
            # just by identifying its Instrument.
            # A real-world Camera DatasetType should be identified by a validity
            # range as well.
            cameraDatasetType = DatasetType("camera", dataUnits=["Instrument"],
                                            storageClass=scFactory.getStorageClass("Camera"))
            butler.registry.registerDatasetType(cameraDatasetType)

            # Define a DatasetType for cameraGeom.Detectors, which can be accessed
            # by identifying its Instrument and (Butler) Detector.
            # A real-world Detector DatasetType probably doesn't need to exist, as
            # it would just duplicate information in the Camera, and reading a full
            # Camera just to get a single Detector should be plenty efficient.
            detectorDatasetType = DatasetType("detector", dataUnits=["Instrument", "Detector"],
                                              storageClass=scFactory.getStorageClass("Detector"))
            butler.registry.registerDatasetType(detectorDatasetType)

            # Put and get the Camera.
            dataId = dict(instrument=instrument.instrument)
            butler.put(instrument.camera, "camera", dataId=dataId)
            camera = butler.get("camera", dataId)
            # Full camera comparisons are *slow*; just compare names.
            self.assertEqual(instrument.camera.getName(), camera.getName())

            # Put and get a random subset of the Detectors.
            allDetectors = list(instrument.camera)
            numDetectors = min(3, len(allDetectors))
            someDetectors = [allDetectors[i] for i in self.rng.choice(len(allDetectors),
                                                                      size=numDetectors, replace=False)]
            for cameraGeomDetector in someDetectors:
                # Right now we only support integer detector IDs in data IDs;
                # support for detector names and groups (i.e. rafts) is definitely
                # planned but not yet implemented.
                dataId = dict(instrument=instrument.instrument, detector=cameraGeomDetector.getId())
                butler.put(cameraGeomDetector, "detector", dataId=dataId)
                cameraGeomDetector2 = butler.get("detector", dataId=dataId)
                # Full detector comparisons are *slow*; just compare names and serials.
                self.assertEqual(cameraGeomDetector.getName(), cameraGeomDetector2.getName())
                self.assertEqual(cameraGeomDetector.getSerial(), cameraGeomDetector2.getSerial())

    def testLsstCam(self):
        self.checkInstrumentWithRegistry(LsstCamInstrument)

    def testImsimCam(self):
        self.checkInstrumentWithRegistry(ImsimInstrument)

    def testPhosimCam(self):
        self.checkInstrumentWithRegistry(PhosimInstrument)

    def testTs8(self):
        self.checkInstrumentWithRegistry(Ts8Instrument)

    def testAuxTel(self):
        self.checkInstrumentWithRegistry(AuxTelInstrument)


if __name__ == "__main__":
    unittest.main()
