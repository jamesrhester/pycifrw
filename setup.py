# Setup file for creation of the PyCIFRW
# distribution
from __future__ import print_function

from setuptools import setup, Extension
from sys import version_info

if version_info.major >= 3:
    print ("Python 3 setup")
    c_scanner = Extension("CifFile.StarScan",
                      sources = ["src3/lib/lex.yy.c","src3/lib/py_star_scan.c"])
    package_dir = {'CifFile':'src3'}
else:
    print ("Python 2 setup")
    # The compiled scanner for speed

    c_scanner = Extension("CifFile.StarScan",
                      sources = ["src2/lib/lex.yy.c","src2/lib/py_star_scan.c"])
    package_dir = {'CifFile':'src2'}

#### Do the setup

setup(name="PyCifRW",
      version = "4.2.3",
      description = "CIF/STAR file support for Python",
      author = "James Hester",
      author_email = "jamesrhester at gmail.com",
      license = 'Python 2.0',
      url="https://bitbucket.org/jamesrhester/pycifrw/overview",
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
      py_modules = ['CifFile.CifFile','CifFile.yapps3_compiled_rt','CifFile.YappsStarParser_1_1','CifFile.YappsStarParser_1_0',
                    'CifFile.YappsStarParser_STAR2','CifFile.YappsStarParser_2_0','CifFile.StarFile','CifFile.TypeContentsParser'],
      ext_modules = [c_scanner],
      package_dir = package_dir,
      packages = ['CifFile', 'CifFile.drel'],
      test_suite = 'TestPyCifRW'
      )

