# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.

config.isr.doCrosstalk=True
config.isr.doBrighterFatter = True
config.isr.doWrite = False

# Additional configs for star+galaxy ref cats now that DM-17917 is merged
config.calibrate.astrometry.referenceSelector.doUnresolved = True
config.calibrate.astrometry.referenceSelector.unresolved.name = 'resolved'
config.calibrate.astrometry.referenceSelector.unresolved.minimum = None
config.calibrate.astrometry.referenceSelector.unresolved.maximum = 0.5

# Make sure galaxies are not used for zero-point calculation.
config.calibrate.photoCal.match.referenceSelection.doUnresolved = True
config.calibrate.photoCal.match.referenceSelection.unresolved.name = 'resolved'
config.calibrate.photoCal.match.referenceSelection.unresolved.minimum = None
config.calibrate.photoCal.match.referenceSelection.unresolved.maximum = 0.5

# DM-17043 and DM-16785
config.charImage.measurePsf.starSelector["objectSize"].doFluxLimit = False
config.charImage.measurePsf.starSelector["objectSize"].doSignalToNoiseLimit = True
config.charImage.measurePsf.starSelector["objectSize"].signalToNoiseMin = 20

# Discussed on Slack #desc-dm-dc2 with Lauren and set to 200 for Run2.1i
# For Run2.2i, setting to zero per https://github.com/LSSTDESC/ImageProcessingPipelines/issues/136
config.charImage.measurePsf.starSelector["objectSize"].signalToNoiseMax = 0

# S/N cuts for computing aperture corrections.
config.charImage.measureApCorr.sourceSelector['science'].doFlags = True
config.charImage.measureApCorr.sourceSelector['science'].doSignalToNoise = True
config.charImage.measureApCorr.sourceSelector['science'].flags.good = ['calib_psf_used']
config.charImage.measureApCorr.sourceSelector['science'].flags.bad = []
config.charImage.measureApCorr.sourceSelector['science'].signalToNoise.minimum = 150.0
config.charImage.measureApCorr.sourceSelector['science'].signalToNoise.maximum = None
config.charImage.measureApCorr.sourceSelector['science'].signalToNoise.fluxField = 'base_PsfFlux_instFlux'
config.charImage.measureApCorr.sourceSelector['science'].signalToNoise.errField = 'base_PsfFlux_instFluxErr'
config.charImage.measureApCorr.sourceSelector.name = 'science'

# S/N cuts for zero-point calculation
config.calibrate.photoCal.match.sourceSelection.doSignalToNoise = True
config.calibrate.photoCal.match.sourceSelection.signalToNoise.minimum = 150
config.calibrate.photoCal.match.sourceSelection.signalToNoise.fluxField = 'base_PsfFlux_instFlux'
config.calibrate.photoCal.match.sourceSelection.signalToNoise.errField = 'base_PsfFlux_instFluxErr'
