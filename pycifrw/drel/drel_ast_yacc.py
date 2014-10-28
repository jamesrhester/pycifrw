# A dREL grammar written for python-ply
#
# The output should be an AST that represents a function that will
# be called with a PyCIFRW CifBlock object as a single argument
# "cfdata".

# The object so defined will be transformable into a Python method of 
# the dictionary object, taking
# arguments self,cfdata.  Therefore dictionary information is accessed
# through "self", and data through "cfdata".

import drel_lex
import ply.yacc as yacc
tokens = drel_lex.tokens

# Overall translation unit
# We return the text of the function, as well as a table of 'with' packets 
# and corresponding index names
# 

# Our input is a sequence of statements
def p_input(p):
    '''input : maybe_nline statement
             | input statement '''
    if p[1] is None:
        p[0] = p[2]
    else:
         so_far = p[1][1]
         new_statements = p[2][1]
         p[0] = ["STATEMENTS",p[1][1] + p[2][1]]
         #print 'input now ' + `p[0]`

# We distinguish between compound statements and
# small statements. Small statements may be
# chained together on a single line with semicolon
# separators. Compound statements are not separated
# in this way, and will always be terminated by
# a newline.
def p_statement(p):
    '''statement : simple_stmt newlines
                 | simple_stmt ";" newlines
                 | compound_stmt '''
    p[0] = p[1]

# A simple statement is a sequence of small statements terminated by
# a NEWLINE or EOF
def p_simple_stmt(p):
    ''' simple_stmt : small_stmt
                    | simple_stmt ";" small_stmt '''
    if len(p) == 2:
        p[0] = ["STATEMENTS",[p[1]]]
    else:
        p[0] = ["STATEMENTS",p[1][1] + [p[3]]]

# This production appears inside a set of braces. Any statement
# will be automatically terminated by a newline so we do not
# need to include that here
def p_statements(p): 
    '''statements : statement
                 | statements statement '''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = ["STATEMENTS", p[1][1] + [p[2]]]
    
def p_small_stmt(p):
    '''small_stmt :   expr_stmt
                    | print_stmt
                    | break_stmt
                    | next_stmt'''
    p[0] = p[1]

def p_break_stmt(p):
    '''break_stmt : BREAK'''
    p[0] = ["BREAK"]

def p_next_stmt(p):
    '''next_stmt : NEXT'''
    p[0] = ["NEXT"]

def p_print_stmt(p):
    '''print_stmt : PRINT expression '''
    p[0] = ['PRINT', p[2]]

# Note here that a simple testlist_star_expr is useless as in our
# side-effect-free world it will be evaluated and discarded. We
# could just drop it right now but we let it go through to the
# AST processor for language-dependent processing
def p_expr_stmt(p):
    ''' expr_stmt : testlist_star_expr
                  | testlist_star_expr AUGOP testlist_star_expr 
                  | testlist_star_expr "=" testlist_star_expr
                  | fancy_drel_assignment_stmt '''
    if len(p) == 2 and p[1][0] != 'FANCY_ASSIGN':  # we have a list of expressions which we
        p[0] = ["EXPRLIST",p[1]]
    elif len(p) == 2 and p[1][0] == 'FANCY_ASSIGN':
        p[0] = p[1]
    else:
        p[0] = ["ASSIGN",p[1],p[2],p[3]]

def p_testlist_star_expr(p):  # list of expressions in fact
    ''' testlist_star_expr : expression
                           | testlist_star_expr "," maybe_nline expression '''
    if len(p) == 2:
       p[0] = [p[1]]
    else:
       p[0] = p[1] + [p[4]]

# note do not accept trailing commas

#def p_expression_list(p):
#    '''expression_list : expression
#                        | expression_list "," expression '''
#
#    if len(p) == 2: p[0] = [p[1]]
#    else: 
#        p[0] = p[1] + [p[3]]


# Simplified from the python 2.5 version due to apparent conflict with
# the other type of IF expression...
#
def p_expression(p):
    '''expression : or_test '''
    p[0] = ["EXPR",p[1]]

# This is too generous, as it allows a function call on the
# LHS to be assigned to.  This will cause a syntax error on
# execution we hope.

def p_or_test(p):
    ''' or_test : and_test
                 | or_test OR and_test
                 | or_test BADOR and_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = ["MATHOP","or",p[1],p[3]]

def p_and_test(p):
    '''and_test : not_test
                 | and_test AND not_test
                 | and_test BADAND not_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = ["MATHOP","and", p[1],p[3]]

