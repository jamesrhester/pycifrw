"""
1. This software copyright  Australian Synchrotron Research Program Inc.

2. Permission is hereby granted to use, copy and modify this software for
non-commercial purposes only.  Permission is also granted to use
reasonable portions of it in other software for non-commercial
purposes, provided that suitable acknowledgement is made.  Australian
Synchrotron Research Program Inc., as the owner of the copyright in
the software, does not grant any right to publish, sell or otherwise
redistribute the software, or modified versions of the software, to
third parties.  You are encouraged to communicate useful modifications
to Australian Synchrotron Research Program Inc. for inclusion in
future versions.
"""

class CifFile:
    def __init__(self,datasource=None):
        from types import *
        self.dictionary = {}
        if isinstance(datasource,DictType):
            for (key,value) in datasource.items():
                self.__setitem__(key,value)
        elif type(datasource) is StringType:
            self.ReadCif(datasource)
        elif isinstance(datasource,CifFile):
            self.dictionary = datasource.dictionary.copy()
        self.checklengths()

    def checklengths(self):
        blocks = self.dictionary.items()
        for name,block in blocks:
            toolong = len(filter(lambda a:len(a)>78, block.keys()))
            if toolong:
                print 'Warning: block ' + name + ' has ' + `toolong` + ' overlength data names'

    def __str__(self):
        return self.WriteOut()

    def __setitem__(self,key,value):
        if isinstance(value,CifBlock):
            self.NewBlock(key,value)
        else: raise TypeError

    def __getitem__(self,key):
        return self.dictionary[key]

    def __delitem__(self,key):
        del self.dictionary[key]

    def __len__(self):
        return len(self.dictionary)

    def keys(self):
        return self.dictionary.keys()

    def has_key(self,key):
        return self.dictionary.has_key(key)

    def clear(self):
        self.dictionary.clear()

    def copy(self):   
        newcopy = self.dictionary.copy()
        return CifFile('',newcopy)
     
    def update(self,adict):
        for key in adict.keys():
            self.dictionary[key] = adict[key]

    def ReadCif(self,filename):
        import kwCifParse
        stream = open(filename,'r')
        text = stream.read()
        stream.close()
        if not text:      # empty file, return empty block
            return
        parser = kwCifParse.CifGramBuild()
        context = {"loops":[]}
        try:
            filecontents = parser.DoParse1(text,context)
        except SyntaxError,LexTokenError:
            raise CifError, 'Cif file badly formatted'
        if not filecontents: # comments only, return empty
            return
        for block in filecontents.keys():
            self.dictionary.update({block:CifBlock(filecontents[block])})

    def NewBlock(self,blockname,blockcontents=()):
        import re
        if not blockcontents:
            blockcontents = CifBlock()
        elif not isinstance(blockcontents,CifBlock):
            raise TypeError, 'Cif files can only contain CifBlocks'
        newblockname = re.sub('\W','_',blockname)
        blocknames = self.dictionary.keys()
        i = 0
        while blocknames.count(newblockname):
            i = i + 1
            newblockname = newblockname+`i`
        if len(newblockname) > 73:
            raise CifError, 'Cif block name too long:' + newblockname
        self.dictionary.update({newblockname:blockcontents})
        return newblockname

    def WriteOut(self,comment=''):
        if not comment:
            comment = \
"""
##########################################################################
#               Crystallographic Information Format file 
#               Produced by PyCifRW module
# 
#  This is a CIF file.  CIF has been adopted by the International
#  Union of Crystallography as the standard for data archiving and 
#  transmission.
#
#  For information on this file format, follow the CIF links at
#  http://www.iucr.org
##########################################################################
"""
        outstring = comment
        for datablock in self.dictionary.keys():
            outstring = outstring + '\ndata_'+datablock+'\n'
            outstring = outstring + str(self.dictionary[datablock])
        return outstring


