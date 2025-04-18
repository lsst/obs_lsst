# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Utilities and a class to help the camera team use LSST DM camera utilities

Mostly support mapping between amp/ccd/focal plane coordinates, but
also the odd utility function
"""
import lsst.geom as geom
import lsst.afw.cameraGeom as cameraGeom

__all__ = ["LsstCameraTransforms"]


class LsstCameraTransforms():
    """Package up DM's camera geometry in ways useful to the camera team."""
    def __init__(self, camera, detectorName=None):
        r"""Make a new LsstCameraTransforms.

        Parameters
        ----------
        camera : `lsst.afw.cameraGeom.Camera`
            The object describing a/the LSST Camera.
        detectorName : `str`
            A default detector name (e.g. "R12_S01"); used when you don't
            pass a detectorName (None to disable the default detectorName).
        """
        self.camera = camera
        self.__detectorName = detectorName

    def setDetectorName(self, detectorName):
        r"""Set the default detector

        Parameters
        ----------
        detectorName : `str`
            The detector (e.g. "R34_S00") to use when none is passed to a
            method. Set to None to disable the use of a default.
        """

        self.__detectorName = detectorName

    def getDetector(self, detectorName=None):
        r"""Return a specified Detector, or the default Detector.

        Parameters
        ----------
        detectorName : `str`
            Name of detector (or default from setDetectorName() if None).

        Returns
        -------
        detector : `lsst.afw.cameraGeom.Detector`
            The requested detector.
        """

        if detectorName is None:
            detectorName = self.__detectorName

        if detectorName is None:
            raise RuntimeError("Please specify a detector name, "
                               "or set a default with LsstCameraTransforms.setDetectorName()")

        return self.camera[detectorName]

    def ampPixelToCcdPixel(self, ampX, ampY, ampName, detectorName=None):
        r"""Given amplifier coordinate pixel position return pixel
        position on full detector.

        Parameters
        ----------
        ampX : `float`
            column on amp segment.
        ampY : `float`
            row on amp segment.
        ampName : `str`
            Name of amplifier.
        detectorName : `str`
            Name of detector (or default from setDetectorName() if None).

        Notes
        -----
        N.b. all pixel coordinates have the centre of the bottom-left pixel
        at (0.0, 0.0). Also, both amplifier and full detector pixel
        coordinates are trimmed (overscan-free).

        Returns
        -------
        ccdX : `float`
            The column pixel position relative to the corner of the detector.
        ccdY : `float`
            The row pixel position relative to the corner of the detector.
        """

        return ampPixelToCcdPixel(ampX, ampY, self.getDetector(detectorName), ampName)

    def ccdPixelToAmpPixel(self, ccdX, ccdY, detectorName=None):
        r"""Given pixel position within a detector, return the amplifier
        pixel position.

        Parameters
        ----------
        ccdX : `float`
            Column pixel position within detector.
        ccdY : `float`
            Row pixel position within detector.
        detectorName : `str`
            Name of detector (or default from setDetectorName() if None).

        Notes
        -----
        N.b. all pixel coordinates have the centre of the bottom-left pixel
        at (0.0, 0.0). Also, both amplifier and full detector pixel
        coordinates are trimmed (overscan-free).

        Returns
        -------
        ampName: `str`
            Amplifier name, eg. 'C10'
        ampX : `float`
            The column coordinate relative to the corner of the single-amp
            image.
        ampY : `float`
            The row coordinate relative to the corner of the single-amp image.

        Raises
        ------
        RuntimeError
            If the requested pixel doesn't lie on the detector.
        """

        amp, ampXY = ccdPixelToAmpPixel(geom.PointD(ccdX, ccdY), self.getDetector(detectorName))

        ampX, ampY = ampXY
        return amp.getName(), ampX, ampY

    def ccdPixelToFocalMm(self, ccdX, ccdY, detectorName=None):
        r"""Given position within a detector return the focal plane position.

        Parameters
        ----------
        ccdX : `float`
            column pixel position within detector.
        ccdY : `float`
            row pixel position within detector.
        detectorName : `str`
            Name of detector (or default from setDetectorName() if None).

        Notes
        -----
        N.b. all pixel coordinates have the centre of the bottom-left pixel
        at (0.0, 0.0), and CCD columns are taken to be vertical, with "R00"
        in the bottom left of the image.

        Returns
        -------
        focalPlaneX : `float`
            The x-focal plane position (mm) relative to the centre of the
            camera.
        focalPlaneY : `float`
            The y-focal plane position (mm) relative to the centre of the
            camera.
        """
        detector = self.getDetector(detectorName)

        return detector.transform(geom.Point2D(ccdX, ccdY), cameraGeom.PIXELS, cameraGeom.FOCAL_PLANE)

    def ampPixelToFocalMm(self, ampX, ampY, ampName, detectorName=None):
        r"""Given position within an amplifier return the focal plane position.

        ampX : `float`
           column on amp segment.
        ampY : `float`
           row on amp segment.
        ampName: `int`
           Name of amplifier.
        detectorName : `str`
           Name of detector (or default from setDetectorName() if None).

        Notes
        -----
        N.b. all pixel coordinates have the centre of the bottom-left pixel
        at (0.0, 0.0), and CCD columns are taken to be vertical, with "R00"
        in the bottom left of the image.

        Returns
        -------
        focalPlaneX : `float`
            The x-focal plane position (mm) relative to the centre of the
            camera.
        focalPlaneY : `float`
            The y-focal plane position (mm) relative to the centre of the
            camera.

        Raises
        ------
        RuntimeError
            If the requested pixel doesn't lie on the detector.
        """

        detector = self.getDetector(detectorName)

        ccdX, ccdY = ampPixelToCcdPixel(ampX, ampY, detector, ampName)

        return detector.transform(geom.Point2D(ccdX, ccdY), cameraGeom.PIXELS, cameraGeom.FOCAL_PLANE)

    def focalMmToCcdPixel(self, focalPlaneX, focalPlaneY):
        r"""Given focal plane position return the detector position.

        Parameters
        ----------
        focalPlaneX : `float`
            The x-focal plane position (mm) relative to the centre of the
            camera.
        focalPlaneY : `float`
            The y-focal plane position (mm) relative to the centre of the
            camera.

        Notes
        -----
        N.b. all pixel coordinates have the centre of the bottom-left pixel
        at (0.0, 0.0) and CCD columns are taken to be vertical, with "R00" in
        the bottom left of the image.

        Returns
        -------
        detectorName : `str`
            The name of the detector.
        ccdX : `float`
            The column pixel position relative to the corner of the detector.
        ccdY : `float`
            The row pixel position relative to the corner of the detector.

        Raises
        ------
        RuntimeError
            If the requested position doesn't lie on a detector.
        """
        detector, ccdXY = focalMmToCcdPixel(self.camera, geom.PointD(focalPlaneX, focalPlaneY))
        ccdX, ccdY = ccdXY

        return detector.getName(), ccdX, ccdY

    def focalMmToAmpPixel(self, focalPlaneX, focalPlaneY):
        r"""Given a focal plane position plane return the amplifier position.

        Parameters
        ----------
        focalPlaneX : `float`
            The x-focal plane position (mm) relative to the centre of the
            camera.
        focalPlaneY : `float`
            The y-focal plane position (mm) relative to the centre of the
            camera.

        Notes
        -----
        N.b. all pixel coordinates have the centre of the bottom-left pixel
        at (0.0, 0.0) and CCD columns are taken to be vertical, with "R00" in
        the bottom left of the image.

        Returns
        -------
        detectorName : `str`
            The name of the detector.
        ampName: `str`
            The name of the amplifier.
        ampX : `float`
            The physical column coordinate relative to the corner of the
            single-amp image.
        ampY : `float`
            The physical row coordinate relative to the corner of the
            single-amp image.

        Raises
        ------
        RuntimeError
            If the requested position doesn't lie on a detector.
        """

        detector, ccdXY = focalMmToCcdPixel(self.camera, geom.PointD(focalPlaneX, focalPlaneY))
        amp, ampXY = ccdPixelToAmpPixel(ccdXY, detector)

        ampX, ampY = ampXY
        return detector.getName(), amp.getName(), ampX, ampY


