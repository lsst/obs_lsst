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
import lsst.obs.lsst


class TestObsTest(lsst.obs.base.tests.ObsTests, lsst.utils.tests.TestCase):
    def setUp(self):
        product_dir = getPackageDir('obs_lsst')
        data_dir = os.path.join(product_dir, 'data', 'input', 'phosim')

        butler = lsst.daf.persistence.Butler(root=data_dir)
        mapper = lsst.obs.lsst.phosim.PhosimMapper(root=data_dir)
        dataIds = {'raw': {'visit': 204595, 'detectorName': 'S20', 'raftName': 'R11'},
                   'bias': unittest.SkipTest,
                   'flat': unittest.SkipTest,
                   'dark': unittest.SkipTest
                   }
        self.setUp_tests(butler, mapper, dataIds)

        ccdExposureId_bits = 32
        exposureIds = {'raw': 40919042}
        filters = {'raw': 'i'}
        exptimes = {'raw': 30.0}
        detectorIds = {'raw': 42}
        detector_names = {'raw': 'R11_S20'}
        detector_serials = {'raw': 'ITL-3800C-102-Dev'}
        dimensions = {'raw': Extent2I(4176, 4020)}
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

        path_to_raw = os.path.join(data_dir, "raw", "204595", "R11", "00204595-R11-S20-det042-000.fits")
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
        self.setUp_mapper(output=data_dir,
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
                          )

        self.setUp_camera(camera_name='lsstCam',
                          n_detectors=225,
                          first_detector_name='R01_S00',
                          plate_scale=20.0 * arcseconds,
                          )

        super(TestObsTest, self).setUp()

class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
