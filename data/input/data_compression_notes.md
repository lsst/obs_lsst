## Notes on how the data compression for test data was done

For the raw data, the pixel arrays were zeroed out and the files were
compressed with gzip.  There is no `gz` extension as we still need the
template strings to work.

For calibrated data, the individual image, mask, and variance planes were
zeroed and then put back into the repository with the appropriate `butler.put`.
This writes the files as tile compressed by default.
