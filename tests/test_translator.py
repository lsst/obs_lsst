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

import os.path
import unittest
import astropy
import astropy.units as u
import astropy.units.cds as cds
import lsst.obs.lsst.translators  # noqa: F401 -- register the translators

from astro_metadata_translator.tests import MetadataAssertHelper

TESTDIR = os.path.abspath(os.path.dirname(__file__))


class LsstMetadataTranslatorTestCase(unittest.TestCase, MetadataAssertHelper):
    datadir = os.path.join(TESTDIR, "headers")

    def test_phosim_translator(self):
        test_data = (("phosim-lsst_a_204595_f3_R11_S02_E000.yaml",
                      dict(telescope="LSST",
                           instrument="PhoSim",
                           boresight_rotation_coord="sky",
                           dark_time=30.0*u.s,
                           detector_exposure_id=40919038,
                           detector_group="R11",
                           detector_name="S02",
                           detector_num=38,
                           detector_serial="R11_S02",
                           exposure_id=204595,
                           exposure_time=30.0*u.s,
                           object="unknown",
                           observation_id="204595",
                           observation_type="science",
                           physical_filter="i",
                           pressure=520.0*cds.mmHg,
                           relative_humidity=40.0,
                           science_program="204595",
                           temperature=20.0*u.deg_C,
                           visit_id=204595,
                           wcs_params=dict(max_sep=3000.))),  # 2022
                     )
        for file, expected in test_data:
            with self.subTest(f"Testing {file}"):
                # PhoSim data are in the future and Astropy complains
                # about astrometry errors.
                with self.assertWarns(astropy.utils.exceptions.AstropyWarning):
                    self.assertObservationInfoFromYaml(file, dir=self.datadir, **expected)

    def test_auxtel_translator(self):
        test_data = (("auxTel-2018-09-20-05700065-det000.yaml",
                      dict(telescope="LSSTAuxTel",
                           instrument="LATISS",
                           boresight_rotation_coord="unknown",
                           dark_time=27.0*u.s,
                           detector_exposure_id=20180920000065,
                           detector_group="RXX",
                           detector_name="S00",
                           detector_num=0,
                           detector_serial="ITL-3800C-098",
                           exposure_id=20180920000065,
                           exposure_time=27.0*u.s,
                           object=None,
                           observation_id="AT_C_20180920_000065",
                           observation_type="dark",
                           physical_filter=None,
                           pressure=None,
                           relative_humidity=None,
                           science_program="unknown",
                           temperature=None,
                           visit_id=20180920000065,
                           )),
                     )
        for file, expected in test_data:
            with self.subTest(f"Testing {file}"):
                self.assertObservationInfoFromYaml(file, dir=self.datadir, **expected)

    def test_imsim_translator(self):
        test_data = (("imsim-bias-lsst_a_3010002_R11_S00.yaml",
                      dict(telescope="LSST",
                           instrument="ImSim",
                           boresight_rotation_coord="sky",
                           dark_time=0.0*u.s,
                           detector_exposure_id=602000436,
                           detector_group="R11",
                           detector_name="S00",
                           detector_num=36,
                           detector_serial="LCA-11021_RTM-000",
                           exposure_id=3010002,
                           exposure_time=0.0*u.s,
                           object="unknown",
                           observation_id="3010002",
                           observation_type="science",  # The header is wrong
                           physical_filter="i",
                           pressure=None,
                           relative_humidity=40.0,
                           science_program="42",
                           temperature=None,
                           visit_id=3010002,
                           wcs_params=dict(max_sep=3000.),  # 2022
                           )),
                     ("imsim-lsst_a_204595_R11_S02_i.yaml",
                      dict(telescope="LSST",
                           instrument="ImSim",
                           boresight_rotation_coord="sky",
                           dark_time=30.0*u.s,
                           detector_exposure_id=40919038,
                           detector_group="R11",
                           detector_name="S02",
                           detector_num=38,
                           detector_serial="LCA-11021_RTM-000",
                           exposure_id=204595,
                           exposure_time=30.0*u.s,
                           object="unknown",
                           observation_id="204595",
                           observation_type="science",  # The header is wrong
                           physical_filter="i",
                           pressure=None,
                           relative_humidity=40.0,
                           science_program="204595",
                           temperature=None,
                           visit_id=204595,
                           wcs_params=dict(max_sep=3000.),  # 2022
                           )),
                     ("imsim-flats-lsst_a_5000007_R11_S20_i.yaml",
                      dict(telescope="LSST",
                           instrument="ImSim",
                           boresight_rotation_coord="sky",
                           dark_time=30.0*u.s,
                           detector_exposure_id=1000001442,
                           detector_group="R11",
                           detector_name="S20",
                           detector_num=42,
                           detector_serial="LCA-11021_RTM-000",
                           exposure_id=5000007,
                           exposure_time=30.0*u.s,
                           object="unknown",
                           observation_id="5000007",
                           observation_type="flat",
                           physical_filter="i",
                           pressure=None,
                           relative_humidity=40.0,
                           science_program="5000007",
                           temperature=None,
                           visit_id=5000007,
                           wcs_params=dict(max_sep=3000.),  # 2022
                           )),
                     ("imsim-dark-lsst_a_4010003_R11_S11.yaml",
                      dict(telescope="LSST",
                           instrument="ImSim",
                           boresight_rotation_coord="sky",
                           dark_time=500.0*u.s,
                           detector_exposure_id=802000640,
                           detector_group="R11",
                           detector_name="S11",
                           detector_num=40,
                           detector_serial="LCA-11021_RTM-000",
                           exposure_id=4010003,
                           exposure_time=500.0*u.s,
                           object="unknown",
                           observation_id="4010003",
                           observation_type="science",  # The header is wrong
                           physical_filter="i",
                           pressure=None,
                           relative_humidity=40.0,
                           science_program="42",
                           temperature=None,
                           visit_id=4010003,
                           wcs_params=dict(max_sep=3000.),  # 2022
                           )),
                     )
        for file, expected in test_data:
            with self.subTest(f"Testing {file}"):
                # ImSim data are in the future and Astropy complains
                # about astrometry errors.
                if expected["observation_type"] == "science":
                    with self.assertWarns(astropy.utils.exceptions.AstropyWarning):
                        self.assertObservationInfoFromYaml(file, dir=self.datadir, **expected)
                else:
                    self.assertObservationInfoFromYaml(file, dir=self.datadir, **expected)

    def test_ts8_translator(self):
        test_data = (("ts8-E2V-CCD250-179_lambda_bias_024_6006D_20180724104156.yaml",
                      dict(telescope="LSST",
                           instrument="TS8",
                           detector_exposure_id=2700961194,
                           detector_group="R10",
                           detector_name="S11",
                           detector_num=4,
                           detector_serial="E2V-CCD250-179",
                           exposure_id=270096119,
                           exposure_time=0.0*u.s,
                           observation_id="E2V-CCD250-179_lambda_bias_024_6006D_20180724104156",
                           observation_type="bias",
                           physical_filter="y",
                           science_program="6006D",
                           visit_id=270096119)),
                     ("ts8-E2V-CCD250-200-Dev_lambda_flat_0700_6006D_20180724102845.yaml",
                      dict(telescope="LSST",
                           instrument="TS8",
                           detector_exposure_id=2700953282,
                           detector_group="R10",
                           detector_name="S02",
                           detector_num=2,
                           detector_serial="E2V-CCD250-200",
                           exposure_id=270095328,
                           exposure_time=21.913*u.s,
                           observation_id="E2V-CCD250-200-Dev_lambda_flat_0700_6006D_20180724102845",
                           observation_type="flat",
                           physical_filter="z",
                           science_program="6006D",
                           visit_id=270095328)),
                     )
        for file, expected in test_data:
            with self.subTest(f"Testing {file}"):
                self.assertObservationInfoFromYaml(file, dir=self.datadir, **expected)


if __name__ == "__main__":
    unittest.main()
