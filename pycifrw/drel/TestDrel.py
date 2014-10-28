# Test suite for the dRel parser
#

import unittest
import drel_lex
import drel_ast_yacc
import py_from_ast
import drel_runtime
import numpy
import CifFile
from CifFile import StarFile

class AugOpTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def testListAppend(self):
        a = [[1,2],[3,4]]
        b = drel_runtime.aug_append(a,1)
        c = drel_runtime.aug_append(a,[3])
        d = drel_runtime.aug_append(a,[[4,5,6]])
        self.failUnless(b == [[1,2],[3,4],1])
        self.failUnless(c == [[1,2],[3,4],3])
        self.failUnless(d == [[1,2],[3,4],[4,5,6]])

    def testListAdd(self):
        a = [[1,2],[3,4]]
        aa = 5
        b = drel_runtime.aug_add(a,1)
        c = drel_runtime.aug_add(a,[[1,2],[7,6]])
        d = drel_runtime.aug_add(5,2)
        self.failUnless((c == numpy.array([[2,4],[10,10]])).all())
        self.failUnless((b == numpy.array([[2,3],[4,5]])).all())
        self.failUnless(d == 7)

    def testListUnappend(self):
        a = [[1,2],[3,4]]
        c = drel_runtime.aug_remove(a,[1,2])
        self.failUnless(c == [[3,4]])

    def testListSubtract(self):
        a = [[1,2],[3,4]]
        aa = 5
        b = drel_runtime.aug_sub(a,1)
        c = drel_runtime.aug_sub(a,[[1,2],[7,6]])
        d = drel_runtime.aug_sub(5,2)
        self.failUnless((c == numpy.array([[0,0],[-4,-2]])).all())
        self.failUnless((b == numpy.array([[0,1],[2,3]])).all())
        self.failUnless(d == 3)

# Test simple statements

class SingleSimpleStatementTestCase(unittest.TestCase):
    def setUp(self):
        #create our lexer and parser
        self.lexer = drel_lex.lexer
        self.parser = drel_ast_yacc.parser

    def create_test(self,instring,right_value,debug=False,array=False):
        """Given a string, create and call a function then check result"""
        if instring[-1]!="\n":
           instring += '\n'
        res = self.parser.parse(instring,debug=debug,lexer=self.lexer)
        if debug: print "%s\n -> \n%s \n" % (instring,`res`)
        realfunc = py_from_ast.make_python_function(res,"myfunc",'_a',have_sn=False)
        if debug: print "-> %s" % realfunc
        exec realfunc
        answer = myfunc(self,self)
        if debug: print " -> %s" % `answer`
        if not array:
            self.failUnless(answer == right_value)
        else:
            try:
                self.failUnless((answer == right_value).all())
            except:
                self.failUnless(answer == right_value)

# as we disallow simple expressions on a separate line to avoid a 
# reduce/reduce conflict for identifiers, we need at least an 
# assignment statement

    def testrealnum(self):
        """test parsing of real numbers"""
        self.create_test('_a=5.45',5.45)
        self.create_test('_a=.45e-24',.45e-24)

    def testinteger(self):
        """test parsing an integer"""
        resm = [0,0,0,0]
        checkm = [1230,77,5,473]
        self.create_test('_a = 1230',1230)
        self.create_test('_a = 0x4D',77)
        self.create_test('_a = 0B0101',5)
        self.create_test('_a = 0o731',473)

    def testcomplex(self):
        """test parsing a complex number"""
        self.create_test('_a = 13.45j',13.45j)

    def testList(self):
        """test parsing a list over two lines"""
        self.create_test('_a = [1,2,\n 3,4,\n 5,6]',[1,2,3,4,5,6])

    def testparenth(self):
        """test parsing a parenthesis over two lines"""
        self.create_test('_a = (1,2,\n3,4)',(1,2,3,4))

    def testshortstring(self):
        """test parsing a one-line string"""
        jk = "_a = \"my pink pony's mane\""
        jl = "_a = 'my pink pony\"s mane'"
        self.create_test(jk,jk[6:-1])
        self.create_test(jl,jl[6:-1])
