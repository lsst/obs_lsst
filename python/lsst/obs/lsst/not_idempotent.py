import lsst.obs.base

if hasattr(lsst.obs.base, "new_variable"):
    raise RuntimeError("Unexpected re-import!")

lsst.obs.base.new_variable = 3


def get_new_variable():
    return lsst.obs.base.new_variable
