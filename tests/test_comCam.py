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


class TestLsstCam(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "comCam"

    def setUp(self):
        dataIds = {'raw': {'expId': 3019053000001, 'detectorName': 'S00', 'raftName': 'R22'},
                   'bias': unittest.SkipTest,
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest,
                   }
        self.setUp_tests(self._butler, self._mapper, dataIds)

        ccdExposureId_bits = 52
        exposureIds = {'raw': 3019053000001000,
                       }
        filters = {'raw': 'unknown',
                   }
        exptimes = {'raw': 0.0,
                    }
        detectorIds = {'raw': 0,
                       }
        detector_names = {'raw': 'R22_S00',
                          }
        # This name comes from the camera and not from the butler
        detector_serials = {'raw': 'ITL-3800C-229',
                            }
        dimensions = {'raw': Extent2I(4608, 4096),
                      }
        sky_origin = unittest.SkipTest
        raw_subsets = (({'level': 'sensor'}, 1),
                       ({'level': 'sensor', 'filter': 'unknown'}, 1),
                       ({'level': 'sensor', 'filter': 'foo'}, 0),
                       ({'level': 'sensor', 'visit': 3019053000001}, 1),
                       ({'level': 'filter', 'visit': 3019053000001}, 1),
                       ({'level': 'expId'}, 1),
                       ({'level': 'expId', 'filter': 'unknown'}, 1),
                       ({'level': 'expId', 'filter': 'foo'}, 0)
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

        path_to_raw = os.path.join(self.data_dir, "raw", "2019-05-30", "3019053000001",
                                   "3019053000001-R22-S00-det000.fits")
        keys = set(('filter', 'patch', 'tract', 'visit', 'channel', 'amp', 'style', 'detector', 'dstype',
                    'snap', 'run', 'calibDate', 'half', 'detectorName', 'raftName', 'label',
                    'numSubfilters', 'fgcmcycle', 'name', 'pixel_id', 'description', 'subfilter', 'expId',
                    'dayObs', 'seqNum', 'subdir',))
        query_format = ["expId", "filter"]
        queryMetadata = (({'expId': 3019053000001}, [(3019053000001, 'unknown')]),
                         ({'filter': 'unknown'}, [(3019053000001, 'unknown')]),
                         )
        map_python_type = lsst.afw.image.DecoratedImageF
        map_python_std_type = lsst.afw.image.ExposureF
        map_cpp_type = 'DecoratedImageF'
        map_storage_name = 'FitsStorage'
        metadata_output_path = os.path.join("processCcd_metadata/3019053000001-unknown/R22",
                                            "processCcdMetadata_3019053000001-unknown-R22-S00-det000.yaml")
        raw_filename = '3019053000001-R22-S00-det000.fits'
        default_level = 'sensor'
        raw_levels = (('sensor', set(['expId', 'detector', 'dayObs', 'detectorName', 'raftName'])),
                      ('skyTile', set(['expId', 'dayObs'])),
                      ('filter', set(['expId'])),
                      ('expId', set(['expId', 'dayObs']))
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
                          test_config_metadata=True
                          )

        self.setUp_camera(camera_name='LSSTComCam',
                          n_detectors=9,
                          first_detector_name='R22_S00',
                          plate_scale=20.0 * arcseconds,
                          )

        super().setUp()

    def testCcdExposureId(self):
        with self.assertRaises(KeyError):
            self.butler.get('ccdExposureId', dataId={})

        exposureId = self.butler.get('ccdExposureId', dataId={"visit": 1, "detector": 1})
        self.assertEqual(exposureId, 1001)

        exposureId = self.butler.get('ccdExposureId', dataId={"visit": 1, "raftName": "R22",
                                                              "detectorName": "S00"})
        self.assertEqual(exposureId, 1000)

        with self.assertRaises(ValueError):
            self.butler.get('ccdExposureId', dataId={"visit": 1, "detector": 2000})

        with self.assertRaises(KeyError):
            self.butler.get('ccdExposureId', dataId={"visit": 1})

        with self.assertRaises(ValueError):
            self.butler.get('ccdExposureId', dataId={"visit": 1, "raftName": "R99",
                                                     "detectorName": "S01"})

    def testDetectorName(self):
        name = self.mapper._extractDetectorName({"raftName": "R00", "detectorName": "S00"})
        self.assertEqual(name, "R00_S00")

        name = self.mapper._extractDetectorName({'visit': 3019053000001, 'detectorName': 'S00'})
        self.assertEqual(name, "R22_S00")

        name = self.mapper._extractDetectorName({'visit': 3019053000001, 'detector': 0})
        self.assertEqual(name, "R22_S00")

        name = self.mapper._extractDetectorName({'detector': 0})
        self.assertEqual(name, "R22_S00")

        name = self.mapper._extractDetectorName({'visit': 3019053000001})
        self.assertEqual(name, "R22_S00")

        with self.assertRaises(RuntimeError):
            self.mapper._extractDetectorName({'visit': 1})


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
