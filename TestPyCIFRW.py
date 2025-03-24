# Testing of the PyCif module using the PyUnit framework
#
# To maximize python3/python2 compatibility
# Note that all tests should pass with and without
# unicode literals.
from __future__ import print_function
#from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

import sys,os
#sys.path[0] = '.'
import unittest
import CifFile
from CifFile import StarFile
from CifFile.StarFile import StarDict, StarList, StarLengthError
import re
try:
    from StringIO import StringIO
except:
    from io import StringIO

# Test general string and number manipulation functions
class BasicUtilitiesTestCase(unittest.TestCase):
    def testPlainLineFolding(self):
       """Test that we can fold a line correctly"""
       test_string = "1234567890123456789012"
       outstring = CifFile.apply_line_folding(test_string,5,10)
       out_lines = outstring.split('\n')
       #print(outstring)
       self.assertTrue(out_lines[0]=="\\")
       self.assertTrue(len(out_lines[1])==10)

    def testPreWrappedFolding(self):
       """Test that pre-wrapped lines are untouched"""
       test_string = "123456789\n012345678\n9012"
       outstring = CifFile.apply_line_folding(test_string,5,10)
       self.assertTrue(outstring == test_string)

    def testManyLineEndings(self):
       """Test that empty lines are handled OK"""
       test_string = "123456789\n\n012345678\n\n9012\n\n"
       outstring = CifFile.apply_line_folding(test_string,5,10)
       self.assertTrue(outstring == test_string)

    def testOptionalBreak(self):
       """Test that internal whitespace is used to break"""
       test_string = "123456  7890123  45678\n90 12\n\n"
       outstring = CifFile.apply_line_folding(test_string,5,10)
       #print("\n;" + outstring + "\n;")
       out_lines = outstring.split('\n')
       self.assertTrue(len(out_lines[1]) == 7)

    def testCorrectEnding(self):
       """Make sure that no line feeds are added/removed"""
       test_string = "123456  7890123  45678\n90 12\n\n"
       outstring = CifFile.apply_line_folding(test_string,5,10)
       self.assertTrue(outstring[-4:] == "12\n\n")

    def testFoldingRemoval(self):
       """Test that we round-trip correctly"""
       test_string = "123456  7890123  45678\n90 12\n\n"
       outstring = CifFile.apply_line_folding(test_string,5,10)
       old_string = CifFile.remove_line_folding(outstring)
       #print("Test:" + repr(test_string))
       #print("Fold:" + repr(outstring))
       #print("UnFo:" + repr(old_string))
       self.assertTrue(old_string == test_string)

    def testTrickyFoldingRemoval(self):
       """Try to produce a tough string for unfolding"""
       test_string = "\n1234567890\\\n r t s 345 19\n\nlife don't talk to me about life"
       outstring = CifFile.apply_line_folding(test_string,5,10)
       old_string = CifFile.remove_line_folding(outstring)
       #print("Test:" + repr(test_string))
       #print("Fold:" + repr(outstring))
       #print("UnFo:" + repr(old_string))
       self.assertTrue(old_string == test_string)

    def testTrailingBackslash(self):
       """Make sure that a trailing backslash is not removed"""
       test_string = "\n123\\\n 456\\n\n"
       outstring = CifFile.apply_line_folding(test_string,5,10)
       old_string = CifFile.remove_line_folding(outstring)
       #print("Test:" + repr(test_string))
       #print("Fold:" + repr(outstring))
       #print("UnFo:" + repr(old_string))
       self.assertTrue(old_string == test_string)

    def testFinalBackslash(self):
        """Make sure that a single final backslash is removed when unfolding"""
        test_string = "\n1234567890\\\n r t s 345 19\n\nlife don't talk to me about life"
        folded_string = CifFile.apply_line_folding(test_string,5,10)
        folded_string = folded_string + r"\ "
        old_string = CifFile.remove_line_folding(folded_string)
        self.assertTrue(old_string == test_string)

    def testAddIndent(self):
        """Test insertion of a line prefix"""
        test_string = "\n12345\n678910\n\n"
        outstring = CifFile.apply_line_prefix(test_string,"abc>")
        print("Converted %s to %s " %(test_string,outstring))
        self.assertTrue(outstring == "abc>\\\nabc>\nabc>12345\nabc>678910\nabc>\nabc>")

    def testRemoveIndent(self):
        """Test removal of a line prefix"""
        test_string = "abc>\\\nabc>12345\nabc>678910\nabc>\nabc>"
        outstring = CifFile.remove_line_prefix(test_string)
        print("Removed indent: " + repr(outstring))
        self.assertTrue(outstring == "12345\n678910\n\n")

    def testReverseIndent(self):
        """Test reversible indentation of line"""
        test_string = "12345\n678910\n\n"
        outstring = CifFile.apply_line_prefix(test_string,"cif><")
        newtest = CifFile.remove_line_prefix(outstring)
        print('Before indenting: ' + repr(test_string))
        print('After indenting: ' + repr(outstring))
        print('After unindent: ' + repr(newtest))
        self.assertTrue(newtest == test_string)

    def testPrefixAndFold(self):
        """Test reversible folding and indenting"""
        test_string = "\n1234567890\\\n r t s 345 19\n\nlife don't talk to me about life"
        outstring = CifFile.apply_line_folding(test_string,5,10)
        indoutstring = CifFile.apply_line_prefix(outstring,"CIF>")
        newoutstring = CifFile.remove_line_prefix(indoutstring)
        newtest_string = CifFile.remove_line_folding(newoutstring)
        print("%s -> %s -> %s -> %s -> %s" % (repr(test_string),repr(outstring),repr(indoutstring),repr(newoutstring),repr(newtest_string)))
        self.assertTrue(newtest_string == test_string)

    def testStringiness(self):
        """Check that we can detect string-valued items correctly"""
        import numpy
        self.assertEqual(CifFile.check_stringiness(['1','2','3']),True)
        self.assertEqual(CifFile.check_stringiness([1,2,'3']),False)
        self.assertEqual(CifFile.check_stringiness(['1',['2',['3',4,'5'],'6','7'],'8']),False)
        self.assertEqual(CifFile.check_stringiness(['1',['2',['3','4','5'],'6','7'],'8']),True)
        p = numpy.array([[1,2,3],[4,5,6]])
        self.assertEqual(CifFile.check_stringiness(p),False)

    def testStarList(self):
        """Test that starlists allow comma-based access"""
        p = StarList([StarList([1,2,3]),StarList([4,5,6])])
        self.assertTrue(p[1,0]==4)

# Test basic setting and reading of the CifBlock

class BlockRWTestCase(unittest.TestCase):
    def setUp(self):
        # we want to get a datablock ready so that the test
        # case will be able to write a single item
        # self.cf_old = CifFile.CifBlock(compat_mode=True)
        self.cf = CifFile.CifBlock()

    def tearDown(self):
        # get rid of our test object
        del self.cf

    def testTupleNumberSet(self):
        """Test tuple setting with numbers"""
        self.cf['_test_tuple'] = (11,13.5,-5.6)
        self.assertTrue([float(a) for a in self.cf['_test_tuple']]== [11,13.5,-5.6])

    def testStringSet(self):
        """test string setting"""
        self.cf['_test_string_'] = 'A short string'
        self.assertTrue(self.cf['_test_string_'] == 'A short string')

    def testTooLongSet(self):
        """test setting overlong data names"""
        dataname = '_a_long_long_'*7
        try:
            self.cf[dataname] = 1.0
        except (CifFile.StarError,CifFile.CifError): pass
        else: self.fail()

    def testTooLongLoopSet(self):
        """test setting overlong data names in a loop"""
        dataname = '_a_long_long_'*7
        try:
            self.cf[dataname] = (1.0,2.0,3.0)
        except (CifFile.StarError,CifFile.CifError): pass
        else: self.fail()

    def testBadStringSet(self):
        """test setting values with bad characters"""
        dataname = '_name_is_ok'
        try:
            self.cf[dataname] = "eca234\f\vaqkadlf"
        except CifFile.StarError: pass
        else: self.fail()

    def testBadNameSet(self):
        """test setting names with bad characters"""
        dataname = "_this_is_not ok"
        try:
            self.cf[dataname] = "nnn"
        except CifFile.StarError: pass
        else: self.fail()

    def testMoreBadStrings(self):
        dataname = "_name_is_ok"
        val = (b"so far, ok, but now we have a " + bytearray([128])).decode('latin_1')
        try:
            self.cf[dataname] = val
        except CifFile.StarError: pass
        else: self.fail()

    def testEmptyString(self):
        """An empty string is, in fact, legal"""
        self.cf['_an_empty_string'] = ''

# Now test operations which require a preexisting block
#

class BlockChangeTestCase(unittest.TestCase):
   def setUp(self):
        self.cf = CifFile.CifBlock()
        self.names = ('_item_name_1','_item_name#2','_item_%$#3')
        self.values = ((1,2,3,4),('hello','good_bye','a space','# 4'),
                (15.462, -99.34,10804,0.0001))
        for n,v in zip(self.names, self.values):
            self.cf.AddItem(n, v)
        self.cf.CreateLoop(self.names)

        self.cf['_non_loop_item'] = 'Non loop string item'
        self.cf['_number_item'] = 15.65
        self.cf['_planet'] = 'Saturn'
        self.cf['_satellite'] = 'Titan'
        self.cf['_rings']  = 'True'

   def tearDown(self):
       del self.cf

   def testFromBlockSet(self):
        """Test that we can use a CifBlock to set a CifBlock"""
        df = CifFile.CifFile()
        df.NewBlock('testname',self.cf)
        self.assertEqual(df['testname']['_planet'],'Saturn')
        self.assertEqual(df['testname']['_item_name#2'],list(self.values[1]))

   def testSimpleRemove(self):
       """Check item deletion outside loop"""
       self.cf.RemoveCifItem('_non_loop_item')
       try:
           a = self.cf['_non_loop_item']
       except KeyError: pass
       else: self.fail()

   def testLoopRemove(self):
       """Check item deletion inside loop"""
       print("Before:\n")
       print(self.cf.printsection())
       self.cf.RemoveCifItem(self.names[1])
       print("After:\n")
       print(self.cf.printsection())
       try:
           a = self.cf[self.names[1]]
       except KeyError: pass
       else: self.fail()

   def testFullLoopRemove(self):
       """Check removal of all loop items"""
       for name in self.names: self.cf.RemoveCifItem(name)
       self.assertTrue(len(self.cf.loops)==0, repr(self.cf.loops))

   def testChangeLoop(self):
       """Test changing pre-existing item in loop"""
       # Items should be silently replaced
       self.cf["_item_name_1"] = (5,6,7,8)

