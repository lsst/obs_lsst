from lsst.pipe.tasks.colorterms import Colorterm, ColortermDict


config.data = {
    "atlas_refcat2*": ColortermDict(data={
        "SDSSg_65mm~empty": Colorterm(
            primary="g",
            secondary="r",
            c0=-0.09034144345111599,
            c1=0.1710923238086337,
            c2=-0.038260355621929296,
        ),
        "SDSSr_65mm~empty": Colorterm(
            primary="r",
            secondary="i",
            c0=0.0073632488906825045,
            c1=-0.026620900037027242,
            c2=-0.03203533692013322,
        ),
        "SDSSi_65mm~empty": Colorterm(
            primary="i",
            secondary="r",
            c0=0.016940180565664747,
            c1=0.0610018330811135,
            c2=-0.0722575356707918,
        ),
        # empty~i is the same as i~empty.
        "empty~SDSSi_65mm": Colorterm(
            primary="i",
            secondary="r",
            c0=0.016940180565664747,
            c1=0.0610018330811135,
            c2=-0.0722575356707918,
        ),
        # The following two are blank until we have data to measure them.
        "SDSSz_65mm~empty": Colorterm(
            primary="z",
            secondary="z",
        ),
        # The ATLAS-REFCAT2 does not have y band, so we use z here as
        # a placeholder.
        "SDSSy_65mm~empty": Colorterm(
            primary="z",
            secondary="z",
        ),
        # empty~y is the same as y~empty.
        "empty~SDSSy_65mm": Colorterm(
            primary="z",
            secondary="z",
        ),
    }),
}
