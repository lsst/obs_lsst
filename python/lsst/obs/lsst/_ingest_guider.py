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

from __future__ import annotations

__all__ = ["ingest_guider"]

import contextlib
import json
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

import astropy.io.fits
import lsst.afw.fits
import lsst.obs.lsst.translators  # Force translators to import  # noqa: F401
from astro_metadata_translator import ObservationInfo
from lsst.daf.butler import (Butler, DataCoordinate, DatasetIdGenEnum,
                             DatasetRef, DatasetType, FileDataset)
from lsst.obs.base.formatters.fitsGeneric import FitsGenericFormatter
from lsst.resources import ResourcePath, ResourcePathExpression

_LOG = logging.getLogger(__name__)
_DATASET_TYPE_NAME = "raw_guider"


def _do_nothing(*args: Any, **kwargs: Any) -> None:
    """Do nothing.

    This is a function that accepts anything and does nothing.
    For use as a default in callback arguments.
    """
    pass


def ingest_guider(
    butler: Butler,
    run: str,
    files: list[ResourcePathExpression],
    transfer: str = "auto",
    register_dataset_type: bool = False,
    track_file_attrs: bool = True,
    on_metadata_failure: Callable[[ResourcePath, Exception], Any] = _do_nothing,
    on_undefined_exposure: Callable[[ResourcePath, str], Any] = _do_nothing,
    on_ingest_failure: Callable[[list[FileDataset], Exception], Any] = _do_nothing,
    fail_fast: bool = False,
) -> list[DatasetRef]:
    """Ingest the given files into the butler repository.

    Parameters
    ----------
    butler : `lsst.daf.butler.Butler`
        Butler in which to ingest the guider files.
    run : `str`
        The name of the run that will be receiving these datasets.
    files : `list` [ `lsst.resources.ResourcePathExpression` ]
        Guider files to ingest.
    transfer : `str`, optional
        Transfer mode to use for ingest. Default is "auto". If "direct"
        mode is used ingestion of a file that is already present in the
        butler repo will not be an error.
    register_dataset_type : `bool`, optional
        If `True` the dataset type will be created if it is not defined.
        Default is `False`.
    track_file_attrs : `bool`, optional
        Control whether file attributes such as the size or checksum should
        be tracked by the datastore. Whether this parameter is honored
        depends on the specific datastore implementation.
    on_metadata_failure : `Callable`, optional
        A callback invoked when a failure occurs trying to translate the
        metadata for a file.  Will be passed the URI and the exception, in
        that order, as positional arguments.  Guaranteed to be called in an
        ``except`` block, allowing the callback to re-raise or replace (with
        ``raise ... from``) default exception handling.
    on_undefined_exposure : `Callable`, optional
        A callback invoked when a guider file can't be ingested because the
        corresponding exposure dimension record does not yet exist. Will be
        passed the URI and the OBSID.
    on_ingest_failure : `Callable`, optional
        A callback invoked when dimension record or dataset insertion into the
        database fails for an exposure.  Will be passed a list of
        `~lsst.daf.butler.FileDataset` objects corresponding to the files
        being ingested, and the exception as positional arguments.
        Guaranteed to be called in an ``except`` block, allowing the callback
        to re-raise or replace (with ``raise ... from``) to override the
        usual error handling (before ``fail_fast`` logic occurs).
    fail_fast : `bool`, optional
        If `True` ingest will abort if there is any issue with any files. If
        `False`, an attempt will be made

    Returns
    -------
    refs : `list` [ `DatasetRef` ]
        Butler datasets that were ingested.

    Notes
    -----
    Always uses a dataset type named "raw_guider" with dimensions instrument,
    detector, exposure. The exposure must already be defined. The dataset
    type
    """
    # Force butler to ensure that the required run exists.
    butler = butler.clone(run=run)

    dataset_type = DatasetType(
        _DATASET_TYPE_NAME,
        {"instrument", "detector", "exposure"},
        "Stamps",
        universe=butler.dimensions,
    )
    if register_dataset_type:
        butler.registry.registerDatasetType(dataset_type)

    # Map filenames to initial data ID (using obs ID rather than exposure ID).
    raw_data_id: dict[str, ObservationInfo] = {}

    # Map instrument name to observation IDs.
    obs_ids: dict[str, set[str]] = defaultdict(set)

    # Retain information about failed metadata extraction.
    # Mapping of file name to error message.
    failed_metadata: dict[str, str] = {}

    # Since there may be multiple guider files for a single exposure,
    # accumulate the exposure information before converting obs_id to exposure
    # id.
    file_resources: list[ResourcePath] = []
    for file in files:
        filepath = ResourcePath(file, forceAbsolute=True)
        file_resources.append(filepath)
        metadata_path = filepath.updatedExtension(".json")

        metadata = None
        if metadata_path.exists():
            with contextlib.suppress(Exception):
                metadata = json.loads(metadata_path.read().decode())
        if metadata is None:
            # Could not find sidecar file or it was corrupt. Read from the
            # FITS file itself.
            # Allow direct remote read from S3.
            try:
                fs, fspath = filepath.to_fsspec()
                with fs.open(fspath) as f, astropy.io.fits.open(f) as fits_obj:
                    metadata = fits_obj[0].header
            except Exception as e:
                failed_metadata[file] = str(e)
                on_metadata_failure(file, e)
                if fail_fast:
                    raise RuntimeError(
                        f"Problem extracting metadata for file {file}"
                    ) from e
                continue

        # Do not run fix_header since we only need the OBSID and the detector
        # number.
        required = {"instrument", "detector_num", "observation_id"}
        try:
            info = ObservationInfo(
                metadata, filename=file, subset=required, pedantic=True
            )
        except KeyError as e:
            failed_metadata[file] = str(e)
            on_metadata_failure(file, e)
            if fail_fast:
                raise RuntimeError(f"Problem parsing metadata for file {file}") from e
            continue

        raw_data_id[filepath] = info
        obs_ids[info.instrument].add(info.observation_id)

    if len(obs_ids) > 1:
        # This constraint is not required but it does simplify the run
        # parameter unless we allow the run parameter to be defined as
        # "{instrument}/raw/guider" or something. You likely don't want
        # data for multiple instruments to go in a single RUN collection.
        raise RuntimeError(
            f"Can only ingest data from a single instrument at a time but got {obs_ids.keys()}"
        )

    if failed_metadata:
        msg = "\n".join(f" - {f}" for f in failed_metadata)
        _LOG.warning("Failed to extract useful metadata for:\n%s", msg)

    # Map obs_id to a tuple of instrument and exposure ID in case we are
    # ingesting guiders from multiple instruments.
    obs_id_to_exposure_ids: dict[str, tuple[str, int]] = {}

    requested_obs_ids: set[str] = set()
    found_obs_ids: set[str] = set()

    with butler.query() as query:
        for instrument, observation_ids in obs_ids.items():
            requested_obs_ids.update(observation_ids)
            query = query.where(
                "exposure.obs_id in (OBSID)",
                bind={"OBSID": observation_ids},
                instrument=instrument,
            )

            exposures = {
                e.obs_id: (e.instrument, e.id)
                for e in query.dimension_records("exposure")
            }
            obs_id_to_exposure_ids.update(exposures)
            found_obs_ids.update(exposures.keys())

    if missing_obs_ids := requested_obs_ids - found_obs_ids:
        missing_str = "\n".join(f" - {obs}" for obs in missing_obs_ids)
        _LOG.warning(
            "Failed to find exposure records for the following observation IDs:\n%s",
            missing_str,
        )

    # Now there is enough information to create the ingest datasets.
    failed_exposure_metadata: list[str] = []
    datasets: list[FileDataset] = []
    for file, info in raw_data_id.items():
        if info.observation_id not in obs_id_to_exposure_ids:
            failed_exposure_metadata.append(file)
            on_undefined_exposure(file, info.observation_id)
            if fail_fast:
                raise RuntimeError(
                    f"Exposure metadata not yet defined for OBSID {info.observation_id} "
                    f"but required for file {file}."
                )
            continue

        data_id = DataCoordinate.standardize(
            instrument=info.instrument,
            detector=info.detector_num,
            exposure=obs_id_to_exposure_ids[info.observation_id][1],
            universe=butler.dimensions,
        )
        # These are "raw" type so we want to use a predictable UUID.
        ref = DatasetRef(
            dataset_type,
            data_id,
            run,
            id_generation_mode=DatasetIdGenEnum.DATAID_TYPE_RUN,
        )
        datasets.append(
            FileDataset(path=file, refs=[ref], formatter=FitsGenericFormatter)
        )

    if failed_exposure_metadata:
        failed_exposure_msg = "\n".join(f" - {f}" for f in failed_exposure_metadata)
        _LOG.warning(
            "Failed to match the following files to exposure IDs:\n%s",
            failed_exposure_msg,
        )

    # Now ingest the files.
    if datasets:
        try:
            butler.ingest(
                *datasets, transfer=transfer, record_validation_info=track_file_attrs
            )
        except Exception as e:
            on_ingest_failure(datasets, e)
            raise

    if len(datasets) != len(file_resources):
        ingested_files = {d.file for d in datasets}
        given_files = set(file_resources)
        missing_files = given_files - ingested_files
        msg = "\n".join(f" - {f}" for f in missing_files)
        raise RuntimeError(f"Failed to ingest the following files:\n{msg}")

    return [d.refs[0] for d in datasets]
