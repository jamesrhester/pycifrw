# Noweb literate programming file for Star grammar and parser specification.
# We are using Amit Patel's excellent context-sensitive Yapps2 parser.    
# '                                                                       
# This was chosen                                                         
# because it enables us to process long semicolon delimited strings without
# running into Python recursion limits.  In the original kjParsing implementation,
# it was impossible to get the lexer to return a single line of text within
# the semicolon-delimited string as that re would have matched a single line
# of text anywhere in the file.  The resulting very long match expression 
# only worked for text strings less than about 9000 characters in length. 
# For further information about Yapps2, see                               
# http://theory.stanford.edu/~amitp/Yapps/                                
#                                                                         
# Several standards are available, of which four are implemented: 1.0,    
# 1.1, CIF2 and STAR2.  CIF2 differs from STAR2 in that lists have comma  
# separators and no nested save frames are allowed.  Note that 1.0,1.1    
# and CIF2/STAR2 differ in their treatment of unquoted data values beginning
# with brackets.                                                          
#                                                                         
#                                                                         
# <1.0_syntax>=                                                           
#  Python 2/3 compatibility. We try to keep the code as                   
# portable across the 2-3 divide as we can.                               
#                                                                         
#                                                                         
# <Python2-3 compatibility>=                                              
# To maximize python3/python2 compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

from .StarFile import StarBlock,StarFile,StarList,StarDict
from io import StringIO
#   Helper functions.                                                     
#                                                                         
# We have a monitor function which we can call to save the last parsed    
# value (and print, if we are debugging).   We also have functions for    
# stripping off delimiters from strings.  Finally, we match up our        
# loops after reading them in.  Note that we have function stripextras,   
# which is only for semicolon strings, and stripstring, which is for      
# getting rid of the inverted commas.                                     
#                                                                         
#                                                                         
# <Helper functions>=                                                     
# An alternative specification for the Cif Parser, based on Yapps2
# by Amit Patel (http://theory.stanford.edu/~amitp/Yapps)
#
# helper code: we define our match tokens
lastval = ''
def monitor(location,value):
    global lastval
    #print 'At %s: %s' % (location,repr(value))
    lastval = repr(value)
    return value

# Strip extras gets rid of leading and trailing whitespace, and
# semicolons.
def stripextras(value):
     from .StarFile import remove_line_folding, remove_line_prefix
     # we get rid of semicolons and leading/trailing terminators etc.
     import re
     jj = re.compile("[\n\r\f \t\v]*")
     semis = re.compile("[\n\r\f \t\v]*[\n\r\f]\n*;")
     cut = semis.match(value)
     if cut:        #we have a semicolon-delimited string
          nv = value[cut.end():len(value)-2]
          try:
             if nv[-1]=='\r': nv = nv[:-1]
          except IndexError:    #empty data value
             pass
          # apply protocols
          nv = remove_line_prefix(nv)
          nv = remove_line_folding(nv)
          return nv
     else:
          cut = jj.match(value)
          if cut:
               return stripstring(value[cut.end():])
          return value

# helper function to get rid of inverted commas etc.

def stripstring(value):
     if value:
         if value[0]== '\'' and value[-1]=='\'':
           return value[1:-1]
         if value[0]=='"' and value[-1]=='"':
           return value[1:-1]
     return value

# helper function to get rid of triple quotes
def striptriple(value):
    if value:
        if value[:3] == '"""' and value[-3:] == '"""':
            return value[3:-3]
        if value[:3] == "'''" and value[-3:] == "'''":
            return value[3:-3]
    return value

# helper function to populate a StarBlock given a list of names
# and values .
#
# Note that there may be an empty list at the very end of our itemlists,
# so we remove that if necessary.
#