def p_not_test(p):
    '''not_test : comparison
                 | NOT not_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = ["UNARY","not",p[2]]

def p_comparison(p):
    '''comparison : a_expr
                   | a_expr comp_operator a_expr'''
    if len(p) == 2: p[0] = p[1]
    else:
       p[0] = ["MATHOP",p[2],p[1],p[3]]

def p_comp_operator(p):
    '''comp_operator : restricted_comp_operator
                     | IN
                     | NOT IN '''
    if len(p)==3:
        p[0] = "not in"
    else: p[0] = p[1]

def p_restricted_comp_operator(p):   #for loop tests
    '''restricted_comp_operator :  "<"
                     | ">"
                     | GTE
                     | LTE
                     | NEQ
                     | ISEQUAL '''
    p[0] = p[1]

def p_a_expr(p):
    '''a_expr : m_expr
               | a_expr "+" m_expr
               | a_expr "-" m_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else: 
        p[0] = ["MATHOP",p[2], p[1], p[3]]

def p_m_expr(p):
    '''m_expr : u_expr
               | m_expr "*" u_expr
               | m_expr "/" u_expr 
               | m_expr "^" u_expr '''
    if len(p) == 2:
        p[0] = p[1]
    else: 
        p[0] = ["MATHOP",p[2],p[1],p[3]]

def p_u_expr(p):
    '''u_expr : power
               | "-" u_expr
               | "+" u_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else: 
        p[0] = ["SIGN",p[1],p[2]]

def p_power(p):
    '''power : primary
              | primary POWER u_expr'''
    if len(p) == 2: 
        p[0] = p[1]
    else:
        p[0] = ["MATHOP","**",p[1] , p[3]]
    # print 'At power: p[0] is %s' % `p[0]`

def p_primary(p):
    '''primary : atom
                | primary_att
                | subscription
                | slicing
                | call'''
    # print 'Primary -> %s' % repr(p[1])
    p[0] = p[1]

# Separated out so that we can re-initialise subscription category
def p_primary_att(p):
    '''primary_att : attributeref'''
    p.parser.sub_subject = ""
    p[0] = p[1]

def p_atom(p):
    '''atom : ID 
             | item_tag 
             | literal
             | enclosure'''
    # print 'Atom -> %s' % repr(p[1])
    p[0] = ["ATOM",p[1]]

def p_item_tag(p):
    '''item_tag : ITEM_TAG'''
    p[0] = ["ITEM_TAG",p[1]]

def p_literal(p): 
    '''literal : stringliteral
                  | INTEGER
                  | HEXINT
                  | OCTINT
                  | BININT
                  | REAL
                  | IMAGINARY'''
    # print 'literal-> %s' % repr(p[1])
    p[0] = ["LITERAL",p[1]]

def p_stringliteral(p):
    '''stringliteral : STRPREFIX SHORTSTRING
                     | STRPREFIX LONGSTRING
                     | SHORTSTRING
                     | LONGSTRING'''
    if len(p)==3: p[0] = p[1]+p[2]
    else: p[0] = p[1]

def p_enclosure(p):
    '''enclosure : parenth_form
                  | string_conversion
                  | list_display '''
    p[0]=p[1]

def p_parenth_form(p):
    '''parenth_form : OPEN_PAREN testlist_star_expr CLOSE_PAREN
                     | OPEN_PAREN CLOSE_PAREN '''
    if len(p) == 3: p[0] = ["GROUP"]
    else:
        p[0] = ["GROUP",p[2]]
    # print 'Parens: %s' % `p[0]`

def p_string_conversion(p):
    '''string_conversion : "`" testlist_star_expr "`" '''
    # WARNING: NOT IN PUBLISHED dREL papaer
    p[0] = ["FUNC_CALL","str",p[2]]

def p_list_display(p):
    ''' list_display : "[" maybe_nline listmaker maybe_nline "]"
                     | "[" maybe_nline "]" '''
    if len(p) == 4: p[0] = ["LIST"]
    else:
        p[0] = ["LIST"] + p[3]
    

# scrap the trailing comma
def p_listmaker(p):
    '''listmaker : expression listmaker2  '''
    p[0] = [p[1]] + p[2]
    # print 'listmaker: %s' % `p[0]`

def p_listmaker2(p):
    '''listmaker2 : "," maybe_nline expression 
                  | listmaker2 "," maybe_nline expression
                  |             '''
    if len(p) == 4:
        p[0] = [p[3]]
    elif len(p) < 2:
        p[0] = p[0]
    else:
        p[0] = p[1] + [p[4]] 

# Note that we need to catch tags of the form 't.12', which
# our lexer will interpret as ID REAL.  We therefore also
# accept t.12(3), which is not allowed, but we don't bother
# trying to catch this error here.
 
def p_attributeref(p):
    '''attributeref : primary attribute_tag '''
    p[0] = ["ATTRIBUTE",p[1],p[2]]

def p_attribute_tag(p):
    '''attribute_tag : "." ID 
                     | REAL '''
    if len(p) == 3:
        p[0] = p[2]
    else: 
        p[0] = p[1][1:]

def p_subscription(p):
    '''subscription : primary "[" expression "]" '''
    p[0] = ["SUBSCRIPTION",p[1],p[3]]

def p_slicing(p):
    '''slicing :  primary "[" proper_slice "]"
               |  primary "[" slice_list "]" '''
    p[0] = ["SLICE", p[1], p[3] ] 

def p_proper_slice(p):
    '''proper_slice : short_slice
                    | long_slice '''
    p[0] = [p[1]]

# Our AST slice convention is that, if anything is mentioned,
# the first element is always
# explicitly mentioned. A single element will be a starting
# element. Two elements are start and finish. An empty list
# is all elements. Three elements are start, finish, step.
# We combine these into a list of slices.

def p_short_slice(p):
    '''short_slice : ":"
                   | expression ":" expression
                   | ":" expression
                   | expression ":" '''
    if len(p) == 2: p[0] = []
    if len(p) == 4: p[0] = [p[1],p[3]]
    if len(p) == 3 and p[1] == ":":
        p[0] = [0,p[2]]
    if len(p) == 3 and p[2] == ":":
        p[0] = [p[1]]

def p_long_slice(p):
    '''long_slice : short_slice ":" expression '''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = p[1]

def p_slice_list(p):
    ''' slice_list : slice_item
                   | slice_list "," slice_item '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_slice_item(p):
    ''' slice_item : expression 
                   | proper_slice '''
    p[0] = p[1]

