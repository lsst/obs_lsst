You need the raw data; it's currently in
    /project/rhl/Data/ci_lsst_rawUningested

To run the complete test suite, say
   runPipeline --raw /project/rhl/Data/ci_lsst_rawUningested
Where you can optionally specify a list of cameras.

This is equivalent to
   ingest --raw /project/rhl/Data/ci_lsst_rawUningested
   createCalibs
   runIsr
   processCcd