def makeloop(target_block,loopdata):
    loop_seq,itemlists = loopdata
    if itemlists[-1] == []: itemlists.pop(-1)
    # print('Making loop with %s' % repr(itemlists))
    step_size = len(loop_seq)
    for col_no in range(step_size):
       target_block.AddItem(loop_seq[col_no], itemlists[col_no::step_size],precheck=True)
    # now construct the loop
    try:
        target_block.CreateLoop(loop_seq)  #will raise ValueError on problem
    except ValueError:
        error_string =  'Incorrect number of loop values for loop containing %s' % repr(loop_seq)
        print(error_string, file=sys.stderr)
        raise ValueError(error_string)

# return an object with the appropriate amount of nesting
def make_empty(nestlevel):
    gd = []
    for i in range(1,nestlevel):
        gd = [gd]
    return gd

# this function updates a dictionary first checking for name collisions,
# which imply that the CIF is invalid.  We need case insensitivity for
# names.

# Unfortunately we cannot check loop item contents against non-loop contents
# in a non-messy way during parsing, as we may not have easy access to previous
# key value pairs in the context of our call (unlike our built-in access to all
# previous loops).
# For this reason, we don't waste time checking looped items against non-looped
# names during parsing of a data block.  This would only match a subset of the
# final items.   We do check against ordinary items, however.
#
# Note the following situations:
# (1) new_dict is empty -> we have just added a loop; do no checking
# (2) new_dict is not empty -> we have some new key-value pairs
#
def cif_update(old_dict,new_dict,loops):
    old_keys = map(lambda a:a.lower(),old_dict.keys())
    if new_dict != {}:    # otherwise we have a new loop
        #print 'Comparing %s to %s' % (repr(old_keys),repr(new_dict.keys()))
        for new_key in new_dict.keys():
            if new_key.lower() in old_keys:
                raise CifError("Duplicate dataname or blockname %s in input file" % new_key)
            old_dict[new_key] = new_dict[new_key]
#
# this takes two lines, so we couldn't fit it into a one line execution statement...
def order_update(order_array,new_name):
    order_array.append(new_name)
    return new_name

# and finally...turn a sequence into a python dict (thanks to Stackoverflow)
def pairwise(iterable):
    try:
        it = iter(iterable)
        while 1:
            yield next(it), next(it)
    except StopIteration:
        return
