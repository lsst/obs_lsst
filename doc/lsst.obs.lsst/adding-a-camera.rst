.. _obs_lsst_adding_camera:

Adding a new camera
===================

The ``policy`` directory in the ``obs_lsst`` package contains the files
needed to describe cameras made up of LSST chips. The eventual goal is
to describe the real camera, but for now we also have variants to handle
LATISS data, phosim and imsim simulations (they differ in e.g., the gain and
crosstalk values) and data from various test stands.

Eventually this configuration data will be moved out of
the obs package and into the calibration registry, which will allow us
to track evolution of the system (including replacing failed rafts – not
that that’s going to happen).

The basic strategy is that the ``SConscript`` file in the directory
assembles a suitable ``camera.yaml`` file (e.g. ``phosim.yaml``) and we put
the appropriate entry in the ``_mapper`` file in the data repository.

To add a new camera (e.g., ``fooCam``, made up of 9 CCDs in a single
“raft” – call it ``RXX`` for now):

-  Add a directory ``policy/fooCam``
-  Put a file ``rafts.yaml`` in that directory describing RXX (you can
   start with ``policy/rafts.yaml``).
-  Put a file ``RXX.yaml`` in policy/fooCam (you can start with
   ``policy/lsstCam/R11.yaml``). Note that you can choose an ITL or E2V
   device. Note that you must provide a serial number for each CCD in
   the raft as that’s how I know how many CCDs there are in the “raft”
   (e.g. LATISS has only one)

   The geometryWithinRaft field may be omitted, in which case offsets
   default to 0.0 and the yaw entry is not generated.  These offsets
   are interpreted relative to the nominal positions given in cameraHeader.yaml
   for each type of raft, as adjusted for the centre of the raft; these
   values are therefore reasonable.  (Note that offsets here and elsewhere may
   either be specified as 2-tuples, in which case the z-offset is inferred to be
   0.0, or directly as 3-tuples with their z-offset explicit).

   The yaw (rotation in the plane of the detector) is measured in degrees,
   anticlockwise as shown in cameraGeomUtils.plotFocalPlane (i.e. with ``R00`` in
   the bottom left, and ``R04`` in the bottom right)

-  If you want to add a camera-specific set of transformations, put a
   file ``cameraTransforms.yaml`` in ``policy/fooCam``. Look at the one
   in ``policy/cameraTransforms.yaml`` for inspiration.
-  If you’re plagued by crosstalk, put a file ``ccdData.yaml`` in
   ``policy/fooCam``. Look at the one in ``policy/phosim`` for the
   format – basically a dict crosstalk indexed by the CCD type. There
   are 256 coefficients (16 amplifiers and 256 == 16^2), and we assume
   for now that all CCDs from a given vendor are the same (but the fix
   to ``bin.src/generateCamera.py`` to handle per-CCD coefficients would
   be easy)
-  Edit ``policy/SConscript`` to add your new camera “fooCam” to the
   ``for camera in ...`` loop. note the magic ``--path`` options – it
   tells the code to use your data in fooCam to override lsstCam values.
   This is why there’s no imsim directory and phosim only contains the
   crosstalk coefficients; they take almost everything from
   :literal:`policy/`` and`\ policy/lsstCam\`
-  run ``scons`` in the ``obs_lsst`` directory (or ``scons -u`` in
   policy)
-  add ``fooCam.yaml`` to ``policy/.gitignore``
-  Write a header translator for your instrument. This should be placed in
   ``python/lsst/obs/lsst/translators/fooCam.py``. You can follow the examples
   from other translators there.  Remember to add the new file to
   ``python/lsst/obs/lsst/translators/__init__.py``.
   You can test the translator by running

   .. code-block:: bash

      translate_header.py -p lsst.obs.lsst.translators testfile.fits

   The translators must define the properties specified and defined by
   `~astro_metadata_translator.ObservationInfo`.
   Pay careful attention to how you decide to define ``detector_group``
   and ``detector_name``.  You can read your detector IDs out of the camera
   YAML file once it's created or hard code them into your translator.
-  You will probably also want to copy e.g., ``config/latiss/latiss.py``
   to ``config/fooCam/fooCam.py`` and also files such as
   ``config/latiss/bias.py`` – don’t forget to modify them to import
   ``fooCam.py``!
-  Add a `~lsst.obs.base.Instrument` definition to ``python/lsst/obs/lsst/_instrument.py``.
   You can copy one of the other instrument definitions to suit your needs.
   This tells the butler how to understand this instrument.
-  Add test data and associated unit tests following the instructions in
   :ref:`obs_lsst_testing`.

If these instructions are complete and correct you are good to go. Once
you’re happy commit all your changes to a branch git, and push, and make
a pull request.

We would ideally like to be able to run the integration tests to include
the new camera.  To enable this please also add some test data to the
`testdata_lsst <https://github.com/lsst/testdata_lsst>`_ repository,
and update the `ci_lsst <https://github.com/lsst-dm/ci_lsst>`_ package so that
the new instrument is included in the integration test.
