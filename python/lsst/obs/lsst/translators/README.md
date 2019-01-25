# Metadata translation code for obs_lsst

This directory contains the translator plugins for the
[astro_metadata_translator](https://github.com/lsst/astro_metadata_translator)
package.  The plugins follow the coding style of astro_metadata_translator
rather than the coding style of `obs_lsst`.  The intent is for these plugins
to be transferrable out of this package and integrated into
`astro_metadata_translator` when they become stable.

In order to enable that future migration the license associated with the
code in this directory uses a BSD 3 clause license to match that used in
`astro_metadata_translator`.  It does not use the GPLv3 license that is
used by the rest of the `obs_lsst` package.
