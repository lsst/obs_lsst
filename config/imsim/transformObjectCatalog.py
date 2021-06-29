import os

# Always produce these output bands in the Object Tables,
# regardless which bands were processed
config.outputBands = ["u", "g", "r", "i", "z", "y"]

# Use the environment variable to prevent hardcoding of paths
# into quantum graphs.
config.functorFile = os.path.join('$OBS_LSST_DIR', 'policy', 'imsim', 'Object.yaml')
