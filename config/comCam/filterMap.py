# Mapping of camera filter name: reference catalog filter name
# This file is appropriate for ATLAS Refcat2.

for source, target in [
    # update left hand column with the filter names once we know them
    ("empty", "white"),
    ("u_02", "u"),
    ("u_05", "u"),
    ("u_06", "u"),
    ("g_01", "g"),
    ("g_07", "g"),
    ("r_03", "r"),
    ("i_06", "i"),
    ("z_02", "z"),
    ("z_03", "z"),
    # ATLAS Refcat2 does not have y band.
    ("y_04", "z"),
]:
    config.filterMap[source] = target
