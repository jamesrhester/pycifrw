# Makefile for ANBF Python based Cif handling modules

#
package: py_from_ast.py drel_runtime.py
#
%.py : %.nw
	notangle $< > $@
#
documentation: py_from_ast.nw 
	noweave -html -index -filter l2h py_from_ast.nw > py_from_ast.html
# 
clean: 
	rm -f *.pyc
#