%%
parser StarParser:
    # The original CIF specification allowed brackets to begin data values, even if not quoted.  That is the only difference.
    #                                                                         
    #                                                                         
    # <Regular expressions 1.0>=                                              
    # first handle whitespace and comments, keeping whitespace
    # before a semicolon
    ignore: r"([ \t\n\r](?!;))|[ \t]"
    ignore: r"(#.*[\n\r](?!;))|(#.*)"
    # now the tokens
    token LBLOCK:  "(L|l)(O|o)(O|o)(P|p)_"        # loop_
    token GLOBAL: "(G|g)(L|l)(O|o)(B|b)(A|a)(L|l)_"
    token STOP: "(S|s)(T|t)(O|o)(P|p)_"
    token save_heading: r"(S|s)(A|a)(V|v)(E|e)_[][!%&()*+,./:<=>?@0-9A-Za-z\\\\^`{}|~\"#$';_-]+"
    token save_end: "(S|s)(A|a)(V|v)(E|e)_"
    token data_name: r"_[][!%&()*+,./:<=>?@0-9A-Za-z\\\\^`{}|~\"#$';_-]+" #_followed by stuff
    token data_heading: r"(D|d)(A|a)(T|t)(A|a)_[][!%&()*+,./:<=>?@0-9A-Za-z\\\\^`{}|~\"#$';_-]+"
    token start_sc_line: r"(\n|\r\n);([^\n\r])*(\r\n|\r|\n)+"
    token sc_line_of_text: r"[^;\r\n]([^\r\n])*(\r\n|\r|\n)+"
    token end_sc_line: ";"
    token data_value_1: r"((?!(((S|s)(A|a)(V|v)(E|e)_[^\s]*)|((G|g)(L|l)(O|o)(B|b)(A|a)(L|l)_[^\s]*)|((S|s)(T|t)(O|o)(P|p)_[^\s]*)|((D|d)(A|a)(T|t)(A|a)_[^\s]*)))[^\s\"#$'_][^\s]*)|'(('(?=\S))|([^\n\r\f']))*'+|\"((\"(?=\S))|([^\n\r\"]))*\"+"
    token END: '$'

    # The CIF 1.1 grammar specification does not include bracket expressions, but does exclude brackets from
    # beginning unquoted data values.  We pass through the argument [[prepared]] so we can deal with non-standard
    # dictionary files that contain duplicate datablocks.                     
    #                                                                         
    #                                                                         
    # <Grammar specification 1.1>=                                            
    # now the rules

    rule input<<prepared>>: ( ((
                dblock<<prepared>>         {{allblocks = prepared;allblocks.merge_fast(dblock)}}
                (
                dblock<<prepared>>         {{allblocks.merge_fast(dblock)}} #
                )*
                END
                )
                |
                (
                END                 {{allblocks = prepared}}
                )))                   {{allblocks.unlock();return allblocks}}

        rule dblock<<prepared>>: ( data_heading {{heading = data_heading[5:];thisbc=StarFile(characterset='unicode',standard=prepared.standard);newname = thisbc.NewBlock(heading,prepared.blocktype(overwrite=False));act_block=thisbc[newname]}}# a data heading
                      (
                       dataseq<<thisbc[heading]>>
                      |
                      save_frame<<prepared>>     {{thisbc.merge_fast(save_frame,parent=act_block)}}
                      )*
    # A trick to force rechecking of all datanames, which was skipped by the precheck = True option below
                       )                      {{thisbc[heading].setmaxnamelength(thisbc[heading].maxnamelength);return (monitor('dblock',thisbc))}} # but may be empty

         rule dataseq<<starblock>>:  data<<starblock>>
                           (
                           data<<starblock>>
                           )*

         rule data<<currentblock>>:        top_loop      {{makeloop(currentblock,top_loop)}}
                                            |
                                            datakvpair    {{currentblock.AddItem(datakvpair[0],datakvpair[1],precheck=True)}} #kv pair

         rule datakvpair: data_name data_value {{return [data_name,data_value]}} # name-value

         rule data_value: (data_value_1          {{thisval = stripstring(data_value_1)}}
                          |
                          sc_lines_of_text      {{thisval = stripextras(sc_lines_of_text)}}
                          )                     {{return monitor('data_value',thisval)}}

         rule sc_lines_of_text: start_sc_line   {{lines = StringIO();lines.write(start_sc_line)}}
                                (
                                sc_line_of_text {{lines.write(sc_line_of_text)}}
                                )*
                                end_sc_line     {{lines.write(end_sc_line);return monitor('sc_line_of_text',lines.getvalue())}}

    # due to the inability of the parser to backtrack, we contruct our loops in helper functions,
    # and simply collect data during parsing proper.

         rule top_loop: LBLOCK loopfield loopvalues {{return loopfield,loopvalues}}

    # OK: a loopfield is either a sequence of dataname*,loopfield with stop
    # or else dataname,loopfield without stop

         rule loopfield: (            {{toploop=[]}}
                         (
                                      ( data_name  )  {{toploop.append(data_name)}}
                          )*
                          )                        {{return toploop}} # sequence of data names


         rule loopvalues: (
                           (data_value   ) {{dataloop=[data_value]}}
                           (
                           (data_value  ) {{dataloop.append(monitor('loopval',data_value))}}
                           )*
                           )              {{return dataloop}}

         rule save_frame<<prepared>>: save_heading   {{savehead = save_heading[5:];savebc = StarFile();newname=savebc.NewBlock(savehead,prepared.blocktype(overwrite=False));act_block=savebc[newname] }} 
                          (
                          dataseq<<savebc[savehead]>>
                          |
                          save_frame<<prepared>>     {{savebc.merge_fast(save_frame,parent=act_block)}}
                          )*
                          save_end           {{return monitor('save_frame',savebc)}}


%%