#
# This fails due to extra indentation introduced when constructing the
# enclosing function
#
    def testlongstring(self):
        """test parsing multi-line strings"""
        jk = '''_a = """  a  long string la la la '"'
                  some more
          end""" '''
        jl = """_a = '''  a  long string la la la '"'
                  some more
          end''' """
        self.create_test(jk,jk[7:-3])
        self.create_test(jl,jl[7:-3])

    def testmathexpr(self):
        """test simple maths expressions """
        testexpr = (("_a = 5.45 + 23.6e05",5.45+23.6e05), 
                    ("_a = 11 - 45",11-45),
                    ("_a = 45.6 / 22.2",45.6/22.2))
        for test,check in testexpr:
            self.create_test(test,check)

    def testexprlist(self):
        """test comma-separated expressions"""
        test = "_a = 5,6,7+8.5e2"
        self.create_test(test,(5,6,7+8.5e2))

    def testparen(self):
        """test parentheses"""
        test = "_a = ('once', 'upon', 6,7j +.5e2)"
        self.create_test(test,('once' , 'upon' , 6 , 7j + .5e2 ))

    def testlists(self):
        """test list parsing"""
        test = "_a = ['once', 'upon', 6,7j +.5e2]"
        self.create_test(test,['once' , 'upon' , 6 , 7j + .5e2 ])

    def test_multistatements(self):
        """test multiple statements"""
        test = "_a = 1.2\nb = 'abc'\nqrs = 4.4\n"
        self.create_test(test,1.2)

    def test_semicolon_sep(self):
        """test multiple statements between semicolons"""
        test = "_a = 1.2;b = 'abc';qrs = 4.4"
        self.create_test(test,1.2)

    def test_slicing(self):
        """Test that our slicing is parsed correctly"""
        test = "b = array([[1,2],[3,4],[5,6]]);_a=b[0,1]"
        self.create_test(test,2)

    def test_paren_balance(self):
        """Test that multi-line parentheses work """
        test = """b = (
                       (1,2,(
                             3,4
                            )
                       ,5),6
                     ,7)\n _a=b[0][2][0]"""
        self.create_test(test,3)
    
    def test_non_python_ops(self):
        """Test operators that have no direct Python equivalents"""
        test_expr = (("b = [1,2]; _a = [3,4]; _a++=b",[3,4,1,2]),
        ("b = [1,2]; _a = [3,4]; _a+=b",[4,6]),
        ("b = 3; _a = [3,4]; _a-=b",[0,1]),
        ("b = [1,2]; _a = [[1,2],[3,4]]; _a--=b",[[3,4]]))
        for one_expr in test_expr:
            self.create_test(one_expr[0],one_expr[1],debug=True,array=True)

    def test_tables(self):
       """Test that tables are parsed correctly"""
       teststrg = """
       a = Table()
       a['bx'] = 25
       _jk = a
       """
       print "Table test:"
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_jk",have_sn=False)
       print realfunc
       exec realfunc
       b = myfunc(self,self)
       self.failUnless(b['bx']==25)

    def test_subscription(self):
       """Test proper list of dependencies is returned"""
       teststrg = """
       m   = [15,25,35]
       _a = m [1]
       """
       self.create_test(teststrg,25)

