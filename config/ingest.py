from lsst.obs.lsst.ingest import LsstCamParseTask

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
    'raftName': 'translate_raftName',
    'detectorName': 'translate_detectorName',
    'detector': 'translate_detector',
    'snap': 'translate_snap',
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
    'raftName': 'text',
    'detectorName': 'text',
    'detector': 'int',
    'snap': 'int',
    'object': 'text',
    'imageType': 'text',
    'testType': 'text',
    'lsstSerial': 'text',
    'wavelength': 'int',
}
config.register.unique = ["visit", "detector"]
config.register.visit = ['visit', 'filter', 'dateObs', 'expTime']
