from lsst.obs.lsst.phosim import PhosimParseTask

config.parse.retarget(PhosimParseTask)
#
# Workaround problems in the phosim headers
#

# FILTER seems to be random junk for the corner rafts 
del config.parse.translation['filter']
config.parse.translators['filter'] = 'translate_filter'

# OBSID is a string, not an it
del config.parse.translation['visit']
config.parse.translators['visit'] = 'translate_visit'
