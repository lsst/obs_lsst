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
__all__ = ('PhotodiodeIngestConfig', 'PhotodiodeIngestTask')


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


class PhotodiodeIngestConfig(Config):
    """Configuration class for PhotodiodeIngestTask."""

    transfer = makeTransferChoiceField(default="copy")

    def validate(self):
        super().validate()
        if self.transfer != "copy":
            raise ValueError(f"Transfer Must be 'copy' for photodiode data. {self.transfer}")


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
            universe=self.universe,
        )

    def __init__(self, butler, instrument, config=None, **kwargs):
        config.validate()
        super().__init__(config, **kwargs)
        self.butler = butler
        self.universe = self.butler.dimensions
        self.datasetType = self.getDatasetType()
        self.progress = Progress(self.log.name)
        self.instrument = instrument
        self.camera = self.instrument.getCamera()

    def run(self, locations, run=None, file_filter=r"Photodiode_Readings.*txt$|_photodiode.ecsv$",
            track_file_attrs=None):
        """Ingest photodiode data into a Butler data repository.

        Parameters
        ----------
        files : iterable over `lsst.resources.ResourcePath`
            URIs to the files to be ingested.
        run : `str`, optional
            Name of the RUN-type collection to write to,
            overriding the default derived from the instrument
            name.
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
        RuntimeError
            Raised if the number of exposures found for a photodiode
            file is not one
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
        numExisting = 0
        numFailed = 0
        for inputFile in files:
            # Convert the file into the right class.
            calibType = "Unknown"
            try:
                # Can this be read directly in standard form?
                with inputFile.as_local() as localFile:
                    calib = PhotodiodeCalib.readText(localFile.ospath)
                calibType = "full"
            except Exception:
                # Try reading as a two-column file.
                with inputFile.as_local() as localFile:
                    calib = PhotodiodeCalib.readTwoColumnPhotodiodeData(localFile.ospath)
                calibType = "two-column"

            # Get exposure records
            if calibType == "full":
                instrumentName = calib.getMetadata().get('INSTRUME')
                if instrumentName is None:
                    # The field is populated by the calib class, so we
                    # can't use defaults.
                    instrumentName = self.instrument.getName()

                obsId = calib.getMetadata()['obsId']
                whereClause = "exposure.obs_id=obsId"
                binding = {"obsId": obsId}
                logId = obsId

            elif calibType == "two-column":
                dayObs = calib.getMetadata()['day_obs']
                seqNum = calib.getMetadata()['seq_num']

                # Find the associated exposure information.
                whereClause = "exposure.day_obs=dayObs and exposure.seq_num=seqNum"
                instrumentName = self.instrument.getName()
                binding = {"dayObs": dayObs, "seqNum": seqNum}
                logId = (dayObs, seqNum)

            else:
                self.log.warning("Skipping input file %s of unknown type.",
                                 inputFile)
                continue
            exposureRecords = [rec for rec in registry.queryDimensionRecords("exposure",
                                                                             instrument=instrumentName,
                                                                             where=whereClause,
                                                                             bind=binding)]

            nRecords = len(exposureRecords)
            if nRecords == 1:
                exposureId = exposureRecords[0].id
                calib.updateMetadata(camera=self.camera, exposure=exposureId)
            elif nRecords == 0:
                numFailed += 1
                self.log.warning("Skipping instrument %s and identifiers %s: no exposures found.",
                                 instrumentName, logId)
                continue
            else:
                numFailed += 1
                self.log.warning("Multiple exposure entries found for instrument %s and "
                                 "identifiers %s.", instrumentName, logId)
                continue

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
                self.log.debug("Skipping instrument %s and identifiers %s: already exists in run %s.",
                               instrumentName, logId, run)
                numExisting += 1
                continue

            # Ingest must work from a file, but we can't use the
            # original, as we've added new metadata and reformatted
            # it.  Write it to a temp file that we can use to ingest.
            # If we can have the files written appropriately, this
            # will be a direct ingest of those files.
            with ResourcePath.temporary_uri(suffix=".fits") as tempFile:
                calib.writeFits(tempFile.ospath)

                ref = DatasetRef(self.datasetType, dataId, run=run, id_generation_mode=mode)
                dataset = FileDataset(path=tempFile, refs=ref, formatter=FitsGenericFormatter)

                # No try, as if this fails, we should stop.
                self.butler.ingest(dataset, transfer=self.config.transfer,
                                   record_validation_info=track_file_attrs)
                self.log.info("Photodiode %s:%d (%s) ingested successfully", instrumentName, exposureId,
                              logId)
                refs.append(dataset)

        if numExisting != 0:
            self.log.warning("Skipped %d entries that already existed in run %s", numExisting, run)
        if numFailed != 0:
            raise RuntimeError(f"Failed to ingest {numFailed} entries due to missing exposure information.")
        return refs
