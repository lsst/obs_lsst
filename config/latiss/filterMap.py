# Mapping of camera filter name: reference catalog filter name
# This file is appropriate for the_monster.

for source, target in [
    ("SDSSg_65mm~empty", "monster_LATISS_g"),
    ("SDSSr_65mm~empty", "monster_LATISS_r"),
    ("SDSSi_65mm~empty", "monster_LATISS_i"),
    ("empty~SDSSi_65mm", "monster_LATISS_i"),
    ("SDSSz_65mm~empty", "monster_LATISS_z"),
    ("SDSSy_65mm~empty", "monster_LATISS_y"),
    ("empty~SDSSy_65mm", "monster_LATISS_y"),
    ("y", "monster_LATISS_y"),
]:
    config.filterMap[source] = target