def p_call(p):
    '''call : ID OPEN_PAREN CLOSE_PAREN
            | ID OPEN_PAREN argument_list CLOSE_PAREN '''
    if len(p) == 4:
        p[0] = ["FUNC_CALL",p[1],[]]
    else:
        p[0] = ["FUNC_CALL",p[1],p[3]]
    #print "Function call: %s" % `p[0]`

# These are the arguments to a call, not a definition

def p_argument_list(p):
    '''argument_list : func_arg 
                     | argument_list "," func_arg '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_func_arg(p):
    '''func_arg : expression '''
    p[0] = p[1]
                 
#def p_augmented_assignment_stmt(p):
#    '''augmented_assignment_stmt : target_list AUGOP testlist_star_expr'''
#    if p[2] == "++=":          #append to list
#        p[0] = ["CONCAT",p[1],p[3]]
#    else:
#        p[0] = ["ASSIGN",p[1],p[2],p[3]]

# We simultaneously create multiple results for a single category.  In 
# this case __dreltarget is a dictionary with keys for each category
# entry.

def p_fancy_drel_assignment_stmt(p):
    '''fancy_drel_assignment_stmt : ID OPEN_PAREN dotlist CLOSE_PAREN ''' 
    p[0] = ["FANCY_ASSIGN",p[1],p[3]]
#    print "Fancy assignment -> " + `p[0]`

# Something made up specially for drel.  We accumulate results for a series of
# items in a dictionary which is returned.  A newline is OK between assignments

def p_dotlist(p):
    '''dotlist : "." ID "=" expression
               | dotlist "," "." ID "=" expression '''               
    if len(p) <= 5:   #first element of dotlist
        p[0] = [[p[2],p[4]]]
    #    p.parser.fancy_drel_id = p[-2]
    #    if p[-2] == p.parser.target_id:      #we will return the results
    #        realid = p[-2]+"."+p[2]
    #        p[0] = "__dreltarget.update({'%s':__dreltarget.get('%s',[])+[%s]})\n" % (realid,realid,p[4])
    #    else:
    #        p[0] = p[-2] + "".join(p[1:]) + "\n"
    #    print 'Fancy id is ' + `p[-2]`
    else:              #append to previous elements
         p[0] = p[1] + [[p[4],p[6]]]
    #    if p.parser.fancy_drel_id == p.parser.target_id:
    #        realid = p.parser.fancy_drel_id + "." + p[4]
    #        p[0] = p[1] + "__dreltarget.update({'%s':__dreltarget.get('%s',[])+[%s]})\n" % (realid,realid,p[6])
    #    else:
    #        p[0] =  p[1] + p.parser.fancy_drel_id + "".join(p[3:]) + "\n"

#def p_assignment_stmt(p):
#    '''assignment_stmt : target_list "=" testlist_star_expr '''
#    p[0] = ["ASSIGN", p[1],"=",p[3]]

def p_exprlist(p):
    ''' exprlist : a_expr
                 | exprlist "," a_expr ''' 
    if len(p) == 2:
        p[0] = [p[1]]
    else: p[0] = p[1] + [p[3]]

# now for the compound statements. We prepare them as a "STATEMENT"
# list for smooth processing in the simple_stmt production

def p_compound_stmt(p):
    '''compound_stmt : if_stmt
                     | if_else_stmt
                     | for_stmt
                     | do_stmt
                     | loop_stmt
                     | with_stmt
                     | repeat_stmt
                     | funcdef '''
    p[0] = ["STATEMENTS",[p[1]]]
    #print "Compound statement: \n" + p[0]

# There must only be one else statement at the end of the else if statements,
# so we show this by creating a separate production
def p_if_else_stmt(p):
    '''if_else_stmt : if_stmt ELSE suite'''
    p[0] = p[1]
    p[0].append(p[3])

# The AST node is [IF_EXPR,cond, suite,[[elseif cond1,suite],[elseifcond2,suite]...]]
def p_if_stmt(p):
    '''if_stmt : IF OPEN_PAREN expression CLOSE_PAREN maybe_nline suite 
               | if_stmt ELSEIF OPEN_PAREN expression CLOSE_PAREN maybe_nline suite '''
    if len(p) == 7:
       p[0] = ["IF_EXPR"]
       p[0].append(p[3])
       p[0].append(p[6])
       p[0].append([])
    else:
       p[0] = p[1]
       p[0][3].append([p[4],p[7]])

# Note the dREL divergence from Python here: we allow compound
# statements to follow without a separate block (like C etc.)
# For simplicity we indent consistently (further up). Where
# we have a single statement immediately following we have
# to make the statement block.  A small_stmt will be a single
# production, so must be put into a list in order to match
# the 'statements' structure (i.e. 2nd element is a list of
# statements).  A compound_stmt is thus forced to be also a
# non-listed object.

def p_suite(p):
    '''suite : statement
               | "{" maybe_nline statements "}" maybe_nline '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[3]  #already have a statement block

