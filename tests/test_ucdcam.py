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
from lsst.afw.geom import arcseconds, Extent2I
import lsst.afw.image
import lsst.obs.base.tests

from lsst.obs.lsst.testHelper import ObsLsstButlerTests


class TestUcdCam(lsst.obs.base.tests.ObsTests, ObsLsstButlerTests):
    instrumentDir = "ucd"

    def setUp(self):
        dataIds = {'raw': {'visit': 20180530150355, 'detectorName': 'S00', 'raftName': 'R02'},
                   'bias': unittest.SkipTest,
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest
                   }
        self.setUp_tests(self._butler, self._mapper, dataIds)

        ccdExposureId_bits = 36
        exposureIds = {'raw': 201805301503552}
        filters = {'raw': 'r'}
        exptimes = {'raw': 0.5}
        detectorIds = {'raw': 2}
        detector_names = {'raw': 'R02_S00'}
        detector_serials = {'raw': 'ITL-3800C-002'}
        dimensions = {'raw': Extent2I(0, 0)}
        sky_origin = unittest.SkipTest
        raw_subsets = (({'level': 'detector', 'filter': 'r'}, 2),
                       ({'level': 'detector', 'visit': 20180530150355}, 1),
                       ({'level': 'filter', 'visit': 20180530150355}, 1),
                       ({'level': 'visit', 'filter': 'r'}, 2)
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

        path_to_raw = os.path.join(self.data_dir, "raw", "2018-05-30", "20180530150355-S00-det002")
        keys = set(('filter', 'patch', 'tract', 'visit', 'channel', 'amp', 'style', 'detector', 'dstype',
                    'snap', 'run', 'calibDate', 'half', 'detectorName', 'raftName', 'label',
                    'numSubfilters', 'fgcmcycle', 'name', 'pixel_id', 'description', 'subfilter'))
        query_format = ["visit", "filter"]
        queryMetadata = (({'visit': 20180530150355}, [(20180530150355, 'r')]),
                         ({'detector': '2'}, [(20180530150355, 'r')]),
                         )
        map_python_type = lsst.afw.image.DecoratedImageF
        map_python_std_type = lsst.afw.image.ExposureF
        map_cpp_type = 'DecoratedImageF'
        map_storage_name = 'FitsStorage'
        metadata_output_path = None  # Not on sky data so processCcd not run.

        raw_filename = '20180530150355-S00-det002'
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
                          test_config_metadata=False
                          )

        self.setUp_camera(camera_name='lsstCam',
                          n_detectors=3,
                          first_detector_name='R00_S00',
                          plate_scale=20.0 * arcseconds,
                          )

        super().setUp()


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
