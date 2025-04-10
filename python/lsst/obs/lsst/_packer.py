# This file is part of obs_base.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
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

from __future__ import annotations

__all__ = ("RubinDimensionPacker",)

import datetime
import math

from lsst.daf.butler import DataCoordinate, DimensionPacker
from lsst.pex.config import Config, Field, DictField
from lsst.pipe.base import observation_packer_registry
from .translators.lsst import CONTROLLERS, EXPOSURE_ID_MAXDIGITS, LsstBaseTranslator


def convert_day_obs_to_ordinal(day_obs: int) -> int:
    """Convert a YYYYMMDD decimal-digit integer date to a day ordinal.

    Parameters
    ----------
    day_obs : `int`
        A YYYYMMDD decimal-digit integer.

    Returns
    -------
    day_ordinal : `int`
        An integer that counts days directly, with absolute offset
        unspecified.
    """
    year_month, day = divmod(day_obs, 100)
    year, month = divmod(year_month, 100)
    return datetime.date(year, month, day).toordinal()


def convert_ordinal_to_day_obs(day_ordinal: int) -> int:
    """Convert a day ordinal to a YYYYMMDD decimal-digit integer date.

    Parameters
    ----------
    day_ordinal : `int`
        An integer that counts days directly, with absolute offset
        unspecified.

    Returns
    -------
    day_obs : `int`
        A YYYYMMDD decimal-digit integer.
    """
    date = datetime.date.fromordinal(day_ordinal)
    return (date.year * 100 + date.month) * 100 + date.day


def _is_positive(x: int) -> bool:
    """Callable that tests whether an integer is positive, for use as a
    config ``check`` argument."""
    return x > 0


class RubinDimensionPackerConfig(Config):

    controllers = DictField(
        "Mapping from controller code to integer.",
        keytype=str,
        itemtype=int,
        # Default is to assume all data we're using a dimension packer on is
        # OCS, since the main use of the packer for source/object IDs.
        default={"O": 0},
    )

    n_controllers = Field(
        "Reserved number of controller codes.  May be larger than `len(controllers)`.",
        dtype=int,
        check=_is_positive,
        default=1,
    )

    n_visit_definitions = Field(
        "Reserved number of visit definitions a single exposure may belong to.",
        dtype=int,
        check=_is_positive,
        default=2,
        # We need one bit for one-to-one visits that contain only the first
        # exposure in a sequence that was originally observed as a multi-snap
        # sequence.
    )

    n_days = Field(
        "Reserved number of distinct valid-date day_obs values, starting from `day_obs_begin`.",
        dtype=int,
        check=_is_positive,
        default=16384,
        # Default of 16384 is about 45 years, which with day_obs_begin is
        # roughly consistent (and a bit bigger than) the bounds permitted by
        # the translator.
    )

    n_seq_nums = Field(
        "Reserved number of seq_num values, starting from 0.",
        dtype=int,
        check=_is_positive,
        default=32768,
        # Default is one exposure every 2.63s for a full day, which is really
        # close to the hardware limit of one every 2.3s, and far from what
        # anyone would actually do in practice.
    )

    n_detectors = Field(
        "Reserved number of detectors, starting from 0.",
        dtype=int,
        check=_is_positive,
        default=256
        # Default is the number of actual detectors (201, including corner
        # rafts) rounded up to a power of 2.
    )

    day_obs_begin = Field(
        "Inclusive lower bound on day_obs.",
        dtype=int,
        default=20100101
        # Default is just a nice round date that (with n_days) puts the end
        # point just after the 2050 bound in the translators.
    )

    def use_controllers(self) -> None:
        """Configure this packer to include all known controllers, instead
        of eliminating that field to save bit space.

        This still does not make the packing of controller, day_obs, and
        seq_num here the same as what is done in the translator class
        calculations of exposure_id, because that translator calculation is
        day_obs dependent.
        """
        self.controllers = {c: i for i, c in enumerate(CONTROLLERS)}
        self.n_controllers = 8

    def validate(self):
        super().validate()
        for c, i in self.controllers.items():
            if i >= self.n_controllers:
                raise ValueError(
                    f"Controller code {c!r} has index {i}, which is out of bounds "
                    f"for n_controllers={self.n_controllers}."
                )


