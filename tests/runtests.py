#  Run files in the list, and catch any expected exceptions
from __future__ import absolute_import
from __future__ import print_function

import sys
from CifFile import ReadCif,CifError
from CifFile.StarFile import StarError

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
            stype,svalue,ss = sys.exc_info()
            if testresult == 'OK':
                print ("%s causes error where none expected" % filename)
                print ("%s\n%s" % (repr(stype),svalue))
            else:
                if stype in testresult:
                    print ("%s passes" % filename)
                else:
                    print ("Unexpected exception %s for %s" % (repr(stype),filename))
        else:     #no exception
            if testresult == 'OK':
                print( "%s passes" % filename)
            else:
                print( "%s: Expected %s, got nothing" % (filename,repr(testresult)))
if __name__ == "__main__":
    print("Testing interpreted tokenizer")
    runtests("standard")
    print("Testing compiled tokenizer")
    runtests("flex")
