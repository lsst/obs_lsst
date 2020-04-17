import os.path

config.load(os.path.join(os.path.dirname(__file__), "lsstCamCommon.py"))
config.isrForFlats.load(os.path.join(os.path.dirname(__file__), "isr.py"))
config.isrForDarks.load(os.path.join(os.path.dirname(__file__), "isr.py"))

config.ccdKey = 'detector'

# the default is False as most obs_packages don't have runs, but LSST does
# and when runs are present the default behavior should be to ensure
# that only data from within a run is processed together
config.assertSameRun = True

config.isrForDarks.doFlat = False  # don't flatfield darks

# none of the calibration products exists to perform these yet
for config in [config.isrForDarks, config.isrForFlats]:
    config.doCrosstalk = False
    config.doAddDistortionModel = False
    config.doUseOpticsTransmission = False
    config.doUseFilterTransmission = False
    config.doUseSensorTransmission = False
    config.doUseAtmosphereTransmission = False
    config.doAttachTransmissionCurve = False
