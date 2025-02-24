# Mapping of camera band to reference catalog filter name
# This file is appropriate for the_monster


# This includes mappings for both filter and band, because photoCalTask
# switches between the two depending on whether color term corrections are
# enabled. Once that is fixed, this should be keyed by band as per RFC-976.
for source, target in [
    ("empty", "monster_ComCam_r"),
    ("white", "monster_ComCam_r"),
    ("u_02", "monster_ComCam_u"),
    ("u_05", "monster_ComCam_u"),
    ("u_06", "monster_ComCam_u"),
    ("g_01", "monster_ComCam_g"),
    ("g_07", "monster_ComCam_g"),
    ("r_03", "monster_ComCam_r"),
    ("i_06", "monster_ComCam_i"),
    ("z_02", "monster_ComCam_z"),
    ("z_03", "monster_ComCam_z"),
    ("y_04", "monster_ComCam_y"),
    ("u", "monster_ComCam_u"),
    ("g", "monster_ComCam_g"),
    ("r", "monster_ComCam_r"),
    ("i", "monster_ComCam_i"),
    ("z", "monster_ComCam_z"),
    ("y", "monster_ComCam_y"),
]:
    config.filterMap[source] = target