def p_for_stmt(p):
    '''for_stmt : FOR exprlist IN testlist_star_expr suite'''
    p[0] = ["FOR", p[2], p[4], p[5]]

# We split the loop statement into parts so that we can capture the
# ID before the suite is processed.  Note that we should record that
# we have an extra indent due to the loop test and remove it at the
# end, but we haven't done this yet.

def p_loop_stmt(p):
    '''loop_stmt : loop_head suite '''
    p[0] = ["LOOP"] + p[1] + [p[2]]

# We capture a list of all the actually present items in the current
# datafile
def p_loop_head(p):
    '''loop_head : LOOP ID AS ID 
                 | LOOP ID AS ID ":" ID 
                 | LOOP ID AS ID ":" ID restricted_comp_operator ID '''

    p[0] = [p[2],p[4]]
    if len(p)>= 7:
        p[0] = p[0] + [p[6]]
    else: p[0] = p[0] + [""]
    if len(p) >= 9:
        p[0] = p[0] + [p[7],p[8]]
    else: p[0] = p[0] + ["",""]

def p_do_stmt(p):
    '''do_stmt : do_stmt_head suite '''
    p[0] = p[1] + [p[2]]

# To translate the dREL do to a for statement, we need to make the
# end of the range included in the range

def p_do_stmt_head(p):
    '''do_stmt_head : DO ID "=" expression "," expression
                    | DO ID "=" expression "," expression "," expression'''

    p[0] = ["DO",p[2],p[4],p[6]]
    if len(p)==9:
        p[0] = p[0] + [p[8]]
    else:
        p[0] = p[0] + [["EXPR",["LITERAL","1"]]]

def p_repeat_stmt(p):
    '''repeat_stmt : REPEAT suite'''
    p[0] = ["REPEAT",p[2]]

def p_with_stmt(p):
    '''with_stmt : with_head maybe_nline suite'''
    p[0] = p[1]+[p[3]] 
    #outgoing = p.parser.special_id.pop()
    #outindents = filter(lambda a:a[2],outgoing.values())
    #p.parser.indent = p.parser.indent[:len(p.parser.indent)-4*len(outindents)]

# Done here to capture the id before processing the suite
# A with statement doesn't need any indenting...
# We assume a variable 'loopable_cats' is available to us
# We have a somewhat complex structure to allow for multiple simultaneous
# with statements, although that is not in the standard.  We could
# probably assume a single packet variable per with statement and
# simplify the special_id structure a bit