class RubinDimensionPacker(DimensionPacker):
    """A data ID packer that converts Rubin visit+detector and
    exposure+detector data IDs to integers.

    Parameters
    ----------
    data_id : `lsst.daf.butler.DataCoordinate`
        Data ID identifying at least the instrument dimension.  Does not need
        to have dimension records attached.
    config : `RubinDimensionPackerConfig`, optional
        Configuration for this dimension packer.
    is_exposure : `bool`, optional
        If `False`, construct a packer for visit+detector data IDs.  If `True`,
        construct a packer for exposure+detector data IDs.  If `None`, this is
        determined based on whether ``visit`` or ``exposure`` is present in
        ``data_id``, with ``visit`` checked first and hence used if both are
        present.

    Notes
    -----
    The packing used by this class is considered stable and part of its public
    interface so it can be reimplemented in contexts where delegation to this
    code is impractical (e.g. SQL user-defined functions)::

        packed = \
            detector + config.n_detectors * (
                seq_num + config.n_seq_nums * (
                    convert_day_obs_to_ordinal(day_obs)
                    - convert_day_obs_to_ordinal(config.day_obs_begin)
                    + config.n_days * (
                        config.controllers[controllers]
                        config.n_controllers * is_one_to_one_reinterpretation
                    )
                )
            )

    See `RubinDimensionPackerConfig` and `pack_decomposition` for definitions
    of the above variables.
    """

    ConfigClass = RubinDimensionPackerConfig

    def __init__(
        self,
        data_id: DataCoordinate,
        *,
        config: RubinDimensionPackerConfig | None = None,
        is_exposure: bool | None = None,
    ):
        if config is None:
            config = RubinDimensionPackerConfig()
        fixed = data_id.subset(data_id.universe.conform(["instrument"]))
        if is_exposure is None and data_id is not None:
            if "visit" in data_id.graph.names:
                is_exposure = False
            elif "exposure" in data_id.graph.names:
                is_exposure = True
            else:
                raise ValueError(
                    "'is_exposure' was not provided and 'data_id' has no visit or exposure value."
                )
        if is_exposure:
            dimensions = fixed.universe.conform(["instrument", "exposure", "detector"])
        else:
            dimensions = fixed.universe.conform(["instrument", "visit", "detector"])
        super().__init__(fixed, dimensions)
        self.config = config
        self.is_exposure = is_exposure
        self._max_bits = (
            math.prod(
                [
                    self.config.n_visit_definitions,
                    self.config.n_controllers,
                    self.config.n_days,
                    self.config.n_seq_nums,
                    self.config.n_detectors,
                ]
            )
            - 1
        ).bit_length()

    @property
    def maxBits(self) -> int:
        # Docstring inherited from DimensionPacker.maxBits
        return self._max_bits

    def _pack(self, dataId: DataCoordinate) -> int:
        # Docstring inherited from DimensionPacker._pack
        is_one_to_one_reinterpretation = False
        if not self.is_exposure:
            # Using a leading "9" as the indicator of a
            # one_to_one_reinterpretation visit is _slightly_ distasteful, as
            # it'd be better to delegate that to something in obs_base closer
            # to what puts the "9" there in the first place, but that class
            # doesn't have its own public interface where we could put such
            # things, and we don't have much choice but to assume which of the
            # visit system definitions we're using anyway.  Good news is that
            # this is all very strictly RFC-controlled stable stuff that is
            # not going to change out from under us without warning.
            nine_if_special, exposure_id = divmod(
                dataId["visit"], 10**EXPOSURE_ID_MAXDIGITS
            )
            if nine_if_special == 9:
                is_one_to_one_reinterpretation = True
            elif nine_if_special != 0:
                raise ValueError(f"Could not parse visit in {dataId}.")
        else:
            exposure_id = dataId["exposure"]
        # We unpack the exposure ID (which may really be [the remnant of] a
        # visit ID) instead of extracting these values from dimension records
        # because we really don't want to demand that the given data ID have
        # records attached.
        return self.pack_id_pair(
            exposure_id,
            dataId["detector"],
            is_one_to_one_reinterpretation,
            config=self.config,
        )

    def unpack(self, packedId: int) -> DataCoordinate:
        # Docstring inherited from DimensionPacker.unpack
        (
            exposure_id,
            detector,
            is_one_to_one_reinterpretation,
        ) = self.unpack_id_pair(packedId, config=self.config)
        if self.is_exposure:
            if is_one_to_one_reinterpretation:
                raise ValueError(
                    f"Packed data ID {packedId} may correspond to a valid visit ID, "
                    "but not a valid exposure ID."
                )
            return DataCoordinate.standardize(
                self.fixed, exposure=exposure_id, detector=detector
            )
        else:
            if is_one_to_one_reinterpretation:
                visit_id = int(f"9{exposure_id}")
            else:
                visit_id = exposure_id
            return DataCoordinate.standardize(
                self.fixed, visit=visit_id, detector=detector
            )

    @staticmethod
    def pack_id_pair(
        exposure_id: int,
        detector: int,
        is_one_to_one_reinterpretation: bool = False,
        config: RubinDimensionPackerConfig | None = None,
    ) -> int:
        """Pack data ID values passed as arguments.

        Parameters
        ----------
        exposure_id : `int`
            Integer that uniquely identifies an exposure.
        detector : `int`
            Integer that uniquely identifies a detector.
        is_one_to_one_reinterpretation : `bool`, optional
            If `True`, instead of packing the given ``exposure_id``, pack a
            visit ID that represents the alternate interpretation of that
            exposure (which must be the first snap in a multi-snap sequence) as
            a standalone visit.

        Returns
        -------
        packed_id : `int`
            Integer that reversibly combines all of the given arguments.

        Notes
        -----
        This is a `staticmethod` and hence does not respect the config passed
        in at construction when called on an instance.  This is to support
        usage in contexts where construction (which requires a
        `lsst.daf.butler.DimensionUniverse`) is inconvenient or impossible.
        """
        day_obs, seq_num, controller = LsstBaseTranslator.unpack_exposure_id(
            exposure_id
        )
        return RubinDimensionPacker.pack_decomposition(
            int(day_obs),
            seq_num,
            detector=detector,
            controller=controller,
            is_one_to_one_reinterpretation=is_one_to_one_reinterpretation,
            config=config,
        )

    @staticmethod
    def unpack_id_pair(
        packed_id: int, config: RubinDimensionPackerConfig | None = None
    ) -> tuple[int, int, bool]:
        """Unpack data ID values directly.

        Parameters
        ----------
        packed_id : `int`
            Integer produced by one of the methods of this class using the same
            configuration.

        Returns
        -------
        exposure_id : `int`
            Integer that uniquely identifies an exposure.
        detector : `int`
            Integer that uniquely identifies a detector.
        is_one_to_one_reinterpretation : `bool`, optional
            If `True`, instead of packing the given ``exposure_id``, the packed
            ID corresponds to the visit that represents the alternate
            interpretation of the first snap in a multi-snap sequence as a
            standalone visit.

        Notes
        -----
        This is a `staticmethod` and hence does not respect the config passed
        in at construction when called on an instance.  This is to support
        usage in contexts where construction (which requires a
        `lsst.daf.butler.DimensionUniverse`) is inconvenient or impossible.
        """
        (
            day_obs,
            seq_num,
            detector,
            controller,
            is_one_to_one_reinterpretation,
        ) = RubinDimensionPacker.unpack_decomposition(packed_id, config=config)
        return (
            LsstBaseTranslator.compute_exposure_id(str(day_obs), seq_num, controller),
            detector,
            is_one_to_one_reinterpretation,
        )

    @staticmethod
    def pack_decomposition(
        day_obs: int,
        seq_num: int,
        detector: int,
        controller: str = "O",
        is_one_to_one_reinterpretation: bool = False,
        config: RubinDimensionPackerConfig | None = None,
    ) -> int:
        """Pack Rubin-specific identifiers directly into an integer.

        Parameters
        ----------
        day_obs : `int`
            Day of observation as a YYYYMMDD decimal integer.
        seq_num : `int`
            Sequence number
        detector : `int`
            Detector ID.
        controller : `str`, optional
            Single-character controller code defined in
            `RubinDimensionPackerConfig.controllers`.
        is_one_to_one_reinterpretation : `bool`, optional
            If `True`, this is a visit ID that differs from the exposure ID of
            its first snap because it is the  alternate interpretation of that
            first snap as a standalone visit.
        config : `RubinDimensionPackerConfig`, optional
            Configuration, including upper bounds on all arguments.

        Returns
        -------
        packed_id : `int`
            Integer that reversibly combines all of the given arguments.

        Notes
        -----
        This is a `staticmethod` and hence does not respect the config passed
        in at construction when called on an instance.  This is to support
        usage in contexts where construction (which requires a
        `lsst.daf.butler.DimensionUniverse`) is inconvenient or impossible.
        """
        if config is None:
            config = RubinDimensionPackerConfig()
        day_obs_ordinal_begin = convert_day_obs_to_ordinal(config.day_obs_begin)
        result = int(is_one_to_one_reinterpretation)
        result *= config.n_controllers
        try:
            result += config.controllers[controller]
        except KeyError:
            raise ValueError(f"Unrecognized controller code {controller!r}.") from None
        day_obs_ordinal = convert_day_obs_to_ordinal(day_obs) - day_obs_ordinal_begin
        if day_obs_ordinal < 0:
            raise ValueError(
                f"day_obs {day_obs} is out of bounds; must be >= "
                f"{convert_ordinal_to_day_obs(day_obs_ordinal_begin)}."
            )
        if day_obs_ordinal > config.n_days:
            raise ValueError(
                f"day_obs {day_obs} is out of bounds; must be < "
                f"{convert_ordinal_to_day_obs(day_obs_ordinal_begin + config.n_days)}."
            )
        result *= config.n_days
        result += day_obs_ordinal
        if seq_num < 0:
            raise ValueError(f"seq_num {seq_num} is negative.")
        if seq_num >= config.n_seq_nums:
            raise ValueError(
                f"seq_num is out of bounds; must be < {config.n_seq_nums}."
            )
        result *= config.n_seq_nums
        result += seq_num
        if detector < 0:
            raise ValueError(f"detector {detector} is out of bounds; must be >= 0.")
        if detector >= config.n_detectors:
            raise ValueError(
                f"detector {detector} is out of bounds; must be < {config.n_detectors}."
            )
        result *= config.n_detectors
        result += detector
        return result

    @staticmethod
    def unpack_decomposition(
        packed_id: int, config: RubinDimensionPackerConfig | None = None
    ) -> tuple[int, int, int, str, bool]:
        """Unpack an integer into Rubin-specific identifiers.

        Parameters
        ----------
        packed_id : `int`
            Integer produced by one of the methods of this class using the same
            configuration.
        config : `RubinDimensionPackerConfig`, optional
            Configuration, including upper bounds on all arguments.

        Returns
        -------
        day_obs : `int`
            Day of observation as a YYYYMMDD decimal integer.
        seq_num : `int`
            Sequence number
        detector : `int`
            Detector ID.
        controller : `str`
            Single-character controller code defined in
            `RubinDimensionPackerConfig.controllers`.
        is_one_to_one_reinterpretation : `bool`
            If `True`, this is a visit ID that differs from the exposure ID of
            its first snap because it is the alternate interpretation of that
            first snap as a standalone visit.

        Notes
        -----
        This is a `staticmethod` and hence does not respect the config passed
        in at construction when called on an instance.  This is to support
        usage in contexts where construction (which requires a
        `lsst.daf.butler.DimensionUniverse`) is inconvenient or impossible.
        """
        if config is None:
            config = RubinDimensionPackerConfig()
        rest, detector = divmod(packed_id, config.n_detectors)
        rest, seq_num = divmod(rest, config.n_seq_nums)
        rest, day_obs_ordinal = divmod(rest, config.n_days)
        rest, controller_int = divmod(rest, config.n_controllers)
        rest, is_one_to_one_reintepretation_int = divmod(
            rest, config.n_visit_definitions
        )
        if rest:
            raise ValueError(
                f"Unexpected overall factor {rest} in packed data ID {packed_id}."
            )
        for controller_code, index in config.controllers.items():
            if index == controller_int:
                break
        else:
            raise ValueError(
                f"Unrecognized controller index {controller_int} in packed data ID {packed_id}."
            )
        return (
            convert_ordinal_to_day_obs(day_obs_ordinal + convert_day_obs_to_ordinal(config.day_obs_begin)),
            seq_num,
            detector,
            controller_code,
            bool(is_one_to_one_reintepretation_int),
        )


# The double-registration guard here would be unnecessary if not for
# pytest-flake8 and some horribleness it must be doing to circumvent Python's
# own guards against importing the same module twice in the same process.
if "rubin" not in observation_packer_registry:
    observation_packer_registry.register("rubin", RubinDimensionPacker)
