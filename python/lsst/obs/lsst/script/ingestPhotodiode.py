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
from lsst.daf.butler import Butler
from lsst.pipe.base.configOverrides import ConfigOverrides
from lsst.pipe.base import Instrument
from .. import PhotodiodeIngestTask, PhotodiodeIngestConfig
from .. import (ShutterMotionOpenIngestConfig, ShutterMotionCloseIngestConfig,
                ShutterMotionOpenIngestTask, ShutterMotionCloseIngestTask)


def ingestPhotodiode(repo, instrument, locations, regex, output_run, config=None, config_file=None,
                     transfer="copy", track_file_attrs=True):
    """Ingests photodiode data into the butler registry.

    Parameters
    ----------
    repo : `str`
        URI to the repository.
    instrument : `str`
        The name or fully-qualified class name of an instrument.
    locations : `list` [`str`]
        Files to ingest and directories to search for files that match
        ``regex`` to ingest.
    regex : `str`
        Regex string used to find files in directories listed in locations.
    output_run : `str`
        The path to the location, the run, where datasets should be put.
    config : `dict` [`str`, `str`] or `None`
        Key-value pairs to apply as overrides to the ingest config.
    config_file : `str` or `None`
        Path to a config file that contains overrides to the ingest config.
    transfer : `str` or None
        The external data transfer type, by default "copy".
    track_file_attrs : `bool`, optional
        Control whether file attributes such as the size or checksum should
        be tracked by the datastore. Whether this parameter is honored
        depends on the specific datastore implentation.

    Raises
    ------
    Exception
        Raised if operations on configuration object fail.
    """
    butler = Butler(repo, writeable=True)
    instr = Instrument.from_string(instrument, butler.registry)

    # We'll reuse `config`, so get the overrides stored first.
    configOverrides = ConfigOverrides()
    if config_file is not None:
        configOverrides.addFileOverride(config_file)
    if config is not None:
        for name, value in config.items():
            configOverrides.addValueOverride(name, value)

    config = PhotodiodeIngestConfig()
    config.transfer = transfer
    configOverrides.applyTo(config)

    task = PhotodiodeIngestTask(butler=butler, instrument=instr, config=config)
    task.run(locations, run=output_run, file_filter=regex,
             track_file_attrs=track_file_attrs)


def ingestShutterMotion(repo, instrument, locations, regex, output_run, config=None, config_file=None,
                        transfer="copy", track_file_attrs=True):
    """Ingests photodiode data into the butler registry.

    Parameters
    ----------
    repo : `str`
        URI to the repository.
    instrument : `str`
        The name or fully-qualified class name of an instrument.
    locations : `list` [`str`]
        Files to ingest and directories to search for files that match
        ``regex`` to ingest.
    regex : `str`
        Regex string used to find files in directories listed in locations.
    output_run : `str`
        The path to the location, the run, where datasets should be put.
    config : `dict` [`str`, `str`] or `None`
        Key-value pairs to apply as overrides to the ingest config.
    config_file : `str` or `None`
        Path to a config file that contains overrides to the ingest config.
    transfer : `str` or None
        The external data transfer type, by default "copy".
    track_file_attrs : `bool`, optional
        Control whether file attributes such as the size or checksum should
        be tracked by the datastore. Whether this parameter is honored
        depends on the specific datastore implentation.

    Raises
    ------
    Exception
        Raised if operations on configuration object fail.
    """
    butler = Butler(repo, writeable=True)
    instr = Instrument.from_string(instrument, butler.registry)

    # Store the overrides first:
    configOverrides = ConfigOverrides()
    if config_file is not None:
        configOverrides.addFileOverride(config_file)
    if config is not None:
        for name, value in config.items():
            configOverrides.addValueOverride(name, value)

    configOpen = ShutterMotionIngestOpenConfig()
    configOpen.transfer = transfer
    configOverrides.applyTo(configOpen)

    task = ShutterMotionOpenIngestTask(butler=butler, instrument=instr, config=configOpen)
    task.run(locations, run=output_run, file_filter=regex,
             track_file_attrs=track_file_attrs)

    configClose = ShutterMotionIngestCloseConfig()
    configClose.transfer = transfer
    configOverrides.applyTo(configClose)
    task = ShutterMotionCloseIngestTask(butler=butler, instrument=instr, config=configClose)
    task.run(locations, run=output_run, file_filter=regex,
             track_file_attrs=track_file_attrs)
