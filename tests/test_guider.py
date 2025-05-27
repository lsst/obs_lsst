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
#

import os
import unittest
import contextlib
from lsst.daf.butler import MissingDatasetTypeError, Config
from lsst.daf.butler.tests import makeTestRepo
from lsst.daf.butler.tests.utils import makeTestTempDir, removeTestTempDir
from lsst.obs.lsst import LsstCam, ingest_guider
from lsst.obs.base import RawIngestTask

TESTDIR = os.path.abspath(os.path.dirname(__file__))
DATAROOT = os.path.join(TESTDIR, os.path.pardir, "data", "input", "guider")


class GuiderIngestTestCase(unittest.TestCase):
    """Test guider file ingest."""

    def setUp(self):
        # Repository should be re-created for each test case since
        # dimension records are set.
        self.root = makeTestTempDir(TESTDIR)
        self.addClassCleanup(removeTestTempDir, self.root)

        config = Config()
        config["datastore", "cls"] = "lsst.daf.butler.datastores.fileDatastore.FileDatastore"
        self.butler = makeTestRepo(self.root, config=config)
        self.instrument = LsstCam()
        self.instrument.register(self.butler.registry)

    def test_ingest_guider_fail(self):

        failed = {}

        def on_undefined_exposure(path, obsid):
            failed[path] = obsid

        with self.assertRaises(MissingDatasetTypeError):
            ingest_guider(
                self.butler,
                [os.path.join(DATAROOT, "guider_data", "MC_C_20230616_000013_R04_SG0.fits")],
                on_undefined_exposure=on_undefined_exposure,
            )

        with contextlib.suppress(Exception):
            ingest_guider(
                self.butler,
                [os.path.join(DATAROOT, "guider_data", "MC_C_20230616_000013_R04_SG0.fits")],
                register_dataset_type=True,
                on_undefined_exposure=on_undefined_exposure,
            )

        failed_obsids = list(failed.values())
        self.assertEqual(failed_obsids, ["MC_C_20230616_000013"], msg=f"{failed}")

    def test_ingest_guider(self):
        # First ingest a raw to get the exposure defined.
        config = RawIngestTask.ConfigClass()
        task = RawIngestTask(config=config, butler=self.butler)
        # This will read the metadata from the sidecar file.
        task.run([os.path.join(DATAROOT, "raw", "MC_C_20240918_000013_R42_S11.fits")])

        ingested = []

        def on_success(datasets):
            ingested.extend(datasets)

        # Ingest guider data.
        refs = ingest_guider(
            self.butler,
            [os.path.join(DATAROOT, "guider_data", "MC_C_20240918_000013_R00_SG0_guider.fits")],
            group_files=False,
            register_dataset_type=True,
            on_success=on_success,
        )

        self.assertEqual(len(ingested), 1)

        # Check that the guider metadata is set.
        guider = self.butler.get(refs[0])
        self.assertIsNone(guider.metadata)



if __name__ == '__main__':
    unittest.main()
