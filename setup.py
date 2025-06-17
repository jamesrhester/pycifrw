# Setup file for creation of the PyCIFRW
# distribution
from __future__ import print_function

from setuptools import setup, Extension, find_packages

#### Do the setup
c_scanner = Extension("CifFile.StarScan",
            sources = ["src/lib/lex.yy.c","src/lib/py_star_scan.c"])

setup(name="PyCifRW",
      py_modules = ['CifFile.CifFile_module','CifFile.yapps3_compiled_rt','CifFile.YappsStarParser_1_1','CifFile.YappsStarParser_1_0',
                    'CifFile.YappsStarParser_STAR2','CifFile.YappsStarParser_2_0','CifFile.StarFile','CifFile.TypeContentsParser',
                    'CifFile.cif_files_validator'],
      ext_modules = [c_scanner],
      packages = ['CifFile', 'CifFile.drel'],
      test_suite = 'TestPyCIFRW',
      package_dir = {'CifFile':'src'},
      install_requires = [
          "prettytable",
          "ply",
          "numpy"
      ]
      )
