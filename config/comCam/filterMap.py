# Mapping of camera band to reference catalog filter name
# This file is appropriate for the_monster


# This includes mappings for both filter and band, because photoCalTask
# switches between the two depending on whether color term corrections are
# enabled. Once that is fixed, this should be keyed by band as per RFC-976.
for source, target in [
    ("empty", "monster_SynthLSST_r"),
    ("white", "monster_SynthLSST_r"),
    ("u_02", "monster_SynthLSST_u"),
    ("u_05", "monster_SynthLSST_u"),
    ("u_06", "monster_SynthLSST_u"),
    ("g_01", "monster_SynthLSST_g"),
    ("g_07", "monster_SynthLSST_g"),
    ("r_03", "monster_SynthLSST_r"),
    ("i_06", "monster_SynthLSST_i"),
    ("z_02", "monster_SynthLSST_z"),
    ("z_03", "monster_SynthLSST_z"),
    ("y_04", "monster_SynthLSST_y"),
    ("u", "monster_SynthLSST_u"),
    ("g", "monster_SynthLSST_g"),
    ("r", "monster_SynthLSST_r"),
    ("i", "monster_SynthLSST_i"),
    ("z", "monster_SynthLSST_z"),
    ("y", "monster_SynthLSST_y"),
]:
    config.filterMap[source] = target
