# Setup file for automatic installation of the PyCIFRW
# distribution
from distutils.core import setup

setup(name="PyCifRW",
      version = 3.0,
      description = "CIF/STAR file support for Python",
      author = "James Hester",
      author_email = "jrh at anbf2.kek.jp",
      url="http://anbf2.kek.jp/CIF/index.html",
      py_modules = ['CifFile','yappsrt','YappsStarParser','StarFile'],
      )
