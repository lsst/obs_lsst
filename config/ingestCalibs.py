from lsst.obs.lsstCam.ingest import LsstCamCalibsParseTask
config.parse.retarget(LsstCamCalibsParseTask)

config.register.columns = {'filter': 'text',
                           'raft': 'text',
                           'ccd': 'text',
                           'calibDate': 'text',
                           'validStart': 'text',
                           'validEnd': 'text',
                           }

config.parse.translators = {'ccd': 'translate_ccd',
                            'raft': 'translate_raft',
                            'filter': 'translate_filter',
                            'calibDate': 'translate_calibDate',
                            }

config.register.unique = ['filter', 'raft', 'ccd', 'calibDate']
config.register.tables = ['bias', 'dark', 'flat', 'fringe']
config.register.visit = ['calibDate', 'filter']
