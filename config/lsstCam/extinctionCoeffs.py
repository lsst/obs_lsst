# Extinction coefficients (R_filter) for LSSTCam filters for conversion
# from E(B-V) to extinction: A_filter = E(B-V) * R_filter
# Band, R_filter

# These default extinction coefficients are not optimal for the FGCM standard
# bandpasses.
# From rubin_sim.phot_utils, DustValues().r_x provides the
# values for the Rubin filters. These values are calculated using the CCM89
#  extinction curve (Cardelli, Clayton, and Mathis 1989), assuming a flat
# spectral energy distribution and R_v=3.1 (for the Milky Way diffuse ISM).
config.extinctionCoeffs = {
    "u": 4.75721,
    "g": 3.66056,
    "r": 2.701367,
    "i": 2.053659,
    "z": 1.59009,
    "y": 1.3077049,
}
