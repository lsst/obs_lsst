config.isr.doFlat = False  # mandatory for this task

# to be re-examined once more calibration products are available
config.isr.doBias = True
config.isr.doDark = True
config.isr.doFringe = False
config.isr.doLinearize = False
config.isr.doDefect = False

config.isr.doWrite = False

config.isr.overscanFitType = "AKIMA_SPLINE"
config.isr.overscanOrder = 30

# config.isr.crosstalk.value.coeffs.values = [0.0e-6, -125.0e-6, -149.0e-6, -156.0e-6,
#                                             -124.0e-6, 0.0e-6, -132.0e-6, -157.0e-6,
#                                             -171.0e-6, -134.0e-6, 0.0e-6, -153.0e-6,
#                                             -157.0e-6, -151.0e-6, -137.0e-6, 0.0e-6]

# Added by Merlin:
config.isr.doAddDistortionModel = False
config.isr.doUseOpticsTransmission = False
config.isr.doUseFilterTransmission = False
config.isr.doUseSensorTransmission = False
config.isr.doUseAtmosphereTransmission = False
config.isr.doAttachTransmissionCurve = False
