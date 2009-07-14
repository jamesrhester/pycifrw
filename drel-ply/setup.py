# Setup file for automatic installation of the dREL parser 
# distribution
from setuptools import setup, Extension

setup(name="dREL-ply",
      version = "0.5",
      description = "Conversion from dREL to python",
      author = "James Hester",
      author_email = "jamesrhester at gmail.com",
      url="http://pycifrw.berlios.de",
      py_modules = ['drel_yacc','drel_lex'],
      install_requires = ['ply>=2.5']
      )
