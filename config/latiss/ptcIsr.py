import os.path

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