def ampPixelToCcdPixel(x, y, detector, ampName):
    r"""Given a position in a raw amplifier return position on full detector.

    Parameters
    ----------
    x : `float`
        physical column on amp segment.
    y : `float`
        physical row on amp segment.
    detector : `lsst.afw.cameraGeom.Detector`
        The requested detector.
    ampName : `str`
        The name of the amplifier.

    Returns
    -------
    ccdX : `float`
        The column pixel position relative to the corner of the detector.
    ccdY : `float`
        The row pixel position relative to the corner of the detector.
    """

    amp = detector[ampName]
    ampBBox = amp.getBBox()
    # Allow for flips (due e.g. to physical location of the amplifiers)
    w, h = ampBBox.getDimensions()
    if amp.getRawFlipX():
        ampBBox.flipLR(w)
        x = w - x - 1

    if amp.getRawFlipY():
        ampBBox.flipTB(h)
        y = h - y - 1

    xyout = amp.getBBox().getBegin() + geom.ExtentD(x, y)

    return xyout


def ccdPixelToAmpPixel(xy, detector):
    r"""Given an position within a detector return position within an
    amplifier.

    Parameters
    ----------
    xy : `lsst.geom.PointD`
        pixel position within detector.
    detector : `lsst.afw.cameraGeom.Detector`
        The requested detector.

    Notes
    -----
    N.b. all pixel coordinates have the centre of the bottom-left pixel
    at (0.0, 0.0).

    Returns
    -------
    amp : `lsst.afw.table.AmpInfoRecord`
        The amplifier that the pixel lies in.
    ampXY : `lsst.geom.PointD`
        The physical pixel coordinate relative to the corner of the
        single-amp image.

    Raises
    ------
    RuntimeError
        If the requested pixel doesn't lie on the detector.
    """
    found = False
    for amp in detector:
        if geom.BoxD(amp.getBBox()).contains(xy):
            found = True
            break

    if not found:
        raise RuntimeError("Point (%g, %g) does not lie on detector %s" % (xy[0], xy[1], detector.getName()))

    x, y = xy - amp.getBBox().getBegin()   # offset from origin of amp's data segment

    # Allow for flips (due e.g. to physical location and orientation
    # of the amplifiers)
    w, h = amp.getBBox().getDimensions()
    if amp.getRawFlipX():
        x = w - x - 1

    if amp.getRawFlipY():
        y = h - y - 1

    xy = geom.ExtentD(x, y)

    return amp, xy


def focalMmToCcdPixel(camera, focalPlaneXY):
    r"""Given an position in the focal plane, return the position on a
    detector.

    Parameters
    ----------
    camera : `lsst.afw.cameraGeom.Camera`
        The object describing a/the LSST Camera.
    focalPlaneXY : `lsst.geom.PointD`
        The focal plane position (mm) relative to the centre of the camera.

    Notes
    -----
    N.b. all pixel coordinates have the centre of the bottom-left pixel
    at (0.0, 0.0) and CCD columns are taken to be vertical, with "R00"
    in the bottom left of the image.

    Returns
    -------
    detector : `lsst.afw.cameraGeom.Detector`
        The requested detector.
    ccdPos : `lsst.geom.Point2D`
        The pixel position relative to the corner of the detector.

    Raises
    ------
    RuntimeError
        If the requested position doesn't lie on a detector.
    """

    for detector in camera:
        ccdXY = detector.transform(focalPlaneXY, cameraGeom.FOCAL_PLANE, cameraGeom.PIXELS)
        if geom.BoxD(detector.getBBox()).contains(ccdXY):
            return detector, ccdXY

    raise RuntimeError("Failed to map focal plane position (%.3f, %.3f) to a detector" % (focalPlaneXY))