class CifBlock:
    def __init__(self,data = ()):
        from types import *
        self.block = {"loops":[]}
        if type(data) is DictType:     #direct placement
            self.block = data
            if not self.block.has_key("loops"):
                self.block.update({"loops":[]})
        elif type(data) is TupleType:
            for item in data:
                self.AddCifItem(item)
        else: raise TypeError

    def __str__(self):
        return self.printsection()

    def __setitem__(self,key,value):
        self.AddCifItem((key,value))

    def __getitem__(self,key):
        return self.GetCifItem(key)

    def __delitem__(self,key):
        self.RemoveCifItem(key)

    def __len__(self):
        blen = len(self.block) - 1   #non-looped items
        for aloop in self.block["loops"]:
            blen = blen + len(aloop.keys())
        return blen    

    def __nonzero__(self):
        if len(self.block) == 1 and len(self.block["loops"]) == 0:
            return 0
        return 1

    def keys(self):
        thesekeys = self.block.keys()
        for aloop in self.block["loops"]:
            thesekeys.extend(aloop.keys())
        return thesekeys

    def has_key(self,key):
        if self.block.has_key(key):
            return 1
        for aloop in self.block["loops"]:
            if aloop.has_key(key):
                return 1
        return 0

    def clear(self):
        self.block = self.NewBlock()

    def copy(self):
        newcopy = self.block.copy()
        newcopy["loops"] = []
        for aloop in self.block["loops"]:  # do a deeper copy
            newcopy["loops"].append(aloop.copy())
        return CifBlock(newcopy)
     
    def update(self,adict):
        loopdone = []
        if not isinstance(adict,CifBlock):
            raise TypeError
        for key in adict.block.keys():
            if key!="loops":
                self.AddCifItem((key,adict[key]))
            else:
                for aloop in adict.block["loops"]:
                    self.AddCifItem((aloop.keys(),aloop.values()))

    def GetCifItem(self,itemname):
        if self.block.has_key(itemname):
            return self.block[itemname]
        else:
            for aloop in self.block["loops"]:
                if aloop.has_key(itemname):
                    return aloop[itemname]
        raise KeyError, 'Item not in Cif block'

    def RemoveCifItem(self,itemname):
        if self.block.has_key(itemname):
            del self.block[itemname]
            return
        for aloop in self.block["loops"]:
            if aloop.has_key(itemname):
                del aloop[itemname]
        self.block["loops"] = filter(None, self.block["loops"])

    def AddCifItem(self,data):
        import types
        # we accept only tuples, strings and lists!!
        if not (isinstance(data[0],types.StringType) or isinstance(data[0],types.TupleType)
              or isinstance(data[0],types.ListType)):
                  raise TypeError, 'Cif datanames are either a string, tuple or list'
        # now put into the dictionary properly...
        if isinstance(data[0],types.StringType):   # a single name        
            if len(data[0])>78:                   # too long
                raise CifError, 'Dataname ' + data[0] + ' too long.'
            self.block.update({data[0]:data[1]})  # trust the data is OK
            for aloop in self.block["loops"]:
                if aloop.has_key(data[0]):
                    del aloop[data[0]]
            self.block["loops"] = filter(len,self.block["loops"])
        else:                                # we loop
           if(len(data[0])!=len(data[1])):
               raise TypeError, 'Length mismatch between itemnames and values'
           dellist = []
           for itemname in data[0]:
               if len(itemname)>78 or not isinstance(itemname,types.StringType): # no good
                   raise CifError, 'Bad item name ' + `itemname`
               self.block["loops"] = filter(lambda a,b=itemname:b not in a.keys(),self.block["loops"])
           newdict = {}
           map(lambda a,b,c=newdict:c.update({a:b}),data[0],data[1])
           self.block["loops"].append(newdict)
        return

    def GetLoop(self,itemname):
        for aloop in self.block["loops"]:
            if aloop.has_key(itemname):
                return aloop.items()
        # not a looped item
        if self.block.has_key(itemname):
            raise TypeError, 'Non-looped item'
        raise KeyError, 'Item not in loop'

    def printsection(self,order=[]):
        import types
        # first make an ordering
        if not order:
            order = self.block.keys()
            order.sort()
        # now prune that ordering...
        order = filter(lambda a,b=self.block:b.has_key(a),order)
        order.remove('loops')
        # now do it...
        outstring = ''       # the returned string
        for itemname in order:
            itemvalue = self.block[itemname]
            if isinstance(itemvalue,types.StringType):
                  thisstring = self._formatstring(itemvalue)
                  if len(thisstring) + len(itemname) < 78:
                          outstring = outstring + '%s %s\n' % (itemname,thisstring)
                  else:
                          outstring = outstring + '%s\n %s\n' % (itemname, thisstring)
            else: 
                      if len(str(itemvalue)) + len(itemname) < 78:
                          outstring = outstring + '%s %s\n' % (itemname, itemvalue)
                      else:
                          outstring = outstring + '%s\n %s\n' % (itemname, itemvalue)
            continue
        #do the loops
        for aloop in self.block["loops"]:
               outstring = outstring + '\n loop_\n'
               loopnames = aloop.keys()
               loopnames.sort()
               numdata = len(aloop[loopnames[0]])
               for name in loopnames: 
                   outstring = outstring + '   %-75s\n' % name
                   if len(aloop[name]) != numdata:
                       raise CifError,'Loop data mismatch for ' + name + ':output aborted'
               curstring = ''      
               for position in range(numdata):
                   for name in loopnames:
                       # at each point, get the next data value
                       datapoint = aloop[name][position]
                       if isinstance(datapoint,types.StringType):
                           thisstring = ' %s ' % (self._formatstring(datapoint))
                           if '\n' in thisstring:
                               outstring = outstring + curstring + thisstring
                               curstring = ''
                               continue
                       else: 
                           thisstring = ' %s ' % datapoint
                       if len(curstring) + len(thisstring)> 80: #past end of line
                           outstring = outstring + curstring+'\n'
                           curstring = ''
                       curstring = curstring + thisstring
                   outstring = outstring + curstring+'\n'
                   curstring = ''
        return outstring

    def _formatstring(self,instring):
        import re, string
        if len(instring)< 75 and '\n' not in instring:   #single line?
            if not ' ' in instring and not '\t' in instring and not '\v' \
              in instring:                  # no blanks
                return instring
            if not "'" in instring:                                       #use apostrophes
                return "'%s'" % (instring)
            elif not "\"" in instring:
                return '"%s"' % (instring)
        # is a long one
        outstring = "\n;\n"
        # if there are returns in the string, try to work with them
        while 1:
            retin = string.find(instring,'\n')+1
            if retin < 80 and retin > 0:      # honour this break
                outstring = outstring + instring[:retin]
                instring = instring[retin:]
            elif len(instring)<80:            # finished
                outstring = outstring + instring + '\n;\n'
                break
            else:                             # find a space
                for letter in range(79,40,-1): 
                    if instring[letter] in ' \t\f': break
                outstring = outstring + instring[:letter+1]
                outstring = outstring + '\n'
                instring = instring[letter+1:]            
        return outstring


class CifError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        print `value`

