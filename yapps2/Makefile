ALL: $(shell echo *.g examples/*.g | sed s/.g/.py/g )

%.py: %.g yapps2.py yappsrt.py Makefile
	python yapps2.py $<

DOC:	yapps2.ps

yapps2.ps: yapps2.dvi
	dvips -q yapps2.dvi -o yapps2.ps

yapps2.dvi: yapps2.tex
	latex yapps2.tex


DISTRIB:
	cd ..; zip -u yapps2.zip yapps2/{LICENSE,yapps2.py,yappsrt.py,parsedesc.g,examples/*.g,NOTES,yapps2.tex,Makefile}

