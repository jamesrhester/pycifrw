#  Run files in the list, and catch any expected exceptions
import sys
from CifFile import ReadCif,CifError,StarError

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
                sei = sys.exc_info()
                if testresult == 'OK':
                    print("%s causes error where none expected" % filename)
                    print("%s\n%s" % (repr(sei[0]),sei[1]))
                else:
                    if sei[0] in testresult:
                        print("%s passes" % filename)
                    else:
                        print("Unexpected exception %s for %s" % (repr(sei[0]),filename))
        else:     #no exception
                if testresult == 'OK':
                    print("%s passes" % filename)
                else:
                    print("%s: Expected %s, got nothing" % (filename,repr(testresult)))

if __name__ == "__main__":
    print("Testing interpreted tokenizer")
    runtests("standard")
    print("Testing compiled tokenizer")
    runtests("flex")
