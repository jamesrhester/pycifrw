# Makefile for ANBF Python based Cif handling modules

#
package: CifFile.py kwCifParse.py documentation
#
../PyCifRW.tar: clean package
	(cd ..; tar cvf PyCifRW.tar --exclude tests --exclude CVS PyCifRW)
#
documentation: CifFile.nw kwCifParse.nw
	noweave -html -index -filter l2h CifFile.nw > CifFile.html
	noweave -html -index -filter l2h kwCifParse.nw > kwCifParse.html
# 
CifFile.py: CifFile.nw kwCifParse.py
	notangle CifFile.nw > CifFile.py
#
kwCifParse.py: kwCifParse.nw kjCParseBuild.py kjCParser.py
	notangle kwCifParse.nw > kwCifParse.py
#
xfiles.py: xfiles.nw CifFile.py
	notangle xfiles.nw > xfiles.py
#
install: package
	install kjCParseBuild.py kjCParser.py kjSet.py CifFile.py kwCifParse.py /usr/local/lib/python1.5/site-packages/ANBF/PyCifRW
	install kjCParseBuild.py kjCParser.py CifFile.py kjSet.py kwCifParse.py /usr/local/lib/python2.0/site-packages/ANBF/PyCifRW
#
clean: 
	rm *.pyc
