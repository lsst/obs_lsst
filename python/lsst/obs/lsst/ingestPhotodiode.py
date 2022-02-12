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
import tempfile

from lsst.daf.butler import (
    CollectionType,
    DataCoordinate,
    DatasetIdGenEnum,
    DatasetRef,
    DatasetType,
    FileDataset,
    Progress,
)
from lsst.ip.isr import PhotodiodeCalib
from lsst.obs.base import makeTransferChoiceField
from lsst.obs.base.formatters.fitsGeneric import FitsGenericFormatter
from lsst.pex.config import Config
from lsst.pipe.base import Task
from lsst.resources import ResourcePath


__all__ = ('PhotodiodeIngestConfig', 'PhotodiodeIngestTask')


class PhotodiodeIngestConfig(Config):
    """Configuration class for PhotodiodeIngestTask."""

    transfer = makeTransferChoiceField()


class PhotodiodeIngestTask(Task):
    """Task to ingest photodiode data into a butler repository.

    Parameters
    ----------
    config : `PhotodiodeIngestConfig`
        Configuration for the task.
    instrument : `~lsst.obs.base.Instrument`
        The instrument these photodiode datasets are from.
    butler : `~lsst.daf.butler.Butler`
        Writable butler instance, with ``butler.run`` set to the
        appropriate `~lsst.daf.butler.CollectionType.RUN` collection
        for these datasets.
    **kwargs
        Additional keyword arguments.
    """

    ConfigClass = PhotodiodeIngestConfig
    _DefaultName = "photodiodeIngest"

    def getDatasetType(self):
        """Return the DatasetType of the photodiode datasets."""
        return DatasetType(
            "photodiode",
            ("instrument", "exposure"),
            "IsrCalib",
            universe=self.butler.registry.dimensions,
        )

    def __init__(self, butler, instrument, config=None, **kwargs):
        super().__init__(config, **kwargs)
        self.butler = butler
        self.universe = self.butler.registry.dimensions
        self.datasetType = self.getDatasetType()
        self.progress = Progress("obs.lsst.PhotodiodeIngestTask")
        self.instrument = instrument
        self.camera = self.instrument.getCamera()

    def run(self, locations, run=None, file_filter=r".*Photodiode_Readings.*txt",
            track_file_attrs=None):
        """Ingest photodiode data into a Butler data repository.

        Parameters
        ----------
        files : iterable over `lsst.resources.ResourcePath`
            URIs to the files to be ingested.
        pool : `multiprocessing.Pool` optional
            If not `None`, a process pool with which to
            parallelize some operations.
        processes : `int`, optional
            The number of processes to use.  Ignored if ``pool`` is `None`.
        run : `str`, optional
            Name of the RUN-type collection to write to,
            overriding the default derived from the instrument
            name
        skip_existing_exposures : `bool`, optional
            If `True`, skip photodiodes that have already been
            ingested (i.e. raws for which we already have a
            dataset with the same data ID in the target
            collection).
        track_file_attrs : `bool`, optional
            Control whether file attributes such as the size or
            checksum should be tracked by the datastore.  Whether
            this parameter is honored depends on the specific
            datastore implementation.

        Returns
        -------
        refs : `list` [`lsst.daf.butler.DatasetRef`]
            Dataset references for ingested raws.

        Raises
        ------
        RuntimeError :
            Raised if multiple exposures are found for a photodiode file.
        """
        files = ResourcePath.findFileResources(locations, file_filter)

        registry = self.butler.registry
        registry.registerDatasetType(self.datasetType)

        # Find and register run that we will ingest to.
        if run is None:
            run = self.instrument.makeCollectionName("calib", "photodiode")
        registry.registerCollection(run, type=CollectionType.RUN)

        # Use datasetIds that match the raw exposure data.
        if self.butler.registry.supportsIdGenerationMode(DatasetIdGenEnum.DATAID_TYPE_RUN):
            mode = DatasetIdGenEnum.DATAID_TYPE_RUN
        else:
            mode = DatasetIdGenEnum.UNIQUE

        refs = []
        for inputFile in files:
            # Convert the file into the right class.
            if inputFile.isLocal:
                calib = PhotodiodeCalib.readTwoColumnPhotodiodeData(inputFile.path)
            else:
                print("Non-local file.")
            dayObs = calib.getMetadata()['day_obs']
            seqNum = calib.getMetadata()['seq_num']

            # Find the associated exposure information.
            whereClause = "exposure.day_obs=dayObs and exposure.seq_num=seqNum"
            instrumentName = self.instrument.getName()
            exposureRecords = [rec for rec in registry.queryDimensionRecords("exposure",
                                                                             instrument=instrumentName,
                                                                             where=whereClause,
                                                                             bind={"dayObs": dayObs,
                                                                                   "seqNum": seqNum})]

            nRecords = len(exposureRecords)
            if nRecords == 1:
                exposureId = exposureRecords[0].id
                calib.updateMetadata(camera=self.camera, exposure=exposureId)
            elif nRecords == 0:
                self.log.warn("Skipping instrument %s and dayObs/seqNum %d %d: no exposures found.",
                              instrumentName, dayObs, seqNum)
                continue
            else:
                raise RuntimeError("Multiple exposure entries found for instrument %s and "
                                   "dayObs/seqNum %d %d.", instrumentName, dayObs, seqNum)

            # Generate the dataId for this file.
            dataId = DataCoordinate.standardize(
                instrument=self.instrument.getName(),
                exposure=exposureId,
                universe=self.universe,
            )

            # If this already exists, we should skip it and continue.
            existing = {
                ref.dataId
                for ref in self.butler.registry.queryDatasets(self.datasetType, collections=[run],
                                                              dataId=dataId)
            }
            if existing:
                self.log.warn("Skipping instrument %s and dayObs/seqNum %d %d: already exists in run %s.",
                              instrumentName, dayObs, seqNum, run)
                continue

            # Ingest must work from a file, but we can't use the
            # original, as we've added new metadata and reformatted
            # it.  Write it to a temp file that we can use to ingest.
            tempFile = tempfile.mktemp() + ".fits"
            calib.writeFits(tempFile)

            ref = DatasetRef(self.datasetType, dataId)
            dataset = FileDataset(path=tempFile, refs=ref, formatter=FitsGenericFormatter)

            # No try, as if this fails, we should stop.
            self.butler.ingest(dataset, transfer=self.config.transfer, run=run,
                               idGenerationMode=mode,
                               record_validation_info=track_file_attrs)
            self.log.info("Photodiode %s:%d (%d/%d) ingested successfully", instrumentName, exposureId,
                          dayObs, seqNum)
            os.unlink(tempFile)
            refs.append(dataset)

        return refs
