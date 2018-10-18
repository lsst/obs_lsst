from lsst.obs.lsst.ts8 import Ts8ParseTask

config.parse.retarget(Ts8ParseTask)

config.parse.translation = {
    'date': 'DATE-OBS',
    'dateObs': 'DATE-OBS',
    'lsstSerial': 'LSST_NUM',
    'expTime': 'EXPTIME',
    'imageType': 'IMGTYPE',
    'object': 'OBJECT',
    'run': 'RUNNUM',
    'seqNum': 'SEQNUM',
    'wavelength': 'MONOWL',
}
config.parse.translators = {
    'dayObs': 'translate_dayObs',
    'detector': 'translate_detector',
    'detectorName': 'translate_detectorName',
    'filter' : 'translate_filter',
    'visit': 'translate_visit',
    'wavelength': 'translate_wavelength',
}
config.parse.defaults = {
    'object': "UNKNOWN",
    'imageType': "UNKNOWN",
}
config.parse.hdu = 0

config.register.columns = {
    'run': 'text',
    'date': 'text',
    'dateObs': 'text',
    'dayObs': 'text',
    'detector': 'int',
    'detectorName': 'text',
    'expTime': 'double',
    'filter': 'text',
    'imageType': 'text',
    'lsstSerial': 'text',
    'object': 'text',
    'seqNum': 'int',
    'visit': 'int',
    'wavelength': 'int',
}
config.register.unique = ["visit", "detector"]
config.register.visit = list(config.register.columns.keys())
