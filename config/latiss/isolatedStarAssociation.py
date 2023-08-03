# Override calibration apertures as appropriate for LATISS plate scale.
config.inst_flux_field='apFlux_35_0_instFlux'

config.extra_columns = [
    'x',
    'y',
    'apFlux_50_0_instFlux',
    'apFlux_50_0_instFluxErr',
    'apFlux_50_0_flag',
    'localBackground_instFlux',
    'localBackground_flag',
]

config.source_selector['science'].flags.bad = [
    'pixelFlags_edge',
    'pixelFlags_interpolatedCenter',
    'pixelFlags_saturatedCenter',
    'pixelFlags_crCenter',
    'pixelFlags_bad',
    'pixelFlags_interpolated',
    'pixelFlags_saturated',
    'centroid_flag',
    'apFlux_35_0_flag',
]

config.source_selector['science'].signalToNoise.fluxField = 'apFlux_35_0_instFlux'
config.source_selector['science'].signalToNoise.errField = 'apFlux_35_0_instFluxErr'
