# Test suite for the dRel parser
#

import unittest
import drel_lex
import drel_ast_yacc
import py_from_ast
import CifFile
from CifFile import StarFile

# Test simple statements

class SimpleStatementTestCase(unittest.TestCase):
    def setUp(self):
        #create our lexer and parser
        self.lexer = drel_lex.lexer
        self.parser = drel_ast_yacc.parser

# as we disallow simple expressions on a separate line to avoid a 
# reduce/reduce conflict for identifiers, we need at least an 
# assignment statement

    def testrealnum(self):
        """test parsing of real numbers"""
        res = self.parser.parse('_a=5.45\n',lexer=self.lexer)
        realfunc = py_from_ast.make_python_function(res,"myfunc","_a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self)==5.45)
        res = self.parser.parse('_a=.45e-24\n',lexer=self.lexer)
        realfunc= py_from_ast.make_python_function(res,"myfunc","_a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) ==.45e-24)

    def testinteger(self):
        """test parsing an integer"""
        resm = [0,0,0,0]
        checkm = [1230,77,5,473]
        resm[0] = self.parser.parse('_a = 1230\n',lexer=self.lexer)
        resm[1] = self.parser.parse('_a = 0x4D\n',lexer=self.lexer)
        resm[2] = self.parser.parse('_a = 0B0101\n',lexer=self.lexer)
        resm[3] = self.parser.parse('_a = 0o731\n',lexer=self.lexer)
        for res,check in zip(resm,checkm):
            realfunc = py_from_ast.make_python_function(res,"myfunc","_a",have_sn=False)
            exec realfunc
            self.failUnless(myfunc(self,self) == check)

    def testcomplex(self):
        """test parsing a complex number"""
        res = self.parser.parse('_a = 13.45j\n',lexer=self.lexer)
        realfunc = py_from_ast.make_python_function(res,"myfunc","_a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) == 13.45j)

    def testshortstring(self):
        """test parsing a one-line string"""
        jk = "_a = \"my pink pony's mane\""
        jl = "_a = 'my pink pony\"s mane'"
        ress = self.parser.parse(jk+"\n",lexer=self.lexer)
        resr = self.parser.parse(jl+"\n",lexer=self.lexer)
        realfunc = py_from_ast.make_python_function(ress,"myfunc","_a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) == jk[6:-1])
        realfunc = py_from_ast.make_python_function(resr,"myfunc","_a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) == jl[6:-1])
#
# This fails due to extra indentation introduced when constructing the
# enclosing function
#
    def testlongstring(self):
        """test parsing multi-line strings"""
        jk = '''_a = """  a  long string la la la '"'
                  some more
          end"""'''
        jl = """_a = '''  a  long string la la la '"'
                  some more
          end'''"""
        ress = self.parser.parse(jk+"\n",lexer=self.lexer)
        resr = self.parser.parse(jl+"\n",lexer=self.lexer)
        realfunc = py_from_ast.make_python_function(ress,"myfunc","_a",have_sn=False)
        exec realfunc
        print myfunc(self,self)
        print jk[8:-3]
        self.failUnless(myfunc(self,self) == jk[7:-3])
        realfunc = py_from_ast.make_python_function(resr,"myfunc","_a",have_sn=False)
        exec realfunc
        print myfunc(self,self)
        print jl[8:-3]
        self.failUnless(myfunc(self,self) == jl[7:-3])

    def testmathexpr(self):
        """test simple maths expressions """
        testexpr = (("_a = 5.45 + 23.6e05",5.45+23.6e05), 
                    ("_a = 11 - 45",11-45),
                    ("_a = 45.6 / 22.2",45.6/22.2))
        for test,check in testexpr:
            res = self.parser.parse(test+"\n",lexer=self.lexer)
            realfunc = py_from_ast.make_python_function(res,"myfunc","_a",have_sn=False)
            exec realfunc
            self.failUnless(myfunc(self,self) == check)

    def testexprlist(self):
        """test comma-separated expressions"""
        test = "_a = 5,6,7+8.5e2"
        res = self.parser.parse(test+"\n",lexer=self.lexer) 
        realfunc = py_from_ast.make_python_function(res,"myfunc","_a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) ==(5,6,7+8.5e2))

    def testparen(self):
        """test parentheses"""
        test = "_a = ('once', 'upon', 6,7j +.5e2)"
        res = self.parser.parse(test+"\n",lexer=self.lexer) 
        realfunc = py_from_ast.make_python_function(res,"myfunc","_a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) ==('once' , 'upon' , 6 , 7j + .5e2 ))

    def testlists(self):
        """test list parsing"""
        test = "_a = ['once', 'upon', 6,7j +.5e2]"
        res = self.parser.parse(test+"\n",lexer=self.lexer) 
        realfunc = py_from_ast.make_python_function(res,"myfunc","_a",have_sn=False)
        exec realfunc
        self.failUnless(myfunc(self,self) ==['once' , 'upon' , 6 , 7j + .5e2 ])

class MoreComplexTestCase(unittest.TestCase):
   def setUp(self):
       #create our lexer and parser
       self.lexer = drel_lex.lexer
       self.parser = drel_ast_yacc.parser

   def testassignment(self):
       """Test that an assignment works"""
       teststrg = "_n  = 11" 
       res = self.parser.parse(teststrg,lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_n",have_sn=False)
       exec realfunc
       self.failUnless(myfunc(self,self)==11)
    
   def test_simple_do(self):
       """Test a simple do statement"""
       teststrg = """
       total = 0
       jjj = 11.5
       _i = 0
       do jkl = 0,10,2 {_i = _i + jkl}
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_i",have_sn=False)
       exec realfunc
       realres = myfunc(self,self)
       # Do statements are inclusive
       print "Do statement returns %d" % realres
       self.failUnless(realres==30)
       print res

   def test_do_stmt(self):
       """Test how a do statement comes out"""
       teststrg = """
       _total = 0
       do jkl = 0,20,2 { _total = _total + jkl
          }
       do emm = 1,5 {
          _total = _total + emm
          }
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_total",have_sn=False)
       exec realfunc
       realres = myfunc(self,self)
       # Do statements are inclusive
       print "Do statement returns %d" % realres
       self.failUnless(realres==125)
       print res

   def test_do_stmt_2(self):
       """Test how another do statement comes out"""
       teststrg = """
       _pp = 0
       geom_hbond = [(1,2),(2,3),(3,4)]
       do i= 0,1 {
          l,s = geom_hbond [i] 
          _pp += s
          }
       """
       self.parser.special_id = [{'axy':1}]
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_pp",have_sn=False)
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
       _othertotal = 0
       do jkl = 0,20,2 { total = total + jkl 
          do emm = 1,5 { _othertotal = _othertotal + 1 } 
          }
       end_of_loop = -25.6
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_othertotal",have_sn=False)
       print "Nested do:\n" + realfunc
       exec realfunc
       othertotal = myfunc(self,self)
       print "nested do returns %d" % othertotal 
       self.failUnless(othertotal==55)

   def test_if_stmt(self):
       """test parsing of if statement"""
       teststrg = """
       dmin = 5.0
       d1 = 4.0
       rad1 = 2.2
       radius_bond = 2.0
       If (d1<dmin or d1>(rad1+radius_bond)) _b = 5 
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_b",have_sn=False)
       exec realfunc
       b = myfunc(self,self)
       print "if returns %d" %  b 
       self.failUnless(b==5)

   def test_complex_if(self):
       """Test if with single-statement suite"""
       teststrg = """
       setting = 'triclinic'
       a   = 20.0
       b   = 20.0
       c   = 20.0
       d   = 0.01
       alp = 90.0
       bet = 90.0
       gam = 90.0
       warn_len = 'Possible mismatch between cell lengths and cell setting'
       warn_ang = 'Possible mismatch between cell angles and cell setting'
 
       If(setting == 'triclinic') {
         If( Abs(a-b)<d || Abs(a-c)<d || Abs(b-c)<d )          Alert('B', warn_len)
         If( Abs(alp-90)<d || Abs(bet-90)<d || Abs(gam-90)<d ) Alert('B', warn_ang)
       } else _res = ('None',"")
       """
       res = self.parser.parse(teststrg + "\n",debug=True,lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_res",have_sn=False)
       exec realfunc
       b = myfunc(self,self)
       print "if returns " + `b` 
       self.failUnless(b==('B', 'Possible mismatch between cell angles and cell setting'))

   def test_for_statement(self):
       """Test for statement with list"""
       teststrg = """
       _total = 0
       for [a,b] in [[1,2],[3,4],[5,6]] {
           _total += a + 2*b
       }"""
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_total",have_sn=False)
       exec realfunc
       b = myfunc(self,self)
       print "if returns %d" %  b 
       self.failUnless(b==33)

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
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc",None,cat_meth = True,have_sn=False)
       print "Fancy assign: %s" % res[0]
       exec realfunc
       b = myfunc(self,self)
       print "Geom_angle.angle = %s" % b['_geom_angle.value']
       self.failUnless(b['_geom_angle.value']==[1,2,3,4,5])

   def test_tables(self):
       """Test that tables are parsed correctly"""
       teststrg = """
       _jk = Table()
       _jk['bx'] = 25
       """
       print "Table test:"
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_jk",have_sn=False)
       exec realfunc
       b = myfunc(self,self)
       self.failUnless(b['bx']==25)
       
class WithDictTestCase(unittest.TestCase):
   """Now test flow control which requires a dictionary present"""
   def setUp(self):
       #create our lexer and parser
       self.lexer = drel_lex.lexer
       self.parser = drel_ast_yacc.parser
       #use a simple dictionary
       self.testdic = CifFile.CifDic("testdic",grammar="DDLm",do_minimum=True)
       self.testblock = CifFile.CifFile("nick1.cif",grammar="DDLm")["saly2_all_aniso"]
       #create the global namespace
       self.namespace = self.testblock.keys()
       self.namespace = dict(map(None,self.namespace,self.namespace))
       self.special_ids = [self.namespace]

   def test_with_stmt(self):
       """Test what comes out of a simple flow statement, including
          multiple with statements"""
       teststrg = """
       with e as exptl
       with c as cell_length {
           x = 22
           j = 25
           jj = e.crystals_number
           px = c.a
           _exptl.method = "single-crystal diffraction"
           }"""
       self.parser.loopable_cats = []   #none looped
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_exptl.method")
       print "With statement -> \n" + realfunc
       exec realfunc
       # attach dictionary  
       self.testblock.assign_dictionary(self.testdic)
       newmeth = myfunc(self.testdic,self.testblock)
       print 'exptl method now %s' % newmeth 
       self.failUnless(newmeth == "single-crystal diffraction")

   def test_loop_statement(self):
       """Test proper processing of loop statements"""
       teststrg = """
       mass = 0.
       Loop t as atom_type  {
                   mass += t.number_in_cell * t.atomic_mass
       }
       _cell.atomic_mass = mass
            """
       loopable_cats = ['atom_type']   #
       ast = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(ast,"myfunc","_cell.atomic_mass",loopable=loopable_cats)
       print "Loop statement -> \n" + realfunc
       exec realfunc
       #  
       # testdic = CifFile.CifDic("testdic",grammar="DDLm",do_minimum=True)
       # attach dictionary to testblock, which will trigger conversion of
       # string values to numeric values...
       self.testblock.assign_dictionary(self.testdic)
       atmass = myfunc(self.testdic,self.testblock)
       print 'atomic mass now %f' % atmass  
       self.failUnless(atmass == 552.488)
       
   def test_functions(self):
       """Test that functions are converted correctly"""
       pass
       
   def test_attributes(self):
       """Test that attributes of complex expressions come out OK"""
       # We need to do a scary funky attribute of a key lookup 
       ourdic = CifFile.CifDic("testdic2",grammar="DDLm")
       testblock = CifFile.CifFile("test_data.cif",grammar="DDLm")["testdata"]
       loopable_cats = ['geom','position'] #
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
       res = self.parser.parse(teststrg+"\n",debug=True,lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","PointList",loopable=loopable_cats)
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
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       print "Function -> \n" + res
       exec res
       retval = Closest(0.2,0.8)
       print 'Closest 0.2,0.8 returns ' + ",".join([`retval[0]`,`retval[1]`])
       self.failUnless(retval == StarFile.StarTuple(1.2,1))
       
if __name__=='__main__':
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(MoreComplexTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

