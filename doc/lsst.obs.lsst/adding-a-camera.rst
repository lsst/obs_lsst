.. _obs_lsst_adding_camera:

Adding a new camera
===================

The ``policy`` directory in the ``obs_lsst`` package contains the files
needed to describe cameras made up of LSST chips. The eventual goal is
to describe the real camera, but for now we also have variants to handle
AuxTel data, phosim and imsim simulations (they differ in e.g., the gain and
crosstalk values) and data from various test stands.

Once Butler Gen3 is ready this configuration data will be moved out of
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
   (e.g. auxTel has only one)
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
-  Create a new file ``python/lsst/obs/lsst/fooCam.py`` (see
   ``auxTel.py`` for an example)

   Add a class ``FooCamMapper`` to the same file, setting a class-level
   string ``_cameraName`` to “fooCam”. You also need to specify the metadata
   translation class to use such as ``LsstFooCamTranslator``. Look at the example in
   ``python/lsst/obs/lsst/auxTel/auxTel.py`` – you’ll see that this
   overrides some entries in ``lsstCamMapper.yaml`` (in the class data
   member ``yamlFileList``) with ``auxTelMapper.yaml``. If you want to
   provide your own templates you’ll need to do the same thing, adding a
   file ``policy/fooCam/fooCamMapper.yaml``

   The name you provided as ``_cameraName`` is also used to e.g.,
   provide per-camera configuration files (for example
   ``config/auxTel/ingest.py``)

   Don’t forget to add ``FooCamMapper`` to ``__all__``
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
   ``exposure_id`` and ``detector_exposure_id`` should be written in such
   a way that they can be called from the mapper class to allow the values
   to be determined from dataIds.
-  Add a ``FooCamParseTask`` to ``python/lsst/obs/lsst/fooCam.py``.
   It’ll need to set a class variable ``_mapperClass = FooCamMapper`` and
   also a class variable ``_translatorClass = LsstFooCamTranslator`` (the same
   class as used in the mapper).  Most of the metadata translations are
   inherited from the base class so you only need to add translations here
   if you are adding something non-standard.
   Don’t forget to add ``FooCamParseTask`` to ``__all__``
-  Put a ``_mapper`` file in the root of your repository, containing
   ``lsst.obs.lsstCam.fooCam.FooCamMapper``
-  Retarget ``config.parse`` in ``config/fooCam/ingest.py`` to
   ``FooCamParseTask``
-  You will probably also want to copy e.g., ``config/auxTel/auxTel.py``
   to ``config/fooCam/fooCam.py`` and also files such as
   ``config/auxTel/bias.py`` – don’t forget to modify them to import
   ``fooCam.py``!
-  Add ``FooCam.yaml`` to ``policy/.gitignore``
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
