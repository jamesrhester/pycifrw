all: package documentation
#
package: setup.py sources drel
	python setup.py sdist
	python setup.py bdist_wheel
	python3 setup.py bdist_wheel
#
documentation:
	$(MAKE) -C docs
#
sources:
	$(MAKE) -C src2
	$(MAKE) -C src3
#
drel:
	$(MAKE) -C src2/drel
	$(MAKE) -C src3/drel
