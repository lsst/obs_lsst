from lsst.obs.lsst.ingest import LsstCamParseTask

config.parse.retarget(LsstCamParseTask)

config.parse.translation = {
    'testType': 'TESTTYPE',
}
config.parse.translators = {
    'expTime': 'translate_expTime',
    'object': 'translate_object',
    'imageType': 'translate_imageType',
    'filter': 'translate_filter',
    'lsstSerial': 'translate_lsstSerial',
    'date': 'translate_date',
    'dateObs': 'translate_dateObs',
    'run': 'translate_run',
    'visit': 'translate_visit',
    'wavelength': 'translate_wavelength',
    'raftName': 'translate_raftName',
    'detectorName': 'translate_detectorName',
    'detector': 'translate_detector',
    'snap': 'translate_snap',
}
config.parse.defaults = {
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
