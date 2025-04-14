# List of filters to put into the look-up table (LUT)
config.physicalFilters = [
    "u_24",
    "g_6",
    "r_57",
    "i_39",
    "z_20",
    "y_10",
]

# FGCM name or filename of precomputed atmospheres
config.atmosphereTableName = "fgcm_atm_lsst2"

# Initial FGCM lookup table is based on per-detector filter transmissions.
config.doFilterDetectorTransmission = True
