# Configuration for lsstCam

if hasattr(config, 'ccdKeys'):
    config.ccdKeys = ['raft', 'ccd', 'snap']

config.isr.doLinearize = False
config.isr.doDefect = False
config.isr.doAddDistortionModel = False
