# Mapping of camera filter name: reference catalog filter name
# This file is appropriate for the_monster

for source, target in [
    ("SDSSg_65mm~empty", "monster_SynthLATISS_g"),
    ("SDSSr_65mm~empty", "monster_SynthLATISS_r"),
    ("SDSSi_65mm~empty", "monster_SynthLATISS_i"),
    ("empty~SDSSi_65mm", "monster_SynthLATISS_i"),
    ("SDSSz_65mm~empty", "monster_SynthLATISS_z"),
    ("SDSSy_65mm~empty", "monster_SynthLATISS_y"),
    ("empty~SDSSy_65mm", "monster_SynthLATISS_y"),
]:
    config.filterMap[source] = target
