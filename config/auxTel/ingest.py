from lsst.obs.lsst.auxTel import AuxTelParseTask

config.parse.retarget(AuxTelParseTask)

del config.parse.translation['testType']

del config.parse.translators['run']
del config.parse.translators['raftName']
del config.parse.translators['lsstSerial']
del config.parse.translators['snap']

config.parse.translators['dayObs'] = 'translate_dayObs'
config.parse.translators['seqNum'] = 'translate_seqNum'

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
