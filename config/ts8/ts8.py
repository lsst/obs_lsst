# Configuration for TS8

if hasattr(config, 'ccdKeys'):
    config.ccdKeys = ['detector', 'detectorName']

config.isr.doLinearize = False
config.isr.doDefect = False
config.isr.doCrosstalk=True
config.isr.doAddDistortionModel = False
