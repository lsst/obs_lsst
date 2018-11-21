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


class PhoSimTestCase(unittest.TestCase, MetadataAssertHelper):
    datadir = os.path.join(TESTDIR, "headers")

    def test_phosim_translator(self):
        test_data = (("phosim-lsst_a_204595_f3_R11_S02_E000.yaml",
                      dict(telescope="LSST",
                           instrument="PhoSim",
                           boresight_rotation_coord="sky",
                           dark_time=30.0*u.s,
                           detector_exposure_id=40919105,
                           detector_name="R11_S02",
                           detector_num=105,
                           exposure_id=204595,
                           exposure_time=30.0*u.s,
                           object="unknown",
                           observation_id="204595",
                           observation_type="science",
                           physical_filter="i",
                           pressure=520.0*cds.mmHg,
                           relative_humidity=40.0,
                           science_program="phosim",
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


if __name__ == "__main__":
    unittest.main()