#
#  Test the mapping type implementation
#
   def testGetOperation(self):
       """Test the get mapping call"""
       self.cf.get("_item_name_1")
       self.cf.get("_item_name_nonexist")

#
#  Test case insensitivity
#
   def testDataNameCase(self):
       """Test same name, different case causes error"""
       self.assertEqual(self.cf["_Item_Name_1"],self.cf["_item_name_1"])
       self.cf["_Item_NaMe_1"] = "the quick pewse fox"
       self.assertEqual(self.cf["_Item_NaMe_1"],self.cf["_item_name_1"])

class SyntaxErrorTestCase(unittest.TestCase):
    """Check that files with syntax errors are found"""
    def tearDown(self):
        try:
            os.remove("tests/syntax_check.cif")
        except:
            pass

    def testTripleApostropheCase(self):
        teststrg = "#\\#CIF_2.0\ndata_testblock\n _item_1 ''' ''' '''\n"
        f = open("tests/syntax_check.cif","w")
        f.write(teststrg)
        f.close()
        self.assertRaises(CifFile.StarError, CifFile.ReadCif,"tests/syntax_check.cif",grammar="2.0")

    def testTripleQuoteCase(self):
        teststrg = '#\\#CIF_2.0\ndata_testblock\n _item_1 """ """ """\n'
        f = open("tests/syntax_check.cif","w")
        f.write(teststrg)
        f.close()
        self.assertRaises(CifFile.StarError, CifFile.ReadCif,"tests/syntax_check.cif",grammar="2.0")

class LoopBlockTestCase(unittest.TestCase):
   """Check operations on loop blocks"""
   def setUp(self):
        self.cf = CifFile.CifBlock()
        self.names = ('_Item_Name_1','_item_name#2','_item_%$#3')
        self.values = ((1,2,3,4),('hello','good_bye','a space','# 4'),
            (15.462, -99.34,10804,0.0001))
        for n,v in zip(self.names, self.values):
            self.cf.AddItem(n, v)
        self.cf.CreateLoop(self.names)
        
        self.cf['_non_loop_item'] = 'Non loop string item'
        self.cf['_number_item'] = 15.65
        self.cf['_planet'] = 'Saturn'
        self.cf['_satellite'] = 'Titan'
        self.cf['_rings']  = 'True'
        # A loop with compound keys
        self.cf['_ck_1'] = ['1','1','1','2','2','2','3','3','3']
        self.cf['_Ck_2'] = ['r','g','b','r','g','b','r','g','b']
        self.cf['_stuff'] = ['Q','W','E','R','T','Y','U','I','O']
        self.cf.CreateLoop(['_ck_1','_ck_2','_stuff'])

   def tearDown(self):
       del self.cf

   def testLoop(self):
        """Check GetLoop returns values and names in matching order"""
        results = self.cf.GetLoop(self.names[2])
        lowernames = [a.lower() for a in self.names]
        for key in results.keys():
            self.assertTrue(key.lower() in lowernames)
            self.assertTrue(tuple(results[key]) == self.values[lowernames.index(key.lower())])

   def testLoopCharCase(self):
       """Test that upper/lower case names in loops works correctly"""
       # Note the wildly varying case for these two names
       self.cf['_item_name_20'] = ['a','b','c','q']
       self.cf.AddLoopName('_item_Name_1','_Item_name_20')
       self.assertTrue(self.cf.FindLoop('_Item_name_1')==self.cf.FindLoop('_Item_Name_20'))

   def testGetLoopCase(self):
       """Check that getloop works for any case"""
       results = self.cf.GetLoop('_Item_Name_1')
       self.assertEqual(results['_item_name_1'][1],2)

   def testLoopOutputOrder(self):
       """Check that an item placed in a loop no longer appears in the output order"""
       self.cf['_item_name_20'] = ['a','b','c','q']
       self.cf.AddLoopName('_item_Name_1','_Item_name_20')
       self.assertTrue('_item_name_20' not in self.cf.GetItemOrder())

   def testLoopify(self):
       """Test changing unlooped data to looped data"""
       self.cf.CreateLoop(["_planet","_satellite","_rings"])
       newloop = self.cf.GetLoop("_rings")
       self.assertFalse(newloop.has_key("_number_item"))

   def testLoopifyCif(self):
       """Test changing unlooped data to looped data does
          not touch already looped data for a CIF file"""
       self.cf.CreateLoop(["_planet","_satellite","_rings"])
       newloop = self.cf.GetLoop("_rings")
       self.assertTrue(newloop.has_key('_planet'))
       self.assertTrue(isinstance(self.cf["_planet"],list))

#  Test iteration
#
   def testIteration(self):
       """We create an iterator and iterate"""
       testloop = self.cf.GetLoop("_item_name_1")
       i = 0
       for test_pack in testloop:
           self.assertEqual(test_pack._item_name_1,self.values[0][i])
           self.assertEqual(getattr(test_pack,"_item_name#2"),self.values[1][i])
           i += 1

   def testPacketContents(self):
       """Test that body of packet is filled in as well"""
       testloop = self.cf.GetLoop("_item_name_1")
       it_order = testloop.GetItemOrder()
       itn_pos = it_order.index("_item_name_1")
       for test_pack in testloop:
           print('Test pack: ' + repr(test_pack))
           self.assertEqual(test_pack._item_name_1,test_pack[itn_pos])

   def testPacketAttr(self):
       """Test that packets have attributes"""
       testloop = self.cf.GetLoop("_item_name_1")
       self.assertEqual(testloop[1]._item_name_1,2)

   def testKeyPacket(self):
       """Test that a packet can be returned by key value"""
       testpack = self.cf.GetKeyedPacket("_item_name_1",2)
       self.assertEqual("good_bye",getattr(testpack,"_item_name#2"))

   def testCompoundKeyPacket(self):
       """Test that a compound key can also be used"""
       testpack = self.cf.GetCompoundKeyedPacket({"_ck_1":('2',False),"_ck_2":('b',False)})
       self.assertEqual("Y",getattr(testpack,"_stuff"))

   def testPacketMerge(self):
       """Test that a packet can be merged with another packet"""
       bigcf = CifFile.CifFile("tests/C13H22O3.cif")
       bigcf = bigcf["II"]
       testpack = bigcf.GetKeyedPacket("_atom_site_label","C4A")
       newpack = bigcf.GetKeyedPacket("_atom_site_aniso_label","C4A")
       testpack.merge_packet(newpack)
       self.assertEqual(getattr(testpack,'_atom_site_aniso_U_22'),'0.0312(15)')
       self.assertEqual(getattr(testpack,'_atom_site_fract_x'),'0.7192(3)')

   def testRemovePacket(self):
       """Test that removing a packet works properly"""
       print('Before packet removal')
       print(str(self.cf))
       testloop = self.cf.GetLoop("_item_name_1")
       testloop.RemoveKeyedPacket("_item_name_1",3)
       print('After packet 3 removal:')
       jj = testloop.GetKeyedPacket("_item_name_1",2)
       kk = testloop.GetKeyedPacket("_item_name_1",4)
       self.assertEqual(getattr(jj,"_item_name#2"),"good_bye")
       self.assertEqual(getattr(kk,"_item_name#2"),"# 4")
       self.assertRaises(ValueError,testloop.GetKeyedPacket,"_item_name_1",3)
       print('After packet removal:')
       print(str(self.cf))

   def testAddPacket(self):
       """Test that we can add a packet"""
       import copy
       testloop = self.cf.GetLoop("_item_name_1")
       workingpacket = copy.copy(testloop.GetPacket(0))
       workingpacket._item_name_1 = '5'
       workingpacket.__setattr__("_item_name#2", 'new' )
       testloop.AddPacket(workingpacket)
       # note we assume that this adds on to the end, which is not
       # a CIF requirement
       self.assertEqual(testloop["_item_name_1"][4],'5')
       self.assertEqual(testloop["_item_name#2"][4],'new')

#
#  Test changing item order
#
   def testChangeOrder(self):
       """We move some stuff around"""
       testloop = self.cf.GetLoop("_item_name_1")
       self.cf.ChangeItemOrder("_Number_Item",0)
       testloop.ChangeItemOrder("_Item_Name_1",2)
       self.assertEqual(testloop.GetItemOrder()[2],"_Item_Name_1".lower())
       self.assertEqual(self.cf.GetItemOrder()[0],"_Number_Item".lower())

   def testGetOrder(self):
       """Test that the correct order value is returned"""
       self.assertEqual(self.cf.GetItemPosition("_Number_Item"),(-1,2))

   def testReplaceOrder(self):
       """Test that a replaced item is at the same position it
       previously held"""
       testloop = self.cf.GetLoop("_item_name_1")
       oldpos = testloop.GetItemPosition('_item_name#2')
       testloop['_item_name#2'] = ("I'm",' a ','little','teapot')
       self.assertEqual(testloop.GetItemPosition('_item_name#2'),oldpos)
#
#  Test setting of block names
#

