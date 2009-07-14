#Attempt to implement dREL using PLY (Python Lex Yacc)
import ply.lex as lex
import re    #for multiline flag

tokens = (
    'SHORTSTRING',
    'LONGSTRING',
    'INTEGER',
    'BININT',
    'HEXINT',
    'OCTINT',
    'REAL',
    'POWER',
    'ISEQUAL',
    'NEQ',
    'GTE',
    'LTE',
    'IMAGINARY',
    'ID',            #variable name
    'ITEM_TAG',      #cif item as variable
    'COMMENT',
    'STRPREFIX',
    'ELLIPSIS',
    'AND',
    'OR',
    'IN',
    'NOT',
    'DO',
    'FOR',
    'LOOP',
    'AS',
    'WITH',
    'WHERE',
    'ELSE',
    'BREAK',
    'NEXT',
    'IF',
    'SWITCH',
    'CASE',
    'DEFAULT',
    'AUGOP',
    'PRINT',
    'FUNCTION'
     )

literals = '+*-/;()[],:^<>{}=.`'
t_ignore = ' \t\n'

def t_error(t):
    print 'Illegal character %s' % repr(t.value[0])

t_POWER = r'\*\*'
t_ISEQUAL = r'=='
t_NEQ = r'!='
t_GTE = r'>='
t_LTE = r'<='
t_ELLIPSIS = r'\.\.\.'

def t_AUGOP(t):
    r'(\+\+=)|(\+=)|(-=)|(\*=)|(/=)'
    return t

# Do the reals before the integers, otherwise the integer will
# match the first part of the real
#
def t_IMAGINARY(t):
    r'(((([0-9]+[.][0-9]*)|([.][0-9]+))([Ee][+-]?[0-9]+)?)|([0-9]+))[jJ]'
    return t

def t_REAL(t):
    r'(([0-9]+[.][0-9]*)|([.][0-9]+))([Ee][+-]?[0-9]+)?'
    try:
        value = float(t.value)
    except ValueError:
        print 'Error converting %s to real' % t.value
    return t

# Do the binary,octal etc before decimal integer otherwise the 0 at
# the front will match the decimal integer 0
#
def t_BININT(t):
    r'0[bB][0-1]+'
    try:
        t.value = `int(t.value[2:],base=2)`
    except ValueError:
        print 'Unable to convert binary value %s' % t.value
    return t

def t_OCTINT(t):
    r'0[oO][0-7]+'
    try:
        t.value = `int(t.value[2:],base=8)`
    except ValueError:
        print 'Unable to convert octal value %s' % t.value
    return t

def t_HEXINT(t):
    r'0[xX][0-9a-fA-F]+'
    try:
        t.value = `int(t.value,base=16)`
    except ValueError:
        print 'Unable to convert hex value %s' % t.value
    return t 

def t_INTEGER(t):
    r'[0-9]+'
    try:
        value = int(t.value)
    except ValueError:
        print 'Incorrect integer value %s' % t.value
    return t

def t_STRPREFIX(t):
    r'r(?=["\'])|u(?=["\'])|R(?=["\'])|U(?=["\'])|ur(?=["\'])|UR(?=["\'])|Ur(?=["\'])|uR(?=["\'])'
    return t

# try longstring first as otherwise the '' will match a shortstring
def t_LONGSTRING(t):
    r"('''([^\\]|(\\.))*''')|(\"\"\"([^\\]|(\\.))*\"\"\")"
    return t


def t_SHORTSTRING(t):
    r"('([^'\n]|(\\.))*')|(\"([^\"\n]|(\\.))*\")"
    return t

reserved = {
    'and': 'AND',
    'or': 'OR',
    'in': 'IN',
    'not': 'NOT',
    'do': 'DO',
    'Do': 'DO',
    'for': 'FOR',
    'For': 'FOR',
    'loop': 'LOOP',
    'Loop': 'LOOP',
    'as': 'AS',
    'with': 'WITH',
    'With': 'WITH',
    'where': 'WHERE',
    'Where': 'WHERE',
    'else': 'ELSE',
    'Else': 'ELSE',
    'Next': 'NEXT',
    'next' : 'NEXT',
    'break': 'BREAK',
    'if': 'IF',
    'If': 'IF',
    'switch': 'SWITCH',
    'case' : 'CASE',
    'Function' : 'FUNCTION',
    'function' : 'FUNCTION',
    'Print' : 'PRINT',
    'print' : 'PRINT',
    'default' : 'DEFAULT'
    }

def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_$]*'
    t.type = reserved.get(t.value,'ID')
    if t.type == 'NEXT': t.value = 'continue'
    return t

# Item tags can have periods and underscores inside, and must have
# at least one of them at the front 
def t_ITEM_TAG(t):
    r'_[a-zA-Z_.]+'
    return t

def t_COMMENT(t):
    r'\#.*'
    pass

lexer = lex.lex(reflags=re.MULTILINE)
if __name__ == "__main__":
    lex.runmain(lexer)
