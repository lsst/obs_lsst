# Config overrides for converting gen2 to gen3 repos.

# For LSST data the raw file is associated with the raw_amp dataset type
config.rawDatasetType = "raw_amp"

# LSST names its detectors differently in the registry
config.ccdKey = "detector"

# Ignore these special dataset types
config.datasetIgnorePatterns.extend(["_raw", "raw_hdu", "raw_amp"])

config.curatedCalibrations.extend(["defects", "qe_curve"])
