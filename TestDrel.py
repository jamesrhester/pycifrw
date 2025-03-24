# Test suite for the dRel parser
#
# Testing of the PyCif module using the PyUnit framework
#
# To maximize python3/python2 compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

import pytest
import CifFile
from CifFile import StarFile,StarList
import numpy
from CifFile.drel import drel_lex,drel_ast_yacc,py_from_ast,drel_runtime
from copy import copy

class TestdRELRuntime():

    def testListAppend(self):
        a = [[1,2],[3,4]]
        b = drel_runtime.aug_append(a,1)
        c = drel_runtime.aug_append(a,[3])
        d = drel_runtime.aug_append(a,[[4,5,6]])
        assert b == [[1,2],[3,4],1]
        assert c == [[1,2],[3,4],[3]]
        assert d == [[1,2],[3,4],[[4,5,6]]]

    def testListAdd(self):
        a = [[1,2],[3,4]]
        aa = 5
        b = drel_runtime.aug_add(a,1)
        c = drel_runtime.aug_add(a,[[1,2],[7,6]])
        d = drel_runtime.aug_add(5,2)
        assert (c == numpy.array([[2,4],[10,10]])).all()
        assert (b == numpy.array([[2,3],[4,5]])).all()
        assert d == 7

    def testListUnappend(self):
        a = [[1,2],[3,4]]
        c = drel_runtime.aug_remove(a,[1,2])
        assert c == [[3,4]]

    def testListSubtract(self):
        a = [[1,2],[3,4]]
        aa = 5
        b = drel_runtime.aug_sub(a,1)
        c = drel_runtime.aug_sub(a,[[1,2],[7,6]])
        d = drel_runtime.aug_sub(5,2)
        assert (c == numpy.array([[0,0],[-4,-2]])).all()
        assert (b == numpy.array([[0,1],[2,3]])).all()
        assert d == 3

    def testDotProduct(self):
        """Test that multiplication works correctly"""
        a = numpy.array([1,2,3])
        b = numpy.array([4,5,6])
        d = drel_runtime.drel_dot(a,b)
        assert d == 32

    def testMatrixMultiply(self):
        """Test that matrix * matrix works"""
        a = numpy.matrix([[1,0,0],[0,1,0],[0,0,1]])
        b = numpy.matrix([[3,4,5],[6,7,8],[9,10,11]])
        c = drel_runtime.drel_dot(a,b)
        assert (c == numpy.matrix([[3,4,5],[6,7,8],[9,10,11]])).any()

    def testMatVecMultiply(self):
        """Test that matrix * vec works"""
        a = numpy.array([0,1,0])
        b = numpy.matrix([[3,4,5],[6,7,8],[9,10,11]])
        c = drel_runtime.drel_dot(a,b)
        d = drel_runtime.drel_dot(b,a)
        assert (d == numpy.matrix([4,7,10])).any()
        assert (c == numpy.matrix([6,7,8])).any()

    def testScalarVecMult(self):
        """Test that multiplying by a scalar works"""
        a = [1,2,3]
        b = 4
        c = drel_runtime.drel_dot(b,a)
        d = drel_runtime.drel_dot(a,b)
        assert (c == numpy.matrix([4,8,12])).any()
        assert (d == numpy.matrix([4,8,12])).any()

    def testArrayAppend(self):
        a = numpy.array([0,1,0])
        b = numpy.array([1,0,0])
        a = drel_runtime.aug_append(a,b)
        assert (a == numpy.array([[0,1,0],[1,0,0]])).any()

# Test simple statements

@pytest.fixture
def setup():
        #create our lexer and parser
        lexer = drel_lex.lexer
        parser = drel_ast_yacc.parser
        dic = CifFile.CifDic("tests/drel/dic_for_tests.dic",grammar="STAR2")
        return lexer, parser, dic

