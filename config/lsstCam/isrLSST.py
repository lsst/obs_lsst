import copy
from lsst.ip.isr.overscanAmpConfig import OverscanAmpConfig, OverscanDetectorConfig, OverscanCameraConfig


# The LSSTCam default will not have any parallel overscan applied.
# The task default is for MEDIAN_PER_ROW serial overscan correction
# skipping the leading and trailing 3 columns.
defaultAmpConfig = OverscanAmpConfig()
defaultAmpConfig.doParallelOverscan = False

defaultDetectorConfig = OverscanDetectorConfig()
defaultDetectorConfig.defaultAmpConfig = defaultAmpConfig

cameraConfig = OverscanCameraConfig()
cameraConfig.defaultDetectorConfig = defaultDetectorConfig

ampConfigWithParallelOverscan = OverscanAmpConfig()
defaultAmpConfig.doParallelOverscan = True

detectorConfigWithParallelOverscan = OverscanDetectorConfig()
detectorConfigWithParallelOverscan.defaultAmpConfig = ampConfigWithParallelOverscan

cameraConfig.detectorRules["R01_S00"] = copy.copy(detectorConfigWithParallelOverscan)
cameraConfig.detectorRules["R01_S11"] = copy.copy(detectorConfigWithParallelOverscan)
cameraConfig.detectorRules["R30_S00"] = copy.copy(detectorConfigWithParallelOverscan)

config.overscanCamera = cameraConfig
