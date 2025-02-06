# Makefile for Python based Cif handling modules

# Customizable variables:
#
# Instance of Python to be used for the yapps2.py script.
PYTHON = python3
# Local helper variables:
#
# Command to execute the yapps2.py script.  Note it sets the PYTHONPATH
# environment variable as yapps requires our modified runtime to run.
YAPPS2CMD = PYTHONPATH=. $(PYTHON) -X utf8 ./yapps3/yapps2.py

package: CifFile_module.py StarFile.py Parsers
#
#%.py : %.nw
#	nountangle -awk $< > $@
#
%.py : %.g
	$(YAPPS2CMD) $<

Parsers: YappsStarParser_STAR2.py YappsStarParser_1_1.py YappsStarParser_1_0.py  TypeContentsParser.py \
	YappsStarParser_2_0.py

#
clean:
	rm -f *.pyc
	rm -f YappsStarParser_*.py TypeContentsParser.py
