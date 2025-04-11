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
import shutil
import tempfile
from cProfile import Profile
from pstats import Stats

import numpy as np

from astro_metadata_translator import ObservationInfo
from lsst.obs.lsst import (LsstCam, LsstComCam, LsstCamImSim, LsstCamPhoSim,
                           LsstTS8, LsstTS3, LsstUCDCam, Latiss, LsstComCamSim,
                           LsstCamSim, readRawFitsHeader)

from lsst.daf.butler import (
    Butler,
    DatasetType,
    StorageClassFactory,
)

TESTDIR = os.path.abspath(os.path.dirname(__file__))
DATAROOT = os.path.join(TESTDIR, os.path.pardir, "data", "input")

# This test is unfortunately slow; leave a profiling option in in case we want
# to improve it later.  Initial version is about 60% YamlCamera construction
# (!) and 40% SQLite operations inside Butler.
PRINT_PROFILE = False


class TestInstruments(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(dir=TESTDIR)
        self.rng = np.random.RandomState(50)  # arbitrary deterministic seed

    @classmethod
    def setUpClass(cls):
        if PRINT_PROFILE:
            cls.profile = Profile()
            cls.profile.enable()

    def tearDown(self):
        if self.root is not None and os.path.exists(self.root):
            shutil.rmtree(self.root, ignore_errors=True)

    @classmethod
    def tearDownClass(cls):
        if PRINT_PROFILE:
            stats = Stats(cls.profile)
            stats.strip_dirs()
            stats.sort_stats("cumtime")
            stats.print_stats()

    def checkInstrumentWithRegistry(self, cls, testRaw):

        Butler.makeRepo(self.root)
        butler = Butler(self.root, run="tests")
        instrument = cls()
        scFactory = StorageClassFactory()

        # Check instrument class and metadata translator agree on
        # instrument name, using readRawFitsHeader to read the metadata.
        filename = os.path.join(DATAROOT, testRaw)
        md = readRawFitsHeader(filename, translator_class=cls.translatorClass)
        obsInfo = ObservationInfo(md, translator_class=cls.translatorClass, filename=filename)
        self.assertEqual(instrument.getName(), obsInfo.instrument)

        # Add Instrument, Detector, and PhysicalFilter entries to the
        # Butler Registry.
        instrument.register(butler.registry)

        # Define a DatasetType for the cameraGeom.Camera, which can be
        # accessed just by identifying its Instrument.
        # A real-world Camera DatasetType should be identified by a
        # validity range as well.
        cameraDatasetType = DatasetType("camera", dimensions=["instrument"],
                                        storageClass=scFactory.getStorageClass("Camera"),
                                        universe=butler.dimensions)
        butler.registry.registerDatasetType(cameraDatasetType)

        # Define a DatasetType for cameraGeom.Detectors, which can be
        # accessed by identifying its Instrument and (Butler) Detector.
        # A real-world Detector DatasetType probably doesn't need to exist,
        # as  it would just duplicate information in the Camera, and
        # reading a full Camera just to get a single Detector should be
        # plenty efficient.
        detectorDatasetType = DatasetType("detector", dimensions=["instrument", "detector"],
                                          storageClass=scFactory.getStorageClass("Detector"),
                                          universe=butler.dimensions)
        butler.registry.registerDatasetType(detectorDatasetType)

        # Put and get the Camera.
        dataId = dict(instrument=instrument.instrument)
        butler.put(instrument.getCamera(), "camera", dataId=dataId)
        camera = butler.get("camera", dataId)
        # Full camera comparisons are *slow*; just compare names.
        self.assertEqual(instrument.getCamera().getName(), camera.getName())

        # Put and get a random subset of the Detectors.
        allDetectors = list(instrument.getCamera())
        numDetectors = min(3, len(allDetectors))
        someDetectors = [allDetectors[i] for i in self.rng.choice(len(allDetectors),
                                                                  size=numDetectors, replace=False)]
        for cameraGeomDetector in someDetectors:
            # Right now we only support integer detector IDs in data IDs;
            # support for detector names and groups (i.e. rafts) is
            # definitely planned but not yet implemented.
            dataId = dict(instrument=instrument.instrument, detector=cameraGeomDetector.getId())
            butler.put(cameraGeomDetector, "detector", dataId=dataId)
            cameraGeomDetector2 = butler.get("detector", dataId=dataId)
            # Full detector comparisons are *slow*; just compare names and
            # serials.
            self.assertEqual(cameraGeomDetector.getName(), cameraGeomDetector2.getName())
            self.assertEqual(cameraGeomDetector.getSerial(), cameraGeomDetector2.getSerial())

    def testLsstCam(self):
        testFpath = "lsstCam/raw/2019-03-22/3019032200002/3019032200002-R10-S22-det035.fits"
        self.checkInstrumentWithRegistry(LsstCam, testFpath)

    def testComCam(self):
        testFpath = "comCam/raw/2019-05-30/3019053000001/3019053000001-R22-S00-det000.fits"
        self.checkInstrumentWithRegistry(LsstComCam, testFpath)

    def testComCamSim(self):
        testFpath = "comCamSim/raw/2024-03-21/7024032100720/7024032100720-R22-S11-det004.fits.fz"
        self.checkInstrumentWithRegistry(LsstComCamSim, testFpath)

    def testImSim(self):
        self.checkInstrumentWithRegistry(LsstCamImSim,
                                         "imsim/raw/204595/R11/00204595-R11-S20-det042.fits")

    def testPhoSim(self):
        self.checkInstrumentWithRegistry(LsstCamPhoSim,
                                         "phosim/raw/204595/R11/00204595-R11-S20-det042.fits")

    def testLsstCamSim(self):
        testFpath = "lsstCamSim/raw/2024-03-21/7024032100720/7024032100720-R22-S11-det094.fits.fz"
        self.checkInstrumentWithRegistry(LsstCamSim, testFpath)

    def testTs8(self):
        self.checkInstrumentWithRegistry(LsstTS8,
                                         "ts8/raw/6006D/201807241028453-RTM-010-S11-det067.fits")

    def testTs3(self):
        self.checkInstrumentWithRegistry(LsstTS3,
                                         "ts3/raw/2016-07-22/201607220607067-R071-S00-det071.fits")

    def testUcdCam(self):
        self.checkInstrumentWithRegistry(LsstUCDCam,
                                         "ucd/raw/2023-10-31/2023103100227-R21-S01-det010.fits")

    def testLatiss(self):
        self.checkInstrumentWithRegistry(Latiss,
                                         "latiss/raw/2018-09-20/3018092000065-det000.fits")

    def test_exposure_max(self):
        # Ensure that the exposure max value does not change.
        for cls, exp_max in (
            (LsstCam, 7050123199999),
            (LsstComCam, 7050123199999),
            (LsstCamImSim, 9999999),
            (LsstCamPhoSim, 9999999),
            (LsstTS8, 205012312359999),
            (LsstTS3, 205012312359999),
            (LsstUCDCam, 7050123199999),
            (Latiss, 7050123199999),
            (LsstComCamSim, 7050123199999),
            (LsstCamSim, 7050123199999),
        ):
            self.assertEqual(cls.translatorClass.max_exposure_id(), exp_max)


if __name__ == "__main__":
    unittest.main()