class BlockNameTestCase(unittest.TestCase):
   def testBlockName(self):
       """Make sure long block names cause errors"""
       df = CifFile.CifBlock()
       cf = CifFile.CifFile()
       try:
           cf['a_very_long_block_name_which_should_be_rejected_out_of_hand123456789012345678']=df
       except CifFile.StarError: pass
       else: self.fail()

   def testBlockOverwrite(self):
       """Upper/lower case should be seen as identical"""
       df = CifFile.CifBlock()
       ef = CifFile.CifBlock()
       cf = CifFile.CifFile(standard=None)
       df['_random_1'] = 'oldval'
       ef['_random_1'] = 'newval'
       print('cf.standard is ' + repr(cf.standard))
       cf['_lowercaseblock'] = df
       cf['_LowerCaseBlock'] = ef
       assert(cf['_Lowercaseblock']['_random_1'] == 'newval')
       assert(len(cf) == 1)

   def testEmptyBlock(self):
       """Test that empty blocks are not the same object"""
       cf = CifFile.CifFile()
       cf.NewBlock('first_block')
       cf.NewBlock('second_block')
       cf['first_block']['_test1'] = 'abc'
       cf['second_block']['_test1'] = 'def'
       self.assertEqual(cf['first_block']['_test1'],'abc')

#
#   Test reading cases
#
class FileWriteTestCase(unittest.TestCase):
   def setUp(self):
       """Write out a file, then read it in again. Non alphabetic ordering to
          check order preservation and mixed case."""
       # fill up the block with stuff
       items = (('_item_1','Some data'),
             ('_item_3','34.2332'),
             ('_item_4','Some very long data which we hope will overflow the single line and force printing of another line aaaaa bbbbbb cccccc dddddddd eeeeeeeee fffffffff hhhhhhhhh iiiiiiii jjjjjj'),
             ('_item_2','Some_underline_data'),
             ('_item_empty',''),
             ('_item_quote',"'ABC"),
             ('_item_apost','"def'),
             ('_item_sws'," \n "),
             ('_item_bad_beg',"data_journal"),
             (('_item_5','_item_7','_item_6'),
             ([1,2,3,4],
              ['a','b','c','d'],
              [5,6,7,8])),
             (('_string_1','_string_2'),
              ([';this string begins with a semicolon',
               'this string is way way too long and should overflow onto the next line eventually if I keep typing for long enough',
               ';just_any_old_semicolon-starting-string'],
               ['a string with a final quote"',
               'a string with a " and a safe\';',
               'a string with a final \''])))
       # save block items as well
       s_items = (('_sitem_1','Some save data'),
             ('_sitem_2','Some_underline_data'),
             ('_sitem_3','34.2332'),
             ('_sitem_4','Some very long data which we hope will overflow the single line and force printing of another line aaaaa bbbbbb cccccc dddddddd eeeeeeeee fffffffff hhhhhhhhh iiiiiiii jjjjjj'),
             (('_sitem_5','_sitem_6','_sitem_7'),
             ([1,2,3,4],
              [5,6,7,8],
              ['a','b','c','d'])),
             (('_string_1','_string_2'),
              ([';this string begins with a semicolon',
               'this string is way way too long and should overflow onto the next line eventually if I keep typing for long enough',
               ';just_any_old_semicolon-starting-string'],
               ['a string with a final quote"',
               'a string with a " and a safe\';',
               'a string with a final \''])))
       self.cf = CifFile.CifBlock(items)
       cif = CifFile.CifFile(scoping='dictionary',maxoutlength=80)
       cif['Testblock'] = self.cf
       # Add some comments
       self.save_block = CifFile.CifBlock(s_items)
       cif.NewBlock("test_Save_frame",self.save_block,parent='testblock')
       self.cfs = cif["test_save_frame"]
       outfile = open('tests/test.cif','w')
       outfile.write(str(cif))
       outfile.close()
       self.ef = CifFile.CifFile('tests/test.cif',scoping='dictionary')
       self.df = self.ef['testblock']
       self.dfs = self.ef["test_save_frame"]
       flfile = CifFile.ReadCif('tests/test.cif',scantype="flex",scoping='dictionary')
       # test passing a stream directly
       tstream = open('tests/test.cif')
       CifFile.CifFile(tstream,scantype="flex")
       CifFile.ReadCif(tstream,scantype="flex")  #different code path
       self.flf = flfile['testblock']
       self.flfs = flfile["Test_save_frame"]

   def tearDown(self):
       try:
           os.remove('tests/test.cif')
           os.remove('tests/test2.cif')
       except:
           pass

       del self.dfs
       del self.df
       del self.cf
       del self.ef
       del self.flf
       del self.flfs

   def testStringInOut(self):
       """Test writing short strings in and out"""
       self.assertTrue(self.cf['_item_1']==self.df['_item_1'])
       self.assertTrue(self.cf['_item_2']==self.df['_item_2'])
       self.assertTrue(self.cfs['_sitem_1']==self.dfs['_sitem_1'])
       self.assertTrue(self.cfs['_sitem_2']==self.dfs['_sitem_2'])
       self.assertTrue(self.cfs['_sitem_1']==self.flfs['_sitem_1'])
       self.assertTrue(self.cfs['_sitem_2']==self.flfs['_sitem_2'])

   def testApostropheInOut(self):
       """Test correct behaviour for values starting with apostrophes
       or quotation marks"""
       self.assertTrue(self.cf['_item_quote']==self.df['_item_quote'])
       self.assertTrue(self.cf['_item_apost']==self.df['_item_apost'])
       self.assertTrue(self.cf['_item_quote']==self.flf['_item_quote'])
       self.assertTrue(self.cf['_item_apost']==self.flf['_item_apost'])

   def testNumberInOut(self):
       """Test writing number in and out"""
       self.assertTrue(self.cf['_item_3']==(self.df['_item_3']))
       self.assertTrue(self.cfs['_sitem_3']==(self.dfs['_sitem_3']))
       self.assertTrue(self.cf['_item_3']==(self.flf['_item_3']))
       self.assertTrue(self.cfs['_sitem_3']==(self.flfs['_sitem_3']))

   def testLongStringInOut(self):
       """Test writing long string in and out
       Note that whitespace may vary due to carriage returns,
       so we remove all returns before comparing"""
       import re
       compstring = re.sub('\n','',self.df['_item_4'])
       self.assertTrue(compstring == self.cf['_item_4'])
       compstring = re.sub('\n','',self.dfs['_sitem_4'])
       self.assertTrue(compstring == self.cfs['_sitem_4'])
       compstring = re.sub('\n','',self.flf['_item_4'])
       self.assertTrue(compstring == self.cf['_item_4'])
       compstring = re.sub('\n','',self.flfs['_sitem_4'])
       self.assertTrue(compstring == self.cfs['_sitem_4'])

   def testEmptyStringInOut(self):
       """An empty string is in fact kosher"""
       self.assertTrue(self.cf['_item_empty']=='')
       self.assertTrue(self.flf['_item_empty']=='')

   def testSemiWhiteSpace(self):
       """Test that white space in a semicolon string is preserved"""
       self.assertTrue(self.cf['_item_sws']==self.df['_item_sws'])
       self.assertTrue(self.cf['_item_sws']==self.flf['_item_sws'])

   def testLoopDataInOut(self):
       """Test writing in and out loop data"""
       olditems = self.cf.GetLoop('_item_5')
       for key,value in olditems.items():
           self.assertTrue(tuple(map(str,value))==tuple(self.df[key]))
           self.assertTrue(tuple(map(str,value))==tuple(self.flf[key]))
       # save frame test
       olditems = self.cfs.GetLoop('_sitem_5').items()
       for key,value in olditems:
           self.assertTrue(tuple(map(str,value))==tuple(self.dfs[key]))
           self.assertTrue(tuple(map(str,value))==tuple(self.flfs[key]))

   def testLoopStringInOut(self):
       """Test writing in and out string loop data"""
       olditems = self.cf.GetLoop('_string_1')
       newitems = self.df.GetLoop('_string_1')
       flexnewitems = self.flf.GetLoop('_string_1')
       for key,value in olditems.items():
           compstringa = [re.sub('\n','',a) for a in value]
           compstringb = [re.sub('\n','',a) for a in self.df[key]]
           compstringc = [re.sub('\n','',a) for a in self.flf[key]]
           self.assertTrue(compstringa==compstringb and compstringa==compstringc)

   def testGetLoopData(self):
       """Test the get method for looped data"""
       newvals = self.df.get('_string_1')
       self.assertTrue(len(newvals)==3)

   def testCopySaveFrame(self):
       """Early implementations didn't copy the save frame properly"""
       jj = CifFile.CifFile(self.ef,scoping='dictionary')  #this will trigger a copy
       self.assertTrue(len(jj["test_save_frame"])>0)

   def testFirstBlock(self):
       """Test that first_block returns a block"""
       self.ef.scoping = 'instance'  #otherwise all blocks are available
       jj = self.ef.first_block()
       self.assertTrue(jj==self.df)

   def testWrongLoop(self):
       """Test derived from error observed during dREL testing"""
       teststrg = """data_test
loop_
_atom_type.symbol
_atom_type.oxidation_number
_atom_type.atomic_mass
_atom_type.number_in_cell
  O    ?   15.999   12
  C    ?   12.011   28
  H    ?   1.008    24
       """
       q = open("tests/test2.cif","w")
       q.write(teststrg)
       q.close()
       testcif = CifFile.CifFile("tests/test2.cif").first_block()
       self.assertTrue(testcif['_atom_type.symbol']==['O','C','H'])

   def testDupName(self):
       """Test that duplicate blocknames are allowed in non-standard mode"""
       outstr = """data_block1 _data_1 b save_ab1 _data_2 c
                  save_
                  save_ab1 _data_3 d save_"""
       b = open("tests/test2.cif","w")
       b.write(outstr)
       b.close()
       testin = CifFile.CifFile("tests/test2.cif",standard=None)

   def testPrefixProtocol(self):
       """Test that pathological strings round-trip correctly"""
       cif_as_text = open('tests/test.cif','r').read()
       bf = CifFile.CifFile(maxoutlength=80)
       bb = CifFile.CifBlock()
       bb['_data_embedded'] = cif_as_text
       bf['tough_one'] = bb
       out_f = open('tests/embedded.cif','w')
       out_f.write(str(bf))
       out_f.close()
       in_emb = CifFile.CifFile('tests/embedded.cif',grammar='2.0')
       self.assertEqual(in_emb['tough_one']['_data_embedded'],cif_as_text)

   def testBadBeginning(self):
       """Test that strings with forbidden beginnings round-trip OK"""
       self.assertTrue(self.cf['_item_bad_beg']==self.df['_item_bad_beg'])

   def testStrayCharacter(self):
       """Test that CIF1 fails with non-ASCII characters"""
       outstr = b"""data_block1 _normal_str 'hello sunshine'
                   _latin1_str abc\xB0efgh"""
       b = open("tests/test3_latin1.cif","wb")
       b.write(outstr)
       b.close()
       try:
           testin =  CifFile.CifFile("tests/test3_latin1.cif",grammar="1.0",permissive=False)
       except CifFile.StarError:
           pass
       
   def testPermissiveRead(self):
       """Test that stray latin-1 characters are accepted in permissive mode"""
       outstr = b"""data_block1 _normal_str 'hello sunshine'
                   _latin1_str abc\xB0efgh"""
       b = open("tests/test3_latin1.cif","wb")
       b.write(outstr)
       b.close()
       testin =  CifFile.CifFile("tests/test3_latin1.cif",grammar="1.0",permissive=True)

   def testItemChange(self):
        """Test that an item from in input file can be changed"""
        self.flf['_item_quote']= '2.3'
        self.assertTrue(self.flf['_item_quote']=='2.3')

   def testEmptyDict(self):
       """Test that a dictionary is processed correctly"""
       outstr = b"""#\\#CIF_2.0\ndata_block1 _a_dict {"a":2}\n"""
       b = open("tests/test4_dict.cif","wb")
       b.write(outstr)
       b.close()
       testin = CifFile.CifFile("tests/test4_dict.cif",grammar="2.0")
       self.assertTrue(testin["block1"]["_a_dict"] == {"a":"2"})
                       
