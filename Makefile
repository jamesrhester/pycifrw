# Makefile for ANBF Python based Cif handling modules

#
package: CifFile.py #documentation
#
../PyCifRW.tar: clean package
	(cd ..; tar cvf PyCifRW.tar --exclude tests --exclude CVS --exclude yapps2 --exclude error_reports --exclude old_stuff PyCifRW)
#
documentation: CifFile.nw YappsCifParser.nw
	noweave -html -index -filter l2h CifFile.nw > CifFile.html
	noweave -html -index -filter l2h YappsCifParser.nw > YappsCifParser.html
# 
CifFile.py: CifFile.nw YappsCifParser.py
	notangle CifFile.nw > CifFile.py
#
YappsCifParser.py: YappsCifParser.nw
	notangle YappsCifParser.nw > YappsCifParser.g
	python ./yapps2/yapps2.py YappsCifParser.g
#
xfiles.py: xfiles.nw CifFile.py
	notangle xfiles.nw > xfiles.py
#
install: package
	install CifFile.py YappsCifParser.py yappsrt.py /usr/lib/python2.0/site-packages/ANBF/PyCifRW
#
clean: 
	rm -f *.pyc *.g
