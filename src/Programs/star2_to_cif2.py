"""
Convert a data/dictionary file in STAR2 to CIF2 format.  STAR2 and CIF2 differ
most markedly in their compound data value delimiters (comma and whitespace
respectively).

We read in the file using STAR2 grammar, then output with CIF2 grammar.

Two optional files may be provided, one giving a top-level comment, and
another the descriptive text for the dictionary.
"""

from __future__ import print_function
from CifFile import ReadCif,CifDic
import time

def do_conversion(infile,outfile,desc=None,comment=None):
    startread = time.clock()
    incif = ReadCif(infile,grammar="STAR2")
    print('Finished reading %s in %f seconds' % (infile,time.clock() - startread))
    try:
        incif = CifDic(incif,do_minimum=True)
    except:
        print('Failed to read as CIF dictionary')
    incif.set_grammar("2.0")
    incif.standard = 'Dic'
    incif.SetTemplate("dic_template.dic")
    if comment is None:
        comment_header = \
"""###############################################################################
#                                                                              #
#                   CIF Dictionary                                             #
#                   --------------                                             #
#                                                                              #
#  CIF data definitions in DDLm format.                                        #
#                                                                              #
################################################################################
"""
    else:
        comment_header = open(comment).read()
    if desc is not None:
        incif.master_block.overwrite=True
        incif.master_block['_description.text'] = open(desc).read()
        incif.master_block.overwrite=False
    # print('Master template: {!r}'.format(incif.dic_as_cif.master_template))
    print('check: {!r}'.format(incif.recurse_child_list('enumeration')))
    of = open(outfile,"w")
    of.write(incif.WriteOut(comment=comment_header,saves_after='_description.text'))
    of.close()
    print('Finished writing %s in %f seconds' % (outfile,time.clock() - startread))

if __name__ == "__main__":
    import sys
    comment_file = None
    description_file = None
    if len(sys.argv)<2 or len(sys.argv)>4:
        print('Usage: python star2_to_cif2.py infile description_file comment_file')
        print("""<infile> should be in STAR2 format. The output file will be <infile>+'.cif2'
Optional description_file contains a description for the dictionary, and optional comment_file
contains a comment for the dictionary header.""")
    infile = sys.argv[1]
    outfile = infile + '.cif2'
    if len(sys.argv)>2:
        description_file = sys.argv[2]
    if len(sys.argv)>3:
        comment_file = sys.argv[3]
    do_conversion(infile,outfile,desc=description_file,comment=comment_file)
