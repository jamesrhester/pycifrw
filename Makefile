all: installed documentation
#
installed: package
	pip install -v -v -v --use-wheel dist/PyCifRW-4.1.1-cp27-none-linux_i686.whl
#
package: setup.py sources drel
	python3 setup.py sdist
	python3 setup.py bdist_wheel
#	python setup.py bdist_wininst
#
documentation:
	cd docs;make
#
sources:
	cd pycifrw;make
#
drel:
	cd pycifrw/drel;make
#
