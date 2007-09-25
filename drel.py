#Attempt to implement dREL using PLY (Python Lex Yacc)
import ply.lex as lex

tokens = (
    'STRING',
    'INTEGER',
    'BININT',
    'HEXINT',
    'OCTINT',
    'ADD',
    'MULTIPLY',
    'POWER',
    'SUBTRACT',
    'DIVIDE',
    'EQUALS',
    'NEQ',
    'GTE',
    'LTE',
    'ID',            #variable name
     )

t_ADD = r'\+'
t_MULTIPLY = r'\*'
t_SUBTRACT = r'-'
t_POWER = r'\*\*'
t_DIVIDE = r'/'

def t_INTEGER(t):
    r'[+-]?[0-9]+'
    try:
        t.value = int(t.value)
    except ValueError:
        print 'Incorrect integer value %s' % t.value
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

