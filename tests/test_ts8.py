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
import sys
import unittest

import lsst.utils.tests
from lsst.geom import arcseconds, Extent2I
import lsst.afw.image

from lsst.obs.lsst.testHelper import ObsLsstButlerTests, ObsLsstObsBaseOverrides


class TestTs8(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "ts8"

    def setUp(self):
        dataIds = {'raw': {'visit': 201807241028453, 'detectorName': 'S11', 'raftName': 'RTM-010'},
                   'bias': unittest.SkipTest,
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest
                   }
        self.setUp_tests(self._butler, self._mapper, dataIds)

        ccdExposureId_bits = 36
        exposureIds = {'raw': 201807241028453067, 'bias': 20180724102845304}
        filters = {'raw': 'z', 'bias': '_unknown_'}
        exptimes = {'raw': 21.913, 'bias': 0}
        detectorIds = {'raw': 67, 'bias': 4}
        detector_names = {'raw': 'RTM-010_S11', 'bias': 'R00_S11'}
        detector_serials = {'raw': 'E2V-CCD250-179', 'bias': 'E2V-CCD250-179'}
        dimensions = {'raw': Extent2I(4608, 4096),
                      'bias': Extent2I(4096, 4004)}
        sky_origin = unittest.SkipTest
        raw_subsets = (({'level': 'sensor', 'filter': 'z'}, 1),
                       ({'level': 'sensor', 'visit': 201807241028453}, 1),
                       ({'level': 'filter', 'visit': 201807241028453}, 1),
                       ({'level': 'visit', 'filter': 'z'}, 1)
                       )
        linearizer_type = unittest.SkipTest
        self.setUp_butler_get(ccdExposureId_bits=ccdExposureId_bits,
                              exposureIds=exposureIds,
                              filters=filters,
                              exptimes=exptimes,
                              detectorIds=detectorIds,
                              detector_names=detector_names,
                              detector_serials=detector_serials,
                              dimensions=dimensions,
                              sky_origin=sky_origin,
                              raw_subsets=raw_subsets,
                              linearizer_type=linearizer_type
                              )

        path_to_raw = os.path.join(self.data_dir, "raw", "6006D", "201807241028453-S11-det067.fits")
        keys = set(('filter', 'patch', 'tract', 'visit', 'channel', 'amp', 'style', 'detector', 'dstype',
                    'calibDate', 'half', 'label', 'run', 'snap', 'detectorName', 'raftName',
                    'numSubfilters', 'fgcmcycle', 'name', 'pixel_id', 'description', 'subfilter'))
        query_format = ["visit", "filter"]
        queryMetadata = (({'visit': 201807241028453}, [(201807241028453, 'z')]),
                         ({'detector': 67}, [(201807241028453, 'z')]),
                         ({'detectorName': 'S11', 'raftName': 'RTM-010'}, [(201807241028453, 'z')]),
                         )
        map_python_type = lsst.afw.image.DecoratedImageF
        map_python_std_type = lsst.afw.image.ExposureF
        map_cpp_type = 'DecoratedImageF'
        map_storage_name = 'FitsStorage'
        metadata_output_path = None  # Not on sky data so processCcd not run.

        raw_filename = '201807241028453-S11-det067.fits'
        default_level = 'visit'
        raw_levels = (('skyTile', set(['visit', 'detector', 'run', 'detectorName'])),
                      ('filter', set(['visit', 'detector', 'run', 'detectorName'])),
                      ('visit', set(['visit', 'detector', 'run', 'detectorName']))
                      )
        self.setUp_mapper(output=self.data_dir,
                          path_to_raw=path_to_raw,
                          keys=keys,
                          query_format=query_format,
                          queryMetadata=queryMetadata,
                          metadata_output_path=metadata_output_path,
                          map_python_type=map_python_type,
                          map_python_std_type=map_python_std_type,
                          map_cpp_type=map_cpp_type,
                          map_storage_name=map_storage_name,
                          raw_filename=raw_filename,
                          default_level=default_level,
                          raw_levels=raw_levels,
                          test_config_metadata=False,
                          )

        self.setUp_camera(camera_name='lsstCam',
                          n_detectors=99,
                          first_detector_name='RTM-002_S00',
                          plate_scale=20.0 * arcseconds,
                          )

        super().setUp()

    def testCcdExposureId(self):
        exposureId = self.butler.get('ccdExposureId', dataId={})
        self.assertEqual(exposureId, 0)

        exposureId = self.butler.get('ccdExposureId', dataId={"visit": 1, "detector": 1})
        self.assertEqual(exposureId, 1001)

        exposureId = self.butler.get('ccdExposureId', dataId={"visit": 1, "detectorName": "S01",
                                                              "raftName": "RTM-002"})
        self.assertEqual(exposureId, 1001)

        with self.assertRaises(KeyError):
            self.butler.get('ccdExposureId', dataId={"visit": 1})

        with self.assertRaises(KeyError):
            self.butler.get('ccdExposureId', dataId={"detector": 1})

        with self.assertRaises(KeyError):
            self.butler.get('ccdExposureId', dataId={"visit": 1, "detectorName": "S44"})

    def testDetectorName(self):
        name = self.mapper._extractDetectorName({"detectorName": "S02", "raftName": "RTM-002"})
        self.assertEqual(name, "RTM-002_S02")

        name = self.mapper._extractDetectorName({"detector": 67, 'visit': 201807241028453})
        self.assertEqual(name, "RTM-010_S11")

        name = self.mapper._extractDetectorName({"detector": 67, 'visit': 201807241028453, "channel": 1})
        self.assertEqual(name, "RTM-010_S11")


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
