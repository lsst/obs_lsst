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
        # The following two are blank until we have data to measure them.
        "SDSSz_65mm~empty": Colorterm(
            primary="z",
            secondary="z",
        ),
        "SDSSy_65mm~empty": Colorterm(
            primary="y",
            secondary="y",
        ),
    }),
}
