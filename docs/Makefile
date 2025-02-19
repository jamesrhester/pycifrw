# make documentation
docs: overview.txt drel_use.txt dict_use.txt
	pdoc -o . --no-include-undocumented CifFile CifFile.StarFile CifFile.drel !CifFile.Yapps
	pandoc -f markdown -o overview.html --css markdown4.css -s overview.txt
	pandoc -f markdown -o drel_use.html --css markdown4.css -s drel_use.txt
	pandoc -f markdown -o dict_use.html --css markdown4.css -s dict_use.txt

clean:
	rm -rf CifFile overview.html drel_use.html dict_use.html
