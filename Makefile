#binary_sources = src2/lib/lex.yy.c src2/lib/star_scanner.h src2/lib/py_star_scan.c \
#                 src3/lib/lex.yy.c src3/lib/star_scanner.h src3/lib/py_star_scan.c

all: package documentation
#
package: lib setup.py sources drel
	python setup.py sdist
	python3 setup.py sdist
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
#
lib: 
	$(MAKE) -C src2/lib
	$(MAKE) -C src3/lib
#
clean:
	$(MAKE) -C src2/lib clean
