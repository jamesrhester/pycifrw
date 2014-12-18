# Setup file for automatic installation of the PyCIFRW
# distribution
from setuptools import setup, Extension

# The compiled scanner for speed

c_scanner = Extension("CifFile.StarScan",
                      sources = ["pycifrw/lib/lex.yy.c","pycifrw/lib/py_star_scan.c"])

setup(name="PyCifRW",
      version = "4.1",
      description = "CIF/STAR file support for Python",
      author = "James Hester",
      author_email = "jamesrhester at gmail.com",
      url="https://bitbucket.org/jamesrhester/pycifrw/overview",
      py_modules = ['CifFile.CifFile','CifFile.yapps3_compiled_rt','CifFile.YappsStarParser_1_1','CifFile.YappsStarParser_1_0',
                    'CifFile.YappsStarParser_STAR2','CifFile.YappsStarParser_2_0','CifFile.StarFile','CifFile.drel.drel_ast_yacc','CifFile.drel.drel_lex',
                    'CifFile.drel.py_from_ast','CifFile.drel.drel_runtime',
                    'CifFile.TypeContentsParser'],
      ext_modules = [c_scanner],
      package_dir = {'CifFile':'pycifrw'},
      packages = ['CifFile'] 
      )
