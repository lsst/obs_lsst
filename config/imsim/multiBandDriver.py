import os.path

configDir = os.path.dirname(__file__)
config.measureCoaddSources.load(os.path.join(configDir, "measureCoaddSources.py"))