class TestSingleSimpleStatement():

    def create_test(self,setup, instring,right_value,debug=False,array=False):
        """Given a string, create and call a function then check result"""
        lexer, parser, dic = setup
        if instring[-1]!="\n":
           instring += '\n'
        res = parser.parse(instring,debug=debug,lexer=lexer)
        if debug: print("%s\n -> \n%r \n" % (instring, res))
        realfunc = py_from_ast.make_python_function(res,"myfunc",'_a.b',have_sn=False,
                                                    cif_dic=dic)
        if debug: print("-> %s" % realfunc)
        exec(realfunc,globals())
        answer = myfunc(self)
        if debug: print(" -> {!r}".format(answer))
        if not array:
            assert answer == right_value
        else:
            try:
                assert (answer == right_value).all()
            except:
                assert answer == right_value

# as we disallow simple expressions on a separate line to avoid a
# reduce/reduce conflict for identifiers, we need at least an
# assignment statement

    def testrealnum(self,setup):
        """test parsing of real numbers"""
        self.create_test(setup, '_a.b=5.45',5.45)
        self.create_test(setup, '_a.b=.45e-24',.45e-24)

    def testinteger(self, setup):
        """test parsing an integer"""
        resm = [0,0,0,0]
        checkm = [1230,77,5,473]
        self.create_test(setup,'_a.b = 1230',1230)
        self.create_test(setup,'_a.b = 0x4D',77)
        self.create_test(setup,'_a.b = 0B0101',5)
        self.create_test(setup,'_a.b = 0o731',473)

    def testcomplex(self, setup):
        """test parsing a complex number"""
        self.create_test(setup,'_a.b = 13.45j',13.45j)

    def testList(self, setup):
        """test parsing a list over two lines"""
        self.create_test(setup,'_a.b = [1,2,\n 3,4,\n 5,6]',StarList([1,2,3,4,5,6]))

    def testparenth(self, setup):
        """test parsing a parenthesis over two lines"""
        self.create_test(setup,'_a.b = (1,2,\n3,4)',(1,2,3,4))

    def testequal(self, setup):
        """test splitting equation over two lines"""
        self.create_test(setup, '_a.b = \n2', 2)
        
    def testshortstring(self, setup):
        """test parsing a one-line string"""
        jk = "_a.b = \"my pink pony's mane\""
        jl = "_a.b = 'my pink pony\"s mane'"
        self.create_test(setup,jk,jk[8:-1])
        self.create_test(setup,jl,jl[8:-1])
