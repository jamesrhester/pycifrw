from string import *
import re
from yapps_compiled_rt import *

class TestScanner(Scanner):
    patterns = [
        ("'a'", re.compile('a')),
        ("'c'", re.compile('c')),
    ]
    def __init__(self, str):
        Scanner.__init__(self,None,[],str)

class Test(Parser):
    def R(self):
        _token_ = self._peek()
        if _token_ == "'a'":
            A = self.A()
        else: # == "'c'"
            pass
        self._scan("'c'")

    def A(self):
        while 1:
            self._scan("'a'")
            if self._peek() != "'a'": break


def parse(rule, text):
    P = Test(TestScanner(text))
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
