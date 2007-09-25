# A dREL grammar written for python-ply
#
import drel_lex
import ply.yacc as yacc
tokens = drel_lex.tokens

def p_error(p):
    print 'Syntax error at token %s, value %s' % (p.type,p.value)

# Overall translation unit

def p_file_input_1(p):
    '''file_input : NEWLINE 
                  | statement'''
    p[0] = p[1]

def p_file_input_2(p):
    '''file_input : file_input NEWLINE
                  | file_input statement'''
    p[0] = p[1]

def p_statement(p):
    '''statement : stmt_list NEWLINE 
                | compound_stmt'''
    p[0] = p[1]

def p_stmt_list(p): 
    '''stmt_list : simple_stmt
                 | stmt_list ";" simple_stmt
                 | stmt_list ";" simple_stmt ";" '''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = ";".join(p[1],p[3])

def p_simple_stmt(p):
    '''simple_stmt : expression_list
                    | assignment_stmt
                    | BREAK
                    | NEXT'''
    p[0] = p[1]

def p_expression_list(p):
    '''expression_list : expression
                        | expression_list "," expression
                        | expression_list "," expression "," '''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = " ".join(p[1],",",p[3])


def p_expression(p):
    '''expression : or_test 
                   | or_test IF or_test ELSE or_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = " ".join(p[1],"if",p[3],"else", p[5])

def p_or_test(p):
    ''' or_test : and_test
                 | or_test OR and_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = " ".join(p[1],"or",p[3])

def p_and_test(p):
    '''and_test : not_test
                 | and_test AND not_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = " ".join(p[1],"and",p[3])

def p_not_test(p):
    '''not_test : comparison
                 | NOT not_test'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = " ".join("not",p[2])

def p_comparison(p):
    '''comparison : a_expr
                   | a_expr comp_operator a_expr'''
    if len(p) == 2: p[0] = p[1]
    else:
       p[0] = " ".join(p[1],p[2],p[3])

def p_comp_operator(p):
    '''comp_operator : "<"
                     | ">"
                     | GTE
                     | LTE
                     | NEQ
                     | EQUALS
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
        p[0] = p[1] + p[2] + p[3]

def p_m_expr(p):
    '''m_expr : u_expr
               | m_expr "*" u_expr
               | m_expr "/" u_expr 
               | m_expr "^" u_expr '''
    if len(p) == 2:
        p[0] = p[1]
    else: 
        if p[2] == "^":
            p[0] = "mat_cross_prod("+p[1]+" , " + p[3]
        else:
            p[0] = p[1] + p[2] + p[3]

def p_u_expr(p):
    '''u_expr : power
               | "-" u_expr
               | "+" u_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else: 
        p[0] = p[1] + p[2] + p[3]

def p_power(p):
    '''power : primary
              | primary POWER u_expr'''
    if len(p) == 2: 
        p[0] = p[1]
    else:
        p[0] = p[1] + "**" + p[3]
    print 'At power: p[0] is %s' % `p[0]`

def p_primary(p):
    '''primary : atom
                | attributeref
                | subscription
                | slicing
                | call'''
    print 'Primary -> %s' % repr(p[1])
    p[0] = p[1]

def p_atom(p):
    '''atom : ID 
             | literal
             | enclosure'''
    print 'Atom -> %s' % repr(p[1])
    p[0] = p[1]

def p_literal(p): 
    '''literal : stringliteral
                  | INTEGER
                  | HEXINT
                  | OCTINT
                  | BININT
                  | REAL
                  | imagnumber'''
    print 'literal-> %s' % repr(p[1])
    p[0] = p[1]

def p_imagnumber(p):
    '''imagnumber : REAL COMPLEX
                   | INTEGER COMPLEX'''
    p[0] = p[1]+'j'
    pass

def p_stringliteral(p):
    '''stringliteral : STRPREFIX SHORTSTRING
                     | STRPREFIX LONGSTRING
                     | SHORTSTRING
                     | LONGSTRING'''
    pass

