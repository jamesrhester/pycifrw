globalvars = {}       # We will store the calculator's variables here

def lookup(map, name):
    for x,v in map:  
        if x==name: return v
    if name not in globalvars.keys(): print 'Undefined:', name
    return globalvars.get(name, 0)


from string import *
import re
from yapps_compiled_rt import *

class CalculatorScanner(Scanner):
    patterns = [
        ('"in"', re.compile('in')),
        ('"="', re.compile('=')),
        ('"let"', re.compile('let')),
        ('"\\\\)"', re.compile('\\)')),
        ('"\\\\("', re.compile('\\(')),
        ('"/"', re.compile('/')),
        ('"[*]"', re.compile('[*]')),
        ('"-"', re.compile('-')),
        ('"[+]"', re.compile('[+]')),
        ('"set"', re.compile('set')),
        ('[ \r\t\n]+', re.compile('[ \r\t\n]+')),
        ('END', re.compile('$')),
        ('NUM', re.compile('[0-9]+')),
        ('VAR', re.compile('[a-zA-Z_]+')),
    ]
    def __init__(self, str):
        Scanner.__init__(self,None,['[ \r\t\n]+'],str)

class Calculator(Parser):
    def goal(self):
        _token_ = self._peek('"set"', 'NUM', 'VAR', '"\\\\("', '"let"')
        if _token_ != '"set"':
            expr = self.expr([])
            END = self._scan('END')
            print '=', expr
            return expr
        else: # == '"set"'
            self._scan('"set"')
            VAR = self._scan('VAR')
            expr = self.expr([])
            END = self._scan('END')
            globalvars[VAR] = expr
            print VAR, '=', expr
            return expr

    def expr(self, V):
        factor = self.factor(V)
        n = factor
        while self._peek('"[+]"', '"-"', 'END', '"\\\\)"', '"in"', '"[*]"', '"/"') in ['"[+]"', '"-"']:
            _token_ = self._peek('"[+]"', '"-"')
            if _token_ == '"[+]"':
                self._scan('"[+]"')
                factor = self.factor(V)
                n = n+factor
            else: # == '"-"'
                self._scan('"-"')
                factor = self.factor(V)
                n = n-factor
        return n

    def factor(self, V):
        term = self.term(V)
        v = term
        while self._peek('"[*]"', '"/"', '"[+]"', '"-"', 'END', '"\\\\)"', '"in"') in ['"[*]"', '"/"']:
            _token_ = self._peek('"[*]"', '"/"')
            if _token_ == '"[*]"':
                self._scan('"[*]"')
                term = self.term(V)
                v = v*term
            else: # == '"/"'
                self._scan('"/"')
                term = self.term(V)
                v = v/term
        return v

    def term(self, V):
        _token_ = self._peek('NUM', 'VAR', '"\\\\("', '"let"')
        if _token_ == 'NUM':
            NUM = self._scan('NUM')
            return atoi(NUM)
        elif _token_ == 'VAR':
            VAR = self._scan('VAR')
            return lookup(V, VAR)
        elif _token_ == '"\\\\("':
            self._scan('"\\\\("')
            expr = self.expr()
            self._scan('"\\\\)"')
            return expr
        else: # == '"let"'
            self._scan('"let"')
            VAR = self._scan('VAR')
            self._scan('"="')
            expr = self.expr(V)
            V = [(VAR, expr)] + V
            self._scan('"in"')
            expr = self.expr(V)
            return expr


def parse(rule, text):
    P = Calculator(CalculatorScanner(text))
    return wrap_error_reporter(P, rule)



if __name__=='__main__':
    print 'Welcome to the calculator sample for Yapps 2.0.'
    print '  Enter either "<expression>" or "set <var> <expression>",'
    print '  or just press return to exit.  An expression can have'
    print '  local variables:  let x = expr in expr'
    # We could have put this loop into the parser, by making the
    # `goal' rule use (expr | set var expr)*, but by putting the
    # loop into Python code, we can make it interactive (i.e., enter
    # one expression, get the result, enter another expression, etc.)
    while 1:
        try: s = raw_input('>>> ')
	except EOFError: break
        if not strip(s): break
        parse('goal', s)
    print 'Bye.'

