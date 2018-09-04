# Configuration for lsstCam

if hasattr(config, 'ccdKeys'):
    config.ccdKeys = ['detector', 'snap', 'raftName', 'detectorName']

config.isr.doLinearize = False
config.isr.doDefect = False
config.isr.doCrosstalk = True
config.isr.doAddDistortionModel = False

# Work-around for median-bug in overscan correction (DM-15203).
config.isr.overscanFitType = 'POLY'
config.isr.overscanOrder = 0
