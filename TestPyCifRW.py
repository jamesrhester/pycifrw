# We attempt to implement testing of the PyCif module using
# the PyUnit framework
#
# 
import unittest, CifFile
import re

# Test basic setting and reading of the CifBlock

class BlockRWTestCase(unittest.TestCase):
    def setUp(self):
    	# we want to get a datablock ready so that the test
	# case will be able to write a single item
	self.cf = CifFile.CifBlock()

    def tearDown(self):
        # get rid of our test object
	del self.cf
	
    def testTupleNumberSet(self):
        """Test tuple setting with numbers"""
        self.cf['_test_tuple'] = (11,13.5,-5.6)
        self.failUnless(map(float,
	     self.cf['_test_tuple']))== [11,13.5,-5.6]

    def testTupleComplexSet(self):
        """Test setting multiple names in loop"""
	names = ('_item_name_1','_item_name#2','_item_%$#3')
	values = ((1,2,3,4),('hello','good_bye','a space','# 4'),
	          (15.462, -99.34,10804,0.0001))
        self.cf.AddCifItem((names,values))
	self.failUnless(tuple(map(float, self.cf[names[0]])) == values[0])
	self.failUnless(tuple(self.cf[names[1]]) == values[1])
	self.failUnless(tuple(map(float, self.cf[names[2]])) == values[2])

    def testStringSet(self):
        """test string setting"""
        self.cf['_test_string_'] = 'A short string'
	self.failUnless(self.cf['_test_string_'] == 'A short string')

    def testTooLongSet(self):
        """test setting overlong data names"""
        dataname = '_a_long_long_'*7
        try:
            self.cf[dataname] = 1.0
        except CifFile.CifError: pass
        else: self.Fail()

    def testTooLongLoopSet(self):
        """test setting overlong data names in a loop"""
        dataname = '_a_long_long_'*7
        try:
            self.cf[(dataname,)] = ((1.0,2.0,3.0),)
        except CifFile.CifError: pass
        else: self.Fail()

# Now test operations which require a preexisting block
#

class BlockChangeTestCase(unittest.TestCase):
   def setUp(self):
        self.cf = CifFile.CifBlock()
	self.names = ('_item_name_1','_item_name#2','_item_%$#3')
	self.values = ((1,2,3,4),('hello','good_bye','a space','# 4'),
	          (15.462, -99.34,10804,0.0001))
        self.cf.AddCifItem((self.names,self.values))
	self.cf['_non_loop_item'] = 'Non loop string item'
	self.cf['_number_item'] = 15.65
       
   def tearDown(self):
       del self.cf

   def testLoop(self):
        """Check GetLoop returns values and names in right order"""
   	results = self.cf.GetLoop(self.names[2])
	for (key,value) in results:
	    self.failUnless(key in self.names)
	    self.failUnless(tuple(value) == self.values[list(self.names).index(key)])
	
   def testSimpleRemove(self):
       """Check item deletion outside loop"""
       self.cf.RemoveCifItem('_non_loop_item')
       try:
           a = self.cf['_non_loop_item']
       except KeyError: pass
       else: self.Fail()

   def testLoopRemove(self):
       """Check item deletion inside loop"""
       self.cf.RemoveCifItem(self.names[1])
       try:
           a = self.cf[self.names[1]]
       except KeyError: pass
       else: self.Fail()

   def testFullLoopRemove(self):
       """Check removal of all loop items"""
       for name in self.names: self.cf.RemoveCifItem(name)
       self.failUnless(len(self.cf.block["loops"])==0, `self.cf.block["loops"]`)

#
#  Test setting of block names
#

class BlockNameTestCase(unittest.TestCase):
   def testBlockName(self):
       """Make sure long block names cause errors"""
       df = CifFile.CifBlock()
       cf = CifFile.CifFile()
       try:
           cf['a_very_long_block_name_which_should_be_rejected_out_of_hand123456789012345']=df
       except CifFile.CifError: pass
       else: self.Fail()

class FileWriteTestCase(unittest.TestCase):
   def setUp(self):
       """Write out a file, then read it in again"""
       # fill up the block with stuff
       items = (('_item_1','Some data'),
             ('_item_2','Some_underline_data'),
             ('_item_3','34.2332'),
             ('_item_4','Some very long data which we hope will overflow the single line and force printing of another line aaaaa bbbbbb cccccc dddddddd eeeeeeeee fffffffff hhhhhhhhh iiiiiiii jjjjjj'),
             (('_item_5','_item_6','_item_7'),
             ([1,2,3,4],
              [5,6,7,8],
              ['a','b','c','d'])),
             (('_string_1','_string_2'),
              ([';this string begins with a semicolon',
               'this string is way way too long and should overflow onto the next line eventually if I keep typing for long enough'],
               [';just_any_old_semicolon-starting-string',
               'a ball of string'])))
       self.cf = CifFile.CifBlock(items)
       cif = CifFile.CifFile()
       cif['testblock'] = self.cf
       outfile = open('test.cif','w')
       outfile.write(str(cif))
       outfile.close()
       self.df = CifFile.CifFile('test.cif')['testblock']

   def tearDown(self):
       import os
       # os.remove('test.cif')
       del self.df
       del self.cf

   def testStringInOut(self):
       """Test writing short strings in and out"""
       self.failUnless(self.cf['_item_1']==self.df['_item_1'])
       self.failUnless(self.cf['_item_2']==self.df['_item_2'])

   def testNumberInOut(self):
       """Test writing number in and out"""
       self.failUnless(self.cf['_item_3']==(self.df['_item_3']))

   def testLongStringInOut(self):
       """Test writing long string in and out
          Note that whitespace may vary due to carriage returns,
	  so we remove all returns before comparing"""
       import re
       compstring = re.sub('\n','',self.df['_item_4'])
       self.failUnless(compstring == self.cf['_item_4'])

   def testLoopDataInOut(self):
       """Test writing in and out loop data"""
       olditems = self.cf.GetLoop('_item_5')
       newitems = self.df.GetLoop('_item_5')
       for key,value in olditems:
           self.failUnless(tuple(map(str,value))==tuple(self.df[key]))

   def testLoopStringInOut(self):
       """Test writing in and out string loop data"""
       olditems = self.cf.GetLoop('_string_1')
       newitems = self.df.GetLoop('_string_1')
       for key,value in olditems:
           compstringa = map(lambda a:re.sub('\n','',a),value)
           compstringb = map(lambda a:re.sub('\n','',a),self.df[key])
           print str(compstringa) +' : ' + str(compstringb)
           self.failUnless(compstringa==compstringb)

if __name__=='__main__':
    unittest.main()

