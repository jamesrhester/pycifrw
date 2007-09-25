# Test suite for the dRel parser
#

import unittest
import drel_lex
import drel_yacc

# Test simple statements

class SimpleStatementTestCase(unittest.TestCase):
    def setUp(self):
        #create our lexer and parser
        self.lexer = drel_lex.lexer
        self.parser = drel_yacc.parser

    def testrealnum(self):
        res = self.parser.parse('5.45\n',lexer=self.lexer)
        assert(res=='5.45')

if __name__=='__main__':
    unittest.main()