class SimpleWriteTestCase(unittest.TestCase):
    def setUp(self):
        self.bf = CifFile.CifBlock()
        self.cf = CifFile.CifFile()
        self.cf['testblock'] = self.bf
        self.testfile  = "tests/test_3.cif"

    def tearDown(self):
        try:
            os.remove(self.testfile)
        except:
            pass

    def testNumpyArray(self):
        """Check that an array can be output properly"""
        import numpy
        vector = numpy.array([1,2,3])
        self.bf['_a_vector'] = vector
        open(self.testfile,"w").write(self.cf.WriteOut())
        df = CifFile.CifFile(self.testfile,grammar="auto").first_block()
        print('vector is ' + repr(df['_a_vector']))
        self.assertTrue(df['_a_vector'] == ['1','2','3'])

    def testNumpyLoop(self):
        """Check that an array in a loop can be output properly"""
        import numpy
        vector_list = [numpy.array([1,2,3]),numpy.array([11,12,13]),numpy.array([-1.0,1.0,0.0])]
        self.bf['_a_vector'] = vector_list
        self.bf.CreateLoop(["_a_vector"])
        open(self.testfile,"w").write(self.cf.WriteOut())
        df = CifFile.CifFile(self.testfile,grammar="auto").first_block()
        print('vector is ' + repr(df['_a_vector']))
        self.assertTrue(df['_a_vector'][2] == ['-1.0','1.0','0.0'])

    def testNDString(self):
        """Check that a string containing square brackets is properly quoted for CIF2.0"""
        self.bf['_tst'] = '3[4^6].8^5[3]'
        self.cf.set_grammar("2.0")
        open(self.testfile,"w").write(self.cf.WriteOut())
        df = CifFile.CifFile(self.testfile,grammar="2.0").first_block()
        result = df['_tst']
        self.assertTrue(df['_tst']== self.bf['_tst'])
                        
    def testLong(self):
        """Check that a long integer is acceptable in Python 2"""
        if sys.version_info < (3,):
            self.bf['_tst'] = long(12)
        else:
            self.bf['_tst'] = 12
        q = str(self.bf)    #this will fail if longs are unacceptable

class TemplateTestCase(unittest.TestCase):
   def setUp(self):
       """Create a template"""
       template_string = r"""#\#CIF_2.0
# Template
#
data_TEST_DIC

    _dictionary.title            DDL_DIC
    _definition.update           2011-07-27
    _description.text
;
     This dictionary specifies through its layout how we desire to
     format datanames.  It is not a valid dictionary, but it must
     be a valid CIF file.
;
    _name.category_id            blahblah
    _name.object_id              ALIAS
    _category.key_id           '_alias.definition_id'
    _category.key_list        ['_alias.definition_id']
    _type.purpose                Key
    _type.dimension              [*]
    _import.get    [{"file":'templ_enum.cif' "save":'units_code'}]
     loop_
    _enumeration_set.state
    _enumeration_set.detail
          Dictionary        "applies to all defined items in the dictionary"
          Category          "applies to all defined items in the category"
          Item              "applies to a single item definition"
    _enumeration.default        Item
"""
       f = open("tests/cif_template.cif","w")
       f.write(template_string)
       f.close()

   def tearDown(self):
       try:
           os.remove("tests/cif_template.cif")
           os.remove("tests/temp_test_file.cif")
           os.remove("tests/temp_test_file_new.cif")
       except:
           pass

   def testTemplateInput(self):
       """Test that an output template is successfully input"""
       p = CifFile.CifFile()
       p.SetTemplate("tests/cif_template.cif")
       #print(p.master_template)
       self.assertTrue(p.master_template[0]['dataname']=='_dictionary.title')
       self.assertTrue(p.master_template[5]['column']==31)
       self.assertTrue(p.master_template[2]['delimiter']=='\n;')
       self.assertTrue(p.master_template[11]['column']==11)
       self.assertTrue(p.master_template[12]['delimiter']=='"')
       self.assertTrue(p.master_template[2]['reformat']==True)
       self.assertTrue(p.master_template[2]['reformat_indent']==5)

   def testTemplateOutputOrder(self):
       """Test that items are output in the correct order"""
       test_file = """##
       data_test
       _enumeration.default Item
       _name.object_id  ALIAS
       _crazy_dummy_dataname 'whahey look at me'
       loop_
          _enumeration_set.detail
          _enumeration_set.state
          _enumeration_set.dummy
          'applies to all'  dictionary 0
          'cat only'  category 1
          'whatever'  item 2
       _name.category_id   blahblah
       _description.text
;a nice long string that we would like
to be formatted really nicely with an appropriate indent and so forth. Note
that the template specifies an indent of 5 characters for this particular
data item, and we shouldn't have more than two spaces in a row if we want it
to work properly.
;
       """
       f = open("tests/temp_test_file.cif","w")
       f.write(test_file)
       f.close()
       p = CifFile.CifFile("tests/temp_test_file.cif")
       p.SetTemplate("tests/cif_template.cif")
       f = open("tests/temp_test_file_new.cif","w")
       f.write(str(p))
       f.close()
       # now read as new file
       g = CifFile.CifFile("tests/temp_test_file_new.cif").first_block()
       self.assertEqual(g.item_order[1],'_name.category_id')
       self.assertEqual(g.loops[1][-1],'_enumeration_set.dummy')
       self.assertEqual(g.loops[1][0],'_enumeration_set.state')
       self.assertEqual(g.item_order[-1],'_crazy_dummy_dataname')

   def testStringInput(self):
        """Test that it works when passed a stringIO object"""
        s = open("tests/cif_template.cif","r").read()
        ss = StringIO(s)
        p = CifFile.CifFile()
        p.SetTemplate(ss)
        self.assertTrue(p.master_template[12]['delimiter']=='"')

       # TODO: check position in loop packets
       # TODO: check delimiters

###### template tests #####
##############################################################
#
#   Test alternative grammars (1.0, 2.0, STAR2)
#
##############################################################
class GrammarTestCase(unittest.TestCase):
   def setUp(self):
       """Write out a file, then read it in again."""
       teststr1_0 = """
       #A test CIF file, grammar version 1.0 conformant
       data_Test
         _item_1 'A simple item'
         _item_2 '(Bracket always ok in quotes)'
         _item_3 [can_have_bracket_here_if_1.0]
       """
       f = open("tests/test_1.0","w")
       f.write(teststr1_0)
       f.close()
       teststr2_0 = r"""#\#CIF_2.0
       data_Test
         _item_1 ['a' 'b' 'c' 'd']
         _item_2 'ordinary string'
         _item_3 {'a':2 'b':3}
       """
       f = open("tests/test_2.0","w")
       f.write(teststr2_0)
       f.close()
       teststr_st = """
       data_Test
         _item_1 ['a' , 'b' , 'c' , 'd']
         _item_2 'ordinary string'
         _item_3 {'a':2 , 'b':3}
       """
       f = open("tests/test_star","w")
       f.write(teststr_st)
       f.close()

   def tearDown(self):
       try:
           os.remove("tests/test_star")
           os.remove("tests/test_2.0")
           os.remove("tests/test_1.0")
       except:
           pass

   def testold(self):
       """Read in 1.0 conformant file; should not fail"""
       f = CifFile.ReadCif("tests/test_1.0",grammar="1.0")
       self.assertEqual(f["test"]["_item_3"],'[can_have_bracket_here_if_1.0]')
       self.assertEqual(f.grammar, "1.0")

   def testNew(self):
       """Read in a 1.0 conformant file with 1.1 grammar; should fail"""
       try:
           f = CifFile.ReadCif("tests/test_1.0",grammar="1.1")
       except CifFile.StarError:
           pass

   def testCIF2(self):
       """Read in a 2.0 conformant file"""
       f = CifFile.ReadCif("tests/test_2.0",grammar="2.0")
       self.assertEqual(f["test"]["_item_3"]['b'],'3')
       self.assertEqual(f.grammar, "2.0")

   def testSTAR2(self):
       """Read in a STAR2 conformant file"""
       f = CifFile.ReadCif("tests/test_star",grammar="STAR2")
       self.assertEqual(f["test"]["_item_3"]['b'],'3')
       self.assertEqual(f.grammar, "STAR2")

   def testAuto(self):
       """Test that grammar is auto-detected"""
       f = CifFile.CifFile("tests/test_1.0",grammar="auto")
       self.assertEqual(f["test"]["_item_3"],'[can_have_bracket_here_if_1.0]')
       self.assertEqual(f.grammar, "1.0")
       h = CifFile.CifFile("tests/test_2.0",grammar="auto")
       self.assertEqual(h["test"]["_item_1"],StarList(['a','b','c','d']))
       self.assertEqual(h.grammar, "2.0")

   def testFlexCIF2(self):
       """Test that CIF2 grammar is detected with flex tokenizer"""
       f = CifFile.CifFile("tests/test_2.0",grammar="2.0",scantype="flex")
       self.assertEqual(f["test"]["_item_3"]['b'],'3')

   def testFlexSTAR2(self):
       """Read in a STAR2 conformant file with flex scanner"""
       f = CifFile.ReadCif("tests/test_star",grammar="STAR2",scantype="flex")
       self.assertEqual(f["test"]["_item_3"]['b'],'3')

   def testRoundTrip(self):
       """Read in STAR2, write out CIF2, read in and check """
       f = CifFile.ReadCif("tests/test_star",grammar="STAR2")
       g = open("tests/star_to_cif2","w")
       f.set_grammar("2.0")
       g.write(str(f))
       g.close()
       h = CifFile.ReadCif("tests/star_to_cif2",grammar="2.0")
       self.assertEqual(f["test"]["_item_3"],h["test"]["_item_3"])

