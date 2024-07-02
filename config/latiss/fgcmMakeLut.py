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

# Override mapping from physical filter labels to 'standard' physical
# filter labels. The 'standard' physical filter defines the transmission
# curve that the FGCM standard bandpass will be based on.
# Any filter not listed here will be mapped to
# itself.  These overrides say that empty~i and empty~y should
# me mapped onto i~empty and y~empty.
config.stdPhysicalFilterOverrideMap = {"empty~SDSSi_65mm": "SDSSi_65mm~empty",
                                       "empty~SDSSy_65mm": "SDSSy_65mm~empty"}

# FGCM name or filename of precomputed atmospheres
config.atmosphereTableName = "fgcm_atm_lsst2"
