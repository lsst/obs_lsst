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
import tempfile
# from multiprocessing import Pool

from lsst.daf.butler import (
    CollectionType,
    DataCoordinate,
    #    DatasetIdGenEnum,
    DatasetRef,
    DatasetType,
    FileDataset,
    Progress,
)

from lsst.pex.config import Config, Field
from lsst.pipe.base import Task
from lsst.resources import ResourcePath
# from lsst.utils.timer import timeMethod

from lsst.ip.isr import PhotodiodeCalib
from lsst.obs.base import Instrument, makeTransferChoiceField
from lsst.obs.base.formatters.fitsGeneric import FitsGenericFormatter


__all__ = ('PhotodiodeIngestConfig', 'PhotodiodeIngestTask')


class PhotodiodeIngestConfig(Config):
    """Configuration class for PhotodiodeIngestTask."""

    transfer = makeTransferChoiceField()
    failFast = Field(
        dtype=bool,
        default=False,
        doc="If True, stop ingest as soon as any problem is encountered with any file. "
        "Otherwise problem files will be skipped and logged and a report issued at completion.",
    )


class PhotodiodeIngestTask(Task):
    """Task to ingest photodiode data into a butler repository.

    Parameters
    ----------
    config : `PhotodiodeIngestConfig`
        Configuration for the task.
    butler : `~lsst.daf.butler.Butler`
        Writable butler instance, with ``butler.run`` set to the appropriate
        `~lsst.daf.butler.CollectionType.RUN` collection for these datasets.
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

    def run(self, locations, run=None, processes=1, file_filter=r".*Photodiode_Readings.*txt",
            track_file_attrs=None):
        """Docs.
        """
        files = ResourcePath.findFileResources(locations, file_filter)

        return self.ingestPhotodiodeFiles(files)

    def ingestPhotodiodeFiles(self, files, *, pool=None, processes=1, run=None,
                              skip_existing_exposures=False, track_file_attrs=True):
        """Ingest files into a Butler data repository.

        CZW: Doc

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
        """
        registry = self.butler.registry
        registry.registerDatasetType(self.datasetType)

        if run is None:
            run = self.instrument.makeCollectionName("calib", "photodiode")
        # if run not in runs:
        registry.registerCollection(run, type=CollectionType.RUN)
        #    runs.add(run)

        # We need to write the files to disk for ingest.

        datasets = []
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
            exposureRecords = [rec for rec in registry.queryDimensionRecords("exposure", instrument=self.instrument.getName(),
                                                                             where=whereClause,
                                                                             bind={"dayObs": dayObs, "seqNum": seqNum})]

            nRecords = len(exposureRecords)
            if nRecords == 1:
                exposureId = exposureRecords[0].id
                calib.updateMetadata(camera=self.camera, exposure=exposureId)
            else:
                # This is a failure.  Do something here.
                print("whoops")

            # Ingest must work from a file, but we can't use the
            # original, as we've added new metadata and reformatted
            # it.  Write it to a temp file that we can use to ingest.
            tempFile = tempfile.mktemp() + ".fits"
            calib.writeFits(tempFile)

            dataId = DataCoordinate.standardize(
                instrument=self.instrument.getName(),
                exposure=exposureId,
                universe=self.universe,
            )

            # does it exist?
            existing = {
                ref.dataId
                for ref in self.butler.registry.queryDatasets(self.datasetType, collections=[run],
                                                              dataId=dataId)
            }
            if existing:
                print(existing)

            ref = DatasetRef(self.datasetType, dataId)

            datasets.append(FileDataset(path=tempFile, refs=ref, formatter=FitsGenericFormatter))

        import pdb; pdb.set_trace()
        results = self.butler.ingest(*datasets, transfer=self.config.transfer, run=run,
                                     # idGenerationMode=mode,
                                     record_validation_info=track_file_attrs)
        return results