class SimpleCompoundStatementTestCase(unittest.TestCase):
   def setUp(self):
       #create our lexer and parser
       self.lexer = drel_lex.lexer
       self.lexer.lineno = 0
       self.parser = drel_ast_yacc.parser

   def create_test(self,instring,right_value,varname="_a",debug=False):
       """Given a string, create and call a function then check result"""
       if instring[-1]!="\n":
           instring += "\n"   # correct termination
       res = self.parser.parse(instring,debug=debug,lexer=self.lexer)
       if debug: print "%s\n -> \n%s \n" % (instring,`res`)
       realfunc = py_from_ast.make_python_function(res,"myfunc",varname,have_sn=False)
       if debug: print "-> %s" % realfunc
       exec realfunc
       self.failUnless(myfunc(self,self) == right_value)

   def test_do_stmt(self):
       """Test how a do statement comes out"""
       teststrg = """
       _total = 0
       dummy = 1
       do jkl = 0,20,2 {
          if (dummy == 1) print 'dummy is 1'
          _total = _total + jkl
          }
       do emm = 1,5 {
          _total = _total + emm
          }
       """
       self.create_test(teststrg,125,varname='_total')

   def test_do_stmt_2(self):
       """Test how another do statement comes out with long suite"""
       teststrg = """
       _pp = 0
       geom_hbond = [(1,2),(2,3),(3,4)]
       do i= 0,1 {
          l,s = geom_hbond [i] 
          a = 'hello'
          c = int(4.5)
          bb = [1,c,a]
          _pp += s
          }
       """
       self.create_test(teststrg,5,varname="_pp")

   def test_if_stmt(self):
       """test parsing of if statement"""
       teststrg = """
       dmin = 5.0
       d1 = 4.0
       rad1 = 2.2
       radius_bond = 2.0
       If (d1<dmin or d1>(rad1+radius_bond)) _b = 5 
       """
       self.create_test(teststrg,5,varname="_b")

   def test_double_if_stmt(self):
       """test parsing of if statement"""
       teststrg = """
       dmin = 5.0
       d1 = 4.0
       rad1 = 2.2
       radius_bond = 2.0
       If (d1<dmin or d1>(rad1+radius_bond)) _b = 5 

       if (d1>dmin or d1<(rad1+radius_bond)) _b = 11
       if (5 > 6 and 6 < 4) _b = -2
       """
       self.create_test(teststrg,11,varname="_b")

   def test_if_else(self):
       """Test that else is properly handled"""
       teststrg = """drp = 'electron'
                     If (drp == "neutron")  _uc =  "femtometres"
                     Else If (drp == "electron") _uc =  "volts"
                     Else      _uc =  "electrons" """
       self.create_test(teststrg,'volts',varname="_uc",debug=True)

   def test_for_statement(self):
       """Test for statement with list"""
       teststrg = """
       _total = 0
       for [a,b] in [[1,2],[3,4],[5,6]] {
           _total += a + 2*b
       }"""
       self.create_test(teststrg,33,varname="_total")

   def test_funcdef(self):
       """Test function conversion"""
       teststrg = """
       function Closest( v :[Array, Real],   # coord vector to be cell translated
                       w :[Array, Real]) { # target vector

            d  =  v - w
            t  =  Int( Mod( 99.5 + d, 1.0 ) - d )
            q = 1 + 1
            Closest = [ v+t, t ]
       } """
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc",None, func_def = True)
       # print "Function -> \n" + realfunc
       exec realfunc
       retval = Closest(0.2,0.8)
       print 'Closest 0.2,0.8 returns ' + ",".join([`retval[0]`,`retval[1]`])
       self.failUnless(retval == [1.2,1])

class MoreComplexTestCase(unittest.TestCase):
   def setUp(self):
       #create our lexer and parser
       self.lexer = drel_lex.lexer
       self.lexer.lineno = 0
       self.parser = drel_ast_yacc.parser
    
   def test_nested_stmt(self):
       """Test how a nested do statement executes"""
       teststrg = """
       total = 0
       _othertotal = 0
       do jkl = 0,20,2 { total = total + jkl 
          do emm = 1,5 { _othertotal = _othertotal + 1
          } 
          }
       end_of_loop = -25.6
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_othertotal",have_sn=False)
       exec realfunc
       othertotal = myfunc(self,self)
       self.failUnless(othertotal==55)

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
         If( Abs(a-b)<d || Abs(a-c)<d || Abs(b-c)<d )          _res = ('B', warn_len)
         If( Abs(alp-90)<d || Abs(bet-90)<d || Abs(gam-90)<d ) _res = ('B', warn_ang)
       } else _res = ('None',"")
       """
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_res",have_sn=False)
       exec realfunc
       b = myfunc(self,self)
       print "if returns " + `b` 
       self.failUnless(b==('B', 'Possible mismatch between cell angles and cell setting'))


