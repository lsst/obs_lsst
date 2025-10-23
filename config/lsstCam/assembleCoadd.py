"""
lsstCam-specific overrides for assembleCoadd and subclasses
"""

# Need to reject VIGNETTED pixels, but VIGNETTED pixels also have NO_DATA set,
# and NO_DATA is in default badMaskPlanes.
config.badMaskPlanes += ["PARTLY_VIGNETTED"]
config.badMaskPlanes += ["SPIKE"]