class ParentChildTestCase(unittest.TestCase):
   def setUp(self):
       """Write out a multi-save-frame file, read in again"""
       outstring = """
data_Toplevel
 _item_1         a
 save_1
   _s1_item1     b
   save_12
   _s12_item1    c
   save_
   save_13
   _s13_item1    d
   save_
 save_
 _item_2         e
 save_2
   _s2_item1     f
   save_21
   _s21_item1    g
     save_211
     _s211_item1 h
     save_
     save_212
     _s212_item1 i
     save_
    save_
   save_22
    _s22_item1   j
   save_
 save_
 save_toplevel
   _item_1       k
 save_
"""
       f = open('tests/save_test.cif','w')
       f.write(outstring)
       f.close()
       self.testcif = CifFile.CifFile('tests/save_test.cif',scoping='dictionary')

   def testGoodRead(self):
       """Check that there is a top level block"""
       self.assertTrue('toplevel+' in [a[0] for a in self.testcif.child_table.items() if a[1].parent is None])
       self.assertTrue(self.testcif.child_table['toplevel'].parent == 'toplevel+')

   def testGetParent(self):
       """Check that parent is correctly identified"""
       self.assertTrue(self.testcif.get_parent('212')=='21')
       self.assertTrue(self.testcif.get_parent('12')=='1')

   def testGetChildren(self):
       """Test that our child blocks are constructed correctly"""
       p = self.testcif.get_children('1')
       self.assertTrue(p.has_key('13'))
       self.assertTrue(not p.has_key('1'))
       self.assertTrue(p.get_parent('13')==None)
       self.assertTrue(p['12']['_s12_item1']=='c')

   def testGetChildrenwithParent(self):
       """Test that the parent is included if necessary"""
       p = self.testcif.get_children('1',include_parent=True)
       self.assertTrue(p.has_key('1'))
       self.assertTrue(p.get_parent('13')=='1')

   def testSetParent(self):
       """Test that the parent is correctly set"""
       self.testcif.set_parent('1','211')
       q = self.testcif.get_children('1')
       self.assertTrue('211' in q.keys())

   def testChangeParent(self):
       """Test that a duplicated save frame is OK if the duplicate name is a data block"""
       self.assertTrue('toplevel+' in self.testcif.keys())
       self.assertTrue(self.testcif.get_parent('1')=='toplevel+')

   def testRename1(self):
       """Test that re-identifying a datablock works"""
       self.testcif._rekey('2','timey-wimey')
       self.assertTrue(self.testcif.get_parent('21')=='timey-wimey')
       self.assertTrue(self.testcif.has_key('timey-wimey'))
       self.assertTrue(self.testcif['timey-wimey']['_s2_item1']=='f')
       print(str(self.testcif))

   def testRename2(self):
       """Test that renamng a block works"""
       self.testcif.rename('2','Timey-wimey')
       self.assertTrue(self.testcif.has_key('timey-wimey'))
       self.assertTrue(self.testcif.child_table['timey-wimey'].block_id=='Timey-wimey')

   def testUnlock(self):
       """Test that unlocking will change overwrite flag"""
       self.testcif['2'].overwrite = False
       self.testcif.unlock()
       self.assertTrue(self.testcif['2'].overwrite is True)

class DDLmTestCase(unittest.TestCase):
   def setUp(self):
       """Write out a file, then read it in again."""
       teststr1_2 = """
       #A test CIF file, grammar version 1.2 nonconformant
       data_Test
         _item_1 'A simple item'
         _item_2 '(Bracket always ok in quotes)'
         _item_3 (can_have_bracket_here_if_1.2)
         _item_4 This_is_so_wrong?*~
       """
       goodstr1_2 = """
       #A test CIF file, grammar version 1.2 conformant with nested save frames
       data_Test
          _name.category_id           CIF_DIC
          _name.object_id             CIF_CORE
          _import.get
        [{"save":'EXPERIMENTAL', "file":'core_exptl.dic', "mode":'full' },
         {"save":'DIFFRACTION',  "file":'core_diffr.dic', "mode":'full' },
         {"save":'STRUCTURE',    "file":'core_struc.dic', "mode":'full' },
         {"save":'MODEL',        "file":'core_model.dic', "mode":'full' },
         {"save":'PUBLICATION',  "file":'core_publn.dic', "mode":'full' },
         {"save":'FUNCTION',     "file":'core_funct.dic', "mode":'full' }]
        save_Savelevel1
         _item_in_save [1,2,3,4]
         save_saveLevel2
            _item_in_inside_save {"hello":"goodbye","e":"mc2"}
         save_
        save_
         _test.1 {"piffle":poffle,"wiffle":3,'''woffle''':9.2}
         _test_2 {"ping":[1,2,3,4],"pong":[a,b,c,d]}
         _test_3 {"ppp":{'qqq':2,'poke':{'joke':[5,6,7],'jike':[{'aa':bb,'cc':dd},{'ee':ff,"gg":100}]}},"rrr":[11,12,13]}
         _triple_quote_test '''The comma is ok if, the quotes
                                are ok'''
         _underscore_test underscores_are_allowed_inside_text
       """
       f = open("tests/test_1.2","w")
       f.write(teststr1_2)
       f.close()
       f = open("tests/goodtest_1.2","w")
       f.write(goodstr1_2)
       f.close()

   def tearDown(self):
       try:
           os.remove("tests/test_1.2")
           os.remove("tests/goodtest_1.2")
           os.remove("tests/newgoodtest_1.2.cif")
           os.remove("tests/cif2goodtest_1.2.cif")
       except:
           pass

   def testold(self):
       """Read in 1.2 nonconformant file; should fail"""
       try:
           f = CifFile.ReadCif("tests/test_1.2",grammar="STAR2")
       except CifFile.StarError:
           pass

   def testgood(self):
       """Read in 1.2 conformant file: should succeed"""
       f = CifFile.ReadCif("tests/goodtest_1.2",grammar="STAR2")

   def testTables(self):
       """Test that DDLm tables are properly parsed"""
       f = CifFile.ReadCif("tests/goodtest_1.2",grammar="STAR2")
       self.assertTrue(f["test"]["_test.1"]["wiffle"] == '3')

   def testTables2(self):
       """Test that a plain table is properly parsed"""
       f = CifFile.ReadCif("tests/goodtest_1.2",grammar="STAR2")
       self.assertTrue(f["test"]["_import.get"][0]["file"] == 'core_exptl.dic')

   def testTables3(self):
       """Test that a nested structure is properly parsed"""
       f = CifFile.ReadCif("tests/goodtest_1.2",grammar="STAR2")
       self.assertTrue(f["test"]["_test_3"]["ppp"]["poke"]["jike"][1]["gg"]=='100')

   def testTripleQuote(self):
       """Test that triple quoted values are treated correctly"""
       f = CifFile.ReadCif("tests/goodtest_1.2",grammar="STAR2")
       print(f["test"]["_triple_quote_test"])
       self.assertTrue(f["test"]["_triple_quote_test"][:9] == 'The comma')

   def testRoundTrip(self):
       """Test that a DDLm file can be read in, written out and read in again"""
       f = CifFile.ReadCif("tests/goodtest_1.2",grammar="STAR2")
       g = open("tests/newgoodtest_1.2.cif","w")
       g.write(str(f))
       g.close()
       h = CifFile.ReadCif("tests/newgoodtest_1.2.cif",grammar="STAR2")
       #print(h['Test'])
       #print(h['Test']['_import.get'])
       #print(h['Test']['_import.get'][2])
       #print(h['Test']['_import.get'][2]['file'])
       self.assertTrue(h['Test']['_import.get'][2]['file']=='core_struc.dic')

   def testUnNest(self):
       """Test that we can convert a nested save frame STAR2 file to a non-nested file"""
       f = CifFile.ReadCif("tests/goodtest_1.2",grammar="STAR2")
       g = open("tests/cif2goodtest_1.2.cif","w")
       f.set_grammar("2.0")
       g.write(str(f))
       h = CifFile.ReadCif("tests/cif2goodtest_1.2.cif")

