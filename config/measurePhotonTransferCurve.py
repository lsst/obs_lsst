import os.path

config.load(os.path.join(os.path.dirname(__file__), "lsstCamCommon.py"))
config.isr.load(os.path.join(os.path.dirname(__file__), "isr.py"))

config.ccdKey = 'detector'

config.isr.doFlat = False
config.isr.doFringe = False
config.isr.doCrosstalk = False
config.isr.doUseOpticsTransmission = False
config.isr.doUseFilterTransmission = False
config.isr.doUseSensorTransmission = False
config.isr.doUseAtmosphereTransmission = False
config.isr.doAttachTransmissionCurve = False

config.isr.doSaturation = False  # critical for the turnover of the PTC to get the variance right
config.isr.doSaturationInterpolation = False
