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


class TestTs3(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "ts3"

    def setUp(self):
        dataIds = {'raw': {'expId': 201607220607067, 'detectorName': 'S00', 'raftName': 'R071'},
                   'bias': unittest.SkipTest,
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest
                   }
        self.setUp_tests(self._butler, self._mapper, dataIds)

        ccdExposureId_bits = 58
        exposureIds = {'raw': 201607220607067071}
        filters = {'raw': '550CutOn'}
        exptimes = {'raw': 30.611}
        detectorIds = {'raw': 71}
        detector_names = {'raw': 'R071_S00'}
        detector_serials = {'raw': 'ITL-3800C-098'}
        dimensions = {'raw': Extent2I(4352, 4096),
                      }
        sky_origin = unittest.SkipTest
        raw_subsets = (({'level': 'sensor'}, 2),
                       ({'level': 'sensor', 'filter': '550CutOn'}, 2),
                       ({'level': 'sensor', 'detector': 71}, 1),
                       ({'level': 'sensor', 'raftName': 'R433'}, 1),
                       ({'level': 'sensor', 'raftName': 'R999'}, 0),
                       ({'level': 'sensor', 'expId': 201607220607067}, 1),
                       ({'level': 'filter'}, 2),
                       ({'level': 'filter', 'expId': 201607220607067}, 1),
                       ({'level': 'expId'}, 2),
                       ({'level': 'expId', 'filter': '550CutOn'}, 2),
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

        path_to_raw = os.path.join(self.data_dir, "raw", "2016-07-22", "201607220607067-R071-S00-det071.fits")
        keys = set(('filter', 'patch', 'tract', 'visit', 'channel', 'amp', 'style', 'detector', 'dstype',
                    'calibDate', 'half', 'label', 'run', 'snap', 'detectorName', 'raftName',
                    'numSubfilters', 'fgcmcycle', 'name', 'pixel_id', 'description', 'subfilter', 'expId',
                    'dayObs', 'seqNum',))
        query_format = ["expId", "filter"]
        queryMetadata = (({'expId': 201607220607067}, [(201607220607067, '550CutOn')]),
                         ({'detector': 71}, [(201607220607067, '550CutOn')]),
                         ({'detectorName': 'S00', 'raftName': 'R071'}, [(201607220607067, '550CutOn')]),
                         )
        map_python_type = lsst.afw.image.DecoratedImageF
        map_python_std_type = lsst.afw.image.ExposureF
        map_cpp_type = 'DecoratedImageF'
        map_storage_name = 'FitsStorage'
        metadata_output_path = None  # Not on sky data so processCcd not run.

        raw_filename = '201607220607067-R071-S00-det071.fits'
        default_level = 'sensor'
        raw_levels = (('sensor', set(['expId', 'detector', 'run', 'detectorName', 'raftName'])),
                      ('skyTile', set(['expId', 'run'])),
                      ('filter', set(['expId'])),
                      ('expId', set(['expId', 'run']))
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

        self.setUp_camera(camera_name='LSST-TS3',
                          n_detectors=435,
                          first_detector_name='R000_S00',
                          plate_scale=20.0 * arcseconds,
                          )

        super().setUp()

    def testCcdExposureId(self):
        exposureId = self.butler.get('ccdExposureId', dataId={})
        self.assertEqual(exposureId, 0)

        exposureId = self.butler.get('ccdExposureId', dataId={"visit": 1, "detector": 1})
        self.assertEqual(exposureId, 1001)

        exposureId = self.butler.get('ccdExposureId', dataId={"visit": 1, "detectorName": "S00",
                                                              "raftName": "R433"})
        self.assertEqual(exposureId, 1433)

        with self.assertRaises(KeyError):
            self.butler.get('ccdExposureId', dataId={"visit": 1})

        with self.assertRaises(KeyError):
            self.butler.get('ccdExposureId', dataId={"detector": 1})

        with self.assertRaises(KeyError):
            self.butler.get('ccdExposureId', dataId={"visit": 1, "detectorName": "S00"})

    def testDetectorName(self):
        name = self.mapper._extractDetectorName({"detectorName": "S00", "raftName": "R002"})
        self.assertEqual(name, "R002_S00")

        name = self.mapper._extractDetectorName({"detector": 71, 'visit': 201607220607067})
        self.assertEqual(name, "R071_S00")

        name = self.mapper._extractDetectorName({"detector": 433, 'visit': 201811151255111, "channel": 1})
        self.assertEqual(name, "R433_S00")


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
