# -*- python -*-
from lsst.sconsUtils import scripts

# Note the ordering here is critical. AuxTel is put at the end here to ensure
# that the tests are run first and version.py is created, because creation of
# of the defect registry required the camera to be instantiated.
# If other cameras add defect generation they should add their build to
# the end of this list, along with auxTel
targetList = ("version", "shebang", "policy",) + scripts.DEFAULT_TARGETS + ("auxTel",)

scripts.BasicSConstruct("obs_lsst", disableCc=True, defaultTargets=targetList)
