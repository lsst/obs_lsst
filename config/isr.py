"""
LSST Cam-specific overrides for IsrTask
"""
if hasattr(config, 'ccdKeys'):
    config.ccdKeys = ['detector', 'snap', 'raftName', 'detectorName']

config.doLinearize = False
config.doDefect = False
config.doCrosstalk=True
config.doAddDistortionModel = False
config.qa.doThumbnailOss = False
config.qa.doThumbnailFlattened = False
