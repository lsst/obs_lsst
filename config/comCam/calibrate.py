import os

obsConfigDir = os.path.join(os.path.dirname(__file__))
config.photoRefObjLoader.load(os.path.join(obsConfigDir, "filterMap.py"))
config.connections.astromRefCat = "the_monster_20240904"

# Loosen maxOffset to account for early pointing model inaccuracy.
config.astrometry.matcher.maxOffsetPix=800
config.astromRefObjLoader.pixelMargin=800

# Loosened for early ComCam with large PSFs.
config.photoCal.match.sourceSelection.doUnresolved = False
