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
__all__ = ('PhotodiodeIngestConfig', 'PhotodiodeIngestTask',
           'ShutterMotionOpenIngestConfig', 'ShutterMotionOpenIngestTask',
           'ShutterMotionCloseIngestConfig', 'ShutterMotionCloseIngestTask')


from lsst.daf.butler import (
    CollectionType,
    DataCoordinate,
    DatasetIdGenEnum,
    DatasetRef,
    DatasetType,
    FileDataset,
    Progress,
)
from lsst.ip.isr import PhotodiodeCalib, ShutterMotionProfile
from lsst.obs.base import makeTransferChoiceField
from lsst.obs.base.formatters.fitsGeneric import FitsGenericFormatter
from lsst.pex.config import Config, Field
from lsst.pipe.base import Task
from lsst.resources import ResourcePath


DEFAULT_PHOTODIODE_REGEX = r"Photodiode_Readings.*txt$|_photodiode.ecsv$|Electrometer.*fits$|EM.*fits$"
DEFAULT_SHUTTER_OPEN_REGEX = r".*shutterMotionProfileOpen.json$"
DEFAULT_SHUTTER_CLOSE_REGEX = r".*shutterMotionProfileClose.json$"

# Base class begin.
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
            The appropriately subclassed implementation for this
            calibration type.
        calibType : `str`
            The calibration type/version name.
        """
        raise NotImplementedError(
            "Subclasses must define how to read their datasets."
        )

    def getAssociationInfo(self, inputFile, calib, calibType):
        """Determine the information needed to create a dataId for this
        dataset.

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
        datasetType = self.datasetType
        registry.registerDatasetType(datasetType)

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
        numSoftFailed = 0
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
                numSoftFailed += 1
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
            if self.config.transfer == "copy":
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
            elif self.config.transfer == "direct":
                if self.config.forceCopyOnly:
                    raise RuntimeError("I probably can never happen.")

                ref = DatasetRef(self.datasetType, dataId, run=run, id_generation_mode=mode)
                dataset = FileDataset(path=inputFile, refs=ref, formatter=FitsGenericFormatter)  # ??
                self.butler.ingest(dataset, transfer=self.config.transfer,
                                   record_validation_info=track_file_attrs)
                self.log.info("Photodiode %s:%d (%s) ingested successfully", instrumentName, exposureId,
                              logId)
                refs.append(dataset)

        if numExisting != 0:
            self.log.warning("Skipped %d entries that already existed in run %s", numExisting, run)
        if numSoftFailed != 0:
            self.log.warning("Skipped %d entries that had no associated exposure", numSoftFailed)
        if numFailed != 0:
            raise RuntimeError(f"Failed to ingest {numFailed} entries due to missing exposure information.")


# Photodiode implementation begin.
class PhotodiodeIngestConfig(IsrCalibIngestConfig):
    """Configuration class for PhotodiodeIngestTask."""
    pass


class PhotodiodeIngestTask(IsrCalibIngestTask):
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
        """Inherited from base class"""
        return DatasetType(
            "photodiode",
            ("instrument", "exposure"),
            "IsrCalib",
            universe=self.universe,
        )

    def getDestinationCollection(self):
        """Inherited from base class"""
        return self.instrument.makeCollectionName("calib", "photodiode")

    def readCalibFromFile(self, inputFile):
        """Inherited from base class"""
        # import pdb; pdb.set_trace()
        try:
            # Try reading as a fits file.  This is the 2025
            # standard, but make sure to include the format
            # version so we can parse that below.
            with inputFile.as_local() as localFile:
                calib = PhotodiodeCalib.readFits(localFile.ospath)
            fitsVersion = int(calib.getMetadata().get("FORMAT_V", 1))
            calibType = f"fits-v{fitsVersion:d}"
            return calib, calibType
        except Exception:
            try:
                # Try reading as a text file
                with inputFile.as_local() as localFile:
                    calib = PhotodiodeCalib.readText(localFile.ospath)
                # This is "full" in that it has everything needed to
                # be read from text.
                calibType = "full"
                return calib, calibType
            except Exception:
                # Try reading as a two-column file.  This was the
                # older version.
                try:
                    with inputFile.as_local() as localFile:
                        calib = PhotodiodeCalib.readTwoColumnPhotodiodeData(localFile.ospath)
                    calibType = "two-column"
                    return calib, calibType
                except Exception:
                    return None, "Unknown"
        # Code should never get here
        return None, "Unknown"

    def getAssociationInfo(self, inputFile, calib, calibType):
        """Inherited from base class"""
        # GET INFO BLOCK
        # Get exposure records so we can associate the photodiode
        # to the exposure.
        if calibType == "fits-v1":
            instrumentName = calib.metadata.get("INSTRUME")
            if instrumentName is None or instrumentName != self.instrument.getName():
                # The field is populated by the calib class, so we
                # can't use defaults.
                instrumentName = self.instrument.getName()

            # This format uses the GROUPID to match what is set in
            # the exposure.  Validate this to be of the form:
            # {initial_group}#{unique identifier}, neither of
            # which should be blank.
            groupId = calib.metadata.get("GROUPID")
            validGroup = True
            if groupId is None:
                validGroup = False
            elif "#" not in groupId:
                validGroup = False
            else:
                splitGroup = groupId.split("#")
                if len(splitGroup) != 2:
                    validGroup = False
                if splitGroup[0] == "" or splitGroup[1] == "":
                    validGroup = False
            if not validGroup:
                self.log.warning("Skipping input file %s with malformed group %s.",
                                 inputFile, groupId)
                return None, None, None, groupId

            whereClause = "exposure.group=groupId"
            binding = {"groupId": groupId}
            logId = groupId
        elif calibType == "full":
            instrumentName = calib.getMetadata().get('INSTRUME')
            if instrumentName is None:
                # The field is populated by the calib class, so we
                # can't use defaults.
                instrumentName = self.instrument.getName()

            # This format uses the obsId to match what is set in
            # the exposure.
            obsId = calib.getMetadata()['obsId']
            whereClause = "exposure.obs_id=obsId"
            binding = {"obsId": obsId}
            logId = obsId
        elif calibType == "two-column":
            dayObs = calib.getMetadata()['day_obs']
            seqNum = calib.getMetadata()['seq_num']

            # This format uses dayObs and seqNum to match what is
            # set in the exposure.
            whereClause = "exposure.day_obs=dayObs and exposure.seq_num=seqNum"
            instrumentName = self.instrument.getName()
            binding = {"dayObs": dayObs, "seqNum": seqNum}
            logId = (dayObs, seqNum)
        else:
            # We've failed somewhere to reach this point
            instrumentName = None
            whereClause = None
            binding = None
            logId = None

        return instrumentName, whereClause, binding, logId


