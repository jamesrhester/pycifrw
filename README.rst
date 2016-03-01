PyCIFRW Readme
==============

Introduction
------------

PyCIFRW provides support for reading and writing CIF (Crystallographic
Information Format) files using Python.  It was developed at the
Australian National Beamline Facility (ANBF), run by the Australian
Synchrotron Research Program (ASRP), as part of a larger project to
provide CIF input/output capabilities for data collection.  It is
currently (Mar 2016) maintained and developed by James Hester
with support from the Australian Nuclear Science and Technology 
Organisation (ANSTO).

Conformance
-----------

The CIF 1.1 and 2.0 working specifications were used as a reference.

PyCifRW has been tested on the IUCr sample CIF trip files located at
http://www.iucr.org/iucr-top/cif/developers/trip and fails or 
successfully reads as it is supposed to (note that ciftest5 contains
characters now forbidden in CIFs).   

Supported Platforms
-------------------

PyCIFRW is written entirely in Python.  While this makes parsing of large
CIF files rather slow, it should run wherever Python runs.  The latest version
has been tested on Linux and Windows 7.

The source code of a C extension module is also included in the distribution.
This module accelerates CIF file reading. From time to time 
system-dependent installation packages are generated containing precompiled
versions of this module. 

Installation
------------

See file INSTALLATION

Use
---

See the various files in the docs directory for details of the interface.  
Essentially, CIF files look like python dictionaries, with each 
entry in the dictionary corresponding to a data block.  The blocks 
themselves are also dictionaries, with each data name being a 
single entry in the dictionary, so for example,
cf['si_std']['_diffrn_meas_wavelength'] will return the value of 
_diffrn_meas_wavelength in the data block named si_std of the Cif file object
cf.


Example
-------

To read in a CIF:

    from CifFile import CifFile
    cf = CifFile.ReadCif('jun_01_2.cif')

to access information in a CIF

    wav = cf['si_std']['_diffrn_meas_wavelength']

to set a value

    cf['si_std']['_diffrn_meas_wavelength'] = 1.54


Extra programs
--------------

The "Programs" directory contains program "validate_cif.py" which
validates a data files against data dictionaries.  Execute this file
without arguments for a help message.
