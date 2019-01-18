# obs_lsst
A repository to hold the description for the LSST 3.2 GPix camera and other cameras which
use LSST CCDs

This package includes metadata translator plugins for the
`astro_metadata_translator` package. To see the translated header of a file
use the `-p` option to register the plugins.

For example:
```
$ translate_header.py -p lsst.obs.lsst.translators data/
```
will report translations of all the files in this repository.
