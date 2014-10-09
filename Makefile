installed: package
	pip install --use-wheel dist/PyCifRW-4.05-cp27-none-linux_i686.whl
#
package: setup.py
	python setup.py sdist
	python setup.py bdist_wheel
#	python setup.py bdist_wininst
