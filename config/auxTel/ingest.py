from lsst.obs.lsst.auxTel import AuxTelParseTask

config.parse.retarget(AuxTelParseTask)

config.parse.translation = {
    'expTime': 'EXPTIME',
    'object': 'OBJECT',
    'imageType': 'IMGTYPE',
    'detectorName': '',
    'dateObs': 'DATE-OBS',
    'date': 'DATE-OBS',
    #'seqNum': 'SEQNUM',
}
config.parse.translators = {
    'dayObs': 'translate_dayObs',
    'detector': 'translate_detector',   # set this way as I can't use a default of 0
    'filter': 'translate_filter',       # we have two filter wheels
    'seqNum': 'translate_seqNum',       # an ID valid within a day
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
    'seqNum': 'int',
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
