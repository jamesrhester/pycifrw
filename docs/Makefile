# make documentation
docs: documentation.txt
	./pdoc-local --html --overwrite CifFile '[A-Z].*'
	pandoc -f markdown -o overview.html --css markdown4.css -s
