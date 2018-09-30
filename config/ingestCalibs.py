from lsst.obs.lsst.ingest import LsstCamCalibsParseTask
config.parse.retarget(LsstCamCalibsParseTask)

config.register.columns = {'filter': 'text',
                           'raftName': 'text',
                           'detectorName': 'text',
                           'detector': 'int',
                           'calibDate': 'text',
                           'validStart': 'text',
                           'validEnd': 'text',
                           }

config.register.detector = ['filter', 'detector']

config.parse.translators = {'detector': 'translate_detector',
                            'raftName': 'translate_raftName',
                            'detectorName': 'translate_detectorName',
                            'filter': 'translate_filter',
                            'calibDate': 'translate_calibDate',
                            }

config.register.unique = ['filter', 'detector', 'calibDate']
config.register.tables = ['bias', 'dark', 'flat', 'fringe']
config.register.visit = ['calibDate', 'filter']
