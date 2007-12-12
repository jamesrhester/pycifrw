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
        [res,ww] = self.parser.parse('5.45\n',lexer=self.lexer)
        self.failUnless(res=='5.45')
        [res,ww] = self.parser.parse('.45e-24\n',lexer=self.lexer)
        self.failUnless(res=='.45e-24')

    def testinteger(self):
        """test parsing an integer"""
        [resd,ww] = self.parser.parse('1230\n',lexer=self.lexer)
        [resx,ww] = self.parser.parse('0x4D\n',lexer=self.lexer)
        [resb,ww] = self.parser.parse('0B0101\n',lexer=self.lexer)
        [reso,ww] = self.parser.parse('0o731\n',lexer=self.lexer)
        self.failUnless(resd=='1230')
        self.failUnless(resx=='77')
        self.failUnless(resb=='5')
        self.failUnless(reso=='473')

    def testcomplex(self):
        """test parsing a complex number"""
        [resc,ww] = self.parser.parse('13.45j\n',lexer=self.lexer)
        self.failUnless(resc=='13.45j')

    def testshortstring(self):
        """test parsing a one-line string"""
        jk = "\"my pink pony's mane\""
        jl = "'my pink pony\"s mane'"
        [ress,ww] = self.parser.parse(jk+"\n",lexer=self.lexer)
        [resr,ww] = self.parser.parse(jl+"\n",lexer=self.lexer)
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
        [ress,ww] = self.parser.parse(jk+"\n",lexer=self.lexer)
        [resr,ww] = self.parser.parse(jl+"\n",lexer=self.lexer)
        self.failUnless(ress == jk)
        self.failUnless(resr == jl)

    def testmathexpr(self):
        """test simple maths expressions """
        testexpr = ("5.45 + 23.6e05", "11 - 45" , "45.6 / 22.2")
        for test in testexpr:
            [res,ww] = self.parser.parse(test+"\n",lexer=self.lexer)
            print `res`
            self.failUnless(res == test)

    def testexprlist(self):
        """test comma-separated expressions"""
        test = "5,6,7+8.5e2"
        [res,ww] = self.parser.parse(test+"\n",lexer=self.lexer) 
        self.failUnless(res == "5 , 6 , 7 + 8.5e2")

    def testparen(self):
        """test parentheses"""
        test = "('once', 'upon', 6,7j +.5e2)"
        [res,ww] = self.parser.parse(test+"\n",lexer=self.lexer) 
        self.failUnless(res == "( 'once' , 'upon' , 6 , 7j + .5e2 )")

    def testlists(self):
        """test list parsing"""
        test = "['once', 'upon', 6,7j +.5e2]"
        [res,ww] = self.parser.parse(test+"\n",lexer=self.lexer) 
        self.failUnless(res == "[ 'once' , 'upon' , 6 , 7j + .5e2 ]")

class MoreComplexTestCase(unittest.TestCase):
   def setUp(self):
       #create our lexer and parser
       self.lexer = drel_lex.lexer
       self.parser = drel_yacc.parser
       self.parser.withtable = {}
       self.parser.special_id = []
       self.parser.target_id = None
       self.parser.indent = ""

   def testassignment(self):
       """Test that an assignment works"""
       teststrg = "n  = 11" 
       res = self.parser.parse(teststrg,lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc","n")
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

   def test_do_stmt_2(self):
       """Test how another do statement comes out"""
       teststrg = """
       pp = 0
       geom_hbond = [(1,2),(2,3),(3,4)]
       do i= 0,1 {
          l,s = geom_hbond [i] 
          pp += s
          }
       """
       self.parser.special_id = [{'axy':1}]
       res = self.parser.parse(teststrg + "\n",debug=True,lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc","pp")
       exec realfunc
       realres = myfunc(self,self)
       # Do statements are inclusive
       print "Do statement returns %d" % realres
       self.failUnless(realres==5)
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

   def test_if_stmt(self):
       """test parsing of if statement"""
       teststrg = """
       dmin = 5.0
       d1 = 4.0
       rad1 = 2.2
       radius_bond = 2.0
       If (d1<dmin or d1>(rad1+radius_bond)) b = 5 
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc","b")
       exec realfunc
       b = myfunc(self,self)
       print "if returns %d" %  b 
       self.failUnless(b==5)

# We don't test the return value until we have a way to actually access it!
   def test_fancy_assign(self):
       """Test fancy assignment"""
       teststrg = """
       a = [2,3,4] 
       b = 3
       c= 4
       do jkl = 1,5,1 {
          geom_angle( .id = Tuple(a,b,c),
                      .distances = Tuple(b,c),
                      .value = jkl)
                      }
       """
       self.parser.target_id = "geom_angle"
       res = self.parser.parse(teststrg + "\n",debug=True,lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc",None,cat_meth = True)
       print "Fancy assign: %s" % res[0]
       exec realfunc
       b = myfunc(self,self)
       print "Geom_angle.angle = %s" % b['geom_angle.value']
       self.failUnless(b['geom_angle.value']==[1,2,3,4])

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
       self.parser.withtable = {}
       self.parser.target_id = None
       self.parser.indent = ""

   def test_with_stmt(self):
       """Test what comes out of a simple flow statement, including
          multiple with statements"""
       teststrg = """
       with p as description
       with q as dictionary {
           x = 22
           j = 25
           jj = q.date
           px = p.text
           _dictionary.date = "2007-04-01"
           }"""
       self.parser.loopable_cats = []   #category dictionary is not looped
       self.parser.target_id = '_dictionary.date'
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc",None)
       print "With statement -> \n" + realfunc
       exec realfunc
       newdate = myfunc(self.testdic,self.testblock)
       print 'date now %s' % newdate 
       self.failUnless(newdate == "2007-04-01")

   def test_loop_statement(self):
       """Test proper processing of loop statements"""
       teststrg = """
       n = 0
       loop p as dictionary_audit n += 1
           _symmetry.ops = n 
            """
       self.parser.loopable_cats = ['dictionary_audit']   #category dictionary is not looped
       self.parser.target_id = '_symmetry.ops'
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer,debug=1)
       realfunc = drel_yacc.make_func(res,"myfunc",None)
       print "Loop statement -> \n" + realfunc
       exec realfunc
       symops = myfunc(self.testdic,self.testblock)
       print 'symops now %d' % symops 
       self.failUnless(symops == 81)
       
   def test_functions(self):
       """Test that functions are converted correctly"""
       struct_testdic = CifFile.CifFile("../pycifrw-ddlm/DDLm_20071010/cif_core.dic")
       struct_testblock = struct_testdic["CIF_CORE"]
       self.parser.loopable_cats = ["import"]   #category import is looped
       self.parser.target_id = "_import_list.id"
       self.parser.withtable = {}
       teststrg = """
       with i as import 
           _import_list.id = List([i.scope, i.block, i.file, i.if_dupl, i.if_miss])
       """
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc",None)
       print "With statement -> \n" + realfunc
       exec realfunc
       retval = myfunc(self.testdic,struct_testblock,3)
       self.failUnless(retval == StarFile.StarList(["dic","CORE_MODEL","core_model.dic","exit","exit"]))
       


if __name__=='__main__':
    unittest.main()
