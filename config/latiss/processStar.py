config.load("latiss.py")

# Configuration for processStarTask

if hasattr(config, "ccdKeys"):
    config.ccdKeys = ["detector", "detectorName"]

config.isr.doLinearize = False

# characterize performance when turning on darks as first attempt found it
# to degrade performance (possibly due to bad darks, but take care here)
config.isr.doDark = False
config.isr.doFlat = False
config.isr.doDefect = True
config.isr.doCrosstalk = False
