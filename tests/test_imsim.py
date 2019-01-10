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
from lsst.utils import getPackageDir
from lsst.afw.geom import arcseconds, Extent2I
import lsst.afw.image
import lsst.obs.base.tests


class TestImsim(lsst.obs.base.tests.ObsTests, lsst.utils.tests.TestCase):
    @classmethod
    def tearDownClass(cls):
        cls._mapper._LsstCamMapper__clearCache()
        del cls._mapper
        del cls._butler

    @classmethod
    def setUpClass(cls):
        product_dir = getPackageDir('obs_lsst')
        cls.data_dir = os.path.join(product_dir, 'data', 'input', 'imsim')

        cls._butler = lsst.daf.persistence.Butler(root=cls.data_dir)
        mapper_class = cls._butler.getMapperClass(root=cls.data_dir)
        mapper_class._LsstCamMapper__clearCache()
        cls._mapper = mapper_class(root=cls.data_dir)

    def setUp(self):
        dataIds = {'raw': {'visit': 204595, 'detectorName': 'S20', 'raftName': 'R11'},
                   'bias': {'visit': 204595, 'detectorName': 'S20', 'raftName': 'R11'},
                   'flat': {'visit': 204595, 'detectorName': 'S20', 'raftName': 'R11', 'filter': 'i'},
                   'dark': {'visit': 204595, 'detectorName': 'S20', 'raftName': 'R11'}
                   }
        self.setUp_tests(self._butler, self._mapper, dataIds)

        ccdExposureId_bits = 32
        exposureIds = {'raw': 40919042,
                       'bias': 40919042,
                       'dark': 40919042,
                       'flat': 40919042
                       }
        filters = {'raw': 'i',
                   'bias': '_unknown_',
                   'dark': '_unknown_',
                   'flat': 'i'
                   }
        exptimes = {'raw': 30.0,
                    'bias': 0.0,
                    'dark': 1.0,
                    'flat': 1.0
                    }
        detectorIds = {'raw': 42,
                       'bias': 42,
                       'dark': 42,
                       'flat': 42
                       }
        detector_names = {'raw': 'R11_S20',
                          'bias': 'R11_S20',
                          'dark': 'R11_S20',
                          'flat': 'R11_S20'
                          }
        detector_serials = {'raw': 'ITL-3800C-102-Dev',
                            'bias': 'ITL-3800C-102-Dev',
                            'dark': 'ITL-3800C-102-Dev',
                            'flat': 'ITL-3800C-102-Dev'
                            }
        dimensions = {'raw': Extent2I(4256, 4040),
                      'bias': Extent2I(4072, 4000),
                      'dark': Extent2I(4072, 4000),
                      'flat': Extent2I(4072, 4000),
                      }
        sky_origin = (55.67759886, -30.44239357)
        raw_subsets = (({'level': 'sensor', 'filter': 'i'}, 1),
                       ({'level': 'sensor', 'visit': 204595}, 1),
                       ({'level': 'filter', 'visit': 204595}, 1),
                       ({'level': 'visit', 'filter': 'i'}, 1)
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

        path_to_raw = os.path.join(self.data_dir, "raw", "204595", "R11", "00204595-R11-S20-det042-000.fits")
        keys = set(('filter', 'patch', 'tract', 'visit', 'channel', 'amp', 'style', 'detector', 'dstype',
                    'snap', 'run', 'calibDate', 'half', 'detectorName', 'raftName', 'label',
                    'numSubfilters', 'fgcmcycle', 'name', 'pixel_id', 'description', 'subfilter'))
        query_format = ["visit", "filter"]
        queryMetadata = (({'visit': 204595}, [(204595, 'i')]),
                         ({'filter': 'i'}, [(204595, 'i')]),
                         )
        map_python_type = lsst.afw.image.DecoratedImageF
        map_python_std_type = lsst.afw.image.ExposureF
        map_cpp_type = 'DecoratedImageF'
        map_storage_name = 'FitsStorage'
        metadata_output_path = os.path.join('processCcd_metadata', '00204595-i', 'R11',
                                            'processCcdMetadata_00204595-i-R11-S20-det042.yaml')
        raw_filename = '00204595-R11-S20-det042-000.fits'
        default_level = 'visit'
        raw_levels = (('skyTile', set(['visit', 'detector', 'snap', 'run', 'detectorName', 'raftName'])),
                      ('filter', set(['visit', 'detector', 'snap', 'run', 'detectorName', 'raftName'])),
                      ('visit', set(['visit', 'detector', 'snap', 'run', 'detectorName', 'raftName']))
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

        self.setUp_camera(camera_name='lsstCam',
                          n_detectors=189,
                          first_detector_name='R01_S00',
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
