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
from lsst.pex.config import Config, Field
from lsst.pipe.base import Task
from lsst.resources import ResourcePath


DEFAULT_PHOTODIODE_REGEX = r"Photodiode_Readings.*txt$|_photodiode.ecsv$|Electrometer.*fits$|EM.*fits$"


class IsrCalibIngestConfig(Config):
    """Configuration class for base IsrCalib ingestion task."""
    transfer = makeTransferChoiceField(default="copy")

    forceCopyOnly = Field(
        dtype=bool,
        doc="Should this ingest force transfer to be copy, to ensure the calib is rewritten?",
        default=True,
    )

    def validate(self):
        super().validate()
        if self.forceCopyOnly and self.transfer != "copy":
            raise ValueError(f"Transfer must be 'copy' for this data: {self.transfer}")


class IsrCalibIngestTask(Task):
    """Base task to ingest data convertable to an IsrCalib into a butler
    repository

    Parameters
    ----------
    config : `IsrCalibIngestConfig`
        Configuration for the task.
    instrument : `~lsst.obs.base.Instrument`
        The instrument these datasets are from.
    butler : `~lsst.daf.butler.Butler`
        Writable butler instance, with ``butler.run`` set to the
        appropriate `~lsst.daf.butler.CollectionType.RUN` collection
        for these datasets.
    **kwargs
        Additional keyword arguments.
    """

    ConfigClass = IsrCalibIngestConfig
    _DefaultName = "genericIsrIngest"

    def __init__(self, butler, instrument, config=None, **kwargs):
        config.validate()
        super().__init__(config, **kwargs)
        self.butler = butler
        self.universe = self.butler.dimensions
        self.datasetType = self.getDatasetType()
        self.progress = Progress(self.log.name)
        self.instrument = instrument
        self.camera = self.instrument.getCamera()


    def getDatasetType(self):
        """Return the DatasetType to be ingested.

        Returns
        -------
        datasetType : `lsst.daf.butler.DatasetType`
            The datasetType for the ingested data.
        """
        raise NotImplementedError(
            "Subclasses must define their datasetType."
        )

    def getDestinationCollection(self):
        """Return the collection that these datasets will be ingested to.

        Returns
        -------
        collectionName : `str`
            The collection the data will be ingested to.
        """
        raise NotImplementedError(
            "Subclasses must define their target collection."
        )

    def readCalibFromFile(self, inputFile):
        """Read the inputFile, and determine its calibration type and read it.

        Parameters
        ----------
        inputFile : `lsst.resources.ResourcePath`
            File to be read to check ingestibility.

        Returns
        -------
        calib : `lsst.ip.isr.IsrCalib`
            The appropriately subclassed implementation for this calibration type.
        calibType : `str`
            The calibration type/version name.
        """
        raise NotImplementedError(
            "Subclasses must define how to read their datasets."
        )

    def getAssociationInfo(self, inputFile, calib, calibType):
        """Determine the information needed to create a dataId for this dataset.

        Parameters
        ----------
        inputFile : `lsst.resources.ResourcePath`
            Original file containing the dataset.  Used for log messages.
        calib : `lsst.ip.isr.IsrCalib`
            The calibration dataset to study.
        calibType : `str`
            The calibration type/version name.

        Returns
        -------
        instrumentName : `str`
            Instrument this dataset belongs to.
        whereClause : `str`
            Butler query "where" that will find the exposure with
            matching dataId.
        binding : `dict` [`str`: `str`]
            Binding values for ``whereClause``.
        logId : `str`
            A string (or dataset convertable to string) to be used in
            downstream logs.
        """
        raise NotImplementedError(
            "Subclasses must define how to associate their datasets."
        )

    def run(self, locations, run=None,
            file_filter=DEFAULT_PHOTODIODE_REGEX,
            track_file_attrs=None):

        """Ingest calibration data into a Butler data repository.

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
            run = self.getDestinationCollection()
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
            calib, calibType = self.readCalibFromFile(inputFile)

            # Get the information we'll need to look up which exposure
            # it matches
            instrumentName, whereClause, binding, logId = self.getAssociationInfo(inputFile, calib, calibType)

            if whereClause is None:
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