#
# This fails due to extra indentation introduced when constructing the
# enclosing function
#
    @pytest.mark.xfail
    def testlongstring(self, setup):
        """test parsing multi-line strings"""
        jk = '''_a.b = """  a  long string la la la '"'
                  some more
          end""" '''
        jl = """_a.b = '''  a  long string la la la '"'
                  some more
          end''' """
        self.create_test(setup,jk,jk[7:-3])
        self.create_test(setup,jl,jl[7:-3])

    def testmathexpr(self, setup):
        """test simple maths expressions """
        testexpr = (("_a.b = 5.45 + 23.6e05",5.45+23.6e05),
                    ("_a.b = 11 - 45",11-45),
                    ("_a.b = 45.6 / 22.2",45.6/22.2))
        for test,check in testexpr:
            self.create_test(setup,test,check)

    def testexprlist(self, setup):
        """test comma-separated expressions"""
        test = "_a.b = 5,6,7+8.5e2"
        self.create_test(setup,test,(5,6,7+8.5e2))

    def testparen(self, setup):
        """test parentheses"""
        test = "_a.b = ('once', 'upon', 6,7j +.5e2)"
        self.create_test(setup,test,('once' , 'upon' , 6 , 7j + .5e2 ))

    def testlists(self, setup):
        """test list parsing"""
        test = "_a.b = ['once', 'upon', 6,7j +.5e2]"
        self.create_test(setup,test,StarList(['once' , 'upon' , 6 , 7j + .5e2 ]))

    def test_multistatements(self, setup):
        """test multiple statements"""
        test1 = "_a.b = 1.2\nb = 'abc'\nqrs = 4.4\n"
        test2 = '\n\nq = _c.d\nnumeric = "01234"\n_a.b=11.2'
        self.create_test(setup,test1,1.2)
        #self.create_test(setup,test2,11.2)

    def test_semicolon_sep(self, setup):
        """test multiple statements between semicolons"""
        test = "_a.b = 1.2;b = 'abc';qrs = 4.4"
        self.create_test(setup,test,1.2)

    def test_slicing(self, setup):
        """Test that our slicing is parsed correctly"""
        test = "b = array([[1,2],[3,4],[5,6]]);_a.b=b[0,1]"
        self.create_test(setup,test,2)

    def test_slice_2(self, setup):
        """Test that first/last slicing works"""
        test = "b = 'abcdef';_a.b=b[1:3]"
        self.create_test(setup,test,'bc')

    def test_slice_3(self, setup):
        test = """
        c = [[0.1,1,2,3],[0.2,4,5,6],[0.3,7,8,9]]
        _a.b = c[:, 0]
        """
        self.create_test(setup, test, [0.1, 0.2, 0.3])

    def test_slice_4(self, setup):
        test = """
        c = [[0.1,1,2,3],[0.2,4,5,6],[0.3,7,8,9]]
        _a.b = c[0:2, 0]
        """
        self.create_test(setup, test, [0.1, 0.2])

    def test_slice_5(self, setup):
        test = """
        c = [[0.1,1,2,3],[0.2,4,5,6],[0.3,7,8,9]]
        _a.b = c[:2, 0]
        """
        self.create_test(setup, test, [0.1, 0.2])

    def test_paren_balance(self, setup):
        """Test that multi-line parentheses work """
        test = """b = (
                       (1,2,(
                             3,4
                            )
                       ,5),6
                     ,7)\n _a.b=b[0][2][0]"""
        self.create_test(setup,test,3)

    def test_list_constructor(self, setup):
        """Test that the list constructor works"""
        test = """_a.b = List(1,2)"""
        self.create_test(setup,test,[1,2])

    def test_non_python_ops(self, setup):
        """Test operators that have no direct Python equivalents"""
        test_expr = (("b = [1,2]; _a.b = [3,4]; _a.b++=b",StarList([3,4,[1,2]])),
        ("b = [1,2]; _a.b = [3,4]; _a.b+=b",[4,6]),
        ("b = 3; _a.b = [3,4]; _a.b-=b",[0,1]),
        ("b = [1,2]; _a.b = [[1,2],[3,4]]; _a.b--=b",[[3,4]]))
        for one_expr in test_expr:
            self.create_test(setup,one_expr[0],one_expr[1],debug=True,array=True)

    def test_tables(self, setup):
       """Test that tables are parsed correctly"""
       teststrg = """
       c = Table()
       c['bx'] = 25
       _a.b = c
       """
       lexer, parser, dic = setup
       print("Table test:")
       res = parser.parse(teststrg+"\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_a.b",have_sn=False,
                                                   cif_dic=dic)
       print(realfunc)
       exec(realfunc,globals())
       b = myfunc(self)
       assert b['bx']==25

    def test_Tables_2(self, setup):
       """Test that brace-delimited tables are parsed correctly"""
       teststrg = """
       c = {'hello':1,'goodbye':2}
       _a.b = c['hello']
       """
       print("Table test:")
       lexer, parser, dic = setup
       res = parser.parse(teststrg+"\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_a.b",have_sn=False,
                                                   cif_dic=dic)
       print(realfunc)
       exec(realfunc,globals())
       b = myfunc(self)
       assert b==1

    def test_subscription(self, setup):
       """Test proper list of dependencies is returned"""
       teststrg = """
       m   = [15,25,35]
       _a.b = m [1]
       """
       self.create_test(setup,teststrg,25)

    def test_list_indices(self, setup):
        """Test that multi-dimensional indices are accessed correctly"""
        teststrg = """
        m = [[1,2,3],[4,5,6],[7,8,9]]
        _a.b = m[1,2]
        """
        self.create_test(setup,teststrg,6,debug=True)

    def test_matrix_indices(self, setup):
        """Test that multi-dimensional indices work for matrices too"""
        teststrg = """
        m = matrix([[1,2,3],[4,5,6],[7,8,9]])
        _a.b = m[1,2]
        """
        self.create_test(setup,teststrg,6,debug=True)

