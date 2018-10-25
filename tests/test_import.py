"""Test that the code in this package can be imported."""

import unittest
import lsst.obs.lsst
import lsst.obs.lsst.auxTel
import lsst.obs.lsst.ts8
import lsst.obs.lsst.phosim
import lsst.obs.lsst.imsim


class ImportTest(unittest.TestCase):
    def testImport(self):
        self.assertTrue(hasattr(lsst.obs.lsst, "__version__"))


if __name__ == "__main__":
    unittest.main()