##########
#
# Test DDLm imports
#
##########
class DDLmImportCase(unittest.TestCase):
    def setUp(self):
        self.testdic = CifFile.CifDic("dictionaries/cif_core_ddlm.dic",grammar="2.0",do_dREL=False)
        self.lightdic = CifFile.CifDic("dictionaries/cif_core_ddlm.dic",grammar="2.0",
                                       do_imports='contents',heavy=False,do_dREL=False)

    def testHeavyImport(self):
        """Test that enumerated types were imported correctly"""
        pp = self.testdic['_atom_type.radius_bond']
        self.assertTrue(pp.has_key('_enumeration_default.index'))
        c_pos = pp['_enumeration_default.index'].index('C')
        self.assertEqual(pp['_enumeration_default.value'][c_pos],'0.77')

    def testLightImport(self):
        """Test that light importation succeeds"""
        pp = self.lightdic['_atom_type.radius_bond']
        self.assertTrue(pp.has_key('_enumeration_default.index'))
        c_pos = pp['_enumeration_default.index'].index('C')
        self.assertEqual(pp['_enumeration_default.value'][c_pos],'0.77')

    def testLightFullImport(self):
        """Test that we properly import nested dictionaries"""
        nested_dic = CifFile.CifDic("dictionaries/cif_nested.dic",grammar="2.0",
                                         do_imports='Full',do_dREL=False,heavy=False)
        self.assertTrue(nested_dic['_refine_diff.density_max']['_enumeration.range']=='-100.:')
        self.assertTrue('_pd_refln.phase_id' in nested_dic['refln']['_category_key.name'])
        
##############################################################
#
# Test dictionary type
#
##############################################################
#ddl1dic = CifFile.CifDic("test/dictionaries/cif_core.dic",scantype="flex",do_minimum=True)

class DictTestCase(unittest.TestCase):
    def setUp(self):
        self.ddldic = CifFile.CifDic("tests/dictionaries/ddl.dic",grammar='2.0',scoping='dictionary',do_minimum=True)  #small DDLm dictionary

    def tearDown(self):
        try:
            os.remove("test_dic_write.cif")
        except:
            pass

    def testnum_and_esd(self):
        """Test conversion of numbers with esds"""
        testnums = ["5.65","-76.24(3)","8(2)","6.24(3)e3","55.2(2)d4"]
        res = [CifFile.get_number_with_esd(a) for a in testnums]
        print(repr(res))
        self.assertTrue(res[0]==(5.65,None))
        self.assertTrue(res[1]==(-76.24,0.03))
        self.assertTrue(res[2]==(8,2))
        self.assertTrue(res[3]==(6240,30))
        self.assertTrue(res[4]==(552000,2000))

    def testdot(self):
        """Make sure a single dot is skipped"""
        res1,res2 = CifFile.get_number_with_esd(".")
        self.assertTrue(res1==None)

    def testCategoryRename(self):
        """Test that renaming a category works correctly"""
        self.ddldic.change_category_name('Description','Opisanie')
        self.assertTrue(self.ddldic.has_key('opisanie'))
        self.assertTrue(self.ddldic['opisanie']['_name.object_id']=='Opisanie')
        self.assertTrue(self.ddldic.has_key('opisanie.text'))
        self.assertTrue(self.ddldic['opisanie.text']['_name.category_id']=='Opisanie')
        self.assertTrue(self.ddldic['opisanie.text']['_definition.id']=='_Opisanie.text')
        self.assertTrue(self.ddldic.has_key('description_example'))

    def testChangeItemCategory(self):
        """Test that changing an item's category works"""
        self.ddldic.change_category('_description.common','type')
        self.assertTrue('_type.common' in self.ddldic)
        self.assertTrue('_description.common' not in self.ddldic)
        self.assertTrue(self.ddldic['_type.common']['_name.category_id'].lower()=='type')
        self.assertTrue(self.ddldic.get_parent('_type.common')=='type')

    def testChangeCategoryCategory(self):
        """Test that changing a category's category works"""
        self.ddldic.change_category('description_example','attributes')
        self.assertTrue(self.ddldic['description_example']['_name.category_id'].lower()=='attributes')
        self.assertTrue(self.ddldic.get_parent('description_example')=='attributes')

    def testChangeName(self):
        """Test that changing the object_id works"""
        self.ddldic.change_name('_description.common','uncommon')
        self.assertTrue('_description.uncommon' in self.ddldic)
        self.assertTrue('_description.common' not in self.ddldic)
        self.assertTrue(self.ddldic['_description.uncommon']['_name.object_id']=='uncommon')
        self.assertTrue(self.ddldic['_description.uncommon']['_definition.id']=='_description.uncommon')

    def testNewCategory(self):
        """Test that we can add a new category"""
        self.ddldic.add_category('brand-new')
        self.assertTrue('brand-new' in self.ddldic)
        self.assertTrue(self.ddldic['brand-new']['_name.object_id']=='brand-new')
        self.assertTrue(self.ddldic.get_parent('brand-new').lower()=='ddl_dic')
        self.assertTrue(self.ddldic['brand-new']['_name.category_id'].lower()=='attributes')

    def testNewDefinition(self):
        """Test that we can add a new definition"""
        realname = self.ddldic.add_definition('_junkety._junkjunk','description')
        print('Real name for new definition is %s' % realname)
        self.assertTrue('_description.junkjunk' in self.ddldic)
        self.assertTrue(self.ddldic['_description.junkjunk']['_name.category_id'].lower()=='description')
        self.assertTrue(self.ddldic['_description.junkjunk']['_name.object_id']=='junkjunk')
        self.assertTrue(self.ddldic['_description.junkjunk']['_definition.id']=='_description.junkjunk')

    def testNewDanglerDef(self):
        """Test that we can add a new definition with external category"""
        self.ddldic.add_definition('_junkety._junkjunk','external_cat',allow_dangler=True)
        self.assertTrue('_external_cat.junkjunk' in self.ddldic)
        self.assertTrue(self.ddldic['_external_cat.junkjunk']['_name.category_id'].lower()=='external_cat')
        self.assertTrue(self.ddldic['_external_cat.junkjunk']['_name.object_id']=='junkjunk')
        self.assertTrue(self.ddldic['_external_cat.junkjunk']['_definition.id']=='_external_cat.junkjunk')


    def testNewDanglerCat(self):
        """Test that we can add a new category with external parent"""
        self.ddldic.add_category('internal_cat','atom_site',allow_dangler=True)
        self.assertTrue('internal_cat' in self.ddldic)
        self.assertTrue(self.ddldic['internal_cat']['_name.object_id']=='internal_cat')
        self.assertTrue(self.ddldic.get_parent('internal_cat').lower()=='ddl_dic')
        self.assertTrue(self.ddldic['internal_cat']['_name.category_id'].lower()=='atom_site')

    def testDeleteDefinition(self):
        """Test that we can delete a definition"""
        self.ddldic.remove_definition('_alias.deprecation_date')
        self.assertTrue('_alias.deprecation_date' not in self.ddldic)

    def testDeleteCategory(self):
        """test that we can delete whole categories"""
        self.ddldic.remove_definition('description')
        self.assertTrue('description' not in self.ddldic)
        self.assertTrue('description_example' not in self.ddldic)

    def testWriteDic(self):
        """Test that we can write a dictionary after adding a category"""
        self.ddldic.add_definition('_junkety._junkjunk_','description')
        self.ddldic.set_grammar('2.0')
        final_str = str(self.ddldic)  #should not fail
        cwd = os.getcwd()
        ffurl = os.path.join(cwd,"tests/test_dic_write.cif")
        ff = open(ffurl,"w")
        ff.write(final_str)
        ff.close()
        incif = CifFile.CifDic("file:"+ffurl,grammar='2.0',do_minimum=True)
        self.assertTrue(incif.has_key('_description.junkjunk'))

    def testSemanticChildren(self):
        """Test that we can obtain the semantic children of a category"""
        children = self.ddldic.ddlm_immediate_children('enumeration_set')
        self.assertTrue('_enumeration_set.state' in children)
        children = self.ddldic.ddlm_immediate_children('enumeration')
        self.assertTrue('enumeration_set' in children)

    def testDanglers(self):
        """Test that we correctly locate missing categories"""
        self.ddldic['_description.text'].overwrite = True
        self.ddldic['_description.text']['_name.category_id'] = 'NNN'
        p = self.ddldic.ddlm_danglers()
        self.assertTrue('_description.text' in p)
        self.assertTrue('ddl_dic' not in p)
        self.assertTrue('attributes' not in p)

    def testAllChildren(self):
        """Test that we can pick up all children"""
        children = self.ddldic.ddlm_all_children('description')
        self.assertTrue('_description_example.detail' in children)

    def testDanglerChildren(self):
        """Test that danglers are found when outputting"""
        self.ddldic.add_definition('_junkety._junkjunk','external_cat',allow_dangler=True)
        self.ddldic.add_category('some_other_cat','atom_site',allow_dangler=True)
        self.ddldic.add_definition('_xxx.more_junk','some_other_cat')
        names = self.ddldic.get_full_child_list()
        self.assertTrue('some_other_cat' in names)
        self.assertTrue('_external_cat.junkjunk' in names)
        self.assertTrue('_some_other_cat.more_junk' in names)

    def testFunnyLayout(self):
        """Test that having some of the data block at the end is OK"""
        good_read = CifFile.CifDic("tests/ddl_rearranged.dic",grammar="2.0",scoping="dictionary",do_minimum=True)

