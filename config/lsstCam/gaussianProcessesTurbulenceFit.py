# Use the TURBO-GP solver (measured 2-point correlation function used
# directly as the Gaussian Processes kernel, solved spectrally; RTN-129)
# to model the atmospheric turbulence for LSSTCam.
config.optimizer = "empirical-2pcf"
config.maxTrainingPoints = 50000
