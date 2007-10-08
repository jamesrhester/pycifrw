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
        """test parsing of real numbers"""
        res = self.parser.parse('5.45\n',lexer=self.lexer)
        self.failUnless(res=='5.45')
        res = self.parser.parse('.45e-24\n',lexer=self.lexer)
        self.failUnless(res=='.45e-24')

    def testinteger(self):
        """test parsing an integer"""
        resd = self.parser.parse('1230\n',lexer=self.lexer)
        resx = self.parser.parse('0x4D\n',lexer=self.lexer)
        resb = self.parser.parse('0B0101\n',lexer=self.lexer)
        reso = self.parser.parse('0o731\n',lexer=self.lexer)
        self.failUnless(resd=='1230')
        self.failUnless(resx=='77')
        self.failUnless(resb=='5')
        self.failUnless(reso=='473')

    def testcomplex(self):
        """test parsing a complex number"""
        resc = self.parser.parse('13.45j\n',lexer=self.lexer)
        self.failUnless(resc=='13.45j')

    def testshortstring(self):
        """test parsing a one-line string"""
        jk = "\"my pink pony's mane\""
        jl = "'my pink pony\"s mane'"
        ress = self.parser.parse(jk+"\n",lexer=self.lexer)
        resr = self.parser.parse(jl+"\n",lexer=self.lexer)
        print 'short string: %s' % ress
        self.failUnless(ress == jk)
        self.failUnless(resr == jl)

    def testlongstring(self):
        """test parsing multi-line strings"""
        jk = '''"""  a  long string la la la '"'
                  some more
             """'''
        jl = """'''  a  long string la la la '"'
                  some more
             '''"""
        ress = self.parser.parse(jk+"\n",lexer=self.lexer)
        resr = self.parser.parse(jl+"\n",lexer=self.lexer)
        self.failUnless(ress == jk)
        self.failUnless(resr == jl)

    def testmathexpr(self):
        """test simple maths expressions """
        testexpr = ("5.45 + 23.6e05", "11 - 45" , "45.6 / 22.2")
        for test in testexpr:
            res = self.parser.parse(test+"\n",lexer=self.lexer)
            print `res`
            self.failUnless(res == test)

    def testexprlist(self):
        """test comma-separated expressions"""
        test = "5,6,7+8.5e2"
        res = self.parser.parse(test+"\n",lexer=self.lexer) 
        self.failUnless(res == "5 , 6 , 7 + 8.5e2")

    def testparen(self):
        """test parentheses"""
        test = "('once', 'upon', 6,7j +.5e2)"
        res = self.parser.parse(test+"\n",lexer=self.lexer) 
        self.failUnless(res == "( 'once' , 'upon' , 6 , 7j + .5e2 )")

    def testlists(self):
        """test list parsing"""
        test = "['once', 'upon', 6,7j +.5e2]"
        res = self.parser.parse(test+"\n",lexer=self.lexer) 
        self.failUnless(res == "[ 'once' , 'upon' , 6 , 7j + .5e2 ]")

class MoreComplexTestCase(unittest.TestCase):
   def setUp(self):
       #create our lexer and parser
       self.lexer = drel_lex.lexer
       self.parser = drel_yacc.parser

   def testassignment(self):
       pass 
    
   def test_with_stmt(self):
       """Test what comes out of a simple flow statement"""
       teststrg = """
       with q as testcat {
           x = 22
           j = 25
           q = 26
           }"""
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       print res

   def test_do_stmt(self):
       """Test how a do statement comes out"""
       teststrg = """
       do jkl = 0,20,2 { total = total + i
          }
       do emm = 1,5 {
          emm = emm + 1
          }
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       print res

   def test_nested_stmt(self):
       """Test how a nested do statement prints"""
       teststrg = """
       do jkl = 0,20,2 { total = total + jkl 
          do emm = 1,5 { emm = emm + 1 } 
          }
       end_of_loop = -25.6
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       print res

if __name__=='__main__':
    unittest.main()
