PyCIFRW Readme
--------------

Introduction
------------

PyCIFRW provides support for reading and writing CIF (Crystallographic
Information Format) files using Python.  It was developed at the
Australian National Beamline Facility (ANBF), run by the Australian
Synchrotron Research Program (ASRP), as part of a larger project to
provide CIF input/output capabilities for data collection.  It is
now (Feb 2025) maintained and developed within the Australian Nuclear Science and
Technology Organisation (ANSTO). Outside contributions are very
welcome.

Conformance
-----------

The specifications found in Vol G of the International Tables for
Crystallography were used as a reference for CIF 1.0/1.1 syntax.
http://dx.doi.org/10.1107/S1600576715021871 was used as the CIF 2.0
reference.

PyCifRW has been tested on the IUCr sample CIF1.1 trip files located at
http://www.iucr.org/iucr-top/cif/developers/trip and fails or
successfully reads as it is supposed to (note that `ciftest5` contains
characters now forbidden in CIFs).

Supported Platforms
-------------------

PyCIFRW is written entirely in Python, and so should run wherever
Python runs.  Any failures on Mac, Windows or Linux should be
communicated to the author, either through the Github issues
tracker (http://github.com/jamesrhester/pycifrw/issues) or email.

The source code of a C extension module is also included in the
distribution. 

Installation
------------

See file [INSTALLATION](https://github.com/jamesrhester/pycifrw/blob/development/INSTALLATION).

License
----------

PyCIFRW is made available using the Python 2.0 license.  The full text is [here](https://github.com/jamesrhester/pycifrw/blob/development/LICENSE)

Use
---

See the various files in the docs directory for details of the interface.
Essentially, CIF files look like python dictionaries, with each
entry in the dictionary corresponding to a data block.  The blocks
themselves are also dictionaries, with each data name being a
single entry in the dictionary, so for example,
`cf['si_std']['_diffrn_meas_wavelength']` will return the value of
`_diffrn_meas_wavelength` in the data block named `si_std` of the Cif file object
`cf`.

Example
-------

To read in a CIF:

    from CifFile import ReadCif
    cf = ReadCif('jun_01_2.cif')

to access information in a CIF

    wav = cf['si_std']['_diffrn_meas_wavelength']

to set a value

    cf['si_std']['_diffrn_meas_wavelength'] = 1.54


Example programs
----------------

The file 'TestPyCIFRW.py' in the source distribution contains around 180 tests
of PyCIFRW functionality and is a good source of examples for using both simple
and advanced PyCIFRW interfaces.

The "Programs" directory in the source distribution contains simple example programs.
Of interest are `validate_cif.py` which validates a data file against data dictionaries
(execute this file at a terminal prompt without arguments for a help message)
and `output_asciidoc.py` which will convert a DDLm dictionary into an
asciidoc document that can then be converted to HTML or other presentation
formats.