# We don't test the return value until we have a way to actually access it!
   def test_fancy_assign(self):
       """Test fancy assignment"""
       teststrg = """
       a = [2,3,4] 
       b = 3
       c= 4
       do jkl = 1,5,1 {
          geom_angle( .id = [a,b,c],
                      .distances = [b,c],
                      .value = jkl)
                      }
       """
       res = self.parser.parse(teststrg + "\n", lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","geom_angle",cat_meth = True,have_sn=False)
       print "Fancy assign: %s" % res[0]
       exec realfunc
       b = myfunc(self,self)
       print "Geom_angle.angle = %s" % b['_geom_angle.value']
       self.failUnless(b['_geom_angle.value']==[1,2,3,4,5])

   def testLists(self):
       """Test case found in Cif dictionary """
       teststrg = """# Store unique sites as a local list
 
     atomlist  = List()
     Loop  a  as  atom_site  {
        axyz       =    a.fract_xyz
        cxyz       =   _atom_sites_Cartn_transform.matrix * axyz
        radb       =   _atom_type[a.type_symbol].radius_bond
        radc       =   _atom_type[a.type_symbol].radius_contact
        ls         =   List ( a.label, "1_555" )
        atomlist ++=   [ls, axyz, cxyz, radb, radc, 0]
     }
     _a = atomlist
"""    
       res = self.parser.parse(teststrg + "\n",lexer=self.lexer)
       realfunc,dependencies = py_from_ast.make_python_function(res,"myfunc","_a",cat_meth=True,
                   loopable=['atom_site'],have_sn=False,depends=True)
       print 'Simple function becomes:'
       print 'Depends on: ' + `dependencies`
       print realfunc
       exec realfunc
       b = myfunc(self,self)
       print "subscription returns " + `b` 

class WithDictTestCase(unittest.TestCase):
   """Now test flow control which requires a dictionary present"""
   def setUp(self):
       #create our lexer and parser
       self.lexer = drel_lex.lexer
       self.parser = drel_ast_yacc.parser
       self.parser.lineno = 0
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

   def test_subscription(self):
       """Test proper list of dependencies is returned"""
       teststrg = """
       _model_site.symop = _model_site.id [1]
       """
       self.parser.loopable_cats = []   #none looped
       res = self.parser.parse(teststrg,lexer=self.lexer)
       print `res`
       realfunc,dependencies = py_from_ast.make_python_function(res,"myfunc","_model_site.symop",depends=True)
       print realfunc, `dependencies`
       self.failUnless(dependencies == set(['_model_site.id']))

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
       
   def test_complex_f(self):
       """This calculation failed during testing"""
       teststrg = """
   With r  as  refln
 
      fc  =   Complex (0., 0.)
      h   =   r.hkl
 
   Loop a  as  atom_site  {
 
          f  =   a.site_symmetry_multiplicity * a.occupancy * (
                 r.form_factor_table [a.type_symbol]      +
                        _atom_type_scat[a.type_symbol].dispersion  )
 
      Loop s  as  symmetry_equiv  {
 
          t   =  Exp(-h * s.R * a.tensor_beta * s.RT * h)
 
          fc +=  f * t * ExpImag(TwoPi *( h *( s.R * a.fract_xyz + s.T)))
   }  }
          _refln.F_complex  =   fc / _symmetry.multiplicity
       """
       loopable_cats = ['symmetry_equiv','atom_site']   #
       ast = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(ast,"myfunc","_refln.F_complex",loopable=loopable_cats)
       print "Incoming AST: " + `ast`
       print "F_complex statement -> \n" + realfunc
       exec realfunc
       #  

   def test_attributes(self):
       """Test that attributes of complex expressions come out OK"""
       # We need to do a scary funky attribute of a key lookup 
       # This is not a proper test as it does not return any value that
       # can be tested.  It is purely a test of the grammar
       ourdic = CifFile.CifDic("testdic2",grammar="DDLm")
       testblock = CifFile.CifFile("test_data.cif",grammar="DDLm")["testdata"]
       loopable_cats = ['geom','position'] #
       teststrg = """
       LineList = []
       _PointList = []
       With p as position
       Loop g as geom {
       If (g.type == "point") {
             _PointList += [g.vertex1_id,p[g.vertex1_id].vector_xyz]
       }
       #Else if (g.type == "line") {
       #      LineList ++= Tuple(Tuple(g.vertex1_id, g.vertex2_id),
       #                            Tuple(p[g.vertex1_id].vector_xyz,
       #                                    p[g.vertex2_id].vector_xyz))
       #}
       }
       """
       res = self.parser.parse(teststrg+"\n",lexer=self.lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_PointList",loopable=loopable_cats)
       print "Function -> \n" + realfunc
       exec realfunc
       retval = myfunc(ourdic,testblock)
       #print "testdic2 return value" + `retval`
       #print "Value for comparison with docs: %s" % `retval[0]`

       
if __name__=='__main__':
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(WithDictTestCase)
    #suite = unittest.TestLoader().loadTestsFromTestCase(SimpleCompoundStatementTestCase)
    #suite = unittest.TestLoader().loadTestsFromTestCase(SingleSimpleStatementTestCase)
    #suite = unittest.TestLoader().loadTestsFromTestCase(MoreComplexTestCase) 
    #suite = unittest.TestLoader().loadTestsFromTestCase(AugOpTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

