# Setup file for automatic installation of the PyCIFRW
# distribution
from distutils.core import setup, Extension

# The compiled scanner for speed

c_scanner = Extension("StarScan",
                      sources = ["lib/lex.yy.c","lib/py_star_scan.c"])

setup(name="PyCifRW",
      version = "3.1.5",
      description = "CIF/STAR file support for Python",
      author = "James Hester",
      author_email = "jrh at anbf2.kek.jp",
      url="http://anbf2.kek.jp/CIF/index.html",
      py_modules = ['CifFile','yapps_compiled_rt','YappsStarParser','StarFile'],
      ext_modules = [c_scanner]
      )
