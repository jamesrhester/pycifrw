# Setup file for creation of the PyCIFRW
# distribution
from setuptools import setup, Extension

# The compiled scanner for speed

c_scanner = Extension("CifFile.StarScan",
                      sources = ["pycifrw/lib/lex.yy.c","pycifrw/lib/py_star_scan.c"])

setup(name="PyCifRW",
      version = "4.2.1",
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
	'Topic :: Scientific/Engineering :: Bio-Informatics',
	'Topic :: Software Development :: Libraries :: Python Modules'
      ],
      py_modules = ['CifFile.CifFile','CifFile.yapps3_compiled_rt','CifFile.YappsStarParser_1_1','CifFile.YappsStarParser_1_0',
                    'CifFile.YappsStarParser_STAR2','CifFile.YappsStarParser_2_0','CifFile.StarFile','CifFile.TypeContentsParser'],
      ext_modules = [c_scanner],
      package_dir = {'CifFile':'pycifrw'},
      packages = ['CifFile','CifFile.drel'] 
      )