@pytest.fixture
def setupcs():
       #create our lexer and parser
       lexer = drel_lex.lexer
       lexer.lineno = 0
       parser = drel_ast_yacc.parser
       dic = CifFile.CifDic("tests/drel/dic_for_tests.dic",grammar="STAR2")
       return lexer, parser, dic

class TestSimpleCompoundStatement():

   def create_test(self, setup, instring,right_value,varname="_a.b",debug=True):
       """Given a string, create and call a function then check result"""

       lexer, parser, dic = setup
       if instring[-1]!="\n":
           instring += "\n"   # correct termination
       res = parser.parse(instring,debug=debug,lexer=lexer)
       if debug: print("%s\n -> \n%r \n" % (instring, res))
       realfunc = py_from_ast.make_python_function(res,"myfunc",varname,have_sn=False,
                                                   cif_dic=dic)
       if debug: print("-> %s" % realfunc)
       exec(realfunc,globals())
       assert myfunc(self) == right_value

   def test_multi_assign(self, setupcs):
       """ Test that multiple assignments are parsed """
       teststrg = """
       f = _a.b
       p = len(f)
       q = 0
       _a.b = 0
       """
       lexer, parser, dic = setupcs
       res = parser.parse(teststrg+"\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc",'_a.b',cif_dic=dic)
       print("-> " + realfunc)

   def test_do_stmt(self, setupcs):
       """Test how a do statement comes out"""
       teststrg = """
       _a.b = 0
       dummy = 1
       do jkl = 0,20,2 {
          if (dummy == 1) print('dummy is 1')
          _a.b = _a.b + jkl
          }
       do emm = 1,5
          {
          _a.b = _a.b + emm
          }
       """
       self.create_test(setupcs,teststrg,125)

   def test_do_stmt_2(self, setupcs):
       """Test how another do statement comes out with long suite"""
       teststrg = """
       _a.b = 0
       geom_hbond = [(1,2),(2,3),(3,4)]
       do i= 0,1
          {
          l,s = geom_hbond [i]
          a = 'hello'
          c = int(4.5)
          bb = [1,c,a]
          _a.b += s
          }
       """
       self.create_test(setupcs,teststrg,5)

   def test_if_stmt(self, setupcs):
       """test parsing of if statement"""
       teststrg = """
       dmin = 5.0
       d1 = 4.0
       rad1 = 2.2
       radius_bond = 2.0
       If (d1<dmin or d1>(rad1+radius_bond)) _a.b = 5
       """
       self.create_test(setupcs,teststrg,5)

   def test_double_if_stmt(self, setupcs):
       """test parsing of if statement"""
       teststrg = """
       dmin = 5.0
       d1 = 4.0
       rad1 = 2.2
       radius_bond = 2.0
       If (d1<dmin or d1>(rad1+radius_bond)) _a.b = 5

       if (d1>dmin or d1<(rad1+radius_bond)) _a.b = 11
       if (5 > 6 and 6 < 4) _a.b = -2
       """
       self.create_test(setupcs,teststrg,11)

   def test_if_else(self, setupcs):
       """Test that else is properly handled"""
       teststrg = """drp = 'electron'
                     If (drp == "neutron")  _a.b =  "femtometres"
                     Else If (drp == "electron") _a.b =  "volts"
                     Else      _a.b =  "electrons" """
       self.create_test(setupcs,teststrg,'volts')

   def test_for_statement(self, setupcs):
       """Test for statement with list"""
       teststrg = """
       _a.b = 0
       for [c,d] in [[1,2],[3,4],[5,6]] {
           _a.b += c + 2*d
       }"""
       self.create_test(setupcs,teststrg,33)

   def test_single_line_suite(self, setupcs):
       """Test singe-line suite"""
       teststrg = """
       _a.b = 0
       for [c,d] in [[1,2],[3,4],[5,6]] { _a.b += c + 2*d }"""
       self.create_test(setupcs, teststrg, 33)
       
   def test_funcdef(self, setupcs):
       """Test function conversion"""
       teststrg = """
       function Closest( v :[Array, Real],   # coord vector to be cell translated
                       w :[Array, Real]) { # target vector

            d  =  v - w
            t  =  Int( Mod( 99.5 + d, 1.0 ) - d )
            q = 1 + 1
            Closest = [ v+t, t ]
       } """
       lexer, parser, dic = setupcs
       res = parser.parse(teststrg+"\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc",None, func_def = True)
       # print "Function -> \n" + realfunc
       exec(realfunc,globals())
       retval = Closest(0.2,0.8,None)
       print('Closest 0.2,0.8 returns {!r},{!r}'.format(retval[0], retval[1]))
       assert retval == StarList([1.2,1])

