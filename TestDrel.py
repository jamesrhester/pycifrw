# Test suite for the dRel parser
#

import unittest
import drel_lex
import drel_yacc
import CifFile
import StarFile

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
       """Test that an assignment works"""
       teststrg = "jk = 11" 
       res = self.parser.parse(teststrg,lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc","jk")
       exec realfunc
       self.failUnless(myfunc(self,self)==11)
    
   def test_do_stmt(self):
       """Test how a do statement comes out"""
       teststrg = """
       total = 0
       do jkl = 0,20,2 { total = total + jkl
          }
       do emm = 1,5 {
          total = total + emm
          }
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc","total")
       exec realfunc
       realres = myfunc(self,self)
       # Do statements are inclusive
       print "Do statement returns %d" % realres
       self.failUnless(realres==125)
       print res

   def test_nested_stmt(self):
       """Test how a nested do statement prints"""
       teststrg = """
       total = 0
       othertotal = 0
       do jkl = 0,20,2 { total = total + jkl 
          do emm = 1,5 { othertotal = othertotal + 1 } 
          }
       end_of_loop = -25.6
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc","othertotal,total")
       print "Nested do:\n" + realfunc
       exec realfunc
       othertotal,total = myfunc(self,self)
       print "nested do returns %d, %d" % (othertotal,total) 
       self.failUnless(othertotal==55)
       self.failUnless(total==110)

class WithDictTestCase(unittest.TestCase):
   """Now test flow control which requires a dictionary present"""
   def setUp(self):
       #create our lexer and parser
       self.lexer = drel_lex.lexer
       self.parser = drel_yacc.parser
       #use a simple dictionary
       self.testdic = CifFile.CifDic("testdic")
       self.testblock = CifFile.CifFile("testdic")["DDL_DIC"]
       #create the global namespace
       self.namespace = self.testblock.keys()
       self.namespace = dict(map(None,self.namespace,self.namespace))
       self.parser.special_id = [self.namespace]

   def test_with_stmt(self):
       """Test what comes out of a simple flow statement"""
       teststrg = """
       with q as dictionary {
           x = 22
           j = 25
           jj = q.date
           _dictionary.date = "2007-04-01"
           }"""
       self.parser.loopable_cats = []   #category dictionary is not looped
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc",None)
       print "With statement -> \n" + realfunc
       exec realfunc
       myfunc(self.testblock,self.testblock)
       print 'date now %s' % self.testblock["_dictionary.date"]
       self.failUnless(self.testblock["_dictionary.date"]=="2007-04-01")

   def test_functions(self):
       """Test that functions are converted correctly"""
       struct_testdic = CifFile.CifFile("../pycifrw-ddlm/DDLm_20071010/cif_core.dic")
       struct_testblock = struct_testdic["CIF_CORE"]
       self.parser.loopable_cats = ["import"]   #category import is looped
       self.parser.target_name = "_import_list.id"
       teststrg = """
       with i as import 
           _import_list.id = List([i.scope, i.block, i.file, i.if_dupl, i.if_miss])
       """
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc","__dreltarget")
       print "With statement -> \n" + realfunc
       print "Before execution:\n"
       print struct_testblock.printsection()
       exec realfunc
       retval = myfunc(self.testdic,struct_testblock)
       # struct_testblock["_import_list.id"] = ret_list
       print "After execution"
       print struct_testblock.printsection()
       self.failUnless(struct_testblock["_import_list.id"][3] == StarFile.StarList(["dic","CORE_MODEL","core_model.dic","exit","exit"]))
       

if __name__=='__main__':
    unittest.main()
