from lsst.obs.lsst.ts8 import Ts8ParseTask

config.parse.retarget(Ts8ParseTask)

# what used to be config.parse.translation = {
del config.parse.translation['testType']
del config.parse.translation['filter']
del config.parse.translation['visit']
config.parse.translation['seqNum'] = 'SEQNUM'
config.parse.translation['wavelength'] = 'MONOWL'

# what used to be config.parse.translators = {
del config.parse.translators['raftName']
del config.parse.translators['snap']
config.parse.translators['dayObs'] = 'translate_dayObs'
config.parse.translators['filter'] = 'translate_filter'
config.parse.translators['visit'] = 'translate_visit'

# what used to be config.parse.defaults = {
config.parse.defaults['imageType'] = "UNKNOWN"

config.parse.hdu = 0

# what used to be config.register.columns = {
del config.register.columns['raftName']
del config.register.columns['snap']
del config.register.columns['testType']
config.register.columns['dayObs'] = 'text'
config.register.columns['seqNum'] = 'int'

config.register.unique = ["visit", "detector"]
config.register.visit = list(config.register.columns.keys())
