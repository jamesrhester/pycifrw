# A dREL grammar written for python-ply
#
# The output string should be a series of executable python statements,
# which define a function which is called with a PyCIFRW CifBlock
# object as single argument "cfdata"
#
# The object so defined will be a method of the dictionary object, taking
# arguments self,cfdata.  Therefore dictionary information is accessed
# through "self", and data through "cfdata".

import drel_lex
import ply.yacc as yacc
tokens = drel_lex.tokens

# Overall translation unit
def p_input(p):
    '''input : statement
             | input statement'''
    p[0] = "\n".join(p[1:])

def p_statement(p):
    '''statement : stmt_list
                | compound_stmt'''
    p[0] = p[1]

def p_stmt_list(p): 
    '''stmt_list : simple_stmt
                 | stmt_list ";" simple_stmt
                 | stmt_list ";" simple_stmt ";" '''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = ";".join((p[1],p[3]))

def p_simple_stmt(p):
    '''simple_stmt : expression_list
                    | assignment_stmt
                    | BREAK
                    | NEXT'''
    p[0] = p[1]

# note do not accept trailing commas

def p_expression_list(p):
    '''expression_list : expression
                        | expression_list "," expression '''

    if len(p) == 2: p[0] = p[1]
    else: 
        p[0] = " ".join((p[1],",",p[3]))
        print "constructing expr list: %s" % `p[0]`


def p_expression(p):
    '''expression : or_test 
                   | or_test IF or_test ELSE or_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = " ".join((p[1],"if",p[3],"else", p[5]))

def p_or_test(p):
    ''' or_test : and_test
                 | or_test OR and_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = " ".join((p[1],"or",p[3]))

def p_and_test(p):
    '''and_test : not_test
                 | and_test AND not_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = " ".join((p[1],"and",p[3]))

def p_not_test(p):
    '''not_test : comparison
                 | NOT not_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = " ".join(("not",p[2]))

def p_comparison(p):
    '''comparison : a_expr
                   | a_expr comp_operator a_expr'''
    if len(p) == 2: p[0] = p[1]
    else:
       p[0] = " ".join((p[1],p[2],p[3]))

def p_comp_operator(p):
    '''comp_operator : "<"
                     | ">"
                     | GTE
                     | LTE
                     | NEQ
                     | ISEQUAL
                     | IN
                     | NOT IN '''
    if len(p)==2:
        p[0] = " not in "
    else: p[0] = p[1]

def p_a_expr(p):
    '''a_expr : m_expr
               | a_expr "+" m_expr
               | a_expr "-" m_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else: 
        p[0] = " ".join((p[1] , p[2] , p[3]))

def p_m_expr(p):
    '''m_expr : u_expr
               | m_expr "*" u_expr
               | m_expr "/" u_expr 
               | m_expr "^" u_expr '''
    if len(p) == 2:
        p[0] = p[1]
    else: 
        if p[2] == "^":
            p[0] = "mat_cross_prod(" + p[1] + " , " + p[3] + ")"
        else:
            p[0] = " ".join((p[1] , p[2] , p[3]))

def p_u_expr(p):
    '''u_expr : power
               | "-" u_expr
               | "+" u_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else: 
        p[0] = " ".join(p[1:])

def p_power(p):
    '''power : primary
              | primary POWER u_expr'''
    if len(p) == 2: 
        p[0] = p[1]
    else:
        p[0] = " ".join((p[1] , "**" , p[3]))
    print 'At power: p[0] is %s' % `p[0]`

def p_primary(p):
    '''primary : atom
                | attributeref
                | subscription
                | slicing
                | call'''
    # print 'Primary -> %s' % repr(p[1])
    p[0] = p[1]

def p_atom(p):
    '''atom : ID 
             | item_tag 
             | literal
             | enclosure'''
    # print 'Atom -> %s' % repr(p[1])
    p[0] = p[1]

def p_item_tag(p):
    '''item_tag : ITEM_TAG'''
    p[0] = "ciffile['%s']" % p[1]

def p_literal(p): 
    '''literal : stringliteral
                  | INTEGER
                  | HEXINT
                  | OCTINT
                  | BININT
                  | REAL
                  | IMAGINARY'''
    # print 'literal-> %s' % repr(p[1])
    p[0] = p[1]

def p_stringliteral(p):
    '''stringliteral : STRPREFIX SHORTSTRING
                     | STRPREFIX LONGSTRING
                     | SHORTSTRING
                     | LONGSTRING'''
    if len(p)==3: p[0] = p[1]+p[2]
    else: p[0] = p[1]

