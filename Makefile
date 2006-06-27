# Makefile for ANBF Python based Cif handling modules

#
package: CifFile.py StarFile.py YappsStarParser.py documentation
	python setup.py sdist
	python setup.py bdist
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
# 
clean: 
	rm -f *.pyc *.g
#
YappsStarParser.py: YappsStarParser.nw
	notangle YappsStarParser.nw > YappsStarParser.g
	python ./yapps2/yapps2.py YappsStarParser.g
#
