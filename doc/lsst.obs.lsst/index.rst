.. py:currentmodule:: lsst.obs.lsst

.. _lsst.obs.lsst:

#############
lsst.obs.lsst
#############

The ``obs_lsst`` module defines LSST camera specific configuration.

.. Add subsections with toctree to individual topic pages.

.. _lsst.obs.lsst-contributing:

Contributing
============

``lsst.obs.lsst`` is developed at https://github.com/lsst/obs_lsst.
You can find Jira issues for this module under the `obs_lsst <https://jira.lsstcorp.org/issues/?jql=project%20%3D%20DM%20AND%20component%20%3D%20obs_lsst>`_ component.

.. toctree::
   :maxdepth: 1

   adding-a-camera.rst
   testing.rst

.. _lsst.obs.lsst-scripts:

Command Line Scripts
====================

.. autoprogram:: lsst.obs.lsst.script.generateCamera:build_argparser()
  :prog: generateCamera.py
  :groups:

.. autoprogram:: lsst.obs.lsst.script.rewrite_ts8_qe_files:build_argparser()
  :prog: rewrite_ts8_qe_files.py
  :groups:

.. _lsst.obs.lsst-pyapi:

Python API reference
====================

.. automodapi:: lsst.obs.lsst
   :no-main-docstr:
.. automodapi:: lsst.obs.lsst.testHelper
   :no-main-docstr:
.. automodapi:: lsst.obs.lsst.utils
   :no-main-docstr:
.. automodapi:: lsst.obs.lsst.translators
   :no-main-docstr:
