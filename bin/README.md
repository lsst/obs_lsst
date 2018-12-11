You need the raw data; it's currently [here](https://github.com/lsst-dm/testdata_obs_lsst).

To run the complete test suite, say

    runPipeline --raw $TESTDATA_OBS_LSST_DIR/raws --dir [path_to_work_dir]

Where you can optionally specify a list of cameras.

This is equivalent to

    ingest --raw $TESTDATA_OBS_LSST_DIR/raws --dir [path_to_work_dir]
    createCalibs
    runIsr
    processCcd
