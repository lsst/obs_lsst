import lsst.meas.extensions.convolved  # noqa: Load flux.convolved algorithm
config.plugins.names.add("ext_convolved_ConvolvedFlux")
config.plugins["ext_convolved_ConvolvedFlux"].seeing.append(8.0)
