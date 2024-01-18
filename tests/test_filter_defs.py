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
from lsst.obs.lsst import (
    LSSTCAM_FILTER_DEFINITIONS,
    LATISS_FILTER_DEFINITIONS,
    LSSTCAM_IMSIM_FILTER_DEFINITIONS,
    TS3_FILTER_DEFINITIONS,
    TS8_FILTER_DEFINITIONS,
    COMCAM_FILTER_DEFINITIONS,
    GENERIC_FILTER_DEFINITIONS,
)
import lsst.obs.lsst.translators  # noqa: F401 -- register the translators

from astro_metadata_translator import ObservationInfo
from astro_metadata_translator.tests import read_test_file

TESTDIR = os.path.abspath(os.path.dirname(__file__))


class FilterDefTestCase(unittest.TestCase):
    """Each test reads in raw headers from YAML files, constructs an
    `ObservationInfo`, and checks that the filter definitions for the
    corresponding instrument contains the `physical_filter` value
    computed by the translator code.
    """

    datadir = os.path.join(TESTDIR, "headers")

    def assert_in_filter_defs(self, header_file, filter_def_set):
        header = read_test_file(header_file, dir=self.datadir)
        obs_info = ObservationInfo(header, pedantic=True, filename=header_file)
        self.assertIn(obs_info.physical_filter, filter_def_set)

    def test_lsstCam_filterdefs(self):
        filter_def_set = set(_.physical_filter for _ in LSSTCAM_FILTER_DEFINITIONS)
        test_data = (
            "lsstCam-MC_C_20190319_000001_R10_S02.yaml",
            "lsstCam-MC_C_20190319_000001_R22_S21.yaml",
            "lsstCam-MC_C_20190322_000002_R10_S22.yaml",
            "lsstCam-MC_C_20190406_000643_R10_S00.yaml",
            "lsstCam_MC_C_20231125_000600_R12_S10.yaml",
        )
        for filename in test_data:
            with self.subTest(f"Testing {filename}"):
                self.assert_in_filter_defs(filename, filter_def_set)

    def test_latiss_filterdefs(self):
        filter_def_set = set(_.physical_filter for _ in LATISS_FILTER_DEFINITIONS)
        test_data = (
            "latiss-2018-09-20-05700065-det000.yaml",
            "latiss-AT_O_20190306_000014.yaml",
            "latiss-AT_O_20190329_000022-ats-wfs_ccd.yaml",
            "latiss-AT_O_20190915_000037.yaml",
            "latiss-AT_O_20191031_000004.yaml",
            "latiss-AT_O_20191104_000003.yaml",
            "latiss-AT_O_20191113_000061.yaml",
            "latiss-AT_O_20200121_000045.yaml",
            "latiss-AT_O_20200128_000335.yaml",
            "latiss-AT_O_20200128_000379.yaml",
            "latiss-AT_O_20210210_000011.yaml",
            "latiss-AT_O_20210212_000006.yaml",
            "latiss-AT_O_20220405_000348.yaml",
            "latiss-AT_O_20220405_000349.yaml",
            "latiss-AT_O_20230321_000053.yaml",
            "latiss-future.yaml",
        )
        for filename in test_data:
            with self.subTest(f"Testing {filename}"):
                self.assert_in_filter_defs(filename, filter_def_set)

    def test_imsim_filterdefs(self):
        filter_def_set = set(
            _.physical_filter for _ in LSSTCAM_IMSIM_FILTER_DEFINITIONS
        )
        test_data = (
            "imsim-bias-lsst_a_3010002_R11_S00.yaml",
            "imsim-dark-lsst_a_4010003_R11_S11.yaml",
            "imsim-flats-lsst_a_5000007_R11_S20_i.yaml",
            "imsim-lsst_a_204595_R11_S02_i.yaml",
        )
        for filename in test_data:
            with self.subTest(f"Testing {filename}"):
                self.assert_in_filter_defs(filename, filter_def_set)

    def test_ts3_filterdefs(self):
        filter_def_set = set(_.physical_filter for _ in TS3_FILTER_DEFINITIONS)
        test_data = (
            "ts3-E2V-CCD250-411_lambda_flat_1000_025_20181115075559.yaml",
            "ts3-ITL-3800C-098_lambda_flat_1000_067_20160722020740.yaml",
        )
        for filename in test_data:
            with self.subTest(f"Testing {filename}"):
                self.assert_in_filter_defs(filename, filter_def_set)

    def test_ts8_filterdefs(self):
        filter_def_set = set(_.physical_filter for _ in TS8_FILTER_DEFINITIONS)
        test_data = (
            "ts8-E2V-CCD250-179_lambda_bias_024_6006D_20180724104156.yaml",
            "ts8-E2V-CCD250-200-Dev_lambda_flat_0700_6006D_20180724102845.yaml",
            "ts8-E2V-CCD250-220_fe55_fe55_094_6288_20171215114006.yaml",
            "ts8-TS_C_20220711_000174_R22_S00.yaml",
            "ts8-TS_C_20230512_000021_R22_S02.yaml",
        )
        for filename in test_data:
            with self.subTest(f"Testing {filename}"):
                self.assert_in_filter_defs(filename, filter_def_set)

    def test_comCam_filterdefs(self):
        filter_def_set = set(_.physical_filter for _ in COMCAM_FILTER_DEFINITIONS)
        test_data = (
            "comCam-CC_C_20190526_000223_R22_S01.yaml",
            "comCam-CC_C_20190530_000001_R22_S00.yaml",
            "comCam-CC_H_20100217_006001_R22_S00.yaml",
        )
        for filename in test_data:
            with self.subTest(f"Testing {filename}"):
                self.assert_in_filter_defs(filename, filter_def_set)

    def test_generic_filterdefs(self):
        filter_def_set = set(_.physical_filter for _ in GENERIC_FILTER_DEFINITIONS)
        test_data = (
            "phosim-lsst_a_204595_f3_R11_S02_E000.yaml",
            "lsstCam-MC_H_20100217_000032_R22_S00.yaml",  # This is a phosim header
            "UCD-E2V-CCD250-TS_C_20231031_000227_R21_S01.yaml",
            "UCD-ITL-3800C-TS_C_20230730_000237_R22_S01.yaml",
        )
        for filename in test_data:
            with self.subTest(f"Testing {filename}"):
                self.assert_in_filter_defs(filename, filter_def_set)