def p_enclosure(p):
    '''enclosure : parenth_form
                  | list_display '''
    p[0]=p[1]

def p_parenth_form(p):
    '''parenth_form : "(" expression_list ")"
                     | "(" ")" '''
    if len(p) == 3: p[0] = "( )"
    else:
        p[0] = " ".join(p[1:])
    print 'Parens: %s' % `p[0]`

def p_list_display(p):
    ''' list_display : "[" listmaker "]"
                     | "[" "]" '''
    if len(p) == 3: p[0] = "( )"
    else:
        p[0] = " ".join(p[1:])
    

# scrap the trailing comma
def p_listmaker(p):
    '''listmaker : expression listmaker2 
                   | expression list_for '''

    p[0] = " ".join(p[1:])   #no need to rewrite for dREL->python 
    print 'listmaker: %s' % `p[0]`

def p_listmaker2(p):
    '''listmaker2 : "," expression 
                  | listmaker2 "," expression
                  |             '''
    p[0] = " ".join(p[1:]) 

def p_list_for(p):
    '''list_for : FOR expression_list IN testlist
                | FOR expression_list IN testlist list_iter'''
    pass

def p_testlist(p):
    '''testlist : or_test
                | testlist "," or_test
                | testlist "," or_test "," '''
    pass

def p_list_iter(p): 
    '''list_iter : list_for 
                  | list_if'''
    pass

def p_list_if(p):
    '''list_if : IF or_test
               | IF or_test list_iter'''
    pass

# We have to intercept attribute references which relate to
# aliased category variables, as well as to catch literal
# item names containing a period.

def p_attributeref(p):
    '''attributeref : primary "." ID ''' 
    # intercept special loop variables
    # print `p.parser.special_id`
    for idtable in p.parser.special_id:
        newid = idtable.get(p[1],0)
        if newid: break
    if newid: 
        p[0] = "ciffile["+'"_'+newid+"."+p[3]+'"]' 
    elif p.parser.special_id[0].has_key("".join(p[1:])):
        # a global variable from the dictionary
        p[0] = 'ciffile['+"".join(p[1:])+']'
    else:
        p[0] = " ".join(p[1:]) 

# A subscription becomes a key lookup if the primary is a 
# pre-defined 'category variable'
def p_subscription(p):
    '''subscription : primary "[" expression_list "]" '''
    # intercept special loop variables
    # print `p.parser.special_id`
    for idtable in p.parser.special_id:
        newid = idtable.get(p[1],0)
        if newid: break
    if newid: 
        key_item = self[p[1]]["_"+newid+"."+p[3]]
        get_loop = "newpack = ciffile.GetLoop('%s')\n" % key_item
        p[0] = "ciffile["+'"_'+newid+"."+p[3]+'"]' 
    else:
        p[0] = " ".join(p[1:]) 
    p[0] = " ".join(p[1:]) 

def p_slicing(p):
    '''slicing : simple_slicing
               | extended_slicing '''
    p[0] = p[1] 

def p_simple_slicing(p):
    '''simple_slicing : primary "[" short_slice "]" '''
    p[0] = " ".join(p[1:]) 

def p_short_slice(p):
    '''short_slice : ":"
                   | expression ":" expression
                   | ":" expression
                   | expression ":" '''
    p[0] = " ".join(p[1:]) 

def p_extended_slicing(p):
    '''extended_slicing : primary "[" slice_list "]" '''
    p[0] = " ".join(p[1:])

def p_slice_list(p):
    '''slice_list : slice_item
                  | slice_list "," slice_item '''
    p[0] = " ".join(p[1:])

def p_slice_item(p):
    '''slice_item : expression
                  | proper_slice
                  | ELLIPSIS '''
    p[0] = p[1] 

def p_proper_slice(p):
    '''proper_slice : short_slice
                    | long_slice '''
    p[0] = p[1]

def p_long_slice(p):
    '''long_slice : short_slice ":"
                  | short_slice ":" expression '''
    p[0] = " ".join(p[1:])

# Last of the primary non-terminals...

def p_call(p):
    '''call : primary "(" ")"
            | primary "(" argument_list ")" '''
    pass

# It seems that in dREL the arguments are expressed differently
# in the form arg [: specifier], arg ...
#
# We assume a simplified form
#
def p_argument_list(p):
    '''argument_list : func_arg 
                     | argument_list "," func_arg '''
    p[0] = " ".join(p[1:])

def p_func_arg(p):
    '''func_arg : ID
                | ID ":" list_display ''' 
    p[0] = p[1]   #ignore list structure for now
                 
def p_assignment_stmt(p):
    '''assignment_stmt : target_list "=" expression_list'''
    p[0] = " ".join(p[1:])

