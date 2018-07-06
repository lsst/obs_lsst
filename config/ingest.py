from lsst.obs.lsstCam.ingest import LsstCamParseTask

config.parse.retarget(LsstCamParseTask)

config.parse.translation = {
    'expTime': 'EXPTIME',
    'object': 'OBJECT',
    'imageType': 'IMGTYPE',
    'testType': 'TESTTYPE',
    'filter': 'FILTER',
    'lsstSerial': 'LSST_NUM',
    'date': 'DATE-OBS',
    'dateObs': 'DATE-OBS',
    'run': 'RUNNUM',
    'visit': 'OBSID',
}
config.parse.translators = {
    'wavelength': 'translate_wavelength',
    'raft' : 'translate_raft',
    'ccdName' : 'translate_ccdName',
    'ccd'  : 'translate_ccd',
    'snap' : 'translate_snap',
}
config.parse.defaults = {
    'object': "UNKNOWN",
}
config.parse.hdu = 0

config.register.columns = {
    'run': 'text',
    'visit': 'int',
    'filter': 'text',
    'date': 'text',
    'dateObs': 'text',
    'expTime': 'double',
    'raft': 'text',
    'ccdName': 'text',
    'ccd': 'int',
    'snap': 'int',
    'object': 'text',
    'imageType': 'text',
    'testType': 'text',
    'lsstSerial': 'text',
    'wavelength': 'int',
}
config.register.unique = ["visit", "raft", "ccd"]
config.register.visit = list(config.register.columns.keys())
