# Setup file for creation of the PyCIFRW
# distribution
from __future__ import print_function

from setuptools import setup, Extension, find_packages

#### Do the setup
c_scanner = Extension("CifFile.StarScan",
            sources = ["src/lib/lex.yy.c","src/lib/py_star_scan.c"])

setup(name="PyCifRW",
      version = "5.0.1",
      description = "CIF/STAR file support for Python",
      author = "James Hester",
      author_email = "jamesrhester@gmail.com",
      license = 'Python 2.0',
      url="https://github.com/jamesrhester/pycifrw/blob/development/README.md",
      classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: Python Software Foundation License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 2',
          'Topic :: Scientific/Engineering :: Bio-Informatics',
          'Topic :: Software Development :: Libraries :: Python Modules'
      ],
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
