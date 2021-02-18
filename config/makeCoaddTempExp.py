import os.path

# Gen3 makeWarp Gen3 supersede makeCoaddTempExp.
# Keep in sync in the meantime
config.load(os.path.join(os.path.dirname(__file__), "makeWarp.py"))