# now for some value testing
class DDLmValueTestCase(unittest.TestCase):
    def setUp(self):
        filedata = """
data_testblock
_float.value 4.2
_hex.value 0xA2
_list1.value [1.2, 2.3, 4.5]
_list2.value [['i',4.2],['j',1.5],['lmnop',-4.5]]
_matrix.value [[1,2,3],[4,5,6],[7,8,9]]
"""
        p = open('tests/ddlm_testdata','w')
        p.write(filedata)
        p.close()
        self.testblock = CifFile.CifFile('tests/ddlm_testdata',grammar="STAR2")['testblock']

    def tearDown(self):
        os.remove("tests/ddlm_testdata")

    def testTypeInterpretation(self):
        """Test that we decode DDLm type.contents correctly"""
        import CifFile.TypeContentsParser as t
        p = t.TypeParser(t.TypeParserScanner('List(Real,Real,Real)'))
        q = getattr(p,"input")()
        print(repr(q))
        self.assertTrue(q == ['Real','Real','Real'])
        p = t.TypeParser(t.TypeParserScanner('List(Real,List(Integer,Real),Real)'))
        q = getattr(p,"input")()
        print(repr(q))
        self.assertTrue(q == ['Real',['Integer','Real'],'Real'])

    def testSingleConversion(self):
        namedef = CifFile.CifBlock()
        namedef['_type.container'] = 'Single'
        namedef['_type.contents'] = 'Real'
        result = CifFile.convert_type(namedef)(self.testblock['_float.value'])
        self.assertTrue(result == 4.2)

    def testListConversion(self):
        namedef = CifFile.CifBlock()
        namedef['_type.container'] = 'List'
        namedef['_type.contents'] = 'List(Text,Real)'
        namedef['_type.dimension'] = '[3]'
        result = CifFile.convert_type(namedef)(self.testblock['_list2.value'])
        print('Result: ' + repr(result))
        self.assertTrue(result ==  [['i',4.2],['j',1.5],['lmnop',-4.5]])

    def testSimpleListConversion(self):
        namedef = CifFile.CifBlock()
        namedef['_type.container'] = 'List'
        namedef['_type.contents'] = 'Real'
        namedef['_type.dimension'] = '[3]'
        result = CifFile.convert_type(namedef)(self.testblock['_list1.value'])
        self.assertEqual(result,  [1.2, 2.3, 4.5])

    def testMatrixConversion(self):
        namedef = CifFile.CifBlock()
        namedef['_type.container'] = 'Matrix'
        namedef['_type.contents'] = 'Integer'
        result = CifFile.convert_type(namedef)(self.testblock['_matrix.value'])
        self.assertTrue(result[1][2] == 6)

    def testValuesReturned(self):
        """Test that values are returned transparently converted when a dictionary is supplied"""
        pass

##############################################################
#
#  Validation testing. Used to use ValidCifFile
#
##############################################################

# We first test single item checking
class DDL1TestCase(unittest.TestCase):

    def setUp(self):
        self.ddl1dic = CifFile.CifDic("tests/dictionaries/cif_core.dic")

    def testReport(self):
        CifFile.validate_report(CifFile.Validate("tests/C13H2203_with_errors.cif",dic=self.ddl1dic))

class DDLmDicTestCase(unittest.TestCase):
    """Test validation of DDLm dictionaries"""
    def setUp(self):
        testdic_string = r"""#\#CIF_2.0
#\#CIF_2.0
##############################################################################
#                                                                            #
#                      DDLm REFERENCE DICTIONARY                             #
#                                                                            #
##############################################################################
data_DDL_DIC

    _dictionary.title            DDL_DIC
    _dictionary.class            Reference
    _dictionary.version          3.11.08
    _dictionary.date             2015-01-28
    _dictionary.uri              www.iucr.org/cif/dic/ddl.dic
    _dictionary.ddl_conformance  3.11.08
    _dictionary.namespace        DdlDic
    _description.text
;
     This dictionary contains the definitions of attributes that
     make up the DDLm dictionary definition language.  It provides
     the meta meta data for all CIF dictionaries.
;

save_ATTRIBUTES

    _definition.id               ATTRIBUTES
    _definition.scope            Category
    _definition.class            Head
    _definition.update           2011-07-27
    _description.text
;
     This category is parent of all other categories in the DDLm
     dictionary.
;
    _name.object_id              ATTRIBUTES

save_

#============================================================================

save_ALIAS

    _definition.id               ALIAS
    _definition.scope            Category
    _definition.class            Loop
    _definition.update           2013-09-08
    _description.text
;
     The attributes used to specify the aliased names of definitions.
;
    _name.category_id            ATTRIBUTES
    _name.object_id              ALIAS
    _category.key_id             '_alias.definition_id'
    loop_
    _category_key.name
                                 '_alias.definition_id'

save_


save_alias.definition_id

    _definition.id               '_alias.definition_id'
    _definition.class            Attribute
    _definition.update           2006-11-16
    _description.text
;
     Identifier tag of an aliased definition.
;
    _name.category_id            alias
    _name.object_id              definition_id
    _type.purpose                Key
    _type.source                 Assigned
    _type.container              Single
    _type.contents               Tag

save_

save_definition.scope

    _definition.id               '_definition.scope'
    _definition.class            Attribute
    _definition.update           2006-11-16
    _description.text
;
     The extent to which a definition affects other definitions.
;
    _name.category_id            definition
    _name.object_id              scope
    _type.purpose                State
    _type.source                 Assigned
    _type.container              Single
    _type.contents               Code
    loop_
    _enumeration_set.state
    _enumeration_set.detail
    _description.common
              Dictionary    'applies to all defined items in the dictionary'   'whoops'
              Category      'applies to all defined items in the category'     'not'
              Item          'applies to a single item definition'              'allowed'
    _enumeration.default         Item

save_


 """
        f = open('tests/ddlm_valid_test.cif2','w')
        f.write(testdic_string)
        f.close()
        self.testcif = CifFile.CifFile('tests/ddlm_valid_test.cif2',grammar='auto')
        self.refdic = CifFile.CifDic('tests/dictionaries/ddl.dic',grammar='auto')

    def tearDown(self):
        pass
        #os.remove('tests/ddlm_valid_test.cif2')

    def testMandatory(self):
        """Test that missing mandatory items are found"""
        del self.testcif['alias.definition_id']['_name.category_id']
        result = self.refdic.run_block_validation(self.testcif['alias.definition_id'])
        self.assertTrue(dict(result['whole_block'])['check_mandatory_items']['result']==False)

    def testProhibited(self):
        """Test that prohibited items are found"""
        self.testcif['alias']['_enumeration_set.state'] = [1,2,3,4]
        result = self.refdic.run_block_validation(self.testcif['alias'])
        self.assertTrue(dict(result['whole_block'])['check_prohibited_items']['result']==False)

    def testUnlooped(self):
        """Test that unloopable data items are found"""
        result = self.refdic.run_loop_validation(self.testcif['definition.scope'].loops[1])
        self.assertTrue(dict(result['_enumeration_set.state'])['validate_looping_ddlm']['result']==False)

    def testWrongLoop(self):
        """Test that non-co-loopable data items are found"""
        del self.testcif['definition.scope']['_description.common']  #get rid of bad one
        self.testcif['definition.scope']['_description_example.case'] = [1,2,3]
        self.testcif['definition.scope'].CreateLoop(['_enumeration_set.state',
                                                      '_enumeration_set.detail',
                                                      '_description_example.case'])
        loop_no = self.testcif['definition.scope'].FindLoop('_enumeration_set.state')
        result = self.refdic.run_loop_validation(self.testcif['definition.scope'].loops[loop_no])
        self.assertTrue(dict(result['_enumeration_set.state'])['validate_loop_membership']['result']==False)

    def testUnKeyed(self):
        """Test that a missing key is found"""
        del self.testcif['definition.scope']['_description.common']
        del self.testcif['definition.scope']['_enumeration_set.state']
        result = self.refdic.run_loop_validation(self.testcif['definition.scope'].loops[1])
        self.assertTrue(dict(result['_enumeration_set.detail'])['validate_loop_key_ddlm']['result']==False)

    def testNotMissingKey(self):
        """Test that a key that should be present is detected"""
        result = self.refdic.run_loop_validation(self.testcif['definition.scope'].loops[1])
        print(repr(result))
        self.assertTrue(dict(result['_enumeration_set.state'])['validate_loop_key_ddlm']['result']==True)

class DicEvalTestCase(unittest.TestCase):
    def setUp(self):
        testdic = CifFile.CifDic("tests/dictionaries/cif_core.dic",grammar="auto")
        c_old = CifFile.CifFile("tests/drel/nick_old.cif",grammar="2.0")
        c_new = CifFile.CifFile("tests/drel/nick_new.cif",grammar="2.0")
        self.fb = c_new['saly2']
        self.fb.assign_dictionary(testdic)
        self.fb_old = c_old['saly2']
        self.fb_old.assign_dictionary(testdic)

    def check_value(self,dataname,scalar=True):
        """Generic check of value"""
        target = self.fb[dataname]
        del self.fb[dataname]
        result = self.fb[dataname]
        print("Result: {!r} Target: {!r}".format(result,target))
        if scalar:
            self.assertTrue(abs(float(target)-float(result))<0.01)
        else:
            self.assertEqual(target,result,"Target = %s, Result = %s" % (repr(target),repr(result)))

    def testCellVolume(self):
        self.check_value('_cell.volume')

    @unittest.expectedFailure
    def testNoInCell(self,scalar=False):
        self.check_value('_atom_type.number_in_cell',scalar=False)

    def testDensity(self):
        self.check_value('_exptl_crystal.density_diffrn')

    @unittest.expectedFailure
    def testReflnF(self):
        self.check_value('_refln.F_calc',scalar=False)

    def testCalcOldAlias(self):
        """Test that a calculation is performed for an old dataname"""
        target = self.fb['_cell.volume']
        print("CalcOldAlias target is {!r}".format(target))
        del self.fb['_cell.volume']
        self.assertTrue(abs(self.fb['_cell_volume']-float(target))<0.01)

    def testFullCalcAlias(self):
        """Test that a calculation is performed if dependent datanames
        have aliased values"""
        del self.fb_old['_refln.F_calc']
        result = self.fb_old['_refln.F_calc']

    def testEigenSystem(self):
        """Test that question marks are seen as missing values"""
        self.fb.provide_value = True
        result = self.fb['_model_site.adp_eigen_system']
        print('adp eigensystem is: ' + repr(result))

    def testCategoryMethod(self):
        """Test that a category method calculates and updates"""
        # delete pre-existing values
        del self.fb['_model_site.adp_eigen_system']
        del self.fb["_model_site.label"]
        del self.fb["_model_site.symop"]
        self.fb.provide_value = True
        result = self.fb['model_site']
        self.fb.provide_value = False
        print('**Updated block:')
        print(str(self.fb))
        self.assertTrue(self.fb.has_key('_model_site.Cartn_xyz'))
        self.assertTrue(self.fb.has_key('_model_site.mole_index'))

    def testEmptyKey(self):
        """Test that empty keys are not stored"""
        del self.fb['_atom_type_scat.symbol']
        del self.fb['_atom_type_scat.dispersion_real']
        del self.fb['_atom_type_scat.dispersion_imag']
        del self.fb['_atom_type_scat.source']
        p = self.fb.GetKeyedSemanticPacket('O','atom_type')
        self.assertTrue(not hasattr(p,'_atom_type_scat.symbol'))


