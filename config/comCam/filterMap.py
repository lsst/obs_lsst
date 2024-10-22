# Mapping of camera filter name: reference catalog filter name
# This file is appropriate for the_monster

for source, target in [
    # update left hand column with the filter names once we know them
    ("empty", "white"),
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
]:
    config.filterMap[source] = target
