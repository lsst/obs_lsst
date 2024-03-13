import os.path

config_dir = os.path.dirname(__file__)

# Fiducial values come from a set of 4334 visits generated in:
# repo='/repo/ops-rehearsal-3-prep'
# collection='u/homer/w_2024_10/DM-43228'
# Plots, including the median values used here, can be found on JIRA ticket DM-42747

config.fiducialPsfSigma = {
    'g': 1.72,
    'r': 1.60,
    'i': 1.57,
}    

config.fiducialSkyBackground = {
    'g': 9.34,
    'r': 19.58,
    'i': 35.97,
}

config.fiducialZeroPoint = {
    'g': 27.68,
    'r': 27.56,
    'i': 27.40,
}
