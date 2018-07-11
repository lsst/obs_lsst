# Configuration for lsstCam

if hasattr(config, 'ccdKeys'):
    config.ccdKeys = ['detector', 'snap']

config.isr.doLinearize = False
config.isr.doDefect = False
config.isr.doAddDistortionModel = False