def p_target_list(p):
    '''target_list : target 
                   | target_list "," target '''
    p[0] = " ".join(p[1:]) 

def p_target(p):
    '''target : ID
              | item_tag 
              | "(" target_list ")"
              | "[" target_list "]"
              | attributeref
              | subscription
              | slicing  '''
    # search our enclosing blocks for special ids
    newid = 0
    # print 'Special ids: %s' % `p.parser.special_id`
    for idtable in p.parser.special_id:
        newid = idtable.get(p[1],0)
        if newid: break
    if newid: 
        p[0] = newid
    else: 
        p[0] = " ".join(p[1:]) 

# now for the compound statements

def p_compound_stmt(p):
    '''compound_stmt : if_stmt
                     | for_stmt
                     | do_stmt
                     | loop_stmt
                     | with_stmt
                     | where_stmt
                     | switch_stmt '''
    p[0] = p[1]

def p_if_stmt(p):
    '''if_stmt : IF expression suite
               | if_stmt ELSE if_stmt
               | if_stmt ELSE suite '''
    pass 

def p_suite(p):
    '''suite : simple_stmt
             | open_brace statement_block close_brace '''
    if len(p) == 2: p[0] =  p[1]
    else:
        p[0] = p[2]  + "\n"

# separate so we can do the indent/dedent thing
def p_open_brace(p):
    '''open_brace : "{"'''
    p.parser.indent += 4*" "
    print 'Parser indent now "%s"' % p.parser.indent

def p_close_brace(p):
    '''close_brace : "}"'''
    p.parser.indent  = p.parser.indent[:-4]
    print 'Parser indent now "%s"' % p.parser.indent

def p_statement_block(p):
    '''statement_block : statement
                      | statement_block statement'''
    if len(p) == 2: p[0] = "\n" + p.parser.indent + p[1] 
    else: p[0] = p[1] + "\n" + p.parser.indent + p[2]

def p_for_stmt(p):
    '''for_stmt : FOR target_list IN expression_list suite'''
    pass

def p_loop_stmt(p):
    '''loop_stmt : LOOP ID AS target_list suite'''
    pass

def p_do_stmt(p):
    '''do_stmt : do_stmt_head suite'''
    p[0] = p[1] + p[2]

# To translate the dREL do to a for statement, we need to make the
# end of the range included in the range

def p_do_stmt_head(p):
    '''do_stmt_head : DO ID "=" expression "," expression
                    | DO ID "=" expression "," expression "," expression '''
    incr = "1"
    if len(p)==9: 
       incr = p[8]
       rangeend = p[6]+"+%s/2" % incr   # avoid float expressions 
    else:
       rangeend = p[6]+"+%s" % incr     # because 1/2 = 0
    p[0] = "for " + p[2] + " in range(" + p[4] + "," + rangeend + "," + incr + "):"

def p_with_stmt(p):
    '''with_stmt : with_head suite'''
    p.parser.special_id.pop()
    p[0] = p[1] + p[2] + "\n" + p.parser.indent + "except IndexError:\n" + p.parser.indent + "    " + "print 'Index Error in with statement'\n"

# Done here to capture the id before processing the suite
# A with statement doesn't need any indenting...
def p_with_head(p):
    '''with_head : WITH ID AS ID'''
    p.parser.special_id.append({p[2]: p[4]})
    print "%s means %s" % (p[2],p[4])
    p[0] = "__pycitems = self.names_in_cat('%s')" % p[4]
    p[0] +="\ntry:"
    

def p_where_stmt(p):
    '''where_stmt : WHERE expression suite ELSE suite'''
    pass

def p_switch_stmt(p):
    '''switch_stmt : SWITCH ID open_brace caselist DEFAULT suite close_brace '''
    pass

def p_caselist(p):
    '''caselist : CASE target_list suite
                | caselist CASE target_list suite'''
    pass

def p_error(p):
    print 'Syntax error at token %s, value %s' % (p.type,p.value)
 
### Now some helper functions
# The following function creates a function.  If returnname is None,
# no variable is returned.  In practice, this means the function
# modifies the 'ciffile' argument in place
#
def make_func(parser_string,funcname,returnname):
    preamble = "def %s(self,ciffile):\n" % funcname
    postamble = ""
    if returnname:
        postamble = "\n    return %s" % returnname   #note indent
    # now indent the string
    noindent = parser_string.splitlines()
    indented = map(lambda a:"    " + a+"\n",noindent)  
    final = preamble + "".join(indented) + postamble
    return final

parser = yacc.yacc()    
parser.indent = ""
parser.special_id=[]
