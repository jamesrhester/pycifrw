""" 
Convert a data/dictionary file in STAR2 to CIF2 format.  STAR2 and CIF2 differ 
most markedly in their compound data value delimiters (comma and whitespace 
respectively).

We read in the file using STAR2 grammar, then output with CIF2 grammar.
"""
from CifFile import ReadCif,CifDic
import time

if __name__ == "__main__":
    import sys
    infile = sys.argv[1]
    if len(sys.argv)>2:
        outfile = sys.argv[2]
    else:
        outfile = infile + '.cif2'
    startread = time.clock()
    incif = ReadCif(infile,grammar="STAR2")
    print 'Finished reading %s in %f seconds' % (infile,time.clock() - startread)
    try:
        incif = CifDic(incif,do_minimum=True)
    except:
        print 'Failed to read as CIF dictionary'
    incif.set_grammar("2.0")
    incif.standard = 'Dic'
    incif.SetTemplate("dic_template.dic")
    comment = """##############################################################################
#                                                                            #
#                      DDLm REFERENCE DICTIONARY                             #
#                                                                            #
##############################################################################"""


    # print 'Master template:' + `incif.dic_as_cif.master_template`
    print 'check: ' + `incif.recurse_child_list('enumeration')`
    of = open(outfile,"w")
    of.write(incif.WriteOut(comment=comment,saves_after='_description.text'))
    of.close()
    print 'Finished writing %s in %f seconds' % (outfile,time.clock() - startread)

