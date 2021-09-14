import os

# Use the environment variable to prevent hardcoding of paths
# into quantum graphs.
config.functorFile = os.path.join('$OBS_LSST_DIR', 'policy', 'imsim', 'ForcedSource.yaml')
