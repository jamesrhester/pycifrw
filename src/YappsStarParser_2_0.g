# The following two recipes produce CIF2 and STAR2 syntax.                
#                                                                         
#                                                                         
# <CIF2_syntax>=                                                          
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
    # CIF 2.0 uses spaces instead of commas to separate list values so commas are allowed in data values
    #                                                                         
    #                                                                         
    # <Regular expressions CIF2>=                                             
    # <STAR2-CIF2 common regular expressions block 1>=                        
    # first handle whitespace and comments, keeping whitespace
    # before a semicolon
    ignore: r"([ \t\n\r](?!;))|[ \t]"
    ignore: r"(#.*[\n\r](?!;))|(#.*)"
    # now the tokens
    token LBLOCK:  "(L|l)(O|o)(O|o)(P|p)_"        # loop_
    token GLOBAL: "(G|g)(L|l)(O|o)(B|b)(A|a)(L|l)_"
    token STOP: "(S|s)(T|t)(O|o)(P|p)_"
    token save_heading: "(S|s)(A|a)(V|v)(E|e)_[][!%&()*+,./:<=>?@0-9A-Za-z\\\\^`{}|~\"#$';_\u00A0-\uD7FF\uE000-\uFDCF\uFDF0-\uFFFD\U00010000-\U0001FFFD\U00020000-\U0002FFFD\U00030000-\U0003FFFD\U00040000-\U0004FFFD\U00050000-\U0005FFFD\U00060000-\U0006FFFD\U00070000-\U0007FFFD\U00080000-\U0008FFFD\U00090000-\U0009FFFD\U000A0000-\U000AFFFD\U000B0000-\U000BFFFD\U000C0000-\U000CFFFD\U000D0000-\U000DFFFD\U000E0000-\U000EFFFD\U000F0000-\U000FFFFD\U00100000-\U0010FFFD-]+"
    token save_end: "(S|s)(A|a)(V|v)(E|e)_"
    token data_name: "_[][!%&()*+,./:<=>?@0-9A-Za-z\\\\^`{}|~\"#$';_\u00A0-\uD7FF\uE000-\uFDCF\uFDF0-\uFFFD\U00010000-\U0001FFFD\U00020000-\U0002FFFD\U00030000-\U0003FFFD\U00040000-\U0004FFFD\U00050000-\U0005FFFD\U00060000-\U0006FFFD\U00070000-\U0007FFFD\U00080000-\U0008FFFD\U00090000-\U0009FFFD\U000A0000-\U000AFFFD\U000B0000-\U000BFFFD\U000C0000-\U000CFFFD\U000D0000-\U000DFFFD\U000E0000-\U000EFFFD\U000F0000-\U000FFFFD\U00100000-\U0010FFFD-]+" #_followed by stuff
    token data_heading: "(D|d)(A|a)(T|t)(A|a)_[][!%&()*+,./:<=>?@0-9A-Za-z\\\\^`{}|~\"#$';_\u00A0-\uD7FF\uE000-\uFDCF\uFDF0-\uFFFD\U00010000-\U0001FFFD\U00020000-\U0002FFFD\U00030000-\U0003FFFD\U00040000-\U0004FFFD\U00050000-\U0005FFFD\U00060000-\U0006FFFD\U00070000-\U0007FFFD\U00080000-\U0008FFFD\U00090000-\U0009FFFD\U000A0000-\U000AFFFD\U000B0000-\U000BFFFD\U000C0000-\U000CFFFD\U000D0000-\U000DFFFD\U000E0000-\U000EFFFD\U000F0000-\U000FFFFD\U00100000-\U0010FFFD-]+"
    token start_sc_line: "(\n|\r\n);([^\n\r])*(\r\n|\r|\n)+"
    token sc_line_of_text: "[^;\r\n]([^\r\n])*(\r\n|\r|\n)+"
    token end_sc_line: ";"
    token c_c_b: "}"
    token o_c_b: "{"
    token c_s_b: "]"
    token o_s_b: r"\["
    #token dat_val_nocomma_nosq: "([^\s\"#$,'_\(\{\[\]][^\s,\[\]]*)|'(('(?![\s,]))|([^\n\r\f']))*'+|\"((\"(?![\s,]))|([^\n\r\"]))*\"+"
    token dat_val_internal_sq: r"\[([^\s[\]]*)\]"
    # token dat_val_nocomma_nocurl: "([^\s\"#$,'_\(\{\[\]][^\s,}]*)|'(('(?![\s,]))|([^\n\r\f']))*'+|\"([^\n\r\"])*\"+"
    # For tests of new DDLm syntax - no quotes or apostrophes in strings, no commas, braces or square brackets in undelimited data values
    # This token for triple-quote delimited strings must come before single-quote delimited strings to avoid the opening quotes being
    # interpreted as a single-quote delimited string
    token triple_quote_data_value: "(?s)'''.*?'''|\"\"\".*?\"\"\""
    token single_quote_data_value: r"'([^\n\r\f'])*'+|\"([^\n\r\"])*\"+"

    token data_value_1: r"((?!(((S|s)(A|a)(V|v)(E|e)_[^\s]*)|((G|g)(L|l)(O|o)(B|b)(A|a)(L|l)_[^\s]*)|((S|s)(T|t)(O|o)(P|p)_[^\s]*)|((D|d)(A|a)(T|t)(A|a)_[^\s]*)))[^\s\"#$'_{}[\]][^\s{}[\]]*)"
    # Currently just a single line but we allow a whole block just in case.   
    #                                                                         
    #                                                                         
    # <STAR2-CIF2 common regular expressions block 2>=                        
    token END: '$'


    # <Grammar specification CIF2>=                                           
    #  CIF2 and STAR2 are almost identical in grammar                         
    #                                                                         
    #                                                                         
    # <CIF2-STAR2 common grammar>=                                            
    # now the rules

    rule input<<prepared>>: ( ((
                dblock<<prepared>>         {{allblocks = prepared; allblocks.merge_fast(dblock)}}
                (
                dblock<<prepared>>         {{allblocks.merge_fast(dblock)}} #
                )*
                END
                )
                |
                (
                END                 {{allblocks = prepared}}
                )))                   {{allblocks.unlock(); return allblocks}}

         rule dblock<<prepared>>: ( data_heading {{heading = data_heading[5:];thisbc=StarFile(characterset='unicode',standard=prepared.standard);act_heading = thisbc.NewBlock(heading,prepared.blocktype(overwrite=False));stored_block = thisbc[act_heading]}}# a data heading
                      (
                       dataseq<<stored_block>>   #because merging may have changed the heading  
                      |
                      save_frame<<prepared>>     {{thisbc.merge_fast(save_frame,parent=stored_block)}}
                      )*
                       )                      {{stored_block.setmaxnamelength(stored_block.maxnamelength);return (monitor('dblock',thisbc))}} # but may be empty

         rule dataseq<<starblock>>:  data<<starblock>>
                           (
                           data<<starblock>>
                           )*

         rule data<<currentblock>>:        top_loop      {{makeloop(currentblock,top_loop)}}
                                            |
                                            datakvpair    {{currentblock.AddItem(datakvpair[0],datakvpair[1],precheck=True)}} #kv pair

         rule datakvpair: data_name data_value {{return [data_name,data_value]}} # name-value

         rule data_value: (data_value_1          {{thisval = data_value_1}}
                          |
                          delimited_data_value  {{thisval = delimited_data_value}}
                          |
                          sc_lines_of_text      {{thisval = stripextras(sc_lines_of_text)}}
                          |
                          bracket_expression    {{thisval = bracket_expression}}
                          )                     {{return monitor('data_value',thisval)}}

         rule delimited_data_value: (triple_quote_data_value      {{thisval = striptriple(triple_quote_data_value)}}
                                    |
                                    single_quote_data_value       {{thisval = stripstring(single_quote_data_value)}}
                                    )                             {{return thisval}}

         rule sc_lines_of_text: start_sc_line   {{lines = StringIO();lines.write(start_sc_line)}}
                                (
                                sc_line_of_text {{lines.write(sc_line_of_text)}}
                                )*
                                end_sc_line     {{lines.write(end_sc_line);return monitor('sc_line_of_text',lines.getvalue())}}

         rule bracket_expression:  square_bracket_expr   {{return square_bracket_expr}}
                                |
                                  curly_bracket_expr    {{return curly_bracket_expr}}


    # due to the inability of the parser to backtrack, we contruct our loops in helper functions,
    # and simply collect data during parsing proper.

         rule top_loop: LBLOCK loopfield loopvalues {{return loopfield,loopvalues}}

    # OK: a loopfield is either a sequence of datanames

         rule loopfield: (            {{loop_seq=[] }}
                         (
                                      ( data_name  )  {{loop_seq.append(data_name)}}
                          )*
                          )                        {{return loop_seq}} # sequence of data names


         rule loopvalues: (
                           (data_value   ) {{dataloop=[data_value]}}
                           (
                           (data_value  ) {{dataloop.append(monitor('loopval',data_value))}}
                           )*
                           )              {{return dataloop}}

         rule save_frame<<prepared>>: save_heading   {{savehead = save_heading[5:];savebc = StarFile(characterset='unicode');newname = savebc.NewBlock(savehead,prepared.blocktype(overwrite=False));stored_block = savebc[newname] }} 
                          (
                          dataseq<<savebc[savehead]>>
                          |
                          save_frame<<prepared>>     {{savebc.merge_fast(save_frame,parent=stored_block)}}
                          )*
                          save_end           {{return monitor('save_frame',savebc)}}

    # <CIF2-specific grammar>=                                                
         rule save_frame<<prepared>>: save_heading   {{savehead = save_heading[5:];savebc = StarFile(characterset='unicode');newname = savebc.NewBlock(savehead,prepared.blocktype(overwrite=False));stored_block = savebc[newname] }} 
                          (
                          dataseq<<savebc[savehead]>>
                          )*
                          save_end           {{return monitor('save_frame',savebc)}}


          rule square_bracket_expr: o_s_b            {{this_list = []}}
                                (  data_value       {{this_list.append(data_value)}}
                                  (
                                    data_value       {{this_list.append(data_value)}}
                                  ) *
                                ) *
                                   c_s_b                     {{return StarList(this_list)}}

         rule curly_bracket_expr: ( o_c_b                    {{table_as_list = []}}
                                (  delimited_data_value      {{table_as_list = [delimited_data_value]}}
                                  ":"
                                  data_value                 {{table_as_list.append(data_value)}}
                                (
                                  delimited_data_value       {{table_as_list.append(delimited_data_value)}}
                                  ":"
                                  data_value                 {{table_as_list.append(data_value)}}
                                ) *
                                ) *
                                  c_c_b )                    {{return StarDict(pairwise(table_as_list))}}




%%
