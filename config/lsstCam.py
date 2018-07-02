# Configuration for lsstCam

if hasattr(config, 'ccdKeys'):
    config.ccdKeys = ['raft', 'ccd', 'snap']

config.isr.doLinearize = False
config.isr.doDefect = False

# Temporarily disable calibration tasks
config.isr.doDark=False
config.isr.doBias=False
config.isr.doFlat=False