@pytest.fixture(scope="module")
def testdic():
    testdic = CifFile.CifDic("tests/dictionaries/cif_core.dic",grammar="2.0",do_imports='Contents')
    # Add drel functions for deriving items
    testdic.initialise_drel()
    return testdic

class TestMoreComplex():

   def test_nested_stmt(self, setupcs):
       """Test how a nested do statement executes"""
       teststrg = """
       total = 0
       _a.b = 0
       do jkl = 0,20,2 { total = total + jkl
          do emm = 1,5 { _a.b = _a.b + 1
          }
          }
       end_of_loop = -25.6
       """
       lexer, parser, dic = setupcs
       res = parser.parse(teststrg + "\n",lexer=lexer, debug = True)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_a.b",have_sn=False,
                                                   cif_dic = dic)
       exec(realfunc,globals())
       othertotal = myfunc(self)
       assert othertotal==55

   def test_complex_if(self, setupcs):
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
         If( Abs(a-b)<d || Abs(a-c)<d || Abs(b-c)<d )          _a.b = ('B', warn_len)
         If( Abs(alp-90)<d || Abs(bet-90)<d || Abs(gam-90)<d ) _a.b = ('B', warn_ang)
       } else _a.b = ('None',"")
       """
       lexer, parser, dic = setupcs
       res = parser.parse(teststrg + "\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_a.b",have_sn=False,
                                                   cif_dic = dic)
       exec(realfunc,globals())
       b = myfunc(self)
       print("if returns {!r}".format(b))
       assert b==('B', 'Possible mismatch between cell angles and cell setting')


# We don't test the return value until we have a way to actually access it!
   def test_fancy_assign(self, setupcs, testdic):
       """Test fancy assignment"""
       teststrg = """
       a = [2,3,4]
       b = 3
       c= 4
       do jkl = 1,5,1 {
          geom_angle(
                      .distances = [b,c],
                      .value = jkl)
                      }
       """
       lexer, parser, _ = setupcs
       res = parser.parse(teststrg + "\n", lexer=lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","geom_angle",cat_meth = True,have_sn=False,
                                                   cif_dic = testdic)
       print("Fancy assign: %s" % res[0])
       exec(realfunc,globals())
       b = myfunc(self)
       print("Geom_angle.angle = %s" % b['_geom_angle.value'])
       assert b['_geom_angle.value']==[1,2,3,4,5]

@pytest.fixture
def setupfull(testdic):
       #create our lexer and parser
       lexer = drel_lex.lexer
       parser = drel_ast_yacc.parser
       parser.lineno = 0
       #use
       testblock = CifFile.CifFile("tests/drel/nick1.cif",grammar="STAR2")["saly2_all_aniso"]
       testblock.assign_dictionary(testdic)
       testblock.provide_value = True  #get values back
       #create the global namespace
       namespace = testblock.keys()
       namespace = dict(zip(namespace,namespace))
       special_ids = [namespace]
       return (lexer, parser, testblock, namespace, special_ids)

class TestWithDict():
   """Now test flow control which requires a dictionary present"""
   #Dictionaries are required whenever a calculation is performed on a
   #datafile-derived object in order to use the correct types.

   def test_loop_with_statement(self, testdic, setupfull):
       """Test with statement on a looped category"""
       teststrg = """
       with t as atom_type
       {
       t.analytical_mass_percent = t.number_in_cell * 10
       }
       """
       lexer, parser, testblock, _, _ = setupfull
       loopable_cats = {'atom_type':["id",["id","number_in_cell"]]}   #
       ast = parser.parse(teststrg+"\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(ast,"myfunc","_atom_type.analytical_mass_percent",
                                                   cif_dic=testdic,loopable=loopable_cats)
       print("With statement for looped category -> \n" + realfunc)
       exec(realfunc,globals())
       #
       atmass = myfunc(testblock)
       print('test value now {!r}'.format(atmass))
       assert atmass == [120,280,240]

   def test_Lists(self, testdic, setupfull):
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
     _geom_bond.id = atomlist
"""
       lexer, parser, testblock, _, _ = setupfull
       loop_cats = {"atom_site":["label",["fract_xyz","type_symbol","label"]],
                    "atom_type":["id",["id","radius_bond","radius_contact"]]}
       res = parser.parse(teststrg + "\n",lexer=lexer)
       realfunc,dependencies = py_from_ast.make_python_function(res,"myfunc","_geom_bond.id",cat_meth=True,
                loopable=loop_cats,have_sn=False,depends=True,cif_dic=testdic)
       print('Simple function becomes:')
       print(realfunc)
       print('Depends on: {!r}'.format(dependencies))
       exec(realfunc,globals())
       b = myfunc(testblock)
       print("subscription returns {!r}".format(b))

   def test_with_stmt(self, testdic, setupfull):
       """Test what comes out of a simple flow statement, including
          multiple with statements"""
       teststrg = """
       with e as exptl
       with c as cell {
           x = 22
           j = 25
           jj = e.crystals_number
           px = c.length_a
           _exptl.method = "single-crystal diffraction"
           }"""
       lexer, parser, testblock, _, _ = setupfull
       loopable_cats = {}   #none looped
       res = parser.parse(teststrg+"\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(res,"myfunc","_exptl.method",cif_dic=testdic)
       print("With statement -> \n" + realfunc)
       exec(realfunc,globals())
       # attach dictionary
       testblock.assign_dictionary(testdic)
       newmeth = myfunc(testblock)
       print('exptl method now %s' % newmeth)
       assert newmeth == "single-crystal diffraction"

   def test_loop_with_stmt_2(self, testdic, setupfull):
       """Test with statement on a looped category, no aliasing"""
       teststrg = """
       _atom_type.analytical_mass_percent = _atom_type.number_in_cell * 10
       """
       lexer, parser, testblock, _, _ = setupfull
       loopable_cats = {'atom_type':["id",["id",'number_in_cell','test']]}   #
       ast = parser.parse(teststrg+"\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(ast,"myfunc","_atom_type.analytical_mass_percent",
                                                   loopable=loopable_cats,
                                                   cif_dic=testdic)
       print("With statement for looped category -> \n" + realfunc)
       exec(realfunc,globals())
       atmass = myfunc(testblock)
       print('test value now {!r}'.format(atmass))
       assert atmass == [120,280,240]

   def test_subscription(self, testdic, setupfull):
       """Test proper list of dependencies is returned"""
       teststrg = """
       _model_site.symop = _model_site.id [1]
       """
       lexer, parser, testblock, _, _ = setupfull
       loopable_cats = {"model_site":["id",["id","symop"]]}
       res = parser.parse(teststrg,lexer=lexer)
       print(repr(res))
       realfunc,dependencies = py_from_ast.make_python_function(res,"myfunc","_model_site.symop",
                                                                loopable=loopable_cats,depends=True,
                                                                cif_dic=testdic)
       print(realfunc, repr(dependencies))
       assert dependencies == set(['_model_site.id'])

   def test_current_row(self, testdic, setupfull):
       """Test that methods using Current_Row work properly"""
       teststrg = """
       _atom_type.description = Current_Row() + 1
       """
       lexer, parser, testblock, _, _ = setupfull
       loopable_cats = {'atom_type':["id",['number_in_cell','atomic_mass','num']]}   #
       ast = parser.parse(teststrg+"\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(ast,"myfunc","_atom_type.description",loopable=loopable_cats,
                                                   cif_dic=testdic)
       print("Current row statement -> \n" + realfunc)
       exec(realfunc,globals())
       rownums = myfunc(testblock)
       print('row id now {!r}'.format(rownums))
       assert rownums == [1,2,3]

   def test_loop_statement(self, testdic, setupfull):
       """Test proper processing of loop statements"""
       teststrg = """
       mass = 0.
       Loop t as atom_type  {
                   mass += t.number_in_cell * t.atomic_mass
       }
       _cell.atomic_mass = mass
            """
       lexer, parser, testblock, _, _ = setupfull
       loopable_cats = {'atom_type':["id",['number_in_cell','atomic_mass']]}   #
       ast = parser.parse(teststrg+"\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(ast,"myfunc","_cell.atomic_mass",loopable=loopable_cats,
                                                   cif_dic=testdic)
       print("Loop statement -> \n" + realfunc)
       exec(realfunc,globals())
       atmass = myfunc(testblock)
       print('atomic mass now %f' % atmass)
       assert atmass == 552.488

   def test_complex_f(self, testdic, setupfull):
       """This calculation failed during testing"""
       teststrg = """
   With r  as  refln

      fc  =   Complex (0., 0.)
      h   =   r.hkl

   Loop a  as  atom_site  {

          f  =   a.site_symmetry_multiplicity * a.occupancy * (
                 r.form_factor_table [a.type_symbol]      +
                        _atom_type_scat[a.type_symbol].dispersion  )

      Loop s  as  space_group_symop  {

          t   =  Exp(-h * s.R * a.tensor_beta * s.RT * h)

          fc +=  f * t * ExpImag(TwoPi *( h *( s.R * a.fract_xyz + s.T)))
   }  }
          _refln.F_complex  =   fc / _space_group.multiplicity
       """
       lexer, parser, testblock, _, _ = setupfull
       loopable_cats = {'space_group_symop':["id",["id","R","RT","T"]],
                        'atom_site':["id",["id","type_symbol","occupancy","site_symmetry_multiplicity",
                                           "tensor_beta","fract_xyz"]],
                        'atom_type_scat':["id",["id","dispersion"]],
                        'refln':["hkl",["hkl","form_factor_table"]]}   #
       ast = parser.parse(teststrg+"\n",lexer=lexer)
       realfunc = py_from_ast.make_python_function(ast,"myfunc","_refln.F_complex",loopable=loopable_cats,
                                                   cif_dic=testdic)
       print("Incoming AST: {!r}".format(ast))
       print("F_complex statement -> \n" + realfunc)
       exec(realfunc,globals())

       # This one also doesn't return anything sensible yet, just a generation check
   def test_fancy_packets(self, testdic, setupfull):
       """Test that full packets can be dealt with properly"""
       teststrg = """[label,symop] =   _model_site.id

     a = atom_site[label]
     s = space_group_symop[SymKey(symop)]

     _model_site.adp_matrix_beta =  s.R * a.matrix_beta * s.RT"""
       lexer, parser, testblock, _, _ = setupfull
       loopable = {"model_site":["id",["id"]],
                   "atom_site":["label",["matrix_beta","label"]],
                   "space_group_symop":["id",["id","RT","R"]]}
       res = parser.parse(teststrg + "\n",lexer=lexer)
       realfunc,deps = py_from_ast.make_python_function(res,"myfunc","_model_site.adp_matrix_beta",
                                                   depends = True,have_sn=False,
                                                        loopable=loopable,cif_dic=testdic)
       print('model_site.adp_matrix_beta becomes...')
       print(realfunc)
       print(deps)
       assert '_space_group_symop.RT' in deps

   def test_array_access(self, testdic, setupfull):
       """Test that arrays are converted and returned correctly"""
       teststrg = """
      _model_site.symop = _model_site.id[1]
      """
       lexer, parser, testblock, _, _ = setupfull
       loopable = {"model_site":["id",["id","symop","adp_eigen_system"]],
                   "atom_site":["label",["matrix_beta","label"]],
                   "space_group_symop":["id",["id","RT","R"]]}
       res = parser.parse(teststrg + "\n",lexer=lexer)
       realfunc,deps = py_from_ast.make_python_function(res,"myfunc","_model_site.symop",
                                                   depends = True,have_sn=False,
                                                        loopable=loopable,cif_dic=testdic)
       print(realfunc)
       exec(realfunc,globals())
       testblock.assign_dictionary(testdic)
       b = myfunc(testblock)
       print('symops are now {!r}'.format(b))
       assert b[1] == '1_555'

   def testIfStatement(self, testdic, setupfull):
        """Test that we handle optional values appropriately"""
        teststrg = """
        with a as atom_site
        label = a.label
        if (a.adp_type == "Uani") {
        Loop b as atom_site_aniso     {
           If(label == b.label)           {
               UIJ = b.matrix_U
               Break
     } } }

     Else If (a.adp_type == 'bani')  {
         Loop b as atom_site_aniso     {
           If(label == b.label)           {

              UIJ = b.matrix_B / (8 * Pi**2)
              Break
     } } }
     Else                                    {
         If (a.adp_type == 'uiso')  U  =  a.U_iso_or_equiv
         Else                       U  =  a.B_iso_or_equiv / (8 * Pi**2)

             UIJ = U * _cell.convert_Uiso_to_Uij
     }
     _atom_site_aniso.matrix_beta = UIJ """
        lexer, parser, testblock, _, _ = setupfull
        loopable = {
                   "atom_site":["label",["matrix_beta","label"]],
                   "atom_site_aniso":["label",["label","matrix_B","matrix_U"]],
                  }
        res = parser.parse(teststrg + "\n",lexer=lexer)
        realfunc,deps = py_from_ast.make_python_function(res,"myfunc","_atom_site_aniso.matrix_beta",
                                                   depends = True,have_sn=False,
                                                        loopable=loopable,cif_dic=testdic)
        funclines = realfunc.splitlines()
        for n,l in enumerate(funclines):
            print("%2d:%s"%(n,l))
        #print(realfunc)
        exec(realfunc,globals())
        testblock.assign_dictionary(testdic)
        b = myfunc(testblock)
        print('matrix beta is now {!r}'.format(b))
        assert b[1][1][1] == 0.031  #U22 for O2

   def testCaptures(self, testdic, setupfull):
        """Test that we catch all dictionary names"""
        teststrg = """
        with a as atom_site_aniso
        label = a.label
        if (a.adp_type == "Uani") {
            UIJ = a.matrix_U
        }
        _atom_site_aniso.matrix_beta = UIJ """
        lexer, parser, testblock, _, _ = setupfull
        loopable = {
                   "atom_site":["label",["matrix_beta","label"]],
                   "atom_site_aniso":["label",["label","matrix_B","matrix_U"]],
                  }
        res = parser.parse(teststrg + "\n",lexer=lexer)
        realfunc,deps = py_from_ast.make_python_function(res,"myfunc","_atom_site_aniso.matrix_beta",
                                                   depends = True,have_sn=False,
                                                        loopable=loopable,cif_dic=testdic)
        funclines = realfunc.splitlines()
        for n,l in enumerate(funclines):
            print("%2d:%s"%(n,l))
        #print(realfunc)
        print("Dependencies: {}".format(deps))
        exec(realfunc,globals())
        testblock.assign_dictionary(testdic)
        b = myfunc(testblock)
        print('matrix beta is now {!r}'.format(b))
        assert b[1][1][1] == 0.031  #U22 for O2
