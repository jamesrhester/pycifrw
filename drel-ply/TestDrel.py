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

# as we disallow simple expressions on a separate line to avoid a 
# reduce/reduce conflict for identifiers, we need at least an 
# assignment statement

    def testrealnum(self):
        """test parsing of real numbers"""
        res = self.parser.parse('a=5.45\n',debug=True,lexer=self.lexer)
        realfunc = drel_yacc.make_func(res,"myfunc","a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self)==5.45)
        res = self.parser.parse('a=.45e-24\n',debug=True,lexer=self.lexer)
        realfunc = drel_yacc.make_func(res,"myfunc","a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) ==.45e-24)

    def testinteger(self):
        """test parsing an integer"""
        resm = [0,0,0,0]
        checkm = [1230,77,5,473]
        resm[0] = self.parser.parse('a = 1230\n',lexer=self.lexer)
        resm[1] = self.parser.parse('a = 0x4D\n',lexer=self.lexer)
        resm[2] = self.parser.parse('a = 0B0101\n',lexer=self.lexer)
        resm[3] = self.parser.parse('a = 0o731\n',lexer=self.lexer)
        for res,check in zip(resm,checkm):
            realfunc = drel_yacc.make_func(res,"myfunc","a",have_sn=False)
            exec realfunc
            self.failUnless(myfunc(self,self) == check)

    def testcomplex(self):
        """test parsing a complex number"""
        resc = self.parser.parse('a = 13.45j\n',lexer=self.lexer)
        realfunc = drel_yacc.make_func(resc,"myfunc","a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) == 13.45j)

    def testshortstring(self):
        """test parsing a one-line string"""
        jk = "a = \"my pink pony's mane\""
        jl = "a = 'my pink pony\"s mane'"
        ress = self.parser.parse(jk+"\n",lexer=self.lexer)
        resr = self.parser.parse(jl+"\n",lexer=self.lexer)
        realfunc = drel_yacc.make_func(ress,"myfunc","a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) == jk[5:-1])
        realfunc = drel_yacc.make_func(resr,"myfunc","a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) == jl[5:-1])
#
# This fails due to extra indentation introduced when constructing the
# enclosing function
#
    def testlongstring(self):
        """test parsing multi-line strings"""
        jk = '''a = """  a  long string la la la '"'
                  some more
          end"""'''
        jl = """a = '''  a  long string la la la '"'
                  some more
          end'''"""
        ress = self.parser.parse(jk+"\n",lexer=self.lexer)
        resr = self.parser.parse(jl+"\n",lexer=self.lexer)
        realfunc = drel_yacc.make_func(ress,"myfunc","a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) == jk[7:-3])
        realfunc = drel_yacc.make_func(resr,"myfunc","a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) == jl[7:-3])

    def testmathexpr(self):
        """test simple maths expressions """
        testexpr = (("a = 5.45 + 23.6e05",5.45+23.6e05), 
                    ("a = 11 - 45",11-45),
                    ("a = 45.6 / 22.2",45.6/22.2))
        for test,check in testexpr:
            res = self.parser.parse(test+"\n",lexer=self.lexer)
            realfunc = drel_yacc.make_func(res,"myfunc","a",have_sn=False)
            exec realfunc
            self.failUnless(myfunc(self,self) == check)

    def testexprlist(self):
        """test comma-separated expressions"""
        test = "a = 5,6,7+8.5e2"
        res = self.parser.parse(test+"\n",lexer=self.lexer) 
        realfunc = drel_yacc.make_func(res,"myfunc","a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) ==(5,6,7+8.5e2))

    def testparen(self):
        """test parentheses"""
        test = "a = ('once', 'upon', 6,7j +.5e2)"
        res = self.parser.parse(test+"\n",lexer=self.lexer) 
        realfunc = drel_yacc.make_func(res,"myfunc","a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) ==('once' , 'upon' , 6 , 7j + .5e2 ))

    def testlists(self):
        """test list parsing"""
        test = "a = ['once', 'upon', 6,7j +.5e2]"
        res = self.parser.parse(test+"\n",lexer=self.lexer) 
        realfunc = drel_yacc.make_func(res,"myfunc","a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) ==['once' , 'upon' , 6 , 7j + .5e2 ])

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
       realfunc = drel_yacc.make_func(res,"myfunc","n",have_sn=False)
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
       realfunc = drel_yacc.make_func(res,"myfunc","total",have_sn=False)
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
       realfunc = drel_yacc.make_func(res,"myfunc","pp",have_sn=False)
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
       realfunc = drel_yacc.make_func(res,"myfunc","othertotal,total",have_sn=False)
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
       realfunc = drel_yacc.make_func(res,"myfunc","b",have_sn=False)
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
       realfunc = drel_yacc.make_func(res,"myfunc",None,cat_meth = True,have_sn=False)
       print "Fancy assign: %s" % res[0]
       exec realfunc
       b = myfunc(self,self)
       print "Geom_angle.angle = %s" % b['geom_angle.value']
       self.failUnless(b['geom_angle.value']==[1,2,3,4])

   def test_tables(self):
       """Test that tables are parsed correctly"""
       teststrg = """
       jk = Table()
       jk['bx'] = 25
       """
       print "Table test:"
       res = self.parser.parse(teststrg+"\n",debug=True,lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc","jk",have_sn=False)
       print "Table: %s" % `res[0]`
       exec realfunc
       b = myfunc(self,self)
       self.failUnless(b['bx']==25)
       
class WithDictTestCase(unittest.TestCase):
   """Now test flow control which requires a dictionary present"""
   def setUp(self):
       #create our lexer and parser
       self.lexer = drel_lex.lexer
       self.parser = drel_yacc.parser
       #use a simple dictionary
       self.testdic = CifFile.CifDic("testdic",grammar="DDLm")
       self.testblock = CifFile.CifFile("testdic",grammar="DDLm")["DDL_DIC"]
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
       struct_testdic = CifFile.CifFile("/home/jrh/COMCIFS/DDLm_20071010/cif_core.dic")
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
       
   def test_attributes(self):
       """Test that attributes of complex expressions come out OK"""
       # We need to do a scary funky attribute of a key lookup 
       ourdic = CifFile.CifDic("testdic2",grammar="DDLm")
       testblock = CifFile.CifFile("test_data.cif",grammar="DDLm")["testdata"]
       self.parser.loopable_cats = ['geom','position'] #
       teststrg = """
       LineList = []
       PointList = []
       With p as position
       Loop g as geom {
       If (g.type == "point") {
             PointList += Tuple(g.vertex1_id,p[g.vertex1_id].vector_xyz)
       }
       #Else if (g.type == "line") {
       #      LineList ++= Tuple(Tuple(g.vertex1_id, g.vertex2_id),
       #                            Tuple(p[g.vertex1_id].vector_xyz,
       #                                    p[g.vertex2_id].vector_xyz))
       #}
       }
       """
       self.parser.target_id = 'PointList'
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = drel_yacc.make_func(res,"myfunc","PointList")
       print "Function -> \n" + realfunc
       exec realfunc
       retval = myfunc(ourdic,testblock,"LineList")
       print "testdic2 return value" + `retval`
       print "Value for comparison with docs: %s" % `retval[0]`

   def test_funcdef(self):
       """Test function conversion"""
       teststrg = """
       function Closest( v :[Array, Real],   # coord vector to be cell translated
                       w :[Array, Real]) { # target vector

            d  =  v - w
            t  =  Int( Mod( 99.5 + d, 1.0 ) - d )

            Closest = Tuple ( v+t, t )
       } """
       self.parser.target_id = 'Closest'
       res,ww = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       print "Function -> \n" + res
       exec res
       retval = Closest(0.2,0.8)
       print 'Closest 0.2,0.8 returns ' + ",".join([`retval[0]`,`retval[1]`])
       self.failUnless(retval == StarFile.StarTuple(1.2,1))
       
if __name__=='__main__':
    unittest.main()
