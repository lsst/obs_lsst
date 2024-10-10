# Mapping of camera filter name: reference catalog filter name
# This file is appropriate for ATLAS Refcat2.

for source, target in [
    # update left hand column with the filter names once we know them
    ("u", "g"),
    ("g", "g"),
    ("r", "r"),
    ("i", "i"),
    ("z", "z"),
    # ATLAS Refcat2 does not have y band.
    ("y", "z"),
]:
    config.filterMap[source] = target
