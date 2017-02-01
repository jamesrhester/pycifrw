# Makefile for ANBF Python based Cif handling modules

#
package: CifFile.py StarFile.py Parsers documentation
#	python setup.py bdist_wininst
#
../PyCifRW.tar: clean package
	(cd ..; tar cvf PyCifRW.tar --exclude tests --exclude CVS --exclude yapps2 --exclude error_reports --exclude old_stuff PyCifRW)
#
%.py : %.nw
	notangle $< > $@
#
documentation: CifFile.nw YappsStarParser.nw StarFile.nw
	noweave -html -index -filter l2h CifFile.nw > CifFile.html
	noweave -html -index -filter l2h StarFile.nw > StarFile.html
	noweave -html -index -filter l2h YappsStarParser.nw > YappsStarParser.html
	noweave -html -index -filter l2h TypeContentsParser.nw > TypeContentsParser.html
# 
Parsers: YappsStarParser_STAR2.py YappsStarParser_1_1.py YappsStarParser_1_0.py  TypeContentsParser.py \
	YappsStarParser_2_0.py
	
#
clean: 
	rm -f *.pyc *.g
#
# Note the pythonpath variable as yapps requires its runtime to run
YappsStarParser_1_0.py: YappsStarParser.nw
	notangle -R1.0_syntax YappsStarParser.nw > YappsStarParser_1_0.g
	export PYTHONPATH=.;python ./yapps3/yapps2.py YappsStarParser_1_0.g
#
YappsStarParser_1_1.py: YappsStarParser.nw
	notangle -R1.1_syntax YappsStarParser.nw > YappsStarParser_1_1.g
	export PYTHONPATH=.;python ./yapps3/yapps2.py YappsStarParser_1_1.g
#
YappsStarParser_2_0.py: YappsStarParser.nw
	notangle -RCIF2_syntax YappsStarParser.nw > YappsStarParser_2_0.g
	export PYTHONPATH=.; python ./yapps3/yapps2.py YappsStarParser_2_0.g
#
YappsStarParser_STAR2.py: YappsStarParser.nw
	notangle -RSTAR2_syntax YappsStarParser.nw > YappsStarParser_STAR2.g
	export PYTHONPATH=.; python ./yapps3/yapps2.py YappsStarParser_STAR2.g
#
TypeContentsParser.py: TypeContentsParser.nw
	notangle -RTypeContents_syntax TypeContentsParser.nw > TypeContentsParser.g
	export PYTHONPATH=.; python ./yapps3/yapps2.py TypeContentsParser.g

