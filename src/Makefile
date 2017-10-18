# Makefile for Python based Cif handling modules

# Customizable variables:
#
# Instance of Python to be used for the yapps2.py script.
PYTHON = python2

package: CifFile_module.py StarFile.py Parsers documentation
#
%.py : %.nw
	notangle $< > $@
#
documentation: CifFile_module.nw YappsStarParser.nw StarFile.nw
	noweave -html -index -filter l2h CifFile_module.nw > CifFile.html
	noweave -html -index -filter l2h StarFile.nw > StarFile.html
	noweave -html -index -filter l2h YappsStarParser.nw > YappsStarParser.html
	noweave -html -index -filter l2h TypeContentsParser.nw > TypeContentsParser.html
#
Parsers: YappsStarParser_STAR2.py YappsStarParser_1_1.py YappsStarParser_1_0.py  TypeContentsParser.py \
	YappsStarParser_2_0.py

#
clean:
	rm -f *.pyc *.g
	rm -f YappsStarParser_*.py TypeContentsParser.py

# Local helper variables:
#
# Command to execute the yapps2.py script.  Note it sets the PYTHONPATH
# environment variable as yapps requires its runtime to run.
YAPPS2CMD = PYTHONPATH=. $(PYTHON) ./yapps3/yapps2.py

YappsStarParser_1_0.py: YappsStarParser.nw
	notangle -R1.0_syntax YappsStarParser.nw > YappsStarParser_1_0.g
	$(YAPPS2CMD) YappsStarParser_1_0.g
#
YappsStarParser_1_1.py: YappsStarParser.nw
	notangle -R1.1_syntax YappsStarParser.nw > YappsStarParser_1_1.g
	$(YAPPS2CMD) YappsStarParser_1_1.g
#
YappsStarParser_2_0.py: YappsStarParser.nw
	notangle -RCIF2_syntax YappsStarParser.nw > YappsStarParser_2_0.g
	$(YAPPS2CMD) YappsStarParser_2_0.g
#
YappsStarParser_STAR2.py: YappsStarParser.nw
	notangle -RSTAR2_syntax YappsStarParser.nw > YappsStarParser_STAR2.g
	$(YAPPS2CMD) YappsStarParser_STAR2.g
#
TypeContentsParser.py: TypeContentsParser.nw
	notangle -RTypeContents_syntax TypeContentsParser.nw > TypeContentsParser.g
	$(YAPPS2CMD) TypeContentsParser.g
