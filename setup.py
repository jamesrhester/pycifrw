# Setup file for automatic installation of the PyCIFRW
# distribution
from distutils.core import setup

setup(name="PyCifRW",
      version = 2.0,
      description = "CIF file support for Python",
      author = "James Hester",
      author_email = "jrh at anbf2.kek.jp",
      url="http://www.ansto.gov.au/natfac/ANBF/CIF/index.html",
      py_modules = ['CifFile','yappsrt','YappsCifParser'],
      )
