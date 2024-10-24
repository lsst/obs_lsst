import os

obsConfigDir = os.path.join(os.path.dirname(__file__))
config.photoRefObjLoader.load(os.path.join(obsConfigDir, "filterMap.py"))
config.connections.astromRefCat = "the_monster_20240904"