class DicStructureTestCase(unittest.TestCase):
    """Tests use of dictionary semantic information for item lookup"""
    def setUp(self):
        self.testdic = CifFile.CifDic("tests/dictionaries/cif_core.dic",grammar="auto")
        cc = CifFile.CifFile("tests/drel/nick.cif",grammar="STAR2")
        self.fb = cc["saly2"]
        self.fb.assign_dictionary(self.testdic)

    def testOldAlias(self):
        """Test finding an older form of a new dataname"""
        self.assertTrue(self.fb['_symmetry.space_group_name_H_M']=='P_1_21/a_1')

    def testNewAlias(self):
        """Test finding a newer form of an old dataname"""
        self.assertTrue(self.fb['_symmetry_space_group_name_Hall']=='-p_2yab')

    def testCatObj(self):
        """Test that we can obtain a name by category/object specification"""
        target = self.testdic.get_name_by_cat_obj('atom_type','Cromer_Mann_coeffs')
        self.assertEqual(target,'_atom_type_scat.Cromer_Mann_coeffs')
        target = self.testdic.get_name_by_cat_obj('cell','volume')
        self.assertEqual(target,'_cell.volume')

    def testCatObj2(self):
        """Test that cat.obj with obj in the parent is found"""
        target = self.testdic.get_name_by_cat_obj('atom_site_aniso','ADP_type')
        assert target == '_atom_site.ADP_type'
        
    def testCatKey(self):
        """Test that we get a complete list of keys for child categories"""
        target = self.testdic.cat_key_table
        self.assertEqual(target['atom_site'],[['_atom_site.label'],['_atom_site_aniso.label']])

    def testEquivKey(self):
        """Test that we can identify equivalent key datanames"""
        target = self.testdic.key_equivs
        self.assertEqual(target['_atom_site_aniso.label'],['_atom_site.label'])

    def testChildPacket(self):
        """Test that a case-insensitive child packet is included in attributes of parent category"""
        target = self.fb.GetKeyedSemanticPacket("o2",'atom_site')
        self.assertTrue(hasattr(target,'_atom_site_aniso.u_23'))
        self.assertEqual(getattr(target,'_atom_site_aniso.U_33'),'.040(3)')

    @unittest.skip("Functionality not yet implemented")
    def testChildPacketMultiKey(self):
        """Test that a case-insensitive child packet is included in attributes of parent category
        using the compound key routine"""
        target = self.fb.GetMultiKeyedSemanticPacket({'_atom_site.label':("o2",True)},'atom_site')
        self.assertEqual(getattr(target,'_atom_site_aniso.U_33'),'.040(3)')
        self.assertTrue(hasattr(target,'_atom_site_aniso.u_23'))

    def testPacketCalcs(self):
        """Test that a star packet can calculate missing values"""
        target = self.fb.GetKeyedSemanticPacket("O",'atom_type')
        rad = getattr(target,'_atom_type.radius_bond')
        self.assertEqual(rad,0.74)

    def testEnumDefault(self):
        """Test that we can obtain enumerated values"""
        target = self.fb['_atom_type.radius_bond']
        self.assertTrue(0.77 in target)

    def testCalcEnumDefault(self):
        """Test that we can calculate defaults"""
        target = self.fb['_atom_sites_cartn_transform.mat_33']
        self.fb.provide_value = True
        assert target == self.fb['_cell.length_c']
        self.fb.provide_value = False
        
    def testCatObjKey(self):
        """Test that keys are correctly handled by the cat/obj table"""
        self.assertEqual(self.testdic.get_name_by_cat_obj('atom_site','label'),"_atom_site.label")

    def testRepeatedName(self):
        """Test that a repeated object_id is handled correctly"""
        self.assertEqual(self.testdic.cat_obj_lookup_table[('atom_site','type_symbol')],
                         ['_atom_site.type_symbol','_atom_site_aniso.type_symbol'])

    def testPrintOut(self):
        """Test that a block with dictionary attached can print(out string values"""
        print(self.fb)

    def pullbacksetup(self):
        """Initial steps when setting up a pullback"""
        dic_info = CifFile.CifDic("tests/full_demo_0.0.6.dic",grammar="auto")
        start_data = CifFile.CifFile("tests/multi-image-test.cif",grammar="auto")
        start_data = start_data['Merged_scans']
        start_data.assign_dictionary(dic_info)
        return start_data

    def unpullbacksetup(self):
        """Initial values when setting up a pullback"""
        dic_info = CifFile.CifDic("tests/full_demo_0.0.6.dic",grammar="auto")
        start_data = CifFile.CifFile("tests/multi-image-test.cif.pulled_back",grammar="auto")
        start_data = start_data['Merged_scans']
        start_data.assign_dictionary(dic_info)
        return start_data

    def testPullBack(self):
        """Test construction of a category that is pulled back from other categories"""
        start_data = self.pullbacksetup()
        q = start_data['_diffrn_detector_monolithic_element.key']
        p = start_data['_diffrn_detector_monolithic_element.detector_id']
        print('p,q = ' + repr(p) + '\n' + repr(q))
        self.assertTrue(q==[['element1','adscq210-sn457']])
        self.assertTrue(p==['ADSCQ210-SN457'])

    def testMultiPullback(self):
        """Test that pullbacks with multiple matches work properly"""
        start_data = self.pullbacksetup()
        q = start_data['_full_frame.id']
        r = start_data['_full_frame.detector_element_id']
        print('Frames from monolithic detector:' + repr(q))
        self.assertTrue(['scan1','frame1'] in q)
        self.assertTrue(['scan1','frame3'] in q)

    def testIntegerFilter(self):
        """Test construction of a block that is filtered from another category"""
        start_data = self.pullbacksetup()
        q = start_data['_diffrn_detector_monolithic.id']
        self.assertTrue(q == ['ADSCQ210-SN457'])

    def testTextFilter(self):
        """Test construction of a block that is filtered using a text string"""
        start_data = self.pullbacksetup()
        q = start_data['_detector_axis.id']
        print('q is ' + repr(q))
        self.assertTrue(['detector_y','detector'] in q)
        self.assertTrue(['goniometer_phi','goniometer'] not in q)

    def testPopulateFromPullback(self):
        """Test population of a category with id items from a pulled-back category"""
        start_data = self.unpullbacksetup()
        q = start_data['_diffrn_data_frame.key']
        self.assertTrue(['SCAN1','FRAME1'] in q)
        self.assertTrue(['SCAN1','Frame3'] in q)

    def testPopulateFromFilter(self):
        """Test population of a category that has been filtered"""
        start_data = self.unpullbacksetup()
        q = start_data['_diffrn_detector.id']
        r = start_data['_diffrn_detector.number_of_elements']
        print('q,r = ' + repr(q) + ' , ' + repr(r))
        self.assertTrue(q==['ADSCQ210-SN457'])
        self.assertTrue(r == [1])

    def testPopulateFromMultiFilters(self):
        """Test population of a category that is filtered into multiple
        streams"""
        start_data = self.unpullbacksetup()
        q = start_data['_axis.key']
        print('q ends up as:' + repr(q))
        self.assertTrue(['detector_x','detector'] in q)
        self.assertTrue(['GONIOMETER_PHI','goniometer'] in q)

    def testPopulateNonIDFromFilter(self):
        """Test that duplicate datanames are populated"""
        start_data = self.unpullbacksetup()
        q = start_data['_diffrn_data_frame.binary_id']
        self.assertTrue('3' in q)

class BlockOutputOrderTestCase(unittest.TestCase):
    def tearDown(self):
        try:
            os.remove("tests/order_test.cif")
            os.remove("tests/round_trip_test.cif")
        except:
            pass

    def testOutputOrder(self):
        outstrg = r"""#\#CIF_2.0
data_testa
_item1 1
data_testb
_item2 2
data_testc
_item3 3
data_testd
_item4 4
"""
        f = open("tests/order_test.cif","w")
        f.write(outstrg)
        f.close()
        q = CifFile.CifFile("tests/order_test.cif",grammar="auto")
        print(repr(q.block_input_order))
        self.assertTrue(q.block_input_order[1] == "testb")
        f = open("tests/round_trip_test.cif","w")
        f.write(str(q))

if __name__=='__main__':
     #suite = unittest.TestLoader().loadTestsFromTestCase(DicEvalTestCase)
     #suite = unittest.TestLoader().loadTestsFromTestCase(SimpleWriteTestCase)
     #suite = unittest.TestLoader().loadTestsFromTestCase(FileWriteTestCase)
     #suite = unittest.TestLoader().loadTestsFromTestCase(GrammarTestCase)
     #suite = unittest.TestLoader().loadTestsFromTestCase(DicStructureTestCase)
     #suite = unittest.TestLoader().loadTestsFromTestCase(BasicUtilitiesTestCase)
     #suite = unittest.TestLoader().loadTestsFromTestCase(BlockRWTestCase)
     #suite = unittest.TestLoader().loadTestsFromTestCase(BlockOutputOrderTestCase)
     #suite = unittest.TestLoader().loadTestsFromTestCase(SyntaxErrorTestCase)
     #suite = unittest.TestLoader().loadTestsFromTestCase(LoopBlockTestCase)
     #suite = unittest.TestLoader().loadTestsFromTestCase(BlockChangeTestCase)
     #suite =  unittest.TestLoader().loadTestsFromTestCase(DDLmValueTestCase)
     #suite =  unittest.TestLoader().loadTestsFromTestCase(DDLmImportCase)
     #suite =  unittest.TestLoader().loadTestsFromTestCase(DDL1TestCase)
     #suite =  unittest.TestLoader().loadTestsFromTestCase(DDLmDicTestCase)
     #suite =  unittest.TestLoader().loadTestsFromTestCase(TemplateTestCase)
     #suite =  unittest.TestLoader().loadTestsFromTestCase(DictTestCase)
     #unittest.TextTestRunner(verbosity=2).run(suite)
     unittest.main()
