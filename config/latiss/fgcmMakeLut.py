# List of filters to put into the look-up table (LUT)
config.physicalFilters = [
    "SDSSg_65mm~empty",
    "SDSSr_65mm~empty",
    "SDSSi_65mm~empty",
    "empty~SDSSi_65mm",
    "SDSSz_65mm~empty",
    "SDSSy_65mm~empty",
    "empty~SDSSy_65mm",
]

# FGCM name or filename of precomputed atmospheres
config.atmosphereTableName = 'fgcm_atm_lsst2'