# Note that we allow multiple with statements grouped together (as long
# as nothing else separates them)
def p_with_head(p):
    '''with_head : WITH ID AS ID'''
    # p[0] = "__pycitems = self.names_in_cat('%s')" % p[4]
    # p.parser.special_id.append({p[2]: [p[4],"",False]})
    # if p[4] in p.parser.loopable_cats:
    #    tb_length = len(p.parser.withtable)  #generate unique id
    #    p.parser.withtable.update({p[4]:"__pi%d" % tb_length})
    #    p.parser.special_id[-1][p[2]][1] = p.parser.withtable[p[4]]
    #print "%s means %s" % (p[2],p.parser.special_id[-1][p[2]][0])
    #if p.parser.special_id[-1][p[2]][1]:
    #    print "%s looped using %s" % (p[2],p.parser.special_id[-1][p[2]][1])
    p[0] = ["WITH",p[2],p[4]]

def p_funcdef(p):
    ''' funcdef : FUNCTION ID OPEN_PAREN arglist CLOSE_PAREN suite '''
    p[0] = ["FUNCTION",p[2],p[4],p[6]]

def p_arglist(p):
    ''' arglist : ID ":" list_display
                | arglist "," ID ":" list_display '''
    if len(p) == 4: p[0] = [(p[1],p[2])]
    else: p[0] = p[1] + [(p[3],p[5])]

def p_maybe_nline(p):
    ''' maybe_nline : newlines
                    | empty '''
    pass

# We need to allow multiple newlines here and not just in the lexer as
# an intervening comment can cause multiple newline tokens to appear
def p_newlines(p):
    ''' newlines : NEWLINE
                 | newlines NEWLINE '''
    pass

def p_empty(p):
    ''' empty       : '''
    pass

def p_error(p):
    print 'Syntax error at position %d, line %d token %s, value %s' % (p.lexpos,p.lineno,p.type,p.value)
    print 'Surrounding text: ' + p.lexer.lexdata[max(p.lexpos - 100,0): p.lexpos] + "*" + \
       p.lexer.lexdata[p.lexpos:min(p.lexpos + 100,len(p.lexer.lexdata))]
    raise SyntaxError, 'Syntax error at token %s, value %s' % (p.type,p.value)
 
# The following function creates a function. The function
# modifies the 'ciffile' argument in place.  The pi argument is a 
# packet index for when we are accessing looped data using a
# 'with' statement.  Returnname is the variable name for returned
# data, and for looped data this should always be "__dreltarget".
# See the test file for ways of using this
#
# The parser data is a two-element list with the first element the text of
# the function, and the second element a table of looped values
#
# Normally this function is called in a context where 'self' is a CifDic
# object; for the purposes of testing, we want to be able to remove any
# references to dictionary methods and so include the have_sn flag.

def make_func(parser_data,funcname,returnname,cat_meth = False,have_sn=True):
    import re
    if not returnname: returnname = "__dreltarget"
    func_text = parser_data[0]
    # now indent the string
    noindent = func_text.splitlines()
    # get the minimum indent and remove empty lines
    noindent = filter(lambda a:a,noindent)
    no_spaces = map(lambda a:re.match(r' *',a),noindent)
    no_spaces = map(lambda a:a.end(),no_spaces)
    min_spaces = min(no_spaces)+4   # because we add 4 ourselves to everything
    with_indices = parser_data[1].values()
    w_i_list = ",".join(with_indices)
    preamble = "def %s(self,ciffile,%s):\n" % (funcname,w_i_list)
    preamble += min_spaces*" " + "import StarFile\n"
    preamble += min_spaces*" " + "import math\n"
    preamble += min_spaces*" " + "import numpy\n"
    if have_sn:
        preamble += min_spaces*" " + "self.switch_numpy(True)\n"
    if cat_meth:
        preamble += min_spaces*" " + "%s = {}\n" % returnname
    indented = map(lambda a:"    " + a+"\n",noindent)  
    postamble = ""
    if have_sn:
        postamble = " "*min_spaces + "self.switch_numpy(False)\n"
    postamble += " "*min_spaces + "return %s" % returnname
    final = preamble + "".join(indented) + postamble
    return final

parser = yacc.yacc()    
parser.indent = ""
parser.special_id=[{}]
parser.looped_value = False    #Determines with statement construction 
parser.target_id = None
parser.withtable = {}          #Table of 'with' packet access info
parser.sub_subject=""