# Shutter Motion Open / Base Class begin:
class ShutterMotionOpenIngestConfig(IsrCalibIngestConfig):
    """Configuration class for ShutterMotionIngestTask."""
    pass


class ShutterMotionOpenIngestTask(IsrCalibIngestTask):
    """Task to ingest shutter motion profiles into a butler repository.

    This task specifically works on the "open" profile.

    Parameters
    ----------
    config : `ShutterMotionIngestConfig`
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

    ConfigClass = ShutterMotionOpenIngestConfig
    _DefaultName = "shutterMotionOpenIngest"

    def getDatasetType(self):
        """Inherited from base class"""
        return DatasetType(
            "shutterMotionProfileOpen",
            ("instrument", "exposure"),
            "IsrCalib",
            universe=self.universe,
        )

    def getDestinationCollection(self):
        """Inherited from base class"""
        return self.instrument.makeCollectionName("calib", "shutterMotion")

    def readCalibFromFile(self, inputFile):
        """Inherited from base class"""
        try:
            # Try reading as a json file.  This is the 2025
            # standard, but make sure to include the format
            # version so we can parse that below.
            with inputFile.as_local() as localFile:
                calib = ShutterMotionProfile.readText(localFile.ospath)
            fitsVersion = int(calib.getMetadata().get("FORMAT_V", 1))
            calibType = f"text-v{fitsVersion:d}"
            return calib, calibType
        except Exception:
            return None, "Unknown"

        # Code should never get here
        return None, "Unknown"

    def getAssociationInfo(self, inputFile, calib, calibType):
        """Inherited from base class"""
        # Get exposure records so we can associate the photodiode
        # to the exposure.
        if calibType == "text-v1":
            instrumentName = calib.metadata.get("INSTRUME")
            if instrumentName is None or instrumentName != self.instrument.getName():
                # The field is populated by the calib class, so we
                # can't use defaults.
                instrumentName = self.instrument.getName()

            # This format uses the GROUPID to match what is set in
            # the exposure.  Validate this to be of the form:
            # {initial_group}#{unique identifier}, neither of
            # which should be blank.
            obsId = calib.metadata.get("obsId")
            if obsId is None:
                self.log.warning("Skipping input file %s with malformed obsId %s.",
                                 inputFile, obsId)
                return None, None, None, obsId

            whereClause = "exposure.obs_id=obsId"
            binding = {"obsId": obsId}
            logId = obsId
        else:
            # We've failed somewhere to reach this point
            instrumentName = None
            whereClause = None
            binding = None
            logId = None

        return instrumentName, whereClause, binding, logId

    # Shutter Motion Open / Base Class begin:
class ShutterMotionCloseIngestConfig(ShutterMotionOpenIngestConfig):
    """Configuration class for ShutterMotionIngestTask."""
    pass


class ShutterMotionCloseIngestTask(ShutterMotionOpenIngestTask):
    """Task to ingest shutter motion profiles into a butler repository.

    This task specifically works on the "Close" profile.

    Parameters
    ----------
    config : `ShutterMotionIngestConfig`
        Configuration for the task.
    instrument : `~lsst.obs.base.Instrument`
        The instrument these profiles are from.
    butler : `~lsst.daf.butler.Butler`
        Writable butler instance, with ``butler.run`` set to the
        appropriate `~lsst.daf.butler.CollectionType.RUN` collection
        for these datasets.
    **kwargs
        Additional keyword arguments.
    """

    ConfigClass = ShutterMotionCloseIngestConfig
    _DefaultName = "shutterMotionCloseIngest"

    def getDatasetType(self):
        """Inherited from base class"""
        return DatasetType(
            "shutterMotionProfileClose",
            ("instrument", "exposure"),
            "IsrCalib",
            universe=self.universe,
        )
