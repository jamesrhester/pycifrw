#Attempt to implement dREL using PLY (Python Lex Yacc)
from __future__ import print_function
import ply.lex as lex
import re    #for multiline flag

states = (
    ('paren','inclusive'),
    )

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
    'BADAND',
    'OR',
    'BADOR',
    'IN',
    'NOT',
    'DO',
    'FOR',
    'LOOP',
    'REPEAT',
    'AS',
    'WITH',
    'WHERE',
    'ELSEIF',
    'ELSE',
    'BREAK',
    'NEXT',
    'IF',
    'SWITCH',
    'CASE',
    'DEFAULT',
    'AUGOP',
    'PRINT',
    'FUNCTION',
    'NEWLINE',
    'ESCAPE_NEWLINE',
    'OPEN_PAREN',
    'CLOSE_PAREN'
     )

literals = '+*-/;[],:^<>{}=.`&|'  #'&' and '|' are pycifrw extensions
t_INITIAL_ignore = ' \t'
t_paren_ignore = ' \t\n'

def t_error(t):
    print('Illegal character %s' % repr(t.value[0]))

t_POWER = r'\*\*'
t_ISEQUAL = r'=='
t_NEQ = r'!='
t_GTE = r'>='
t_LTE = r'<='
t_ELLIPSIS = r'\.\.\.'
t_BADOR = r'\|\|'
t_BADAND = r'&&'

def t_AUGOP(t):
    r'(\+\+=)|(\+=)|(-=)|(--=)|(\*=)|(/=)'
    return t

# We do not have this as a literal so that we can switch to ignoring newlines
def t_INITIAL_OPEN_PAREN(t):
    r'\('
    t.lexer.paren_level = 1
    t.lexer.begin('paren')
    return t

def t_paren_OPEN_PAREN(t):
    r'\('
    t.lexer.paren_level +=1
    return t

def t_paren_CLOSE_PAREN(t):
    r'\)'
    t.lexer.paren_level -=1
    if t.lexer.paren_level == 0:
        t.lexer.begin('INITIAL')
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
        print('Error converting %s to real' % t.value)
    return t

# Do the binary,octal etc before decimal integer otherwise the 0 at
# the front will match the decimal integer 0
#
def t_BININT(t):
    r'0[bB][0-1]+'
    try:
        t.value = repr(int(t.value[2:],base=2))
    except ValueError:
        print('Unable to convert binary value %s' % t.value)
    return t

def t_OCTINT(t):
    r'0[oO][0-7]+'
    try:
        t.value = repr(int(t.value[2:],base=8))
    except ValueError:
        print('Unable to convert octal value %s' % t.value)
    return t

def t_HEXINT(t):
    r'0[xX][0-9a-fA-F]+'
    try:
        t.value = repr(int(t.value,base=16))
    except ValueError:
        print('Unable to convert hex value %s' % t.value)
    return t

def t_INTEGER(t):
    r'[0-9]+'
    try:
        value = int(t.value)
    except ValueError:
        print('Incorrect integer value %s' % t.value)
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

# special to avoid any ambiguity
def t_ELSEIF(t):
    r"(?i)ELSE\s+IF"
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
    'Break': 'BREAK',
    'if': 'IF',
    'If': 'IF',
    'switch': 'SWITCH',
    'case' : 'CASE',
    'Function' : 'FUNCTION',
    'function' : 'FUNCTION',
    'Print' : 'PRINT',
    'print' : 'PRINT',
    'Repeat': 'REPEAT',
    'repeat': 'REPEAT',
    'default' : 'DEFAULT'
    }

def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_$]*'
    t.type = reserved.get(t.value,'ID')
    return t

# Item tags can have underscores and digits inside, and must have
# at least one underscore at the front
def t_ITEM_TAG(t):
    r'_[a-zA-Z_0-9]+'
    return t

def t_ESCAPE_NEWLINE(t):
    r'\\\n'
    t.lexer.lineno += 1

def t_INITIAL_NEWLINE(t):
    r'\n[\n \t]*'
    t.lexer.lineno+=len(t.value)
    return t

def t_COMMENT(t):
    r'\#.*'
    pass

lexer = lex.lex(reflags=re.MULTILINE)
if __name__ == "__main__":
    lex.runmain(lexer)
