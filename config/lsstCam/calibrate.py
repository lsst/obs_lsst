import os

obsConfigDir = os.path.join(os.path.dirname(__file__))
config.photoRefObjLoader.load(os.path.join(obsConfigDir, "filterMap.py"))

config.photoCal.photoCatName = 'gaia_dr3_20230707'
config.connections.photoRefCat = 'ps1_pv3_3pi_20170110'
