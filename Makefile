installed: package
	pip install -v -v -v --use-wheel dist/PyCifRW-4.1-cp27-none-linux_i686.whl
#
package: setup.py
	python setup.py sdist
	python setup.py bdist_wheel
#	python setup.py bdist_wininst
