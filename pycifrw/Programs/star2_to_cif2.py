""" 
Convert a data/dictionary file in STAR2 to CIF2 format.  STAR2 and CIF2 differ 
most markedly in their compound data value delimiters (comma and whitespace 
respectively).

We read in the file using STAR2 grammar, then output with CIF2 grammar.
 
Adjust the comment value for your particular uses.
"""
from CifFile import ReadCif,CifDic
import time

def do_conversion(infile,outfile):
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
    comment = \
"""###############################################################################
#                                                                              #
#                   CIF Dictionary for Modulated Structures                    #
#                   ---------------------------------------                    #
#                                                                              #
#  CIF data definitions specifically for Modulated Structures. These are in    #
#  addition to those defined in the CIF Core Dictionary version 2.3 (2003).    #
#                                                                              #
#  The data included in this dictionary are intended to fulfil the Checklist   #
#  for the Description of Incommensurate Modulated Crystal Structures,         #
#  published by the Commission on Aperiodic Crystals. Acta Cryst. (1997),      #
#  A53, 95-100.                                                                #
#                                                                              #
#                                                                              #
#                                                                              #
#  The DDL1 version of this dictionary was converted to DDLm on 27 June 2014.  #
#                                                                              #
################################################################################
"""
    # print 'Master template:' + `incif.dic_as_cif.master_template`
    print 'check: ' + `incif.recurse_child_list('enumeration')`
    of = open(outfile,"w")
    of.write(incif.WriteOut(comment=comment,saves_after='_description.text'))
    of.close()
    print 'Finished writing %s in %f seconds' % (outfile,time.clock() - startread)


if __name__ == "__main__":
    import sys
    infile = sys.argv[1]
    if len(sys.argv)>2:
        outfile = sys.argv[2]
    else:
        outfile = infile + '.cif2'

    do_conversion(infile,outfile)

