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

import lsst.log
import lsst.utils.tests
from lsst.geom import arcseconds, Extent2I
import lsst.afw.image

from lsst.obs.lsst.testHelper import ObsLsstButlerTests, ObsLsstObsBaseOverrides


class TestLatiss(ObsLsstObsBaseOverrides, ObsLsstButlerTests):
    instrumentDir = "latiss"

    def setUp(self):
        dataIds = {'raw': {'visit': 12018092000065, 'detector': 0, 'dayObs': '2018-09-20', 'seqNum': 65},
                   'bias': {'detector': 0, 'dayObs': '2018-09-20', 'seqNum': 65},
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest
                   }
        self.setUp_tests(self._butler, self._mapper, dataIds)

        ccdExposureId_bits = 54
        exposureIds = {'raw': 12018092000065, 'bias': 12018092000065}
        filters = {'raw': 'NONE', 'bias': '_unknown_'}
        exptimes = {'raw': 27.0, 'bias': 0}
        detectorIds = {'raw': 0, 'bias': 0}
        detector_names = {'raw': 'RXX_S00', 'bias': 'RXX_S00'}
        detector_serials = {'raw': 'ITL-3800C-098', 'bias': 'ITL-3800C-098'}
        dimensions = {'raw': Extent2I(4608, 4096),
                      'bias': Extent2I(4072, 4000)}
        sky_origin = unittest.SkipTest
        raw_subsets = (({'level': 'sensor', 'filter': 'NONE'}, 1),
                       ({'level': 'sensor', 'visit': 12018092000065}, 1),
                       ({'level': 'filter', 'visit': 12018092000065}, 1),
                       ({'level': 'visit', 'filter': 'NONE'}, 1)
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

        path_to_raw = os.path.join(self.data_dir, "raw", "2018-09-20", "12018092000065-det000.fits")
        keys = set(('filter', 'patch', 'tract', 'visit', 'channel', 'amp', 'style', 'detector', 'dstype',
                    'calibDate', 'half', 'label', 'dayObs', 'run', 'snap', 'detectorName', 'raftName',
                    'numSubfilters', 'fgcmcycle', 'name', 'pixel_id', 'description', 'subfilter'))
        query_format = ["visit", "seqNum", "dayObs"]
        queryMetadata = (({'visit': 12018092000065}, [(12018092000065, 65, '2018-09-20')]),
                         ({'detector': 0}, [(12018092000065, 65, '2018-09-20')]),
                         ({'seqNum': 65}, [(12018092000065, 65, '2018-09-20')]),
                         )
        map_python_type = lsst.afw.image.DecoratedImageF
        map_python_std_type = lsst.afw.image.ExposureF
        map_cpp_type = 'DecoratedImageF'
        map_storage_name = 'FitsStorage'
        metadata_output_path = None  # Not on sky data so processCcd not run.

        raw_filename = '12018092000065-det000.fits'
        default_level = 'visit'
        raw_levels = (('skyTile', set(['visit', 'detector', 'dayObs'])),
                      ('filter', set(['visit', 'detector', 'dayObs'])),
                      ('visit', set(['visit', 'detector', 'dayObs']))
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

        self.setUp_camera(camera_name='LATISS',
                          n_detectors=1,
                          first_detector_name='RXX_S00',
                          plate_scale=20.0 * arcseconds,
                          )

        super().setUp()

    def testCcdExposureId(self):
        exposureId = self.butler.get('ccdExposureId', dataId={})
        self.assertEqual(exposureId, 0)

        exposureId = self.butler.get('ccdExposureId', dataId={"visit": 1, "detector": 0})
        self.assertEqual(exposureId, 1)

        exposureId = self.butler.get('ccdExposureId', dataId={"visit": 1})
        self.assertEqual(exposureId, 1)

        exposureId = self.butler.get('ccdExposureId', dataId={"dayObs": "2020-01-01", "seqNum": 999,
                                                              "controller": "O"})
        self.assertEqual(exposureId, 2020010100999)

        # This will trigger a Python log message and lsst.log message
        with self.assertLogs(level="WARNING") as cm:
            with lsst.log.UsePythonLogging():
                exposureId = self.butler.get('ccdExposureId', dataId={"visit": 1, "detector": 1})
        self.assertEqual(len(cm.output), 2)
        self.assertEqual(exposureId, 1)

        with self.assertRaises(ValueError):
            exposureId = self.butler.get('ccdExposureId', dataId={"dayObs": "2020-01-01", "seqNum": 1000000})

        with self.assertRaises(ValueError):
            exposureId = self.butler.get('ccdExposureId', dataId={"dayObs": "20-01-01", "seqNum": 9999})

    def testDetectorName(self):
        name = self.mapper._extractDetectorName({})
        self.assertEqual(name, "RXX_S00")


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
