from lsst.obs.lsstCam.auxTel import AuxTelParseTask

config.parse.retarget(AuxTelParseTask)

config.parse.translation = {
    'expTime': 'EXPTIME',   # values are incorrect in 2018-07-20 (e.g. ats_dark_600*fits)
    'object': 'OBJECT',
    'imageType': 'IMGTYPE',
    'detectorName': '',
    'dateObs': 'DATE-OBS',
    'date': 'DATE-OBS',
    'seqnum': 'SEQNUM',
}
config.parse.translators = {
    'dayObs': 'translate_dayObs',
    'detector': 'translate_detector',   # set this way as I can't use a default of 0
    'filter': 'translate_filter',       # we have two filter wheels
    'kid': 'translate_kid',             # Kirk's time-based ID (valid within a day)
    'visit': 'translate_visit',
    'wavelength': 'translate_wavelength',
}
config.parse.defaults = {
    #'detector': 0,                      # values must be strings as per ParseConfig in pipe_tasks
    'detectorName': "S1",
    'object': "UNKNOWN",
    'imageType': "UNKNOWN",
}
config.parse.hdu = 0

config.register.columns = {
    #'run': 'text',
    'dayObs': 'text',
    'seqnum': 'int',
    'kid': 'int',
    'visit': 'int',
    'detector': 'int',
    'detectorName': 'text',
    'filter': 'text',
    'dateObs': 'text',
    'date': 'text',
    'expTime': 'double',
    'object': 'text',
    'imageType': 'text',
    'wavelength': 'int',
}
config.register.unique = ["visit", "detector"]
config.register.visit = list(config.register.columns.keys())
