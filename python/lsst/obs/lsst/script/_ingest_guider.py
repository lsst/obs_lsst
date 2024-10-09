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

__all__ = ["ingest_guider_simple"]

import logging

from lsst.daf.butler import Butler

from .._ingest_guider import ingest_guider

_LOG = logging.getLogger(__name__)


def ingest_guider_simple(
    repo: str,
    locations: list[str],
    regex: str,
    output_run: str,
    transfer: str = "direct",
    track_file_attrs: bool = True,
    fail_fast: bool = False,
    register_dataset_types: bool = False,
) -> None:
    """Ingests guider data into the butler registry.

    Parameters
    ----------
    repo : `str`
        URI to the repository.
    locations : `list` [`str`]
        Files to ingest and directories to search for files that match
        ``regex`` to ingest.
    regex : `str`
        Regex string used to find files in directories listed in locations.
    output_run : `str`
        The RUN collection where datasets should be ingested.
    transfer : `str` or None
        The external data transfer type, by default "direct". In "direct"
        mode an attempt to re-ingest the same file will not fail.
    track_file_attrs : `bool`, optional
        Control whether file attributes such as the size or checksum should
        be tracked by the datastore. Whether this parameter is honored
        depends on the specific datastore implementation.
    fail_fast : `bool`, optional.
        If `True`, ingest is stopped as soon as any error is encountered.
    register_dataset_types : `bool`, optional
        Whether to try to register the guider dataset type.
    """
    butler = Butler(repo, writeable=True)

    refs = ingest_guider(
        butler,
        locations,
        file_filter=regex,
        transfer=transfer,
        run=output_run,
        track_file_attrs=track_file_attrs,
        register_dataset_type=register_dataset_types,
        fail_fast=fail_fast,
    )

    _LOG.info("Ingested %d guider file%s", len(refs), "" if len(refs) == 1 else "s")
