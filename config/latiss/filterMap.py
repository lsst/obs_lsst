# Mapping of camera filter name: reference catalog filter name
# This file is appropriate for ATLAS Refcat2.

for source, target in [
        ("SDSSg_65mm~empty", "g"),
        ("SDSSr_65mm~empty", "r"),
        ("SDSSi_65mm~empty", "i"),
        ("SDSSz_65mm~empty", "z"),
        # ATLAS Refcat2 does not have y band.
        ("SDSSy_65mm~empty", "z"),
    ]:
    config.filterMap[source] = target