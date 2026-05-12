config.maskPlanes.remove("PARTLY_VIGNETTED")
config.maskPlanes.remove("SPIKE")
config.maskPlanes.remove("NOT_DEBLENDED")
config.maskPlanes += ["CROSSTALK"]
config.maskPlanes += ["SENSOR_EDGE"]
