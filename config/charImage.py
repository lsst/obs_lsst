import os.path

ObsConfigDir = os.path.dirname(__file__)

charImFile = os.path.join(ObsConfigDir, "characterizeImage.py")
config.load(charImFile)