def p_enclosure(p):
    '''enclosure : parenth_form
                  | list_display '''
    pass

def p_parenth_form(p):
    '''parenth_form : "(" expression_list ")"
                     | "(" ")" '''
    pass

def p_list_display(p):
    ''' list_display : "[" listmaker "]"
                     | "[" "]" '''
    pass

def p_listmaker(p):
    '''listmaker : expression listmaker2 ","
                  | expression listmaker2 '''
    pass

def p_listmaker2(p):
    '''listmaker2 : list_for
                  | "," expression
                  |             '''
    pass

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

def p_attributeref(p):
    '''attributeref : primary "." ID ''' 
    pass

def p_subscription(p):
    '''subscription : primary "[" expression_list "]" '''
    pass

def p_slicing(p):
    '''slicing : simple_slicing
               | extended_slicing '''
    pass

def p_simple_slicing(p):
    '''simple_slicing : primary "[" short_slice "]" '''
    pass

def p_short_slice(p):
    '''short_slice : ":"
                   | expression ":" expression
                   | ":" expression
                   | expression ":" '''
    pass

def p_extended_slicing(p):
    '''extended_slicing : primary "[" slice_list "]" '''
    pass

def p_slice_list(p):
    '''slice_list : slice_item
                  | slice_list "," slice_item
                  | slice_list "," slice_item "," '''
    pass

def p_slice_item(p):
    '''slice_item : expression
                  | proper_slice
                  | ELLIPSIS '''
    pass

def p_proper_slice(p):
    '''proper_slice : short_slice
                    | long_slice '''
    pass

def p_long_slice(p):
    '''long_slice : short_slice ":"
                  | short_slice ":" expression '''
    pass

# Last of the primary non-terminals...

def p_call(p):
    '''call : primary "(" ")"
            | primary "(" argument_list ")" '''
    pass

def p_argument_list(p):
    '''argument_list : expression
                     | argument_list "," expression '''
    pass

def p_assignment_stmt(p):
    '''assignment_stmt : target_list "=" expression_list'''
    pass

def p_target_list(p):
    '''target_list : target 
                   | target_list "," target '''
    pass

def p_target(p):
    '''target : ID
              | "(" target_list ")"
              | "[" target_list "]"
              | attributeref
              | subscription
              | slicing  '''
    pass

# now for the compound statements

def p_compound_stmt(p):
    '''compound_stmt : if_stmt
                     | for_stmt
                     | do_stmt
                     | loop_stmt
                     | with_stmt
                     | where_stmt
                     | switch_stmt '''
    pass

def p_if_stmt(p):
    '''if_stmt : IF expression suite
               | if_stmt ELSE if_stmt
               | if_stmt ELSE suite '''
    pass

def p_suite(p):
    '''suite : simple_stmt
             | "{" statement_block "}" '''
    pass

def p_statement_block(p):
    '''statement_block : statement
                      | statement_block statement'''
    pass

def p_for_stmt(p):
    '''for_stmt : FOR target_list IN expression_list suite'''
    pass

def p_loop_stmt(p):
    '''loop_stmt : LOOP ID AS target_list suite'''
    pass

def p_do_stmt(p):
    '''do_stmt : DO ID "=" expression "," expression
               | DO ID "=" expression "," expression "," expression '''
    pass

def p_with_stmt(p):
    '''with_stmt : WITH ID AS target_list suite'''
    pass

def p_where_stmt(p):
    '''where_stmt : WHERE expression suite ELSE suite'''
    pass

def p_switch_stmt(p):
    '''switch_stmt : SWITCH ID "{" caselist DEFAULT suite "}" '''
    pass

def p_caselist(p):
    '''caselist : CASE target_list suite
                | caselist CASE target_list suite'''
    pass

 
parser = yacc.yacc()    
