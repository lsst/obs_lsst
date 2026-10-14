# The same shutter-timing settings as diaPipe.
config.load("diaPipe.py")

# Predict solar system objects at the shutter-corrected time of the pixel
# each falls on (lsst.ip.isr.shutterTiming), from the visit summaries.
config.doShutterTiming = True
