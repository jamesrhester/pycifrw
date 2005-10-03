#  Run files in the list, and catch any expected exceptions
import sys
from CifFile import *

def runtests():
    test_table = [
    ["ciftest1", "OK"],
    ["ciftest2", "OK"],
    ["ciftest3", "OK"],
    ["ciftest4", "OK"],
    ["ciftest5", "OK"],
    ["ciftest6", CifError],
    ["ciftest7", CifError],
    ["ciftest8", CifError],
    ["ciftest9", CifError],
    ["ciftest10", CifError],
    ["ciftest11", "OK"],
    ["ciftest12", "OK"],
    ["ciftest13", "OK"],
    ["ciftest14", CifError],
    ["ciftest15", CifError],
    ["ciftest16", CifError],
    ["ciftest17", CifError],
    ["ciftest18", CifError]
    ]

    for filename, testresult in test_table:
        try:
        	CifFile(filename)
        except:
        	if testresult == 'OK':
           	    print "%s causes error where none expected" % filename
	            print "%s\n%s" % (`sys.exc_type`,sys.exc_value)
        	else:
        	    if sys.exc_type == testresult:
        		print "%s passes" % filename
		    else:
			print "Unexpected exception %s for %s" % (`sys.exc_type`,filename)
        else:     #no exception
        	if testresult == 'OK':
        	    print "%s passes" % filename
        	else:
        	    print "%s: Expected %s, got nothing" % (filename,`testresult`)
if __name__ == "__main__":
    runtests()
