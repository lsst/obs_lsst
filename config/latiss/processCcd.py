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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
import os
from lsst.utils import getPackageDir
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask
from lsst.obs.lsst.filters import LATISS_FILTER_DEFINITIONS

config.isr.doCrosstalk=False

config.calibrate.doPhotoCal = False

REFCAT = "gaia_dr2_20191105"

# Reference catalog
# config.calibrate.refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
# config.calibrate.refObjLoader.load(os.path.join(getPackageDir("obs_lsst"), "config", "filterMap.py"))

# config.calibrate.refObjLoader.ref_dataset_name="cal_ref_cat"
config.calibrate.connections.astromRefCat = REFCAT
config.calibrate.connections.photoRefCat = REFCAT

for refObjLoader in (config.charImage.refObjLoader,
                     config.calibrate.astromRefObjLoader,
                     config.calibrate.photoRefObjLoader):
    refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
    # refObjLoader.load(os.path.join(getPackageDir('obs_lsst'), 'config', 'filterMap.py'))
    refObjLoader.ref_dataset_name = REFCAT

# config.filterMap = {band: '' % (band) for band in 'ugrizy'}
filtMap = {}
filts = LATISS_FILTER_DEFINITIONS
for filt in filts._filters:
    filtMap[filt.physical_filter] = 'phot_g_mean'

# import ipdb as pdb; pdb.set_trace()
config.calibrate.astromRefObjLoader.filterMap = filtMap
config.calibrate.photoRefObjLoader.filterMap = filtMap
# config.imChar.photometryRefObjLoader.filterMap =

# config.calibrate.astrometry.useWcsParity = False
# config.calibrate.astrometry.useWcsPixelScale = False
# config.calibrate.astrometry.useWcsRaDecCenter = False 

OFFSET = 1000
# Padding to add to 4 all edges of the bounding box (pixels)
config.calibrate.astromRefObjLoader.pixelMargin=OFFSET



# Minimum number of matched pairs; see also minFracMatchedPairs.
config.calibrate.astrometry.matcher.minMatchedPairs=5



# Minimum number of matched pairs as a fraction of the smaller of the number of reference stars or the number of good sources; the actual minimum is the smaller of this value or minMatchedPairs.
config.calibrate.astrometry.matcher.minFracMatchedPairs=0.1

# Number of softening iterations in matcher.
config.calibrate.astrometry.matcher.matcherIterations=5

# Maximum allowed shift of WCS, due to matching (pixel). When changing this value, the LoadReferenceObjectsConfig.pixelMargin should also be updated.
config.calibrate.astrometry.matcher.maxOffsetPix=OFFSET

# Rotation angle allowed between sources and position reference objects (degrees).
config.calibrate.astrometry.matcher.maxRotationDeg=5.9

# Number of points to define a shape for matching.
config.calibrate.astrometry.matcher.numPointsForShape=6


# Number of points to try for creating a shape. This value should be greater than or equal to numPointsForShape. Besides loosening the signal to noise cut in the 'matcher' SourceSelector, increasing this number will solve CCDs where no match was found.
config.calibrate.astrometry.matcher.numPointsForShapeAttempt=6

# Distance in units of pixels to always consider a source-reference pair a match. This prevents the astrometric fitter from over-fitting and removing stars that should be matched and allows for inclusion of new matches as the wcs improves.
config.calibrate.astrometry.matcher.minMatchDistPixels=1.0

# Number of implied shift/rotations from patterns that must agree before it a given shift/rotation is accepted. This is only used after the first softening iteration fails and if both the number of reference and source objects is greater than numBrightStars.
config.calibrate.astrometry.matcher.numPatternConsensus=3

# If the available reference objects exceeds this number, consensus/pessimistic mode will enforced regardless of the number of available sources. Below this optimistic mode (exit at first match rather than requiring numPatternConsensus to be matched) can be used. If more sources are required to match, decrease the signal to noise cut in the sourceSelector.
config.calibrate.astrometry.matcher.numRefRequireConsensus=1000

# Maximum number of reference objects to use for the matcher. The absolute maximum allowed for is 2 ** 16 for memory reasons.
config.calibrate.astrometry.matcher.maxRefObjects=65536

# the maximum match distance is set to  mean_match_distance + matchDistanceSigma*std_dev_match_distance; ignored if not fitting a WCS
config.calibrate.astrometry.matchDistanceSigma=2.0


