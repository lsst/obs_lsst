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

import unittest

from lsst.daf.butler import DataCoordinate, RegistryConfig
from lsst.daf.butler.registry.sql_registry import SqlRegistry
from lsst.obs.lsst import (
    Latiss,
    LsstCam,
    LsstCamImSim,
    LsstCamPhoSim,
    LsstCamSim,
    LsstComCam,
    LsstComCamSim,
    LsstTS3,
    LsstTS8,
    LsstUCDCam,
    RubinDimensionPacker,
)
from lsst.pex.config import Config
from lsst.pipe.base import Instrument, ObservationDimensionPacker


class _TestConfig(Config):
    packer = Instrument.make_dimension_packer_config_field()


class RubinDimensionPackerTestCase(unittest.TestCase):
    """Test the custom data ID packer implementation for the main Rubin
    instruments.

    This test mostly checks the data ID packer's methods for self-consistency,
    and that the Instrument-class overrides work as expected.  Direct tests of
    The packing algorithm is tested against hard-coded values in
    test_translators.py, since some translators now delegate to it.
    """

    def setUp(self) -> None:
        registry_config = RegistryConfig()
        registry_config["db"] = "sqlite://"
        self.registry = SqlRegistry.createFromConfig(registry_config)
        self.rubin_packer_instruments = [LsstCam, LsstComCam, LsstComCamSim,
                                         Latiss]
        self.old_packer_instruments = [
            LsstCamImSim,
            LsstCamPhoSim,
            LsstTS8,
            LsstTS3,
            LsstUCDCam,
        ]
        for cls in self.rubin_packer_instruments + self.old_packer_instruments:
            cls().register(self.registry)

    def tearDown(self) -> None:
        self.registry.close()

    def check_rubin_dimension_packer(
        self,
        instrument: Instrument,
        is_exposure: bool,
        *,
        exposure_id: int,
        day_obs: int,
        seq_num: int,
        detector: int,
        controller: str = "O",
        is_one_to_one_reinterpretation: bool = False,
        visit_id: int | None = None,
        use_controllers: bool = False,
    ) -> None:
        """Run tests on an instrument that uses the new Rubin dimension packer.

        Parameters
        ----------
        instrument : `lsst.pipe.base.Instrument`
            Instrument instance to be tested.
        is_exposure : `bool`
            `True` to pack ``{detector, exposure}`` data IDs, `False` to pack
            ``{detector, visit}`` data IDs.
        exposure_id : `int`
            Integer data ID.
        day_obs : `int`
            Date of observations as a YYYYMMDD decimal integer, consistent with
            ``exposure_id``.
        seq_num : `int`
            Instrument sequence number, consistent with ``exposure_id``.
        detector : `int`
            Integer detector data ID value.
        controller : `str`, optional
            Controller code consistent with ``exposure_id``.
        is_one_to_one_reinterpretation : `bool`, optional
            If `True`, this is a visit ID that represents the alternate
            interpretation of that exposure (which must be the first snap in a
            multi-snap sequence) as a standalone visit.
        visit_id : `int`
            Integer visit ID.  Must be provided only if
            ``is_one_to_one_reinterpretatation=True``; otherwise this is the
            same as ``exposure_id``.
        use_controllers : `bool`, optional
            Whether to configure the packer to encode and hence round-trip
            controller values.  This tests more of the functionality but is not
            the default behavior, since we instead want to assume OCS and
            save bits for data releases.
        """
        if visit_id is None:
            assert (
                not is_one_to_one_reinterpretation
            ), "Test should not infer visit_id in this case."
            visit_id = exposure_id
        instrument_data_id = self.registry.expandDataId(instrument=instrument.getName())
        config = _TestConfig()
        if use_controllers:
            config.packer["rubin"].use_controllers()
        packer = config.packer.apply(instrument_data_id, is_exposure=is_exposure)
        self.assertIsInstance(packer, RubinDimensionPacker)
        self.assertEqual(packer.maxBits, 41 if use_controllers else 38)
        full_data_id = DataCoordinate.standardize(
            instrument_data_id, exposure=exposure_id, visit=visit_id, detector=detector
        )
        packed1 = RubinDimensionPacker.pack_decomposition(
            day_obs,
            seq_num,
            detector,
            controller,
            is_one_to_one_reinterpretation=is_one_to_one_reinterpretation,
            config=packer.config,
        )
        packed2 = RubinDimensionPacker.pack_id_pair(
            exposure_id,
            detector,
            is_one_to_one_reinterpretation=is_one_to_one_reinterpretation,
            config=packer.config,
        )
        packed3 = packer.pack(full_data_id)
        self.assertEqual(packed1, packed2)
        self.assertEqual(packed1, packed3)
        (
            u_day_obs,
            u_seq_num,
            u_detector,
            u_controller,
            u_is_one_to_one_reinterpretation,
        ) = RubinDimensionPacker.unpack_decomposition(packed1, config=packer.config)
        self.assertEqual(u_day_obs, day_obs)
        self.assertEqual(u_seq_num, seq_num)
        self.assertEqual(u_detector, detector)
        self.assertEqual(u_controller, controller)
        self.assertEqual(u_is_one_to_one_reinterpretation, is_one_to_one_reinterpretation)
        (
            u_exposure_id,
            u_detector,
            u_is_one_to_one_reinterpretation,
        ) = RubinDimensionPacker.unpack_id_pair(packed1, config=packer.config)
        self.assertEqual(u_exposure_id, exposure_id)
        self.assertEqual(u_detector, detector)
        self.assertEqual(u_is_one_to_one_reinterpretation, is_one_to_one_reinterpretation)
        u_data_id = packer.unpack(packed1)
        self.assertEqual(u_data_id, full_data_id.subset(packer.dimensions))

    def check_old_dimension_packer(
        self,
        instrument: Instrument,
        is_exposure: bool,
    ) -> None:
        """Test that an Instrument's default dimension packer is still
        `lsst.pipe.base.ObservationDimensionPacker`.
        """
        instrument_data_id = self.registry.expandDataId(instrument=instrument.getName())
        config = _TestConfig()
        packer = config.packer.apply(instrument_data_id, is_exposure=is_exposure)
        # This instrument still uses the pipe_base default dimension packer,
        # which is tested there.  Nothing more to do here.
        self.assertIsInstance(packer, ObservationDimensionPacker)

    def test_latiss(self):
        instrument = Latiss()
        instrument.register(self.registry)
        # Input values obtained from:
        # $ butler query-dimension-records /repo/main exposure --where \
        #     "instrument='LATISS'" --limit 1
        self.check_rubin_dimension_packer(
            instrument,
            is_exposure=True,
            exposure_id=2022062800004,
            day_obs=20220628,
            seq_num=4,
            detector=0,
        )
        # Input values obtained from:
        # $ butler query-dimension-records /repo/main visit --where \
        #    "instrument='LATISS'" --limit 1
        self.check_rubin_dimension_packer(
            instrument,
            is_exposure=False,
            exposure_id=2021090800749,
            day_obs=20210908,
            seq_num=749,
            detector=0,
        )
        # Input data obtained from:
        # $ butler query-dimension-records /repo/embargo visit --where \
        #    "instrument='LATISS' AND visit_system=0 AND exposure != visit" \
        #    --limit 1
        self.check_rubin_dimension_packer(
            instrument,
            is_exposure=False,
            exposure_id=2022101101105,
            day_obs=20221011,
            seq_num=1105,
            detector=0,
            visit_id=92022101101105,
            is_one_to_one_reinterpretation=True,
        )

    def test_lsstCam(self):
        instrument = LsstCam()
        instrument.register(self.registry)
        # Input values obtained from:
        # $ butler query-dimension-records /repo/main exposure --where \
        #     "instrument='LSSTCam'" --limit 1
        self.check_rubin_dimension_packer(
            instrument,
            is_exposure=True,
            exposure_id=3021121400075,
            day_obs=20211214,
            seq_num=75,
            detector=150,
            controller="C",
            use_controllers=True,
        )

    def test_comCam(self):
        instrument = LsstComCam()
        instrument.register(self.registry)
        # Input values obtained from:
        # $ butler query-dimension-records /repo/main exposure --where \
        #     "instrument='LSSTComCam'" --limit 1
        self.check_rubin_dimension_packer(
            instrument,
            is_exposure=True,
            exposure_id=2020091100004,
            day_obs=20200911,
            seq_num=4,
            detector=5,
        )

    def test_comCamSim(self):
        instrument = LsstComCamSim()
        instrument.register(self.registry)
        # Input values obtained from:
        # $ butler query-dimension-records data/input/comCamSim exposure \
        #      --where "instrument='LSSTComCamSim'" --limit 1
        self.check_rubin_dimension_packer(
            instrument,
            is_exposure=False,
            exposure_id=7024032100720,
            day_obs=20240321,
            seq_num=720,
            detector=4,
            controller="S",
            use_controllers=True,
        )

    def test_lsstCamSim(self):
        instrument = LsstCamSim()
        instrument.register(self.registry)
        # Input values obtained from:
        # $ butler query-dimension-records data/input/lsstCamSim exposure \
        #      --where "instrument='LSSTCamSim'" --limit 1
        self.check_rubin_dimension_packer(
            instrument,
            is_exposure=True,
            exposure_id=7024032100720,
            day_obs=20240321,
            seq_num=720,
            detector=94,
            controller="S",
            use_controllers=True,
        )

    def test_imsim(self):
        instrument = LsstCamImSim()
        instrument.register(self.registry)
        self.check_old_dimension_packer(instrument, is_exposure=True)
        self.check_old_dimension_packer(instrument, is_exposure=False)

    def test_phosim(self):
        instrument = LsstCamPhoSim()
        instrument.register(self.registry)
        self.check_old_dimension_packer(instrument, is_exposure=True)
        self.check_old_dimension_packer(instrument, is_exposure=False)

    def test_ts3(self):
        instrument = LsstTS3()
        instrument.register(self.registry)
        self.check_old_dimension_packer(instrument, is_exposure=True)

    def test_ts8(self):
        instrument = LsstTS8()
        instrument.register(self.registry)
        self.check_old_dimension_packer(instrument, is_exposure=True)

    def test_ucdcam(self):
        instrument = LsstUCDCam()
        instrument.register(self.registry)
        self.check_old_dimension_packer(instrument, is_exposure=True)


if __name__ == "__main__":
    unittest.main()
