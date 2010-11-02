#  Run files in the list, and catch any expected exceptions
import sys
sys.path.insert(0,"..")
from CifFile import *
from StarFile import *

def runtests(scantype):
    test_table = [
    ["ciftest1", "OK"],
    ["ciftest2", "OK"],
    ["ciftest3", "OK"],
    ["ciftest4", "OK"],
    ]

    for filename, testresult in test_table:
        try:
        	ReadCif(filename,scantype=scantype,grammar="DDLm")
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
