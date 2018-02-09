#  Run files in the list, and catch any expected exceptions
from __future__ import print_function
from __future__ import absolute_import

import sys
#sys.path.insert(0,"..")
from CifFile import ReadCif,CifFile

def runtests(scantype,calling_method):
    """Scantype is flex or standard, calling method is either
    to construct a CifFile object or using ReadCif"""
    test_table = [
    ["ciftest1", "OK"],
    ["ciftest2", "OK"],
    ["ciftest3", "OK"],
    ["ciftest4", "OK"],
    ]

    for filename, testresult in test_table:
        try:
            calling_method(filename,scantype=scantype,grammar="2.0")
        except:
            stype,svalue,sinfo = sys.exc_info()
            if testresult == 'OK':
                print("%s causes error where none expected" % filename)
                print("%s\n%s" % (repr(stype),svalue))
            else:
                if stype in testresult:
                    print("%s passes" % filename)
                else:
                    print("Unexpected exception %s for %s" % (repr(stype),filename))
        else:     #no exception
            if testresult == 'OK':
                print("%s passes" % filename)
            else:
                print("%s: Expected %s, got nothing" % (filename,repr(testresult)))
if __name__ == "__main__":
    print("Testing interpreted tokenizer+ReadCif")
    runtests("standard",ReadCif)
    print("Testing compiled tokenizer+ReadCif",ReadCif)
    runtests("flex",ReadCif)
    print("Testing interpreted tokenizer+CifFile")
    runtests("standard",CifFile)
    print("Testing compiled tokenizer+CifFile")
    runtests("flex",CifFile)
