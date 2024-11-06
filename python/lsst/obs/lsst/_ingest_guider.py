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
                             DatasetRef, DatasetType, FileDataset,
                             MissingDatasetTypeError)
from lsst.obs.base.formatters.fitsGeneric import FitsGenericFormatter
from lsst.resources import ResourcePath, ResourcePathExpression

_LOG = logging.getLogger(__name__)
_DATASET_TYPE_NAME = "guider_raw"
DEFAULT_GUIDER_REGEX = r".*SG.*_guider\.fits$"
_DEFAULT_RUN_FORMAT = "{}/raw/guider"


def _do_nothing(*args: Any, **kwargs: Any) -> None:
    """Do nothing.

    This is a function that accepts anything and does nothing.
    For use as a default in callback arguments.
    """
    pass


def ingest_guider(
    butler: Butler,
    locations: list[ResourcePathExpression],
    *,
    file_filter: str = DEFAULT_GUIDER_REGEX,
    group_files: bool = True,
    run: str | None = None,
    transfer: str = "auto",
    register_dataset_type: bool = False,
    track_file_attrs: bool = True,
    on_success: Callable[[list[FileDataset]], Any] = _do_nothing,
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
    locations : `list` [ `lsst.resources.ResourcePathExpression` ]
        Guider files to ingest or directories of guider files.
    file_filter : `str`, optional
        The file filter to use if directories are to be searched.
    group_files: `bool`, optional
        If `True` files are ingested in groups based on the directories
        they are found in. If `False` directories are searched and all files
        are ingested together. If explicit files are given they are treated
        as their own group.
    run : `str` or `None`, optional
        The name of the run that will be receiving these datasets. By default.
        if `None`, a value of `<INSTRUMENT>/raw/guider` is used.
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
    on_success : `Callable`, optional
        A callback invoked when all of the raws associated with a group
        are ingested.  Will be passed a list of `FileDataset` objects, each
        containing one or more resolved `DatasetRef` objects.  If this callback
        raises it will interrupt the entire ingest process, even if
        ``fail_fast`` is `False`.
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
    Always uses a dataset type named "guider_raw" with dimensions instrument,
    detector, exposure. The exposure must already be defined.
    """
    dataset_type = DatasetType(
        _DATASET_TYPE_NAME,
        {"instrument", "detector", "exposure"},
        "Stamps",
        universe=butler.dimensions,
    )

    if register_dataset_type:
        butler.registry.registerDatasetType(dataset_type)
    else:
        try:
            registry_dataset_type = butler.get_dataset_type(_DATASET_TYPE_NAME)
        except MissingDatasetTypeError as e:
            e.add_note(
                f"Can not ingest guider data without registering the {_DATASET_TYPE_NAME} dataset type. "
                "Consider re-running with 'register_dataset_type' option."
            )
            raise
        if not registry_dataset_type.is_compatible_with(dataset_type):
            raise RuntimeError(
                f"Registry dataset type {registry_dataset_type} is incompatible with "
                f"definition required for guider ingest ({dataset_type})"
            )

    ingested_refs = []
    missing_files = set()
    if group_files:
        for group in ResourcePath.findFileResources(
            locations, file_filter, grouped=True
        ):
            files = list(group)
            _LOG.info(
                "Found group containing %d file%s in directory %s",
                len(files),
                "" if len(files) == 1 else "s",
                files[0].dirname(),
            )
            ingested, missing = _ingest_group(
                butler,
                dataset_type,
                files,
                run=run,
                transfer=transfer,
                track_file_attrs=track_file_attrs,
                on_ingest_failure=on_ingest_failure,
                on_metadata_failure=on_metadata_failure,
                on_undefined_exposure=on_undefined_exposure,
                on_success=on_success,
                fail_fast=fail_fast,
            )
            ingested_refs.extend(ingested)
            missing_files.update(missing)
    else:
        files = list(
            ResourcePath.findFileResources(locations, file_filter, grouped=False)
        )
        _LOG.info("Ingesting %d file%s", len(files), "" if len(files) == 1 else "s")
        ingested_refs, missing_files = _ingest_group(
            butler,
            dataset_type,
            files,
            run=run,
            transfer=transfer,
            track_file_attrs=track_file_attrs,
            on_ingest_failure=on_ingest_failure,
            on_metadata_failure=on_metadata_failure,
            on_undefined_exposure=on_undefined_exposure,
            on_success=on_success,
            fail_fast=fail_fast,
        )

    if n_missed := len(missing_files):
        msg = "\n".join(f" - {f}" for f in missing_files)
        _LOG.warning("Failed to ingest the following:\n%s", msg)
        raise RuntimeError(
            f"Failed to ingest {n_missed} file{'' if n_missed == 1 else 's'}."
        )

    return ingested_refs


def _ingest_group(
    butler: Butler,
    dataset_type: DatasetType,
    files: list[ResourcePath],
    *,
    run: str | None = None,
    transfer: str = "auto",
    track_file_attrs: bool = True,
    on_success: Callable[[list[FileDataset]], Any] = _do_nothing,
    on_metadata_failure: Callable[[ResourcePath, Exception], Any] = _do_nothing,
    on_undefined_exposure: Callable[[ResourcePath, str], Any] = _do_nothing,
    on_ingest_failure: Callable[[list[FileDataset], Exception], Any] = _do_nothing,
    fail_fast: bool = False,
) -> tuple[list[DatasetRef], set[str]]:
    # Map filenames to initial data ID (using obs ID rather than exposure ID).
    raw_data_id: dict[str, ObservationInfo] = {}

    # Map instrument name to observation IDs.
    obs_ids: dict[str, set[str]] = defaultdict(set)

    # Retain information about failed metadata extraction.
    # Mapping of file name to error message.
    failed_metadata: dict[str, str] = {}

    # The GUIDE detectors for each instrument.
    guide_detectors: dict[str, set[int]] = {}

    # Since there may be multiple guider files for a single exposure,
    # accumulate the exposure information before converting obs_id to exposure
    # id.
    for file in files:
        metadata_path = file.updatedExtension(".json")
        if metadata_path == file:
            # Attempting to ingest the sidecar file.
            try:
                raise RuntimeError(
                    f"Can not ingest sidecar file as GUIDER file (attempting {metadata_path})"
                )
            except RuntimeError as e:
                failed_metadata[file] = str(e)
                on_metadata_failure(file, e)
                if fail_fast:
                    raise
            continue

        metadata = None
        if metadata_path.exists():
            with contextlib.suppress(Exception):
                metadata = json.loads(metadata_path.read().decode())
        if metadata is None:
            # Could not find sidecar file or it was corrupt. Read from the
            # FITS file itself.
            # Allow direct remote read from S3.
            try:
                fs, fspath = file.to_fsspec()
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

        # Populate detector lookup table.
        if info.instrument not in guide_detectors:
            guide_detectors[info.instrument] = set(
                rec.id
                for rec in butler.query_dimension_records(
                    "detector", instrument=info.instrument
                )
                if rec.purpose == "GUIDER"
            )

        if info.detector_num not in guide_detectors[info.instrument]:
            # The callbacks are documented to be called within an exception.
            try:
                raise ValueError(f"File {file} is not a GUIDER observation.")
            except ValueError as e:
                failed_metadata[file] = str(e)
                on_metadata_failure(file, e)
                if fail_fast:
                    raise
                continue

        raw_data_id[file] = info
        obs_ids[info.instrument].add(info.observation_id)

    if run is not None and len(obs_ids) > 1:
        # We do not want to ingest files from different instruments into
        # the same run so only allow this if we are defining the RUN
        # internally.
        raise RuntimeError(
            f"Can only ingest data from a single instrument into a single RUN but got {obs_ids.keys()}"
        )

    if failed_metadata:
        msg = "\n".join(f" - {f}" for f in failed_metadata)
        _LOG.warning("Failed to extract usable GUIDER metadata for:\n%s", msg)

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
    output_runs: set[str] = set()
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

        if run is None:
            output_run = _DEFAULT_RUN_FORMAT.format(info.instrument)
        else:
            output_run = run

        if output_run not in output_runs:
            # Always try to create on first pass.
            butler.collections.register(output_run)
            output_runs.add(output_run)

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
            output_run,
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
            datasets = []  # Effectively nothing was ingested.
            if fail_fast:
                raise
        else:
            on_success(datasets)

    missing_files = set()
    if len(datasets) != len(files):
        ingested_files = {d.path for d in datasets}
        given_files = set(files)
        missing_files = given_files - ingested_files

    return [d.refs[0] for d in datasets], missing_files
