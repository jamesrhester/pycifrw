from string import *
import re
from yapps_compiled_rt import *

class CalculatorScanner(Scanner):
    patterns = [
        ('"\\\\)"', re.compile('\\)')),
        ('"\\\\("', re.compile('\\(')),
        ('"/"', re.compile('/')),
        ('"[*]"', re.compile('[*]')),
        ('"-"', re.compile('-')),
        ('"[+]"', re.compile('[+]')),
        ('END', re.compile('$')),
        ('NUM', re.compile('[0-9]+')),
    ]
    def __init__(self, str):
        Scanner.__init__(self,None,[],str)

class Calculator(Parser):
    def goal(self):
        expr = self.expr()
        END = self._scan('END')
        return expr

    def expr(self):
        factor = self.factor()
        v = factor
        while self._peek('"[+]"', '"-"', 'END', '"\\\\)"') in ['"[+]"', '"-"']:
            _token_ = self._peek('"[+]"', '"-"')
            if _token_ == '"[+]"':
                self._scan('"[+]"')
                factor = self.factor()
                v = v+factor
            else: # == '"-"'
                self._scan('"-"')
                factor = self.factor()
                v = v-factor
        return v

    def factor(self):
        term = self.term()
        v = term
        while self._peek('"[*]"', '"/"', '"[+]"', '"-"', 'END', '"\\\\)"') in ['"[*]"', '"/"']:
            _token_ = self._peek('"[*]"', '"/"')
            if _token_ == '"[*]"':
                self._scan('"[*]"')
                term = self.term()
                v = v*term
            else: # == '"/"'
                self._scan('"/"')
                term = self.term()
                v = v/term
        return v

    def term(self):
        _token_ = self._peek('NUM', '"\\\\("')
        if _token_ == 'NUM':
            NUM = self._scan('NUM')
            return atoi(NUM)
        else: # == '"\\\\("'
            self._scan('"\\\\("')
            expr = self.expr()
            self._scan('"\\\\)"')
            return expr


def parse(rule, text):
    P = Calculator(CalculatorScanner(text))
    return wrap_error_reporter(P, rule)

if __name__=='__main__':
    from sys import argv, stdin
    if len(argv) >= 2:
        if len(argv) >= 3:
            f = open(argv[2],'r')
        else:
            f = stdin
        print parse(argv[1], f.read())
    else: print 'Args:  <rule> [<filename>]'
