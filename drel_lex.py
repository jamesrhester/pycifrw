#Attempt to implement dREL using PLY (Python Lex Yacc)
import ply.lex as lex

tokens = (
    'SHORTSTRING',
    'LONGSTRING',
    'INTEGER',
    'BININT',
    'HEXINT',
    'OCTINT',
    'POWER',
    'EQUALS',
    'NEQ',
    'GTE',
    'LTE',
    'ID',            #variable name
    'COMMENT',
    'ASSIGN',        #assignment
    'COMPLEX',
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
    'DEFAULT'
     )

literals = '+*-/;()[],:^'
t_ignore = ' \t'
def t_error(t):
    print 'Illegal character %s' % repr(t.value[0])

t_POWER = r'\*\*'
t_EQUALS = r'=='
t_NEQ = r'!='
t_GTE = r'>='
t_LTE = r'<='
t_ASSIGN = r'='
t_COMPLEX = r'[jJ]'
t_ELLIPSIS = r'...'

def t_INTEGER(t):
    r'[+-]?[0-9]+'
    try:
        t.value = int(t.value)
    except ValueError:
        print 'Incorrect integer value %s' % t.value
    return t

def t_STRPREFIX(t):
    r'r|u|R|U|ur|UR|Ur|uR'
    return t

def t_SHORTSTRING(t):
    '''('([^'\\\\n]|(\\.))*')|("([^"\\\\n]|(\\.))*")'''
    return t

def t_LONGSTRING(t):
    '''("""([^\\]|(\\.))*""")|\'\'\'([^\\]|(\\.))*\'\'\''''
    return t

def t_BININT(t):
    r'0[bB][0-1]+'
    try:
        t.value = int(t.value[2:],base=2)
    except ValueError:
        print 'Unable to convert binary value %s' % t.value
    return t

def t_OCTINT(t):
    r'0[oO][0-7]+'
    try:
        t.value = int(t.value[2:],base=8)
    except ValueError:
        print 'Unable to convert octal value %s' % t.value
    return t

def t_HEXINT(t):
    r'0[xX][0-9a-fA-F]+'
    try:
        t.value = int(t.value,base=16)
    except ValueError:
        print 'Unable to convert hex value %s' % t.value
    return t

def t_REAL(t):
    r'[+-]?(([0-9]+.[0-9]*)|(.[0-9]+))[Ee][+-]?[0-9]+'
    try:
        t.value = float(t.value)
    except ValueError:
        print 'Error converting %s to real' % t.value
    return t

reserved = {
    'and': 'AND',
    'or': 'OR',
    'in': 'IN',
    'not': 'NOT',
    'do': 'DO',
    'for': 'FOR',
    'loop': 'LOOP',
    'as': 'AS',
    'with': 'WITH',
    'where': 'WHERE',
    'else': 'ELSE',
    'break': 'BREAK',
    'next': 'NEXT',
    'if': 'IF',
    'switch': 'SWITCH',
    'case' : 'CASE',
    'default' : 'DEFAULT'
    }

def t_ID(t):
    r'[a-zA-Z][a-zA-z0-9_.$]*'
    t.type = reserved.get(t.value,'ID')
    return t

def t_COMMENT(t):
    r'#.*'
    pass

lexer = lex.lex()
if __name__ == "__main__":
    lex.runmain(lexer)
