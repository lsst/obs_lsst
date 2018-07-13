config.isr.doFlat = False  # mandatory for this task
config.ccdKey = 'detector'

# to be re-examined once more calibration products are available
config.isr.doBias = True
config.isr.doDark = True
config.isr.doFringe = False
config.isr.doLinearize = False
config.isr.doDefect = False

config.isr.doWrite = False

config.isr.overscanFitType = "AKIMA_SPLINE"
config.isr.overscanOrder = 30

config.isr.doAddDistortionModel = False
config.isr.doUseOpticsTransmission = False
config.isr.doUseFilterTransmission = False
config.isr.doUseSensorTransmission = False
config.isr.doUseAtmosphereTransmission = False
config.isr.doAttachTransmissionCurve = False
