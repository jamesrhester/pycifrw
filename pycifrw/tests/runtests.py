#  Run files in the list, and catch any expected exceptions
import sys
from CifFile import *
from StarFile import *

def runtests(scantype):
    test_table = [
    ["ciftest1", "OK"],
    ["ciftest2", "OK"],
    ["ciftest3", "OK"],
    ["ciftest4", "OK"],
    ["ciftest5", "OK"],
    ["ciftest6", [CifError,StarError]],
    ["ciftest7", [CifError,StarError]],
    ["ciftest8", [CifError,StarError]],
    ["ciftest9", [CifError,StarError]],
    ["ciftest10", [CifError,StarError]],
    ["ciftest11", "OK"],
    ["ciftest12", "OK"],
    ["ciftest13", "OK"],
    ["ciftest14", [CifError,StarError]],
    ["ciftest15", [CifError,StarError]],
    ["ciftest16", [CifError,StarError]],
    ["ciftest17", [CifError,StarError]],
    ["ciftest18", [CifError,StarError]]
    ]

    for filename, testresult in test_table:
        try:
        	ReadCif(filename,scantype=scantype)
        except:
        	if testresult == 'OK':
           	    print "%s causes error where none expected" % filename
	            print "%s\n%s" % (`sys.exc_type`,sys.exc_value)
        	else:
        	    if sys.exc_type in testresult:
        		print "%s passes" % filename
		    else:
			print "Unexpected exception %s for %s" % (`sys.exc_type`,filename)
        else:     #no exception
        	if testresult == 'OK':
        	    print "%s passes" % filename
        	else:
        	    print "%s: Expected %s, got nothing" % (filename,`testresult`)
if __name__ == "__main__":
    print "Testing interpreted tokenizer"
    runtests("standard")
    print "Testing compiled tokenizer"
    runtests("flex")
