from string import *
import re
from yappsrt import *

class LispScanner(Scanner):
    patterns = [
        ('r"\\)"', re.compile('\\)')),
        ('r"\\("', re.compile('\\(')),
        ('\\s+', re.compile('\\s+')),
        ('NUM', re.compile('[0-9]+')),
        ('ID', re.compile('[-+*/!@$%^&=.a-zA-Z0-9_]+')),
        ('STR', re.compile('"([^\\\\"]+|\\\\.)*"')),
    ]
    def __init__(self, str):
        Scanner.__init__(self,None,['\\s+'],str)

class Lisp(Parser):
    def expr(self):
        _token_ = self._peek('ID', 'STR', 'NUM', 'r"\\("')
        if _token_ == 'ID':
            ID = self._scan('ID')
            return ('id',ID)
        elif _token_ == 'STR':
            STR = self._scan('STR')
            return ('str',eval(STR))
        elif _token_ == 'NUM':
            NUM = self._scan('NUM')
            return ('num',atoi(NUM))
        else: # == 'r"\\("'
            r"\(" = self._scan('r"\\("')
            e = []
            while self._peek() != 'r"\\)"':
                expr = self.expr()
                e.append(expr)
            r"\)" = self._scan('r"\\)"')
            return e


def parse(rule, text):
    P = Lisp(LispScanner(text))
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
