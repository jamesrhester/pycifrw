# make documentation
docs: overview.txt drel_use.txt dict_use.txt
	./pdoc-local --html --overwrite CifFile '[A-Z].*'
	pandoc -f markdown -o overview.html --css markdown4.css -s overview.txt
	pandoc -f markdown -o drel_use.html --css markdown4.css -s drel_use.txt
	pandoc -f markdown -o dict_use.html --css markdown4.css -s dict_use.txt
