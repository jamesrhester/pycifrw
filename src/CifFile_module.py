# \section{Introduction}                                                  
#                                                                         
# This file implements a general CIF reading/writing utility.  The basic  
# objects ([[CifFile/CifBlock]]) read and write syntactically correct     
# CIF 1.1 files including save frames.  Objects for validating CIFs are   
# built on these basic objects: A [[CifDic]] object is derived from a     
# [[CifFile]] created from a DDL1/2 dictionary; and the                   
# [[ValidCifFile/ValidCifBlock]] objects allow creation/checking of CIF   
# files against a list of CIF dictionaries.                               
#                                                                         
# The [[CifFile]] class is initialised with either no arguments (a new CIF file)
# or with the name of an already existing CIF file.  Data items are       
# accessed/changed/added using the python mapping type ie to get          
# [[dataitem]] you would type [[value = cf[blockname][dataitem]]].        
#                                                                         
# Note also that a CifFile object can be accessed as a mapping type, ie using
# square brackets.  Most mapping operations have been implemented (see below).
#                                                                         
# We build upon the objects defined in the StarFile class, by imposing a few
# extra restrictions where necessary.                                     
#                                                                         
#                                                                         
# <*>=                                                                    
# To maximize python3/python2 compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

import collections
import ast   #for parsing dimension literals

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

# Python 2,3 compatibility
try:
    from urllib import urlopen         # for arbitrary opening
    from urlparse import urlparse, urljoin
except:
    from urllib.request import urlopen
    from urllib.parse import urlparse, urljoin

from prettytable import PrettyTable

# The unicode type does not exist in Python3 as the str type
# encompasses unicode.  PyCIFRW tests for 'unicode' would fail
# Suggestions for a better approach welcome.
#
# long type no longer exists in Python3, so we alias to int
#
if isinstance(u"abc",str):   #Python3
    unicode = str
    long = int

# <Copyright statement>=                                                  
__copyright = """
PYCIFRW License Agreement (Python License, Version 2)
-----------------------------------------------------

1. This LICENSE AGREEMENT is between the Australian Nuclear Science
and Technology Organisation ("ANSTO"), and the Individual or
Organization ("Licensee") accessing and otherwise using this software
("PyCIFRW") in source or binary form and its associated documentation.

2. Subject to the terms and conditions of this License Agreement,
ANSTO hereby grants Licensee a nonexclusive, royalty-free, world-wide
license to reproduce, analyze, test, perform and/or display publicly,
prepare derivative works, distribute, and otherwise use PyCIFRW alone
or in any derivative version, provided, however, that this License
Agreement and ANSTO's notice of copyright, i.e., "Copyright (c)
2001-2014 ANSTO; All Rights Reserved" are retained in PyCIFRW alone or
in any derivative version prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on
or incorporates PyCIFRW or any part thereof, and wants to make the
derivative work available to others as provided herein, then Licensee
hereby agrees to include in any such work a brief summary of the
changes made to PyCIFRW.

4. ANSTO is making PyCIFRW available to Licensee on an "AS IS"
basis. ANSTO MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED. BY WAY OF EXAMPLE, BUT NOT LIMITATION, ANSTO MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYCIFRW WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

5. ANSTO SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYCIFRW
FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A
RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYCIFRW, OR ANY
DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any
relationship of agency, partnership, or joint venture between ANSTO
and Licensee. This License Agreement does not grant permission to use
ANSTO trademarks or trade name in a trademark sense to endorse or
promote products or services of Licensee, or any third party.

8. By copying, installing or otherwise using PyCIFRW, Licensee agrees
to be bound by the terms and conditions of this License Agreement.

"""


import re,sys
from . import StarFile
from .StarFile import StarList  #put in global scope for exec statement
from . import CifSyntaxError
try:
    import numpy                   #put in global scope for exec statement
    from .drel import drel_runtime  #put in global scope for exec statement
except ImportError:
    pass                       #will fail when using dictionaries for calcs
from copy import copy          #must be in global scope for exec statement
import json

# Decorators. The following decorator keeps track of calls in order to    
# detect recursion.  We raise a special recursion error to allow the      
# [[derive_item]] method to act accordingly.  We also propagate the       
# first-seen value of 'allow_defaults' recursively, so that the original call can
# control whether or not to use default values. Typically methods can     
# be tried without, and then with, default values, to ensure that all     
# possibilities for deriving the function are attempted first.            
#                                                                         
#                                                                         
# <Decorators>=                                                           
def track_recursion(in_this_func):
    """Keep an eye on a function call to make sure that the key argument hasn't been
    seen before"""
    def wrapper(*args,**kwargs):
        key_arg = args[1]
        if key_arg in wrapper.called_list:
            print('Recursion watch: {} already called {} times'.format(key_arg,wrapper.called_list.count(key_arg)))
            raise CifRecursionError( key_arg,wrapper.called_list[:])    #failure
        if len(wrapper.called_list) == 0:   #first time
            wrapper.stored_use_defaults = kwargs.get("allow_defaults",False)
            print('All recursive calls will set allow_defaults to ' + repr(wrapper.stored_use_defaults))
        else:
            kwargs["allow_defaults"] = wrapper.stored_use_defaults
        wrapper.called_list.append(key_arg)
        print('Recursion watch: call stack: ' + repr(wrapper.called_list))
        try:
            result = in_this_func(*args,**kwargs)
        except StarFile.StarDerivationError as s:
            if len(wrapper.called_list) == 1: #no more
                raise StarFile.StarDerivationFailure(wrapper.called_list[0])
            else:
                raise
        finally:
            wrapper.called_list.pop()
            if len(wrapper.called_list) == 0:
                wrapper.stored_used_defaults = 'error'
        return result
    wrapper.called_list = []
    return wrapper

# \section{Cif Block class}                                               
#                                                                         
# CifBlocks exist(ed) as a separate class in order to enforce non-nested  
# loops and maximum dataname lengths. As nested loops have been removed   
# completely from PyCIFRW, they are no longer necessary but kept here for 
# backwards compatibility.                                                
#                                                                         
#                                                                         
# <CifBlock class>=                                                       
class CifBlock(StarFile.StarBlock):
    """
    A class to hold a single block of a CIF file.  A `CifBlock` object can be treated as
    a Python dictionary, in particular, individual items can be accessed using square
    brackets e.g. `b['_a_dataname']`.  All other Python dictionary methods are also
    available (e.g. `keys()`, `values()`).  Looped datanames will return a list of values.

    ## Initialisation

    When provided, `data` should be another `CifBlock` whose contents will be copied to
    this block.

    * if `strict` is set, maximum name lengths will be enforced

    * `maxoutlength` is the maximum length for output lines

    * `wraplength` is the ideal length to make output lines

    * When set, `overwrite` allows the values of datanames to be changed (otherwise an error
    is raised).

    * `compat_mode` will allow deprecated behaviour of creating single-dataname loops using
    the syntax `a[_dataname] = [1,2,3,4]`.  This should now be done by calling `CreateLoop`
    after setting the dataitem value.
    """
    # A CifBlock is a StarBlock with a very few restrictions.                 
    #                                                                         
    #                                                                         
    # <Initialise Cif Block>=                                                 
    def __init__(self,data = (), strict = 1, compat_mode=False, **kwargs):
        """When provided, `data` should be another CifBlock whose contents will be copied to
        this block.

        * if `strict` is set, maximum name lengths will be enforced

        * `maxoutlength` is the maximum length for output lines

        * `wraplength` is the ideal length to make output lines

        * When set, `overwrite` allows the values of datanames to be changed (otherwise an error
        is raised).

        * `compat_mode` will allow deprecated behaviour of creating single-dataname loops using
        the syntax `a[_dataname] = [1,2,3,4]`.  This should now be done by calling `CreateLoop`
        after setting the dataitem value.
        """
        if strict: maxnamelength=75
        else:
           maxnamelength=-1
        super(CifBlock,self).__init__(data=data,maxnamelength=maxnamelength,**kwargs)
        self.dictionary = None   #DDL dictionary referring to this block
        self.compat_mode = compat_mode   #old-style behaviour of setitem

    def RemoveCifItem(self,itemname):
        """Remove `itemname` from the CifBlock"""
        self.RemoveItem(itemname)

    # The second line in the copy method switches the class of the            
    # returned object to be a CifBlock. It may not be necessary.              
    #                                                                         
    #                                                                         
    # <Adjust emulation of a mapping type>=                                   
    def __setitem__(self,key,value):
        self.AddItem(key,value)
        # for backwards compatibility make a single-element loop
        if self.compat_mode:
            if isinstance(value,(tuple,list)) and not isinstance(value,StarFile.StarList):
                 # single element loop
                 self.CreateLoop([key])

    def copy(self):
        newblock = super(CifBlock,self).copy()
        return self.copy.im_class(newblock)   #catch inheritance

    # This function was added for the dictionary validation routines.  It     
    # will return a list where each member is itself a list of item names,    
    # corresponding to the names in each loop of the file.                    
    #                                                                         
    #                                                                         
    # <Return all looped names>=                                              
    def loopnames(self):
        return [self.loops[a] for a in self.loops]


# \section{CifFile}                                                       
#                                                                         
# A CifFile is subclassed from a StarFile.  Our StarFile class has an     
# optional check of line length, which we use.                            
#                                                                         
# A CifFile object is a dictionary of                                     
# CifBlock objects, accessed by block name.  As the maximum line length   
# is subject to change, we allow the length to be specified, with the     
# current default set at 2048 characters (Cif 1.1).  For reading in files,
# we only                                                                 
# flag a length error if the parameter [[strict]] is true, in which case  
# we use parameter [[maxinlength]] as our maximum line length on input.   
# Parameter [[maxoutlength]] sets the maximum line size for output.  If   
# [[maxoutlength]] is not specified, it defaults to the maximum input     
# length.                                                                 
#                                                                         
# Note that this applies to the input only.  For changing output length,  
# you can provide an optional parameter in the [[WriteOut]] method.       
#
# allow_partial reads permissively, so that a parsing error will simply
# return the CIF file so far, together with the error information. It
# is False by default for backwards compatibility.
#                                                                         
# <CifFile class>=                                                        
class CifFile(StarFile.StarFile):
# When initialising, we add those parts that are unique to the CifFile as 
# opposed to a simple collection of blocks - i.e. reading in from a file, 
# and some line length restrictions.  We do not indent this section in this
# noweb file, so that our comment characters output at the beginning of the
# line.                                                                   
#                                                                         
#                                                                         
# <Initialise data structures>=                                           
    def __init__(self,datasource=None,strict=1,standard='CIF',from_str=False,
                 allow_partial = False, **kwargs):
        super(CifFile,self).__init__(datasource=datasource,standard=standard, from_str=from_str, **kwargs)
        self.strict = strict
        self.header_comment = \
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
        pr = self.get_parsing_result()
        if not allow_partial and len(pr) > 0 and pr[0] < 0: #Fail aggressively
            print_cif_syntax_error(pr, self.my_uri)
            raise pr[1]

    def get_parsing_result(self):
        return self.parsing_result

    # DDLm tags have a '.' in their name, whereas the original DDL1
    # tags do not.
    #
    def convert_to_canonical(self, dictionary):
        """DDLm tags have a '.' in their name, whereas DDL1 tags do
        not. This routine consults the provided dictionary to find
        the canonical names for all data names in the data file,
        and changes them, returning a list of data names that were
        not found in the dictionary.
        """

        tags_without_alias = []
        for block_name, block_contents in self.items():

            for tag, value in block_contents.items():
                # The tag does not have any point
                # The tag is DDL1
                tag_definition = dictionary.get(tag, None)

                if tag_definition is None:
                    tags_without_alias.append(tag)
                    continue

                tag_name_ddlm = tag_definition.get("_definition.id").lower()

                # The tag of the definition and the one that appears in the cif
                # file are different. Therefore the tag in the cif is an alias.
                if tag_name_ddlm != tag:
                    # Add a new block with the proper tag
                    self[block_name].ChangeTagName(tag, tag_name_ddlm)

        return tags_without_alias

    def to_json(self):
        cif_dict = {}

        # Add meta data
        cif_dict['filename'] = self.my_uri
        cif_dict['version'] = self.grammar

        tags_dict = {}
        for key in self.keys():
            datablock_dict = {}
            datablock = self[key]

            for tag in datablock.keys():
                value = self[key][tag]
                datablock_dict[tag] = value

            tags_dict[key] = datablock_dict

        cif_dict['tags'] = tags_dict
        cif_json = json.dumps(cif_dict, indent=2)

        return cif_json

# Defining an error class: we simply derive a 'nothing' class from the root
# Python class                                                            
#                                                                         
#                                                                         
# <Define an error class>=                                                

class CifError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return '\nCif Format error: '+ self.value

class ValidCifError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return '\nCif Validity error: ' + self.value

class CifRecursionError(Exception):
    def __init__(self,key_value,call_stack):
        self.key_value = key_value
        self.call_stack = call_stack
    def __str__(self):
        return "Derivation has recursed, {} seen twice (call stack {})".format(self.key_value,repr(self.call_stack))


# \section {Dictionaries}                                                 
#                                                                         
# To avoid ambiguity with the Python dictionary type, we use capital      
# D to denote CIF Dictionaries where misinterpretation is possible.       
#                                                                         
# We build our Dictionary behaviour on top of the StarFile object, which  
# is notionally a collection of StarBlocks. A Dictionary is simply a      
# collection of datablocks, where each datablock corresponds to a single  
# definition.  DDL1 had no category definitions.                          
#                                                                         
# We adopt a data model whereby the excess information in a DDL2          
# dictionary is absorbed into special methods (and I am thinking here     
# of the [[_item_type_list.construct]] stuff which appears at the         
# global level), which we initialise ourselves for a DDL1 dictionary.     
#                                                                         
# The square bracket notation is repurposed to mean access to the         
# appropriate definition, as the save frame name and the definition       
# may be slightly (or completely) different.                              
#                                                                         
#                                                                         
# <CIF Dictionary type>=                                                  
# \subsection {Dictionary blocks}                                         
#                                                                         
# A dictionary block is essentially identical to a StarBlock, with        
# the extra semantics of chasing through `_import.get` calls in           
# order to transparently return attributes defined in separate            
# dictionaries.  If the `_import_cache` is empty, this is skipped.        
#                                                                         
#                                                                         
# <Dictionary block type>=                                                
class DicBlock(StarFile.StarBlock):
    """A definition block within a dictionary, which allows imports
    to be transparently followed"""

    def __init__(self,*args,**kwargs):
        super(DicBlock,self).__init__(*args,**kwargs)
        self._import_cache = {}

    def __getitem__(self,dataname):
        value = None
        if super(DicBlock,self).has_key("_import.get") and self._import_cache:
            value = self.follow_import(super(DicBlock,self).__getitem__("_import.get"),dataname)
        try:
            final_value = super(DicBlock,self).__getitem__(dataname)
        except KeyError:    #not there
            final_value = value
        if final_value is None:
            raise KeyError("{} not found".format(dataname))
        return final_value

    #
    # We cannot just do `key in self` as we need to mirror
    # the logic in __getitem__
    #
    def has_key(self,key):
        try:
            self[key]
        except KeyError:
            return False
        return True     

    def add_dict_cache(self,name,cached):
        """Add a loaded dictionary to this block's cache"""
        self._import_cache[name]=cached

    def follow_import(self,import_info,dataname):
        """Find the dataname values from the imported dictionary. `import_info`
        is a list of import locations"""
        latest_value = None
        for import_ref in import_info:
            file_loc = import_ref["file"]
            if file_loc not in self._import_cache:
                raise ValueError("Dictionary for import {} not found".format(file_loc))
            import_from = self._import_cache[file_loc]
            miss = import_ref.get('miss','Exit')
            target_key = import_ref["save"]
            try:
                import_target = import_from[target_key]
            except KeyError:
                if miss == 'Exit':
                    raise CifError('Import frame {} not found in {}'.format(target_key,file_loc))
                else: continue
            # now import appropriately
            mode = import_ref.get("mode",'Contents').lower()
            if mode == "contents":   #only this is used at this level
                latest_value = import_target.get(dataname,latest_value)
        return latest_value

class CifDic(StarFile.StarFile):
    """Create a Cif Dictionary object from the provided source, which can
    be a filename/URL or a CifFile.  Optional arguments (relevant to DDLm
    only):

    * do_minimum (Boolean):
         Do not set up the dREL system for auto-calculation or perform
         imports.  This implies do_imports=False and do_dREL=False

    * do_imports = No/Full/Contents/All:
         If not 'No', intepret _import.get statements for
         Full mode/Contents mode/Both respectively. See also option 'heavy'

    * do_dREL = True/False:
         Parse and convert all dREL methods to Python. Implies do_imports=All

    * heavy = True/False:
         (Experimental). If True, importation overwrites definitions. If False,
         attributes are resolved dynamically.
    """
    # \subsection {Initialisation}                                            
    #                                                                         
    # We want to be able to accept strings, giving the file name              
    # of the CIF dictionary, and pre-initialised [[CifFile]] objects.  We do  
    # not accept [[CifDic]] objects.  Our initialisation procedure            
    # first unifies the interface to the Dictionary, and then runs through the
    # Dictionary producing a normalised form.  Following this, type           
    # and category information can be collected for later reference.          
    #                                                                         
    # Validation functions are listed so that it would be possible to         
    # add and remove them from the "valid set".  This behaviour has           
    # not yet been implemented.                                               
    #                                                                         
    # When loading DDLm dictionaries we may recursively call this             
    # initialisation function with a dictionary to be imported as the         
    # argument.  In this case we do not want to do all the method derivation, 
    # as the necessary categories will be loaded into the calling dictionary  
    # rather than the currently initialising dictionary.  So there is a       
    # keyword argument to stop the operations that should operate on the      
    # dictionary as a whole taking place.                                     
    #                                                                         
    # The dREL methods require Numpy support, but we do not wish to introduce 
    # a global dependence on Numpy.  Therefore, we introduce a 'switch' which 
    # will return Numpy arrays from the __getitem__ method instead of StarLists.
    # It is intended that the dREL methods will turn this on only during      
    # execution, then turn it off afterwards.                                 
    #                                                                         
    # Note that DDLm importation logic provides many choices. We have a choice
    # of 'No', 'Contents', 'Full' and 'All' for the amount that is imported. If
    # `heavy` is False, no definition material will be replaced, rather the   
    # import will be resolved dynamically.                                    
    #                                                                         
    #                                                                         
    # <Initialise Cif dictionary>=                                            
    def __init__(self,dic,do_minimum=False,do_imports='All', do_dREL=True,
                 grammar='auto',heavy=True,verbose_import=True,verbose_validation=True,**kwargs):
        self.do_minimum = do_minimum
        if do_minimum:
            do_imports = 'No'
            do_dREL = False
        if do_dREL: do_imports = 'All'
        if heavy == 'Light' and do_imports not in ('contents','No'):
            raise(ValueError,"Light imports only available for mode 'contents'")
        self.template_cache = {}    #for DDLm imports
        self.ddlm_functions = {}    #for DDLm functions
        self.switch_numpy(False)    #no Numpy arrays returned
        super(CifDic,self).__init__(datasource=dic,grammar=grammar,blocktype=DicBlock,**kwargs)
        self.verbose_import=verbose_import
        self.verbose_validation=verbose_validation
        self.standard = 'Dic'    #for correct output order
        self.scoping = 'dictionary'
        (self.dicname,self.dicversion,self.diclang) = self.dic_determine()
        if self.verbose_import:
            print('{} is a {} dictionary'.format(self.dicname,self.diclang))
        self.scopes_mandatory = {}
        self.scopes_naughty = {}
        self._import_dics = []   #Non-empty for DDLm only
        # rename and expand out definitions using "_name" in DDL dictionaries
        if self.diclang == "DDL1":
            self.DDL1_normalise()   #this removes any non-definition entries
        self.create_def_block_table() #From now on, [] uses definition_id
        if self.diclang == "DDL1":
            self.ddl1_cat_load()
        elif self.diclang == "DDL2":
            self.DDL2_normalise()   #iron out some DDL2 tricky bits
        elif self.diclang == "DDLm":
            self.scoping = 'dictionary'   #expose all save frames
            self._import_dics = self.get_dictionaries_to_import()
            if do_imports != 'No':
                self.obtain_imports(import_mode=do_imports,heavy=heavy)#recursively calls this routine
            self.create_alias_table()
            self.create_cat_obj_table()
            self.create_cat_key_table()
            if do_dREL:
                print('Doing full dictionary initialisation')
                self.initialise_drel()
        self.add_category_info(full=do_dREL)
        # initialise type information
        self.typedic={}
        self.primdic = {}   #typecode<->primitive type translation
        self.add_type_info()
        self.install_validation_functions()

    def add_alias_blocks(self):
        '''
        Function to add alias tags to the dictionary. If a datablock has the "_alias.definition_id" tag,
        a new datablock is created with the same information of the original datablock.

        It requires the dictionary to be fully formed.
        '''
        # Retrieve all the alias blocks
        data_blocks_to_edit = []
        for block_name in self.keys():
            block = self[block_name]

            if "_alias.definition_id" in block.keys():
                data_blocks_to_edit.append(block_name)

        # Add the alias blocks to the dictionary
        for data_block in data_blocks_to_edit:
            alias_temp = self[data_block]["_alias.definition_id"]
            contents = self[data_block]

            # Remove alias tag from original datablock ?
            #del self[data_block]["_alias.definition_id"]

            if isinstance(alias_temp, list):
                for alias in alias_temp:
                    #contents["_definition.id"] = alias.lower()
                    #self[alias.lower()] = contents
                    self.NewBlock(alias.lower(), contents)
                    self.block_id_table[alias.lower()] = alias.lower()

            else:
                # Keep the DDLm version of the tag
                #contents["_definition.id"] = alias_temp.lower()
                #self[alias_temp.lower()] = contents
                self.NewBlock(alias_temp.lower(), contents)
                self.block_id_table[alias_temp.lower()] = alias_temp.lower()

        return self

    # These routines seek to impose a uniform structure on dictionaries       
    # written in DDL1, DDL2 and DDLm. Historically, the richer and more       
    # systematic DDL2 approach was used to describe DDL1 definitions. With    
    # the advent of DDLm, the DDLm paradigm is likely to overtake DDL2. When  
    # interpreting the following routines, therefore, bear in mind that they  
    # were originally written with DDL2 in mind, and are gradually shifting   
    # to DDLm.                                                                
    #                                                                         
    #                                                                         
    # <DDL-specific initialisation routines>=                                 
    # This function determines whether we have a DDLm, DDL2 or DDL1 dictionary.  We are
    # built from a [[CifFile]] object.   The current method looks for an      
    # [[on_this_dictionary]] block, which implies DDL1, or a single block,    
    # which implies DDL2/DDLM.  This is also where we define some universal   
    # keys for uniform access to DDL attributes.                              
    #                                                                         
    #                                                                         
    # <Dictionary determination function>=                                    

    def dic_determine(self):
        if "on_this_dictionary" in self:
            self.master_block = super(CifDic,self).__getitem__("on_this_dictionary")
            self.def_id_spec = "_name"
            self.cat_id_spec = "_category.id"   #we add this ourselves
            self.type_spec = "_type"
            self.enum_spec = "_enumeration"
            self.cat_spec = "_category"
            self.esd_spec = "_type_conditions"
            self.must_loop_spec = "_list"
            self.must_exist_spec = "_list_mandatory"
            self.list_ref_spec = "_list_reference"
            self.key_spec = "_list_mandatory"
            self.unique_spec = "_list_uniqueness"
            self.child_spec = "_list_link_child"
            self.parent_spec = "_list_link_parent"
            self.related_func = "_related_function"
            self.related_item = "_related_item"
            self.primitive_type = "_type"
            self.dep_spec = "xxx"
            self.cat_list = []   #to save searching all the time

            # Categories to which their loop id uniqueness validation
            # needs to be avoided due to dictionary ambiguities
            self.black_list_categories = {
                'refln',
                'diffrn_refln',
                'diffrn_standard_refln',
                'exptl_crystal_face',
                'geom_bond',
                'geom_angle',
                'geom_contact',
                'geom_hbond',
                'geom_torsion'
            }
            name = super(CifDic,self).__getitem__("on_this_dictionary")["_dictionary_name"]
            version = super(CifDic,self).__getitem__("on_this_dictionary")["_dictionary_version"]
            return (name,version,"DDL1")
        elif len(self.get_roots()) == 1:              # DDL2/DDLm
            self.master_block = super(CifDic,self).__getitem__(self.get_roots()[0][0])
            # now change to dictionary scoping
            self.scoping = 'dictionary'
            name = self.master_block["_dictionary.title"]
            version = self.master_block["_dictionary.version"]
            if self.master_block.has_key("_dictionary.class"):   #DDLm
                self.enum_spec = '_enumeration_set.state'
                self.key_spec = '_category.key_id'
                self.must_exist_spec = None
                self.cat_spec = '_name.category_id'
                self.primitive_type = '_type.contents'
                self.cat_id_spec = "_definition.id"
                self.def_id_spec = "_definition.id"
                self.unique_spec = "_category_key.name"
                self.alias_spec = "_alias.definition_id"
                self.related_func = "_definition_replaced.by"
                # Categories to which their loop id uniqueness validation
                # needs to be avoided due to dictionary ambiguities
                self.black_list_categories = {
                    'publ_author'
                }
                return(name,version,"DDLm")
            else:   #DDL2
                self.cat_id_spec = "_category.id"
                self.def_id_spec = "_item.name"
                self.key_spec = "_category_mandatory.name"
                self.type_spec = "_item_type.code"
                self.enum_spec = "_item_enumeration.value"
                self.esd_spec = "_item_type_conditions.code"
                self.cat_spec = "_item.category_id"
                self.loop_spec = "there_is_no_loop_spec!"
                self.must_loop_spec = "xxx"
                self.must_exist_spec = "_item.mandatory_code"
                self.child_spec = "_item_linked.child_name"
                self.parent_spec = "_item_linked.parent_name"
                self.related_func = "_item_related.function_code"
                self.related_item = "_item_related.related_name"
                self.unique_spec = "_category_key.name"
                self.list_ref_spec = "xxx"
                self.primitive_type = "_type"
                self.alias_spec = "_alias.definition_id"
                self.dep_spec = "_item_dependent.dependent_name"
                return (name,version,"DDL2")
        else:
            raise CifError("Unable to determine dictionary DDL version")

    # DDL1 differences.  Firstly, in DDL1 you can loop a [[_name]] to get     
    # definitions of related names (e.g. x,y,z).  Secondly, the data block    
    # name is missing the initial underscore, so we need to read the [[_name]]
    # value.  There is one block without a [[_name]] attribute, which we      
    # proceed to destroy (exercise for the reader: which one?).               
    #                                                                         
    # A further complex difference is in the way that ranges are specified.   
    # A DDL2 dictionary generally loops the [[_item_range.maximum/minimum]]   
    # items, in order to specify inclusion of the endpoints of the range,     
    # whereas DDL1 dictionaries simply specify ranges as [[n:m]].  We         
    # translate these values into [[item_range]] specifications.              
    #                                                                         
    # If the [[_list]] item is missing for a dictionary definition, it defaults
    # to no, i.e. the item cannot be listed.  We explicitly include this in   
    # our transformations.                                                    
    #                                                                         
    # The dictionaries also contain categories, which are used to impose      
    # constraints on groupings of items in lists.  Category names in DDL2     
    # dictionaries have no leading underscore, and the constraints            
    # are stored directly in the category definition.  So, with a DDL1        
    # dictionary, we rewrite things to match the DDL2 methods.  In            
    # particular, the [[list_uniqueness]] item becomes the [[category_key.name]]
    # attribute of the category.  This may apply to [[_list_mandatory]] and   
    # /or [[_list_reference]] to, but the current specification is vague.     
    #                                                                         
    # Also, it is possible for cross-item references (e.g. in a               
    # [[_list_reference]])                                                    
    # to include a whole range of items by terminating the name with an       
    # underscore.  It is then understood to include anything starting with    
    # those characters.  We explicitly try to expand these references out.    
    #                                                                         
    # Note the way we convert to DDL2-style type definitions; any definition  
    # having a _type_construct regular expression triggers the definition of  
    # a whole new type, which is stored as per DDL2, for the later type       
    # dictionary construction process to find.                                
    #                                                                         
    #                                                                         
    # <Deal with DDL1 differences>=                                           
    def DDL1_normalise(self):
        # switch off block name collision checks
        self.standard = None
        # add default type information in DDL2 style
        # initial types and constructs
        base_types = ["char","numb","null"]
        prim_types = base_types[:]
        base_constructs = [".*",
            '(-?(([0-9]*[.][0-9]+)|([0-9]+)[.]?)([(][0-9]+[)])?([eEdD][+-]?[0-9]+)?([(][0-9]+[)])?)|\\?|\\.',
            "\"\" "]
        for key,value in self.items():
           newnames = [key]  #keep by default
           if "_name" in value:
               real_name = value["_name"]
               if isinstance(real_name,list):        #looped values
                   for looped_name in real_name:
                      new_value = value.copy()
                      new_value["_name"] = looped_name  #only looped name
                      self[looped_name] = new_value
                   newnames = real_name
               else:
                      self[real_name] = value
                      newnames = [real_name]
           # delete the old one
           if key not in newnames:
              del self[key]
        # loop again to normalise the contents of each definition
        for key,value in self.items():
           #unlock the block
           save_overwrite = value.overwrite
           value.overwrite = True
           # deal with a missing _list, _type_conditions
           if "_list" not in value: value["_list"] = 'no'
           if "_type_conditions" not in value: value["_type_conditions"] = 'none'
           # deal with enumeration ranges
           if "_enumeration_range" in value:
               max,min = self.getmaxmin(value["_enumeration_range"])
               if min == ".":
                   self[key].AddLoopItem((("_item_range.maximum","_item_range.minimum"),((max,max),(max,min))))
               elif max == ".":
                   self[key].AddLoopItem((("_item_range.maximum","_item_range.minimum"),((max,min),(min,min))))
               else:
                   self[key].AddLoopItem((("_item_range.maximum","_item_range.minimum"),((max,max,min),(max,min,min))))
           #add any type construct information
           if "_type_construct" in value:
               base_types.append(value["_name"]+"_type")   #ie dataname_type
               base_constructs.append(value["_type_construct"]+"$")
               prim_types.append(value["_type"])     #keep a record
               value["_type"] = base_types[-1]   #the new type name

        #make categories conform with ddl2
        #note that we must remove everything from the last underscore
           if value.get("_category",None) == "category_overview" \
               and value.get("_name",None) is not None:
                last_under = value["_name"].rindex("_")

                # Take into account the bracket
                if "]" in value["_name"]:
                    last_under = len(value["_name"])

                catid = value["_name"][1:last_under]
                value["_category.id"] = catid  #remove square bracks
                if catid not in self.cat_list: self.cat_list.append(catid)
           value.overwrite = save_overwrite
        # we now add any missing categories before filling in the rest of the
        # information
        for key,value in self.items():
            #print('processing ddl1 definition %s' % key)
            if "_category" in self[key]:
                if self[key]["_category"] not in self.cat_list:
                    # rogue category, add it in
                    newcat = self[key]["_category"]
                    fake_name = "_" + newcat + "_[]"
                    newcatdata = CifBlock()
                    newcatdata["_category"] = "category_overview"
                    newcatdata["_category.id"] = newcat
                    newcatdata["_type"] = "null"
                    self[fake_name] = newcatdata
                    self.cat_list.append(newcat)
        # write out the type information in DDL2 style
        self.master_block.AddLoopItem((
            ("_item_type_list.code","_item_type_list.construct",
              "_item_type_list.primitive_code"),
            (base_types,base_constructs,prim_types)
            ))

    # Loading the DDL1 categories with DDL2-type information.  DDL2 people wisely
    # put category-wide information in the category definition rather than    
    # spreading it out between category items.  We collect this information together
    # here.                                                                   
    #                                                                         
    # This routine is the big time-waster in initialising a DDL1 dictionary, so we have
    # attempted to optimize it by locally defining functions, instead of using lambdas,
    # and making one loop through the dictionary instead of hundreds.         
    #                                                                         
    #                                                                         
    # <Load categories with DDL2-type information>=                           
    def ddl1_cat_load(self):
        deflist = self.keys()       #slight optimization
        cat_mand_dic = {}
        cat_unique_dic = {}
        # a function to extract any necessary information from each definition
        def get_cat_info(single_def):
            if self[single_def].get(self.must_exist_spec)=='yes':
                thiscat = self[single_def]["_category"]
                curval = cat_mand_dic.get(thiscat,[])
                curval.append(single_def)
                cat_mand_dic[thiscat] = curval
            # now the unique items...
            # cif_core.dic throws us a curly one: the value of list_uniqueness is
            # not the same as the defined item for publ_body_label, so we have
            # to collect both together.  We assume a non-listed entry, which
            # is true for all current (May 2005) ddl1 dictionaries.
            if self[single_def].get(self.unique_spec,None)!=None:
                thiscat = self[single_def]["_category"]
                new_unique = self[single_def][self.unique_spec]
                uis = cat_unique_dic.get(thiscat,[])
                if single_def not in uis: uis.append(single_def)
                if new_unique not in uis: uis.append(new_unique)
                cat_unique_dic[thiscat] = uis

        [get_cat_info(a) for a in deflist] # apply the above function
        for cat in cat_mand_dic.keys():
            self[cat]["_category_mandatory.name"] = cat_mand_dic[cat]
        for cat in cat_unique_dic.keys():
            self[cat]["_category_key.name"] = cat_unique_dic[cat]

    # DDL2 has a few idiosyncracies of its own.  For some reason, in the      
    # definition of a parent item, all the child items are listed and their   
    # mandatory/not mandatory status specified.  This duplicates information  
    # under the child item itself, although there is something on the web     
    # indicating                                                              
    # that this is purely cosmetic and not strictly necessary.   For our purposes, we want to extract
    # the mandatory/not mandatory nature of the current item, which appears   
    # to be conventionally at the top of the list (we do not assume this below).
    # The only way of determining what the actual item name is is to look at  
    # the save frame name, which is a bit of a fragile tactic - especially    
    # as dictionary merge operations are supposed to look for _item.name.     
    #                                                                         
    # So, in these cases, we have to assume the save frame name is the one we 
    # want, and find this entry in the list.                                  
    #                                                                         
    # Additionally, the child entry doesn't contain the category specification,
    # so we add this into the child entry at the same time, together with a   
    # pointer to the parent item.                                             
    #                                                                         
    # Such entries then have a loop listing parents and children down the whole
    # hierarchy, starting with the current item.  We disentangle this, placing
    # parent item attributes in the child items, moving sub-children down to  
    # their level.  Sub children may not exist at all, so we create them if   
    # necessary.                                                              
    #                                                                         
    # To make life more interesting, the PDBX have an entry_pc placeholder in 
    # which additional (and sometimes repeated) parent-child relationships    
    # can be expressed. We cannot assume that any given parent-child relationship
    # is stated at a single site in the file.  What is more, it appears that  
    # multiple parents for a single child are defined in the _entry.pdbx_pc entry.
    # Our changes to the file pre-checking are therefore restricted to making 
    # sure that the child contains information about the parents; we do not   
    # interfere with the parent's information about the children, even if we  
    # consider that to be superfluous.  Note that we will have to add         
    # parent-child validity checks to check consistency among all these       
    # relationships.                                                          
    #                                                                         
    # Update: in the DDL-2.1.6 file, only the parents/children are looped,    
    # rather than the item names, so we have to check looping separately.     
    #                                                                         
    # Next: DDL2 contains aliases to DDL1 item names, so in theory we should be
    # able to use a DDL2 dictionary to validate a DDL1-style CIF file.  We    
    # create separate definition blocks for each alias to enable this.        
    #                                                                         
    # Also, we flatten out any single-element lists for item_name.  This is   
    # simply to avoid the value of e.g. category_id being a single-element list
    # instead of a string.                                                    
    #                                                                         
    # Note also that _item.category_id in DDL2 is 'implicit', meaning in this case
    # that you can determine it from the item name.  We add in the category for
    # simplicity.                                                             
    #                                                                         
    #                                                                         
    # <Iron out DDL2 strangeness>=                                            
    # In order to handle parent-child relationships in a regular way, we want to assume
    # that all parent-child entries occur in a loop, with both members present.  This
    # routine does that for us.  If the parent is missing, it is assumed to be the
    # currently-defined item.  If the child is missing, likewise.             
    #                                                                         
    #                                                                         
    # <Loopify parent-child relationships>=                                   
    def create_pcloop(self,definition):
        old_children = self[definition].get('_item_linked.child_name',[])
        old_parents = self[definition].get('_item_linked.parent_name',[])
        if isinstance(old_children,unicode):
             old_children = [old_children]
        if isinstance(old_parents,unicode):
             old_parents = [old_parents]
        if (len(old_children)==0 and len(old_parents)==0) or \
           (len(old_children) > 1 and len(old_parents)>1):
             return
        if len(old_children)==0:
             old_children = [definition]*len(old_parents)
        if len(old_parents)==0:
             old_parents = [definition]*len(old_children)
        newloop = CifLoopBlock(dimension=1)
        newloop.AddLoopItem(('_item_linked.parent_name',old_parents))
        newloop.AddLoopItem(('_item_linked.child_name',old_children))
        try:
            del self[definition]['_item_linked.parent_name']
            del self[definition]['_item_linked.child_name']
        except KeyError:
            pass
        self[definition].insert_loop(newloop)



    def DDL2_normalise(self):
       listed_defs = filter(lambda a:isinstance(self[a].get('_item.name'),list),self.keys())
       # now filter out all the single element lists!
       dodgy_defs = filter(lambda a:len(self[a]['_item.name']) > 1, listed_defs)
       for item_def in dodgy_defs:
          # As some DDL2 dictionaries neglect children, we repopulate the skeleton or non-existent definitions that
          # may be provided in the dictionary.                                      
          #                                                                         
          #                                                                         
          # <Repopulate child definitions>=                                         
                # print("DDL2 norm: processing %s" % item_def)
                thisdef = self[item_def]
                packet_no = thisdef['_item.name'].index(item_def)
                realcat = thisdef['_item.category_id'][packet_no]
                realmand = thisdef['_item.mandatory_code'][packet_no]
                # first add in all the missing categories
                # we don't replace the entry in the list corresponding to the
                # current item, as that would wipe out the information we want
                for child_no in range(len(thisdef['_item.name'])):
                    if child_no == packet_no: continue
                    child_name = thisdef['_item.name'][child_no]
                    child_cat = thisdef['_item.category_id'][child_no]
                    child_mand = thisdef['_item.mandatory_code'][child_no]
                    if child_name not in self:
                        self[child_name] = CifBlock()
                        self[child_name]['_item.name'] = child_name
                    self[child_name]['_item.category_id'] = child_cat
                    self[child_name]['_item.mandatory_code'] = child_mand
                self[item_def]['_item.name'] = item_def
                self[item_def]['_item.category_id'] = realcat
                self[item_def]['_item.mandatory_code'] = realmand

       # Populating parent and child links.  The DDL2 model uses parent-child relationships
       # to create relational database behaviour.  This means that the emphasis is on simply
       # linking two ids together directionally.  This link is not necessarily inside a definition that
       # is being linked, but we require that any parents and children are identified within the
       # definition that they relate to.  This means we have to sometimes relocate and expand links.
       # As an item can simultaneously be both a parent and a child, we need to explicitly fill in
       # the links even within a single definition.                              
       #                                                                         
       #                                                                         
       # <Populate parent and child links correctly>=                            
       target_defs = [a for a in self.keys() if '_item_linked.child_name' in self[a] or \
                                     '_item_linked.parent_name' in self[a]]
       # now dodgy_defs contains all definition blocks with more than one child/parent link
       for item_def in dodgy_defs: self.create_pcloop(item_def)           #regularise appearance
       for item_def in dodgy_defs:
             print('Processing {}'.format(item_def))
             thisdef = self[item_def]
             child_list = thisdef['_item_linked.child_name']
             parents = thisdef['_item_linked.parent_name']
             # for each parent, find the list of children.
             family = list(zip(parents,child_list))
             notmychildren = family         #We aim to remove non-children
             # Loop over the parents, relocating as necessary
             while len(notmychildren):
                # get all children of first entry
                mychildren = [a for a in family if a[0]==notmychildren[0][0]]
                print("Parent {}: {} children".format(notmychildren[0][0],len(mychildren)))
                for parent,child in mychildren:   #parent is the same for all
                         # Make sure that we simply add in the new entry for the child, not replace it,
                         # otherwise we might spoil the child entry loop structure
                         try:
                             childloop = self[child].GetLoop('_item_linked.parent_name')
                         except KeyError:
                             print('Creating new parent entry {} for definition {}'.format(parent,child))
                             self[child]['_item_linked.parent_name'] = [parent]
                             childloop = self[child].GetLoop('_item_linked.parent_name')
                             childloop.AddLoopItem(('_item_linked.child_name',[child]))
                             continue
                         else:
                             # A parent loop already exists and so will a child loop due to the
                             # call to create_pcloop above
                             pars = [a for a in childloop if getattr(a,'_item_linked.child_name','')==child]
                             goodpars = [a for a in pars if getattr(a,'_item_linked.parent_name','')==parent]
                             if len(goodpars)>0:   #no need to add it
                                 print('Skipping duplicated parent - child entry in {}: {} - {}'.format(child,parent,child))
                                 continue
                             print('Adding {} to {} entry'.format(parent,child))
                             newpacket = childloop.GetPacket(0)   #essentially a copy, I hope
                             setattr(newpacket,'_item_linked.child_name',child)
                             setattr(newpacket,'_item_linked.parent_name',parent)
                             childloop.AddPacket(newpacket)
                #
                # Make sure the parent also points to the children.  We get
                # the current entry, then add our
                # new values if they are not there already
                #
                parent_name = mychildren[0][0]
                old_children = self[parent_name].get('_item_linked.child_name',[])
                old_parents = self[parent_name].get('_item_linked.parent_name',[])
                oldfamily = zip(old_parents,old_children)
                newfamily = []
                print('Old parents -> {}'.format(repr(old_parents)))
                for jj, childname in mychildren:
                    alreadythere = [a for a in oldfamily if a[0]==parent_name and a[1] ==childname]
                    if len(alreadythere)>0: continue
                    #'Adding new child %s to parent definition at %s' % (childname,parent_name)
                    old_children.append(childname)
                    old_parents.append(parent_name)
                # Now output the loop, blowing away previous definitions.  If there is something
                # else in this category, we are destroying it.
                newloop = CifLoopBlock(dimension=1)
                newloop.AddLoopItem(('_item_linked.parent_name',old_parents))
                newloop.AddLoopItem(('_item_linked.child_name',old_children))
                del self[parent_name]['_item_linked.parent_name']
                del self[parent_name]['_item_linked.child_name']
                self[parent_name].insert_loop(newloop)
                print('New parents -> {}'.format(repr(self[parent_name]['_item_linked.parent_name'])))
                # now make a new,smaller list
                notmychildren = [a for a in notmychildren if a[0]!=mychildren[0][0]]

       # now flatten any single element lists
       single_defs = filter(lambda a:len(self[a]['_item.name'])==1,listed_defs)
       for flat_def in single_defs:
           flat_keys = self[flat_def].GetLoop('_item.name').keys()
           for flat_key in flat_keys: self[flat_def][flat_key] = self[flat_def][flat_key][0]
       # now deal with the multiple lists
       # next we do aliases
       all_aliases = [a for a in self.keys() if self[a].has_key('_item_aliases.alias_name')]
       for aliased in all_aliases:
          my_aliases = listify(self[aliased]['_item_aliases.alias_name'])
          for alias in my_aliases:
              self[alias] = self[aliased].copy()   #we are going to delete stuff...
              del self[alias]["_item_aliases.alias_name"]

    # DDLm introduces validity information in the enclosing datablock.  It is a loop of scope,
    # attribute values where the scope is one of dictionary (everywhere), category (whole
    # category) and item (just the single definition).  Validity can be mandatory,
    # encouraged or not allowed.  It only appears in the DDLm attributes dictionary, so
    # this information is blank unless we are dealing with the DDLm dictionary.
    #                                                                         
    #                                                                         
    # <Parse DDLm validity information>=                                      
    def ddlm_parse_valid(self):
        if "_dictionary_valid.scope" not in self.master_block:
            return
        for scope_pack in self.master_block.GetLoop("_dictionary_valid.scope"):
            scope = getattr(scope_pack,"_dictionary_valid.scope")
            stance = getattr(scope_pack, "_dictionary_valid.option")
            valid_info = getattr(scope_pack,"_dictionary_valid.attributes")
            if stance == "Mandatory":
                self.scopes_mandatory[scope] = self.expand_category_opt(valid_info)
            elif stance == "Prohibited":
                self.scopes_naughty[scope] = self.expand_category_opt(valid_info)

    # Section{DDLm functionality}                                             
    #                                                                         
    # DDLm is a far more complex dictionary standard than DDL2.  We are able to import
    # definitions in two modes, "Full" and "Contents".  "Contents" simply copies the attributes
    # found in the target definition, and is useful as a templating mechanism for commonly-seen
    # attributes.  "Full" brings in the entire definition block and all child definitions, and
    # is useful for including entire dictionaries.  As a special case, if we import a 'Head'
    # definition into a 'Head' definition, we actually make all non-Head categories of the
    # imported dictionary into child categories of the importing dictionary 'Head' category,
    # and the imported 'Head' category disappears.                            
    #                                                                         
    # ``Contents'' and ``Full'' modes are implemented dynamically, that is,   
    # when the value of an attribute is requested the dictionary resolves     
    # imports.                                                                
    #                                                                         
    # The merging method of the StarFile object is purely syntactic and so does not understand
    # DDLm relationships.  We add all blocks as the children of the top-level dictionary block,
    # and then in the case of a new 'Head' block we simply reparent the immediate semantic
    # children of the old 'Head' block.                                       
    #                                                                         
    #                                                                         
    # <Perform DDLm imports>=                                                 
    # <Get import information>=                                               
    def get_dictionaries_to_import(self):
        import_frames = list([(a,self[a]['_import.get']) for a in self.keys() if '_import.get' in self[a]])

        dictionaries = set()
        for parent_block,import_list in import_frames:
            for import_ref in import_list:
                dictionary_name = import_ref.get("file", "")
                dictionaries.add(dictionary_name)

        return list(dictionaries)

    def obtain_imports(self,import_mode,heavy=False):
        """Collate import information"""
        self._import_dics = []
        import_frames = list([(a,self[a]['_import.get']) for a in self.keys() if '_import.get' in self[a]])
        if self.verbose_import:
            print('Import mode {} applied to following frames'.format(import_mode))
            print(str([a[0] for a in import_frames]))
        if import_mode != 'All':
           for i in range(len(import_frames)):
                import_frames[i] = (import_frames[i][0],[a for a in import_frames[i][1] if a.get('mode','Contents').lower() == import_mode.lower()])
           print('Importing following frames in mode {}'.format(import_mode))
           print(str(import_frames))
        #resolve all references
        for parent_block,import_list in import_frames:
          for import_ref in import_list:
            file_loc = import_ref["file"]
            full_uri = self.resolve_path(file_loc)
            if full_uri not in self.template_cache:
                dic_as_cif = CifFile(full_uri,grammar=self.grammar, characterset=self.characterset)
                self.template_cache[full_uri] = CifDic(dic_as_cif,do_imports=import_mode,heavy=heavy,do_dREL=False, verbose_import=self.verbose_import)  #this will recurse internal imports

                if self.verbose_import:
                    print('Added {} to cached dictionaries'.format(full_uri))
            import_from = self.template_cache[full_uri]
            dupl = import_ref.get('dupl','Exit')
            miss = import_ref.get('miss','Exit')
            target_key = import_ref["save"]
            try:
                import_target = import_from[target_key]
            except KeyError:
                if miss == 'Exit':
                   raise CifError('Import frame {} not found in {}'.format(target_key,full_uri))
                else: continue
            # now import appropriately
            mode = import_ref.get("mode",'Contents').lower()
            if target_key in self and mode=='full':  #so blockname will be duplicated
                if dupl == 'Exit':
                    raise CifError('Import frame {} already in dictionary'.format(target_key))
                elif dupl == 'Ignore':
                    continue
            if heavy:
                self.ddlm_import(parent_block,import_from,import_target,target_key,mode)
            else:
                self.ddlm_import_light(parent_block,import_from,import_target,target_key,file_loc,mode)
    #  The original way of doing imports was to completely merge the information from the
    # imported file.  This is slightly more efficient if information about import statements
    # is not required.                                                        
    #                                                                         
    #                                                                         
    # <Heavy import routine>=                                                 

    def ddlm_import(self,parent_block,import_from,import_target,target_key,mode='All'):
            """Import other dictionaries in place"""

            """
            Parent_block -> Key of the tag that imports data
            Import_from -> Dictionary to import
            Import_target -> Block to be imported
            Target_key -> Key to be imported
            """
            if mode == 'contents':   #merge attributes only
                self[parent_block].merge(import_target)
            elif mode =="full":
                # Do the syntactic merge
                syntactic_head = self[self.get_parent(parent_block)] #root frame if no nesting
                from_cat_head = import_target['_name.object_id']
                child_frames = import_from.ddlm_all_children(from_cat_head)
                 # Check for Head merging Head
                if self[parent_block].get('_definition.class','Datum')=='Head' and \
                   import_target.get('_definition.class','Datum')=='Head':
                      head_to_head = True
                else:
                      head_to_head = False
                      child_frames.remove(from_cat_head)
                # As we are in syntax land, we call the CifFile methods
                child_blocks = list([import_from.block_id_table[a.lower()] for a in child_frames])
                child_blocks = super(CifDic,import_from).makebc(child_blocks)
                # Prune out any datablocks that have identical definitions
                from_defs = dict([(a,child_blocks[a].get('_definition.id','').lower()) for a in child_blocks.keys()])
                double_defs = list([b for b in from_defs.items() if self.has_key(b[1])])
                if self.verbose_import:
                    print('Definitions for {} superseded'.format(repr(double_defs)))

                # Merge different tags of duplicated blocks
                self.merge_duplicates(child_blocks, double_defs)

                for b in double_defs:
                    del child_blocks[b[0]]
                super(CifDic,self).merge_fast(child_blocks,parent=syntactic_head)      #
                if self.verbose_import:
                    print('Syntactic merge of {} ({} defs) in {} mode, now have {} defs'.format(target_key,len(child_frames),
                        mode,len(self)))
                # Now the semantic merge
                # First expand our definition <-> blockname tree
                self.create_def_block_table()
                merging_cat = self[parent_block]['_name.object_id']      #new parent
                if head_to_head:
                    child_frames = self.ddlm_immediate_children(from_cat_head)    #old children
                    #the new parent is the importing category for all old children
                    for f in child_frames:
                        self[f].overwrite = True
                        self[f]['_name.category_id'] = merging_cat
                        self[f].overwrite = False
                    # remove the old head
                    del self[from_cat_head]
                    if self.verbose_import:
                        print('Semantic merge: {} defs reparented from {} to {}'.format(len(child_frames),from_cat_head,merging_cat))
                else:  #imported category is only child
                    from_frame = import_from[target_key]['_definition.id'] #so we can find it
                    child_frame = [d for d in self.keys() if self[d]['_definition.id']==from_frame][0]
                    self[child_frame]['_name.category_id'] = merging_cat
                    if self.verbose_import:
                        print('Semantic merge: category for {} : now {}'.format(from_frame,merging_cat))
            # it will never happen again...
            del self[parent_block]["_import.get"]

    def merge_duplicates(self, child_blocks, double_defs):
        '''
        Duplicated blocks may have different definitions. Therefore deleting them will end up
        creating an incomplete dictionary.
        This functions checks among the duplicated tags, and if a duplicated pair has different
        tags, the remaining tags of the imported block are added to the base block.
        '''

        for double_def in double_defs:
            # Tag name in the dictionary to be imported
            tag_name = double_def[0]
            # Tag name in the base dictionary
            base_tag_name = double_def[1]

            duplicated_block = child_blocks[tag_name]
            base_block = self[base_tag_name]

            duplicated_block_keys = set(duplicated_block.keys())
            base_block_keys = set(base_block.keys())

            # Add category key name

            # What to do in case of lists?
            # Half the ids are the same, and the other half are not
            #if self.unique_spec in duplicated_block_keys and \
            #    base_block[self.unique_spec] != duplicated_block[self.unique_spec]:
            #        original_cat_key = base_block[self.unique_spec]
            #        duplicated_cat_key = duplicated_block[self.unique_spec]
            #
            #        cat_key_set = {original_cat_key, duplicated_cat_key}
            #
            #
            #
            #        self[base_tag_name][self.unique_spec] = cat_key_set

            # Both blocks are equal, continue to the next duplicated block
            if len(duplicated_block_keys) == len(base_block_keys) \
                and duplicated_block_keys == base_block_keys:
                    continue

            # Only add the missing tag values to the base dictionary
            for property_name in duplicated_block.keys():
                if property_name not in base_block_keys:
                    property_value = duplicated_block[property_name]
                    self[base_tag_name][property_name] = property_value

    def resolve_path(self,file_loc):
        url_comps = urlparse(file_loc)
        if url_comps[0]: return file_loc    #already full URI
        new_url = urljoin(self.my_uri,file_loc)
        #print("Transformed %s to %s for import " % (file_loc,new_url))
        return new_url

    #  It is possible to not perform imports at reading time, but simply to register the links
    # and resolve the imports if and when a definition is accessed.           
    #                                                                         
    #                                                                         
    # <Light import routine>=                                                 
    def ddlm_import_light(self,parent_block,import_from,import_target,target_key,file_loc,mode='All'):
        """Register the imported dictionaries but do not alter any definitions. `parent_block`
        contains the id of the block that is importing. `import_target` is the block that
        should be imported. `import_from` is the CifFile that contains the definitions."""
        if mode == 'contents':   #merge attributes only
            self[parent_block].add_dict_cache(file_loc,import_from)
        elif mode =="full":
             # Check for Head merging Head
            if self[parent_block].get('_definition.class','Datum')=='Head' and \
               import_target.get('_definition.class','Datum')=='Head':
                   head_to_head = True
            else:
                   head_to_head = False
            # Figure out the actual definition ID
            head_id = import_target["_definition.id"]
            # Adjust parent information
            merging_cat = self[parent_block]['_name.object_id']
            from_cat_head = import_target['_name.object_id']
            if not head_to_head:   # imported category is only child
                import_target["_name.category_id"]=merging_cat
            self._import_dics = [(import_from,head_id)]+self._import_dics #prepend

    # Lightweight importation simply records the import information without performing the
    # import, and then when keys are accessed it checks through the imported dictionaries. The
    # semantics are such that the last dictionary imported should be the first dictionary
    # checked, as imports overwrite any definitions in preceding imports.     
    #                                                                         
    #                                                                         
    # <Lookup imports for whole dictionary>=                                  
    def lookup_imports(self,key):
        """Check the list of imported dictionaries for this definition"""
        for one_dic,head_def in self._import_dics:
            from_cat_head = one_dic[head_def]['_name.object_id']
            possible_keys = one_dic.ddlm_all_children(from_cat_head)
            if key in possible_keys:
                return one_dic[key]
        raise KeyError("{} not found in import dictionaries".format(key))



    #  CIF Dictionaries use the square bracket notation to refer to the definition, as for CifFile
    # objects, but the key is the definition itself, rather than the block name.  So we have to create
    # a lookup table. However, template dictionaries may not have a _definition.id, which means we
    # have to revert to their blockname, so we use blockname as a default.  We also completely
    # ignore case, which is a bit liberal, as definitions themselves are case-sensitive. We catch
    # duplicate definitions (e.g. as a result of incorrect merging).          
    #                                                                         
    # If a definition is not found, we search any dictionaries that were imported in 'Full' mode.
    # This means that definitions in the dictionary proper override anything in the imported
    # dictionaries, as per definitions.                                       
    #                                                                         
    #                                                                         
    # <Repurpose standard python methods>=                                    
    def create_def_block_table(self):
        """ Create an internal table matching definition to block id """
        proto_table = [(super(CifDic,self).__getitem__(a),a) for a in super(CifDic,self).keys()]
        # now get the actual ids instead of blocks
        proto_table = list([(a[0].get(self.cat_id_spec,a[0].get(self.def_id_spec,a[1])),a[1]) for a in proto_table])
        # remove non-definitions
        if self.diclang != "DDL1":
            top_blocks = list([a[0].lower() for a in self.get_roots()])
        else:
            top_blocks = ["on_this_dictionary"]
        # catch dodgy duplicates
        uniques = set([a[0] for a in proto_table])
        if len(uniques)<len(proto_table):
            def_names = list([a[0] for a in proto_table])
            dodgy = [a for a in def_names if def_names.count(a)>1]
            raise CifError('Duplicate definitions in dictionary:' + repr(dodgy))
        self.block_id_table = dict([(a[0].lower(),a[1].lower()) for a in proto_table if a[1].lower() not in top_blocks])

    def __getitem__(self,key):
        """Access a datablock by definition id, after the lookup has been created"""
        try:
            return super(CifDic,self).__getitem__(self.block_id_table[key.lower()])
        except AttributeError:   #block_id_table not present yet
            return super(CifDic,self).__getitem__(key)
        except KeyError: # key is missing
            try: # print(Definition for %s not found, reverting to CifFile' % key)
                return super(CifDic,self).__getitem__(key)
            except KeyError: # try imports
                return self.lookup_imports(key)

    def __setitem__(self,key,value):
        """Add a new definition block"""
        super(CifDic,self).__setitem__(key,value)
        try:
            self.block_id_table[value['_definition.id']]=key
        except AttributeError:   #does not exist yet
            pass

    def NewBlock(self,*args,**kwargs):
        newname = super(CifDic,self).NewBlock(*args,**kwargs)
        try:
            self.block_id_table[self[newname]['_definition.id']]=newname
        except AttributeError: #no block_id table
            pass

    def __delitem__(self,key):
        """Remove a definition"""
        try:
            super(CifDic,self).__delitem__(self.block_id_table[key.lower()])
            del self.block_id_table[key.lower()]
        except (AttributeError,KeyError):   #block_id_table not present yet
            super(CifDic,self).__delitem__(key)
            return
        # fix other datastructures
        # cat_obj table

    def keys(self):
        """Return all definitions"""
        try:
            return self.block_id_table.keys()
        except AttributeError:
            return super(CifDic,self).keys()

    def has_key(self,key):
        return key in self

    def __contains__(self,key):
        try:
            return key.lower() in self.block_id_table
        except AttributeError:
            return super(CifDic,self).__contains__(key)

    def items(self):
        """Return (key,value) pairs"""
        return list([(a,self[a]) for a in self.keys()])

    # Any Starfile method that uses the square-bracket notation or            
    # build-in syntax (e.g. del) to access keys may fail if the set of keys   
    # it uses is not that provided by the keys() method above, as the         
    # object delegation using super() does not apply.  As we have set         
    # up our methods above to 'fall through' to the underlying CifFile,       
    # the process of renaming may or may not have called our del              
    # method to remove the definition, so we check.                           
    #                                                                         
    #                                                                         
    # <Repurpose Starfile methods>=                                           
    def unlock(self):
        """Allow overwriting of all definitions in this collection"""
        for a in self.keys():
            self[a].overwrite=True

    def lock(self):
        """Disallow changes in definitions"""
        for a in self.keys():
            self[a].overwrite=False

    def rename(self,oldname,newname,blockname_as_well=True):
        """Change a _definition.id from oldname to newname, and if `blockname_as_well` is True,
        change the underlying blockname too."""
        if blockname_as_well:
            super(CifDic,self).rename(self.block_id_table[oldname.lower()],newname)
            self.block_id_table[newname.lower()]=newname
            if oldname.lower() in self.block_id_table: #not removed
               del self.block_id_table[oldname.lower()]
        else:
            self.block_id_table[newname.lower()]=self.block_id_table[oldname.lower()]
            del self.block_id_table[oldname.lower()]
            return

    # \subsection{Semantic information}                                       
    #                                                                         
    #                                                                         
    # <Obtaining semantic information from the dictionary>=                   
    # For convenience we provide ways of interrogating the semantic tree      
    # of categories. Note that if we are passed the top-level datablock, the  
    # semantic children are the syntactic children.  An additional method     
    # finds the 'dangling' definitions, which are definitions that have no    
    # category definition present - these might be definitions added by this  
    # dictionary to categories found in other dictionaries.                   
    #                                                                         
    #                                                                         
    # <Operations with semantic children>=                                    
    def get_root_category(self):
        """Get the single 'Head' category of this dictionary"""
        root_cats = [r for r in self.keys() if self[r].get('_definition.class','Datum')=='Head']
        if len(root_cats)>1 or len(root_cats)==0:
            raise CifError("Cannot determine a unique Head category, got".format(repr(root_cats)))
        return root_cats[0]

    def ddlm_immediate_children(self,catname):
        """Return a list of datanames for the immediate children of catname.  These are
        semantic children (i.e. based on _name.category_id), not structural children as
        in the case of StarFile.get_immediate_children"""

        straight_children = [a for a in self.keys() if self[a].get('_name.category_id','').lower() == catname.lower()]
        return list(straight_children)

    def ddlm_all_children(self,catname):
        """Return a list of all children, including the `catname`"""
        all_children = self.ddlm_immediate_children(catname)
        cat_children = [a for a in all_children if self[a].get('_definition.scope','Item') == 'Category']
        for c in cat_children:
            all_children.remove(c)
            all_children += self.ddlm_all_children(c)
        return all_children + [catname]

    def is_semantic_child(self,parent,maybe_child):
        """Return true if `maybe_child` is a child of `parent`"""
        all_children = self.ddlm_all_children(parent)
        return maybe_child in all_children

    def ddlm_danglers(self):
        """Return a list of definitions that do not have a category defined
        for them, or are children of an unattached category"""
        top_block = self.get_root_category()
        connected = set(self.ddlm_all_children(top_block))
        all_keys = set(self.keys())
        unconnected = all_keys - connected
        return list(unconnected)

    def get_ddlm_parent(self,itemname):
        """Get the parent category of itemname"""
        parent = self[itemname].get('_name.category_id','')
        if parent == '':  # use the top block by default
            raise CifError("{} has no parent".format(itemname))
        return parent

    #  Some methods for interrogating categories for names.                   
    #                                                                         
    #                                                                         
    # <Get category information>=                                             
    def expand_category_opt(self,name_list):
        """Return a list of all non-category items in a category or return the name
           if the name is not a category"""
        new_list = []
        for name in name_list:
          if self.get(name,{}).get('_definition.scope','Item') == 'Category':
            new_list += self.expand_category_opt([a for a in self.keys() if \
                     self[a].get('_name.category_id','').lower() == name.lower()])
          else:
            new_list.append(name)
        return new_list

    def get_categories(self):
        """Return a list of category names"""
        return list([c for c in self.keys() if self[c].get("_definition.scope")=='Category'])

    # This method was added to facilitate running dREL scripts, which treat   
    # certain variables as having attributes which all belong to a single category.
    # We return only the extension in keeping with dREL syntax.  If [[names_only]]
    # is true, we return only the object part of the dataname.  Note that sub 
    # categories are excluded.  TODO: use cat-obj table for speed.            
    #                                                                         
    #                                                                         
    # <List all items in a category>=                                         
    def names_in_cat(self,cat,names_only=False):
        names = [a for a in self.keys() if self[a].get('_name.category_id','').lower()==cat.lower()]
        if not names_only:
            return list([a for a in names if self[a].get('_definition.scope','Item')=='Item'])
        else:
            return list([self[a]["_name.object_id"] for a in names])



    #  A dataname can appear in a file under a different name if it has been aliased. We create
    # an alias table to speed up lookup.  The table is indexed by true name, with a list of
    # alternatives.                                                           
    #                                                                         
    #                                                                         
    # <Create alias table>=                                                   
    def create_alias_table(self):
        """Populate an alias table that we can look up when searching for a dataname"""
        all_aliases = [a for a in self.keys() if '_alias.definition_id' in self[a]]
        self.alias_table = dict([[a,self[a]['_alias.definition_id']] for a in all_aliases])

    # DDLm internally refers to data items by the category.object notation, with the twist
    # that child categories of loops can have their objects appear in the parent category. So
    # this table prepares a complete list of (cat,obj):dataname correspondences, as the
    # implementation of parent-child requires looking up a table each time searching for
    # children.                                                               
    #                                                                         
    # The recursive [[expand_base_table]] function returns a dictionary of (name,definition_id) pairs
    # indexing the corresponding datanames.  We must catch any keys and exclude them from this
    # process, as they are allowed to have the same [[object_id]] as their parent key in the
    # enclosing datablock and will overwrite the entry for the parent key if left in. We also
    # note that the example dictionary allows these types of name collisions if an item is
    # intended to be identical (e.g. _atom_site_aniso.type_symbol and atom_site.type_symbol),
    # so we create a short list of possible alternative names for each (cat,obj) pair.
    #                                                                         
    # The create_nested_key_table stores information about which keys index child categories. This
    # way applications can search for any loops containing these keys and expand packets for dREL
    # accordingly.                                                            
    #                                                                         
    #                                                                         
    # <Create category/object table>=                                         
    def create_cat_obj_table(self):
        """Populate a table indexed by (cat,obj) and returning the correct dataname"""

        # Collect all explicit (cat,obj) pairs for data names
        
        base_table = dict([((self[a].get('_name.category_id','').lower(),self[a].get('_name.object_id','').lower()),[self[a].get('_definition.id','')]) \
                           for a in self.keys() if self[a].get('_definition.scope','Item')=='Item'])

        # Find all loop category parent-child relationships
        
        loopable = self.get_loopable_cats()
        loopers = [self.ddlm_immediate_children(a) for a in loopable]

        if self.verbose_import:
            print('Loopable cats:' + repr(loopable))

        loop_children = [[b for b in a if b.lower() in loopable ] for a in loopers]
        expand_list = dict([(a,b) for a,b in zip(loopable,loop_children) if len(b)>0])

        if self.verbose_import:
            print("Expansion list:" + repr(expand_list))
    
        extra_table = {}   #for debugging we keep it separate from base_table until the end

        # Define a function that puts all child category objects into the parent category,
        # returning the list of new names so it can be used recursively
        
        def expand_base_table(parent_cat,child_cats):

            extra_names = []

            parent_names = [(self[n]['_name.object_id'].lower(),self[n]['_definition.id']) \
                            for n in self.names_in_cat(parent_cat) if self[n].get('_type.purpose','')!='Key']

            # first deal with all the child categories

            for child_cat in child_cats:
                nn = []
              
                if child_cat in expand_list:  # a nested category: grab its names
                    nn = expand_base_table(child_cat,expand_list[child_cat])
                    # store child names
                    extra_names += nn

                # get all child names for this category

                child_names = [(self[n]['_name.object_id'].lower(),self[n]['_definition.id']) \
                             for n in self.names_in_cat(child_cat) if self[n].get('_type.purpose','') != 'Key']
                # update child category with parent names (it can also see the parent)

                extra_table.update(dict([((child_cat,obj),[name]) for obj, name in parent_names if (child_cat, obj) not in extra_table]))

                # and include those from child categories
                
                child_names += extra_names

                # update our reference table for the parent category
                
                extra_table.update(dict([((parent_cat,obj),[name]) for obj,name in child_names if (parent_cat,obj) not in extra_table]))

                
            # and the repeated ones get appended instead

            repeats = [a for a in child_names if a in extra_table]

            for obj,name in repeats:
                extra_table[(parent_cat,obj)] += [name]

            # and finally, add our own names to the return list

            child_names += [(self[n]['_name.object_id'].lower(),self[n]['_definition.id']) \
                            for n in self.names_in_cat(parent_cat) if self[n].get('_type.purpose','')!='Key']
            return child_names

        # Process all parent-child hierarchies that we've found.
        
        [expand_base_table(parent,child) for parent,child in expand_list.items()]

        if self.verbose_import:
            print('Expansion cat/obj values: ' + repr(extra_table))

        # pick over our expanded information: repeats append, new get added

        non_repeats = dict([a for a in extra_table.items() if a[0] not in base_table])
        repeats = [a for a in extra_table.keys() if a in base_table]
        base_table.update(non_repeats)

        for k in repeats:
            base_table[k] += extra_table[k]

        self.cat_obj_lookup_table = base_table
        self.loop_expand_list = expand_list

    def get_loopable_cats(self):
        """A short utility function which returns a list of looped categories. This
        is preferred to a fixed attribute as that fixed attribute would need to be
        updated after any edits"""
        return [a.lower() for a in self.keys() if self[a].get('_definition.class','')=='Loop']

    def create_cat_key_table(self):
        """Create a utility table with a list of keys applicable to each category. A key is
        a compound key, that is, it is a list"""
        self.cat_key_table = dict([(c,[listify(self[c].get("_category_key.name",
            [self[c].get("_category.key_id")]))]) for c in self.get_loopable_cats()])
        def collect_keys(parent_cat,child_cats):
                kk = []
                for child_cat in child_cats:
                    if child_cat in self.loop_expand_list:
                        kk += collect_keys(child_cat)
                    # add these keys to our list
                    kk += [listify(self[child_cat].get('_category_key.name',[self[child_cat].get('_category.key_id')]))]
                self.cat_key_table[parent_cat] = self.cat_key_table[parent_cat] + kk
                return kk
        for k,v in self.loop_expand_list.items():
            collect_keys(k,v)
        if self.verbose_import:
            print('Keys for categories' + repr(self.cat_key_table))

    # Preparing our type expressions                                          
    #                                                                         
    # In DDL2 dictionaries our type expressions are given in the main         
    # block as POSIX regexps, so we can pass them on to the re package.       
    # For DDL1 dictionaries we could get them from the DDL1 language          
    # definition, but for now we just hard code them.  Essentially only       
    # the number definition is important, as the syntax check during          
    # reading/writing will catch any char violations.                         
    #                                                                         
    # Note that the python re engine is not POSIX compliant in that it will   
    # not return the longest leftmost match, but rather the first leftmost    
    # match.  John Bollinger suggested an obvious fix: we append a [[$]] to force
    # a full match.                                                           
    #                                                                         
    # In other regexp editing, the [[\{]] sequence inside the character sets of
    # some of the regexps is actually interpreted as an escaped bracket, so the
    # backslash vanishes.  We add it back in by doing a very hackish and ugly 
    # substitution which substitues these two characters anywhere that they   
    # occur inside square brackets.  A final change is to insert a [[\r]] wherever
    # we find a [[\n]] - it seems that this has been left out.                
    # After these changes, and appending on default                           
    # expressions as well, we can now work with DDL2 expressions directly.    
    #                                                                         
    # We keep the primitive code for the single reason that we need to        
    # know when we are dealing with a number that has an esd appended, and    
    # this is flagged by the primitive code being of type 'numb'.             
    #                                                                         
    #                                                                         
    # <Add type information>=                                                 
    def add_type_info(self):
        if "_item_type_list.construct" in self.master_block:
            types = self.master_block["_item_type_list.code"]
            prim_types = self.master_block["_item_type_list.primitive_code"]
            constructs = list([a + "$" for a in self.master_block["_item_type_list.construct"]])
            # add in \r wherever we see \n, and change \{ to \\{
            def regex_fiddle(mm_regex):
                brack_match = r"((.*\[.+)(\\{)(.*\].*))"
                ret_match = r"((.*\[.+)(\\n)(.*\].*))"
                fixed_regexp = mm_regex[:]  #copy
                # fix the brackets
                bm = re.match(brack_match,mm_regex)
                if bm != None:
                    fixed_regexp = bm.expand(r"\2\\\\{\4")
                # fix missing \r
                rm = re.match(ret_match,fixed_regexp)
                if rm != None:
                    fixed_regexp = rm.expand(r"\2\3\\r\4")
                #print("Regexp %s becomes %s" % (mm_regex,fixed_regexp))
                return fixed_regexp
            constructs = map(regex_fiddle,constructs)
            for typecode,construct in zip(types,constructs):
                self.typedic[typecode] = re.compile(construct,re.MULTILINE|re.DOTALL)
            # now make a primitive <-> type construct mapping
            for typecode,primtype in zip(types,prim_types):
                self.primdic[typecode] = primtype

    # Dictionaries have the category-wide information in the category         
    # definition area.  We do not need to fill all of this in if we are       
    # not planning on running dREL.                                           
    #                                                                         
    #                                                                         
    # <Add category information>=                                             
    def add_category_info(self,full=True):
        if self.diclang == "DDLm":
            # For help in validation we create a lookup table which matches a category to
            # its ultimate parent.  This allows us to quickly check whether or not a data
            # item is allowed to be co-looped with other data items.  Note that we may have
            # to draw in external dictionaries to do this properly, but to avoid holding
            # the whole lot in memory, we simply stop searching up the parent tree if the
            # parent block is missing.                                                
            #                                                                         
            #                                                                         
            # <Create category parent table>=                                         
            catblocks = [c for c in self.keys() if self[c].get('_definition.scope')=='Category']
            looped_cats = [a for a in catblocks if self[a].get('_definition.class','Set') == 'Loop']
            self.parent_lookup = {}
            for one_cat in looped_cats:
                parent_cat = one_cat
                parent_def = self[parent_cat]
                next_up = parent_def['_name.category_id'].lower()
                while next_up in self and self[next_up].get('_definition.class','Set') == 'Loop':
                    parent_def = self[next_up]
                    parent_cat = next_up
                    next_up = parent_def['_name.category_id'].lower()
                self.parent_lookup[one_cat] = parent_cat

            if full:
                # The key hierarchy. This is in many ways reinventing the parent-child    
                # relationships that are laid out in DDL2 definitions.  In order to       
                # access a particular packet using multiple datanames as compound keys,   
                # we need to be aware of which keys are related to which other            
                # keys. Relationships are always made explicit via the                    
                # '_name.linked_item_id' attribute in DDLm, which always points to the    
                # parent.  This is always present, even though it may be often be inferred
                # using Loop category parent/child relationships, as compound keys in     
                # categories might introduce ambiguity.                                   
                #                                                                         
                # This datastructure allows us to provide a key, and obtain a list of     
                # equivalent keys, being all those above it in the hierarchy, that is,    
                # which it can be replaced by.  If we are not doing dREL, we can afford   
                # to skip this.                                                           
                #                                                                         
                #                                                                         
                # <Create key hierarchy>=                                                 
                self.key_equivs = {}
                for one_cat in looped_cats:   #follow them up
                    if '_category_key.name' not in self[one_cat].keys():
                        continue

                    lower_keys = listify(self[one_cat]['_category_key.name'])
                    start_keys = lower_keys[:]
                    while len(lower_keys)>0:
                        if lower_keys[0] not in self.keys():
                            break

                        this_cat = self[lower_keys[0]]['_name.category_id']
                        parent = [a for a in looped_cats if self[this_cat]['_name.category_id'].lower()==a]
                        #print(Processing %s, keys %s, parent %s" % (this_cat,repr(lower_keys),repr(parent)))
                        if len(parent)>1:
                            raise CifError("Category {} has more than one parent: {}".format(one_cat,repr(parent)))
                        if len(parent)==0: break
                        parent = parent[0]
                        parent_keys = listify(self[parent]['_category_key.name'])

                        linked_key_found = True
                        for l in lower_keys:
                            if "_name.linked_item_id" not in self[l].keys():
                                linked_key_found = False

                        if linked_key_found:
                            linked_keys = [self[l]["_name.linked_item_id"] for l in lower_keys]
                            # sanity check
                            if set(parent_keys) != set(linked_keys):
                                raise CifError("Parent keys and linked keys are different! {}/{}".format(parent_keys,linked_keys))
                                # now add in our information
                            for parent,child in zip(linked_keys,start_keys):
                                self.key_equivs[child] = self.key_equivs.get(child,[])+[parent]
                            lower_keys = linked_keys  #preserves order of start keys

                        else:
                            # It is assumed that there are no more linked_keys, therefore return an empty list
                            lower_keys = []

        else:
            self.parent_lookup = {}
            self.key_equivs = {}

    #  These methods were added when developing interactive editing tools, which allow
    # shifting categories around.                                             
    #                                                                         
    #                                                                         
    # <Definition manipulation methods>=                                      
    # Changing a category name involves changing the [[_name.category_id]]    
    # in all children as well as the category definition itself and           
    # datablock names, then updating our internal structures.                 
    #                                                                         
    #                                                                         
    # <Changing and updating categories>=                                     
    def change_category_name(self,oldname,newname):
        self.unlock()
        """Change the category name from [[oldname]] to [[newname]]"""
        if oldname not in self:
            raise KeyError('Cannot rename non-existent category {} to {}'.format(oldname,newname))
        if newname in self:
            raise KeyError('Cannot rename {} to {} as {} already exists'.format(oldname,newname,oldname))
        child_defs = self.ddlm_immediate_children(oldname)
        self.rename(oldname,newname)   #NB no name integrity checks
        self[newname]['_name.object_id']=newname
        self[newname]['_definition.id']=newname
        for child_def in child_defs:
            self[child_def]['_name.category_id'] = newname
            if self[child_def].get('_definition.scope','Item')=='Item':
                newid = self.create_catobj_name(newname,self[child_def]['_name.object_id'])
                self[child_def]['_definition.id']=newid
                self.rename(child_def,newid[1:])  #no underscore at the beginning
        self.lock()

    def create_catobj_name(self,cat,obj):
        """Combine category and object in approved fashion to create id"""
        return ('_'+cat+'.'+obj)

    def change_category(self,itemname,catname):
        """Move itemname into catname, return new handle"""
        defid = self[itemname]
        if defid['_name.category_id'].lower()==catname.lower():
            print('Already in category, no change')
            return itemname
        if catname not in self:    #don't have it
            print('No such category {}'.format(catname))
            return itemname
        self.unlock()
        objid = defid['_name.object_id']
        defid['_name.category_id'] = catname
        newid = itemname # stays the same for categories
        if defid.get('_definition.scope','Item') == 'Item':
            newid = self.create_catobj_name(catname,objid)
            defid['_definition.id']= newid
            self.rename(itemname,newid)
        self.set_parent(catname,newid)
        self.lock()
        return newid

    def change_name(self,one_def,newobj):
        """Change the object_id of one_def to newobj. This is not used for
        categories, but can be used for dictionaries"""
        if '_dictionary.title' not in self[one_def]:  #a dictionary block
            newid = self.create_catobj_name(self[one_def]['_name.category_id'],newobj)
            self.unlock()
            self.rename(one_def,newid)
            self[newid]['_definition.id']=newid
            self[newid]['_name.object_id']=newobj
        else:
            self.unlock()
            newid = newobj
            self.rename(one_def,newobj)
            self[newid]['_dictionary.title'] = newid
        self.lock()
        return newid

    # Note that our semantic parent is given by catparent, but our syntactic parent is
    # always just the root block
    def add_category(self,catname,catparent=None,is_loop=True,allow_dangler=False):
        """Add a new category to the dictionary with name [[catname]].
           If [[catparent]] is None, the category will be a child of
           the topmost 'Head' category or else the top data block. If
           [[is_loop]] is false, a Set category is created. If [[allow_dangler]]
           is true, the parent category does not have to exist."""
        if catname in self:
            raise CifError('Attempt to add existing category {}'.format(catname))
        self.unlock()
        syntactic_root = self.get_roots()[0][0]
        if catparent is None:
            semantic_root = [a for a in self.keys() if self[a].get('_definition.class',None)=='Head']
            if len(semantic_root)>0:
                semantic_root = semantic_root[0]
            else:
                semantic_root = syntactic_root
        else:
            semantic_root = catparent
        realname = super(CifDic,self).NewBlock(catname,parent=syntactic_root)
        self.block_id_table[catname.lower()]=realname
        self[catname]['_name.object_id'] = catname
        if not allow_dangler or catparent is None:
            self[catname]['_name.category_id'] = self[semantic_root]['_name.object_id']
        else:
            self[catname]['_name.category_id'] = catparent
        self[catname]['_definition.id'] = catname
        self[catname]['_definition.scope'] = 'Category'
        if is_loop:
            self[catname]['_definition.class'] = 'Loop'
        else:
            self[catname]['_definition.class'] = 'Set'
        self[catname]['_description.text'] = 'No definition provided'
        self.lock()
        return catname

    def add_definition(self,itemname,catparent,def_text='PLEASE DEFINE ME',allow_dangler=False):
        """Add itemname to category [[catparent]]. If itemname contains periods,
        all text before the final period is ignored. If [[allow_dangler]] is True,
        no check for a parent category is made."""
        self.unlock()
        if '.' in itemname:
            objname = itemname.split('.')[-1]
        else:
            objname = itemname
        objname = objname.strip('_')
        if not allow_dangler and (catparent not in self or self[catparent]['_definition.scope']!='Category'):
            raise CifError('No category {} in dictionary'.format(catparent))
        fullname = '_'+catparent.lower()+'.'+objname
        print('New name: {}'.format(fullname))
        syntactic_root = self.get_roots()[0][0]
        realname = super(CifDic,self).NewBlock(fullname, fix=False, parent=syntactic_root) #low-level change
        # update our dictionary structures
        self.block_id_table[fullname]=realname
        self[fullname]['_definition.id']=fullname
        self[fullname]['_name.object_id']=objname
        self[fullname]['_name.category_id']=catparent
        self[fullname]['_definition.class']='Datum'
        self[fullname]['_description.text']=def_text
        return realname

    def remove_definition(self,defname):
        """Remove a definition from the dictionary."""
        if defname not in self:
            return
        if self[defname].get('_definition.scope')=='Category':
            children = self.ddlm_immediate_children(defname)
            [self.remove_definition(a) for a in children]
            cat_id = self[defname]['_definition.id'].lower()
        del self[defname]

    # The DDLm architecture identifies a data definition by (category,object) which
    # identifies a unique textual dataname appearing in the data file.  Because of category
    # joins when nested categories are looped, a single dataname may be referred to
    # by several different category identifiers.  The [[get_name_by_cat_obj]] routine
    # will search all loop categories within the given category hierarchy until
    # it finds the appropriate one.                                           
    #                                                                         
    # If [[give_default]] is True, the default construction '_catid.objid'    
    # is returned if nothin is found in the dictionary.  This should only be  
    # used during testing as the lack of a corresponding definition in the    
    # dictionary means that it is unlikely that anything sensible will        
    # result.                                                                 
    #                                                                         
    #                                                                         
    # <Getting category information>=                                         
    def get_cat_obj(self,name):
        """Return (cat,obj) tuple. [[name]] must contain only a single period"""
        cat,obj = name.split('.')
        return (cat.strip('_'),obj)

    def get_name_by_cat_obj(self,category,object,give_default=False):
        """Return the dataname corresponding to the given category and object"""
        if category[0] == '_':    #accidentally left in
           true_cat = category[1:].lower()
        else:
           true_cat = category.lower()
        try:
            return self.cat_obj_lookup_table[(true_cat,object.lower())][0]
        except KeyError:
            if give_default:
               return '_'+true_cat+'.'+object
        raise KeyError('No such category,object in the dictionary: {} {}'.format(true_cat,object))


    # \subsection {Outputting dictionaries}                                   
    #                                                                         
    # We would like dictionary blocks to be output in a readable order, that is,
    # parent categories before their child definitions.  The base BlockCollection
    # output routines have no knowledge of save frame interrelations, so we have
    # to override the output block order returned by the get_child_list routine.
    #                                                                         
    #                                                                         
    # <Dictionary output routines>=                                           
    def WriteOut(self,**kwargs):
        myblockorder = self.get_full_child_list()
        self.set_grammar(self.grammar)
        self.standard = 'Dic'
        return super(CifDic,self).WriteOut(blockorder = myblockorder,**kwargs)

    def get_full_child_list(self):
        """Return a list of definition blocks in order parent-child-child-child-parent-child..."""
        top_block = self.get_roots()[0][0]
        root_cat = [a for a in self.keys() if self[a].get('_definition.class','Datum')=='Head']
        if len(root_cat) == 1:
            all_names = [top_block] + self.recurse_child_list(root_cat[0])
            unrooted = self.ddlm_danglers()
            double_names =  set(unrooted).intersection(set(all_names))
            if len(double_names)>0:
                raise CifError('Names are children of internal and external categories:{}'.format(repr(double_names)))
            remaining = unrooted[:]
            for no_root in unrooted:
                if self[no_root].get('_definition.scope','Item')=='Category':
                    all_names += [no_root]
                    remaining.remove(no_root)
                    these_children = [n for n in unrooted if self[n]['_name.category_id'].lower()==no_root.lower()]
                    all_names += these_children
                    [remaining.remove(n) for n in these_children]
            # now sort by category
            ext_cats = set([self[r].get('_name.category_id',self.cat_from_name(r)).lower() for r in remaining])
            for e in ext_cats:
                cat_items = [r for r in remaining if self[r].get('_name.category_id',self.cat_from_name(r)).lower() == e]
                [remaining.remove(n) for n in cat_items]
                all_names += cat_items
            if len(remaining)>0:
                print('WARNING: following items do not seem to belong to a category??')
                print(repr(remaining))
                all_names += remaining
            print('Final block order: ' + repr(all_names))
            return all_names
        raise ValueError('Dictionary contains no/multiple Head categories, please print as plain CIF instead')

    def cat_from_name(self,one_name):
        """Guess the category from the name. This should be used only when this is not important semantic information,
        for example, when printing out"""
        (cat,obj) = one_name.split(".")
        if cat[0] == "_": cat = cat[1:]
        return cat

    def recurse_child_list(self,parentname):
        """Recursively expand the logical child list of [[parentname]]"""
        final_list = [parentname]
        child_blocks = [a for a in self.child_table.keys() if self[a].get('_name.category_id','').lower() == parentname.lower()]
        child_blocks.sort()    #we love alphabetical order
        child_items = [a for a in child_blocks if self[a].get('_definition.scope','Item') == 'Item']
        final_list += child_items
        child_cats = [a for a in child_blocks if self[a].get('_definition.scope','Item') == 'Category']
        for child_cat in child_cats:
            final_list += self.recurse_child_list(child_cat)
        return final_list



    # This method was added for DDLm support.  We are passed a category and a 
    # value, and must find a packet which has a matching key.  We use the keyname
    # as a way of finding the loop.                                           
    #                                                                         
    #                                                                         
    # <Return a single packet by key>=                                        
    def get_key_pack(self,category,value,data):
        keyname = self[category][self.unique_spec]
        onepack = data.GetPackKey(keyname,value)
        return onepack

    # This support function uses re capturing to work out the number's value. The
    # re contains 7 groups: group 0 is the entire expression; group 1 is the overall
    # match in the part prior to esd brackets; group 2 is the match with a decimal
    # point, group 3 is the digits after the decimal point, group 4 is the match
    # without a decimal point.  Group 5 is the esd bracket contents, and      
    # group 6 is the exponent.                                                
    #                                                                         
    # The esd should be returned as an independent number.  We count the number
    # of digits after the decimal point, create the esd in terms of this, and then,
    # if necessary, apply the exponent.                                       
    #                                                                         
    #                                                                         
    # <Extract number and esd>=                                               
    def get_number_with_esd(numstring):
        numb_re = '((-?(([0-9]*[.]([0-9]+))|([0-9]+)[.]?))([(][0-9]+[)])?([eEdD][+-]?[0-9]+)?)|(\\?)|(\\.)'
        our_match = re.match(numb_re,numstring)
        if our_match:
            a,base_num,b,c,dad,dbd,esd,exp,q,dot = our_match.groups()
            # print("Debug: {} -> {!r}".format(numstring, our_match.groups()))
        else:
            return None,None
        if dot or q: return None,None     #a dot or question mark
        if exp:          #has exponent
           exp = exp.replace("d","e")     # mop up old fashioned numbers
           exp = exp.replace("D","e")
           base_num = base_num + exp
        # print("Debug: have %s for base_num from %s" % (base_num,numstring))
        base_num = float(base_num)
        # work out esd, if present.
        if esd:
            esd = float(esd[1:-1])    # no brackets
            if dad:                   # decimal point + digits
                esd = esd * (10 ** (-1* len(dad)))
            if exp:
                esd = esd * (10 ** (float(exp[1:])))
        return base_num,esd

    # This function analyses a DDL1-type range expression,  returning         
    # a maximum and minimum value.  If the number                             
    # format were ever to change, we need to change this right here, right    
    # now.                                                                    
    #                                                                         
    #                                                                         
    # <Analyse range>=                                                        
    def getmaxmin(self,rangeexp):
        regexp = '(-?(([0-9]*[.]([0-9]+))|([0-9]+)[.]?)([eEdD][+-]?[0-9]+)?)*'
        regexp = regexp + ":" + regexp
        regexp = re.match(regexp,rangeexp)
        try:
            minimum = regexp.group(1)
            maximum = regexp.group(7)
        except AttributeError:
            print("Can't match {}".format(rangeexp))
        if minimum == None: minimum = "."
        else: minimum = float(minimum)
        if maximum == None: maximum = "."
        else: maximum = float(maximum)
        return maximum,minimum

    # \section{Linkage to dREL}                                               
    #                                                                         
    # The drel_ast_yacc package will generate an Abstract Syntax Tree, which  
    # we then convert to a Python function using [[py_from_ast.make_function]].  We use
    # it during initialisation to transform all methods to python expressions,
    # and then the [[derive_item]] method will use this to try to derive the  
    # expression.  Note that newline is the only recognised statement separator
    # in dREL, so we make sure all lines are separated in this way.  We also allow
    # multiple 'Evaluation' methods, which is an enhancement of the current   
    # standard.                                                               
    #                                                                         
    # The [[make_function]] function requires dictionary information to be    
    # supplied regarding looped categories and keys.                          
    #                                                                         
    # If we were really serious about dictionary-driven software, the attribute
    # lookups that follow would not use get(), but square brackets and allow default
    # values to be returned.  However, that would require assigning a dictionary
    # to the dictionary and consequent automated searches which I cannot be bothered
    # to do at this stage.  Just be aware that the default value in the get() 
    # statement is the _enumeration.default specified in ddl.dic.             
    #                                                                         
    #                                                                         
    # <Linkage to dREL>=                                                      
    # Full initialisation. This can take some time so we optionally skip it, but can
    # call this function separately at a later stage if needed.               
    #                                                                         
    #                                                                         
    # <Initialise dREL functions>=                                            
    def initialise_drel(self):
        """Parse drel functions and prepare data structures in dictionary"""
        self.ddlm_parse_valid() #extract validity information from data block
        self.transform_drel()   #parse the drel functions
        self.add_drel_funcs()   #put the drel functions into the namespace

    # <Transform drel to python>=                                             
    def transform_drel(self):
        from .drel import drel_ast_yacc
        from .drel import py_from_ast
        import traceback
        parser = drel_ast_yacc.parser
        lexer = drel_ast_yacc.lexer
        my_namespace = self.keys()
        my_namespace = dict(zip(my_namespace,my_namespace))
        default_attrs = ["_units.code", "_enumeration.default"]
        # we provide a table of loopable categories {cat_name:((key1,key2..),[item_name,...]),...})
        loopable_cats = self.get_loopable_cats()
        loop_keys = [listify(self[a]["_category_key.name"]) for a in loopable_cats if "_category_key.name" in self[a].keys()]
        loop_keys = [[self[a]['_name.object_id'] for a in b if a in self.keys()] for b in loop_keys]
        cat_names = [self.names_in_cat(a,names_only=True) for a in loopable_cats]
        loop_info = dict(zip(loopable_cats,zip(loop_keys,cat_names)))
        # parser.listable_items = [a for a in self.keys() if "*" in self[a].get("_type.dimension","")]
        derivable_list = [a for a in self.keys() if "_method.expression" in self[a] \
                              and self[a].get("_name.category_id","")!= "function"]
        for derivable in derivable_list:
            # reset the list of visible names for parser
            special_ids = [dict(zip(self.keys(),self.keys()))]
            print("Target id: {}".format(derivable))
            drel_exprs = self[derivable]["_method.expression"]
            drel_purposes = self[derivable]["_method.purpose"]
            all_methods = []
            if not isinstance(drel_exprs,list):
                drel_exprs = [drel_exprs]
                drel_purposes = [drel_purposes]
            for drel_purpose,drel_expr in zip(drel_purposes,drel_exprs):

                target_id = derivable
                drel_expr = "\n".join(drel_expr.splitlines())
                # print("Transforming %s" % drel_expr)
                # List categories are treated differently...
                try:
                    meth_ast = parser.parse(drel_expr+"\n",lexer=lexer)
                except:
                    print('Syntax error in method for {}; leaving as is'.format(derivable))
                    a,b = sys.exc_info()[:2]
                    print((repr(a),repr(b)))
                    print(traceback.print_tb(sys.exc_info()[-1],None,sys.stdout))
                    # reset the lexer
                    lexer.begin('INITIAL')
                    continue
                # Construct the python method
                cat_meth = False
                if self[derivable].get('_definition.scope','Item') == 'Category':
                    cat_meth = True

                # Default methods have a different target_id
                if drel_purpose == "Definition":

                    # Find the DDLm attribute that is being redefined
                    target_id = [d for d in default_attrs if d in drel_expr]
                    if len(target_id) != 1:
                        continue
                    target_id = target_id[0]
                    print("Found default attribute {} for {}".format(target_id, derivable))
                
                pyth_meth = py_from_ast.make_python_function(meth_ast,"pyfunc",target_id,
                                                                           loopable=loop_info,
                                                             cif_dic = self,cat_meth=cat_meth)
                all_methods.append((target_id, pyth_meth))
            if len(all_methods)>0:
                save_overwrite = self[derivable].overwrite
                self[derivable].overwrite = True
                self[derivable]["_method.py_expression"] = all_methods
                self[derivable].overwrite = save_overwrite
            #print("Final result:\n " + repr(self[derivable]["_method.py_expression"]))

    # Drel functions are all stored in category 'functions' in our final dictionary.  We want to
    # convert them to executable python code and store them in an appropriate namespace which we
    # can then pass to our individual item methods.  As dREL accepts only linefeed as a terminator,
    # we convert the input text as required.                                  
    #                                                                         
    #                                                                         
    # <Store dREL functions>=                                                 
    def add_drel_funcs(self):
        from .drel import drel_ast_yacc
        from .drel import py_from_ast
        funclist = [a for a in self.keys() if self[a].get("_name.category_id","")=='function']
        # LOOK AT _function.sawtooth
        # It is trying to take the code expression because in some dics it appears inside a loop
        funcnames = []
        for a in funclist:
            if not self[a].loops.keys():
                temp = (self[a]["_name.object_id"],self[a]["_method.expression"])
            else:
                temp = (self[a]["_name.object_id"], getattr(self[a].GetKeyedPacket("_method.purpose","Evaluation"),"_method.expression"))

            funcnames.append(temp)
        # create executable python code...
        parser = drel_ast_yacc.parser
        # we provide a table of loopable categories {cat_name:(key,[item_name,...]),...})
        loopable_cats = self.get_loopable_cats()
        loop_keys = [listify(self[a]["_category_key.name"]) for a in loopable_cats if "_category_key.name" in self[a].keys()]
        loop_keys = [[self[a]['_name.object_id'] for a in b if a in self.keys()] for b in loop_keys]
        cat_names = [self.names_in_cat(a,names_only=True) for a in loopable_cats]
        loop_info = dict(zip(loopable_cats,zip(loop_keys,cat_names)))
        for funcname,funcbody in funcnames:
            newline_body = "\n".join(funcbody.splitlines())
            parser.target_id = funcname
            res_ast = parser.parse(newline_body)
            py_function = py_from_ast.make_python_function(res_ast,None,targetname=funcname,func_def=True,loopable=loop_info,cif_dic = self)
            #print('dREL library function ->\n' + py_function)
            global_table = globals()
            exec(py_function, global_table)    #add to namespace
        #print('Globals after dREL functions added:' + repr(globals()))
        self.ddlm_functions = globals()  #for outside access

    # When a dictionary is available during CIF file access, we can resolve a missing dataname in
    # four ways: (1) check if it is defined under an alias; (2) use a dREL method to calculate the
    # value; (3) use default values if defined.  We resolve in this priority.  Note that we also
    # convert to the appropriate type.  A subsection of (2) is that, if the entire category is
    # missing, we can either use DDLm category construction information or a category
    # method to find our values; we only do this if no items in the category are present. We
    # raise a StarDerivationError if we cannot derive the item, and internally we set result
    # to None as we go through the various ways of deriving the item.         
    #                                                                         
    # The store_value flag asks us to update the ciffile object with the new value.  We remove any
    # numpy dependencies before doing this, which means that we must recreate the numpy type
    # when returning it.                                                      
    #                                                                         
    # The [[allow_defaults]] flag allows default values to be derived. In a situation where
    # multiple methods are available for deriving an item, a calculation that accepts
    # default values will return incorrect values in any situation where an alternative
    # calculation method would have given correct values. For example, if the default value
    # of axis.vector[n] is 0, but I can use an alternative derivation for axis.vector from
    # a different setting, then a calculation that creates axis.vector from the components
    # will give the wrong answer as it will fill in default values when the components are
    # missing.  The track_recursion decorator code handles this by propagating the initial
    # value of allow_defaults to nested calls.                                
    #                                                                         
    #                                                                         
    # <Derive item information>=                                              
    @track_recursion
    def derive_item(self,start_key,cifdata,store_value = False,allow_defaults=True):
        key = start_key   #starting value
        result = None     #success is a non-None value
        default_result = False #we have not used a default value
        # Aliases.  If we have this item under a different name, find it and      
        # return it immediately after putting it into the correct type. We could  
        # be passed either the dictionary defined dataname, or any of its         
        # previous names. We have stored our aliases as a table indexed by        
        # dictionary-defined dataname in order to potentially translate from old  
        # to new datanames.  Once we find a dataname that                         
        # is present in the datafile, we return it.  Note that we have two types  
        # of check: in one we are given an old-style dataname, and have to find   
        # the new or other old version (in which case we have to check the key    
        # of the table) and in the other check we are given the latest version    
        # of the dataname and have to check for older names in the datafile -     
        # this latter is the dREL situation so we have optimised for it be        
        # checking that first and making the modern datanames the table keys.     
        # Note that this section of code occurs first in the 'derive_item'        
        # routine and will change the value of 'key' to the dictionary value      
        # even if nothing is available in the datafile, thereby enabling the      
        # other derivation routes possible.                                       
        #                                                                         
        #                                                                         
        # <Resolve using aliases>=                                                
        # check for aliases
        # check for an older form of a new value
        found_it = [k for k in self.alias_table.get(key,[]) if k in cifdata]
        if len(found_it)>0:
            corrected_type = self.change_type(key,cifdata[found_it[0]])
            return corrected_type
        # now do the reverse check - any alternative form
        alias_name = [a for a in self.alias_table.items() if key in a[1]]
        print('Aliases for {}: {}'.format(key,repr(alias_name)))
        if len(alias_name)==1:
            key = alias_name[0][0]   #actual definition name
            if key in cifdata: return self.change_type(key,cifdata[key])
            found_it = [k for k in alias_name[0][1] if k in cifdata]
            if len(found_it)>0:
                return self.change_type(key,cifdata[found_it[0]])
        elif len(alias_name)>1:
            raise CifError('Dictionary error: dataname alias appears in different definitions: ' + repr(alias_name))

        the_category = self[key]["_name.category_id"]
        cat_names = [a for a in self.keys() if self[a].get("_name.category_id",None)==the_category]
        has_cat_names = [a for a in cat_names if cifdata.has_key_or_alias(a)]
        # store any default value in case we have a problem
        def_val = self[key].get("_enumeration.default","")
        def_index_val = self[key].get("_enumeration.def_index_id","")
        if len(has_cat_names)==0: # try category method
            # \subsection{Creating categories}                                        
            #                                                                         
            # A category can be created from scratch (i.e. the identifiers produced)  
            # if the appropriate DDLm attributes are defined - currently,             
            # experimental attributes 'category_construct_local' are included in the test
            # dictionaries for this purpose. They define two types of 'pullback'      
            # (see any category theory textbook), which we can use to create a        
            # category.  If these attributes are absent, we can instead execute a     
            # category method.  We only add any new category items calculated in      
            # this way if the category does not exist or (i) the category IDs are     
            # not already present and (ii) the set of attributes calculated is an     
            # exact match for the set of datanames already present.                   
            #                                                                         
            #                                                                         
            # <Populate a category>=                                                  
            cat_result = {}
            pulled_from_cats = [k for k in self.keys() if '_category_construct_local.components' in self[k]]
            pulled_from_cats = [(k,[
                                  self[n]['_name.category_id'] for n in self[k]['_category_construct_local.components']]
                               ) for k in pulled_from_cats]
            pulled_to_cats = [k[0] for k in pulled_from_cats if the_category in k[1]]
            if '_category_construct_local.type' in self[the_category]:
                print("**Now constructing category {} using DDLm attributes**".format(the_category))
                try:
                    cat_result = self.construct_category(the_category,cifdata,store_value=True)
                except (CifRecursionError,StarFile.StarDerivationError):
                    print('** Failed to construct category {} (error)'.format(the_category))
            # Trying a pull-back when the category is partially populated
            # will not work, hence we test that cat_result has no keys
            if len(pulled_to_cats)>0 and len(cat_result)==0:
                print("**Now populating category {} from pulled-back category {}".format(the_category,repr(pulled_to_cats)))
                try:
                    cat_result = self.push_from_pullback(the_category,pulled_to_cats,cifdata,store_value=True)
                except (CifRecursionError,StarFile.StarDerivationError):
                    print('** Failed to construct category {} from pullback information (error)'.format(the_category))
            if '_method.py_expression' in self[the_category] and key not in cat_result:
                print("**Now applying category method for {} in search of {}**".format(the_category,key))
                cat_result = self.derive_item(the_category,cifdata,store_value=True)
            print("**Tried pullbacks, obtained for {} ".format(the_category + repr(cat_result)))
            # do we now have our value?
            if key in cat_result:
                return cat_result[key]

        # Recalculate in case it actually worked
        has_cat_names = [a for a in cat_names if cifdata.has_key_or_alias(a)]
        the_funcs = [f[1] for f in self[key].get('_method.py_expression',[]) if f[0] == key.lower()]
        if len(the_funcs) > 0:   #attempt to calculate it
            # Executing a dREL method.  The execution defines a function, 'pyfunc' which is
            # then itself executed in global scope.  This has caused us some grief in order to
            # get the bindings right (e.g. having StarList in scope).   Essentially, anything
            # that the method might refer to should be in scope at this point, otherwise the
            # way Python works it will be too late to have things in scope within the enclosing
            # routine that calls this function.  Importing the necessary modules at the beginning
            # of the module file (as done here) seems to be a reliable way to go.     
            #                                                                         
            #                                                                         
            # <Execute pythonised dREL method>=                                       
            #global_table = globals()
            #global_table.update(self.ddlm_functions)
            for one_func in the_funcs:
                print('Executing function for {}:'.format(key))
                #print(one_func)
                exec(one_func, globals())  #will access dREL functions, puts "pyfunc" in scope
                # print('in following global environment: ' + repr(global_table))
                stored_setting = cifdata.provide_value
                cifdata.provide_value = True
                try:
                    result = pyfunc(cifdata)
                except CifRecursionError as s:
                    print(s)
                    result = None
                except StarFile.StarDerivationError as s:
                    print(s)
                    result = None
                finally:
                    cifdata.provide_value = stored_setting
                if result is not None:
                    break
                #print("Function returned {!r}".format(result))

        if result is None and allow_defaults:   # try defaults
            # Using the defaults system. We also check out any default values         
            # which we could return in case of error.  Note that ddlm adds the        
            # '_enumerations.def_index_id' as an alternative way to derive a value    
            # from a table.  During development, we deliberately allow errors         
            # arising from the method to be propagated so that we can see anything    
            # that might be wrong.                                                    
            #                                                                         
            # If we are using default values, we need to fill in the whole column     
            # of a looped category.  This is taken care of at the end of the derivation
            # function, so we simply set a flag to say that this is necessary.        
            #                                                                         
            #                                                                         
            # <Work out default value of dataname>=                                   
            if def_val:
                result = self.change_type(key,def_val)
                default_result = True
            elif def_index_val:            #derive a default value
                index_vals = self[key]["_enumeration_default.index"]
                val_to_index = cifdata[def_index_val]     #what we are keying on
                lcase_comp = False
                if self[def_index_val]['_type.contents'] in ['Code','Name','Tag']:
                    lcase_comp = True
                    index_vals = [a.lower() for a in index_vals]
                # Handle loops
                if isinstance(val_to_index,list):
                    if lcase_comp:
                        val_to_index = [a.lower() for a in val_to_index]
                    keypos = [index_vals.index(a) for a in val_to_index]
                    result = [self[key]["_enumeration_default.value"][a]  for a in keypos]
                else:
                    if lcase_comp:
                        val_to_index = val_to_index.lower()
                    keypos = index_vals.index(val_to_index)   #value error if no such value available
                    result = self[key]["_enumeration_default.value"][keypos]
                    default_result = True   #flag that it must be extended
                result = self.change_type(key,result)
                print("Indexed on {} to get {} for {}".format(def_index_val,repr(result),repr(val_to_index)))

            # Or else find any default functions
            else:
                def_func = [f[1] for f in self[key].get("_method.py_expression",[]) if f[0] == "_enumeration.default"]
                if len(def_func) == 1:
                    print('Executing default function for {}:'.format(key))
                    #print(one_func)
                    exec(def_func[0], globals())  #will access dREL functions, puts "pyfunc" in scope
                    # print('in following global environment: ' + repr(global_table))
                    stored_setting = cifdata.provide_value
                    cifdata.provide_value = True
                    try:
                        result = pyfunc(cifdata)
                    except CifRecursionError as s:
                        print(s)
                        result = None
                    except StarFile.StarDerivationError as s:
                        print(s)
                        result = None
                    finally:
                        cifdata.provide_value = stored_setting

        # read it in
        if result is None:   #can't do anything else
            print('Warning: no way of deriving item {}, allow_defaults is {}'.format(key,repr(allow_defaults)))
            raise StarFile.StarDerivationError(start_key)
        # Adjusting our calculated value. If we have used a default value or we have None, we
        # need to make the dimension match the currently-existing length of the category.
        #                                                                         
        #                                                                         
        # <Adjust value to be appropriate length>=                                
        is_looped = False
        if self[the_category].get('_definition.class','Set')=='Loop':
            is_looped = True
            if len(has_cat_names)>0:   #this category already exists
                if result is None or default_result: #need to create a list of values
                    loop_len = len(cifdata[has_cat_names[0]])
                    out_result = [result]*loop_len
                    result = out_result
            else:   #nothing exists in this category, we can't store this at all
                print('Resetting result {} for {} to null list as category is empty'.format(key,result))
                result = []

        # now try to insert the new information into the right place
        # find if items of this category already appear...
        # Never cache empty values
        if not (isinstance(result,list) and len(result)==0) and\
          store_value:
            if self[key].get("_definition.scope","Item")=='Item':
                if is_looped:
                    result = self.store_new_looped_value(key,cifdata,result,default_result)
                else:
                    result = self.store_new_unlooped_value(key,cifdata,result)
            else:
                self.store_new_cat_values(cifdata,result,the_category)
        return result

    # Storing a dREL-derived value back into our CifFile.  The dREL value (or potentially
    # a simple default value) may correspond to an entire column, or even an entire loop
    # for category methods.  We have to distinguish between list values that are StarLists,
    # that is, a single CIF value, and list values that correspond to a column of a loop.
    # Additionally, testing has revealed that we cannot judge the type of elements in a list
    # by the first element (e.g. could be a plain list, then a numpy array).  
    #                                                                         
    # The [[conv_from_numpy]] mini-functions are designed to handle arbitrary numpy arrays
    # quickly.                                                                
    #                                                                         
    #                                                                         
    # <Storing a dREL-derived value>=                                         
    def store_new_looped_value(self,key,cifdata,result,default_result):
          """Store a looped value from the dREL system into a CifFile"""
          # try to change any matrices etc. to lists
          the_category = self[key]["_name.category_id"]
          out_result = result
          if result is not None and not default_result:
                  # find any numpy arrays
                  def conv_from_numpy(one_elem):
                      if not hasattr(one_elem,'dtype'):
                         if isinstance(one_elem,(list,tuple)):
                            return StarFile.StarList([conv_from_numpy(a) for a in one_elem])
                         return one_elem
                      if one_elem.size > 1:   #so is not a float
                         return StarFile.StarList([conv_from_numpy(a) for a in one_elem.tolist()])
                      else:
                          try:
                            return one_elem.item(0)
                          except:
                            return one_elem
                  out_result = [conv_from_numpy(a) for a in result]
          # so out_result now contains a value suitable for storage
          cat_names = [a for a in self.keys() if self[a].get("_name.category_id",None)==the_category]
          has_cat_names = [a for a in cat_names if a in cifdata]
          print('Adding {}, found pre-existing names: '.format(key) + repr(has_cat_names))
          if len(has_cat_names)>0:   #this category already exists
              cifdata[key] = out_result      #lengths must match or else!!
              cifdata.AddLoopName(has_cat_names[0],key)
          else:
              cifdata[key] = out_result
              cifdata.CreateLoop([key])
          print('Loop info:' + repr(cifdata.loops))
          return out_result

    def store_new_unlooped_value(self,key,cifdata,result):
          """Store a single value from the dREL system"""
          if result is not None and hasattr(result,'dtype'):
              if result.size > 1:
                  out_result = StarFile.StarList(result.tolist())
                  cifdata[key] = out_result
              else:
                  cifdata[key] = result.item(0)
          else:
              cifdata[key] = result
          return result

    # Constructing categories using DDLm attributes. We have defined local    
    # attributes that describe category construction using mathematical       
    # 'pullbacks'.  We can use these to fill a category, but also to populate 
    # a category if the pullback category is available. We use [[list]] to coerce
    # all values to a list in case we are passed a numpy array, which does not
    # have an 'index' method.                                                 
    #                                                                         
    #                                                                         
    # <Construct a category>=                                                 
    def construct_category(self,category,cifdata,store_value=True):
        """Construct a category using DDLm attributes"""
        con_type = self[category].get('_category_construct_local.type',None)
        if con_type == None:
            return {}
        if con_type == 'Pullback' or con_type == 'Filter':
            morphisms  = self[category]['_category_construct_local.components']
            morph_values = [cifdata[a] for a in morphisms] # the mapped values for each cat
            cats = [self[a]['_name.category_id'] for a in morphisms]
            cat_keys = [self[a]['_category.key_id'] for a in cats]
            cat_values = [list(cifdata[a]) for a in cat_keys] #the category key values for each cat
            if con_type == 'Filter':
                int_filter = self[category].get('_category_construct_local.integer_filter',None)
                text_filter = self[category].get('_category_construct_local.text_filter',None)
                if int_filter is not None:
                    morph_values.append([int(a) for a in int_filter])
                if text_filter is not None:
                    morph_values.append(text_filter)
                cat_values.append(range(len(morph_values[-1])))
            # create the mathematical product filtered by equality of dataname values
            pullback_ids = [(x,y) for x in cat_values[0] for y in cat_values[1] \
                            if morph_values[0][cat_values[0].index(x)]==morph_values[1][cat_values[1].index(y)]]
            # now prepare for return
            if len(pullback_ids)==0:
                return {}
            newids = self[category]['_category_construct_local.new_ids']
            fullnewids = [self.cat_obj_lookup_table[(category,n)][0] for n in newids]
            if con_type == 'Pullback':
                final_results = {fullnewids[0]:[x[0] for x in pullback_ids],fullnewids[1]:[x[1] for x in pullback_ids]}
                final_results.update(self.duplicate_datanames(cifdata,cats[0],category,key_vals = final_results[fullnewids[0]],skip_names=newids))
                final_results.update(self.duplicate_datanames(cifdata,cats[1],category,key_vals = final_results[fullnewids[1]],skip_names=newids))
            elif con_type == 'Filter':   #simple filter
                final_results = {fullnewids[0]:[x[0] for x in pullback_ids]}
                final_results.update(self.duplicate_datanames(cifdata,cats[0],category,key_vals = final_results[fullnewids[0]],skip_names=newids))
            if store_value:
                self.store_new_cat_values(cifdata,final_results,category)
            return final_results

    # Going the other way. If we have the pulled-back category, we can populate the
    # pulled-from categories with their identifier items using projections from the
    # pulled-back category.  In the special case that we have a pullback that uses
    # a filter function with a single element, we can automatically populate the
    # whole commutative square.  We also by default populate identically-named
    # datanames.                                                              
    #                                                                         
    # The projection datanames are given in _category_construct_local.new_ids, and they always
    # map to the key of the projected-to category.                            
    #                                                                         
    #                                                                         
    # <Insert category items from pullback information>=                      
    def push_from_pullback(self,target_category,source_categories,cifdata,store_value=True):
        """Each of the categories in source_categories are pullbacks that include
        the target_category"""
        target_key = self[target_category]['_category.key_id']
        result = {target_key:[]}
        first_time = True
        # for each source category, determine which element goes to the target
        for sc in source_categories:
            components = self[sc]['_category_construct_local.components']
            comp_cats = [self[c]['_name.category_id'] for c in components]
            new_ids = self[sc]['_category_construct_local.new_ids']
            source_ids = [self.cat_obj_lookup_table[(sc,n)][0] for n in new_ids]
            if len(components) == 2:  # not a filter
                element_pos = comp_cats.index(target_category)
                old_id = source_ids[element_pos]
                print('Using {} to populate {}'.format(old_id,target_key))
                result[target_key].extend(cifdata[old_id])
                # project through all identical names
                extra_result = self.duplicate_datanames(cifdata,sc,target_category,skip_names=new_ids+[target_key])
                # we only include keys that are common to all categories
                if first_time:
                    result.update(extra_result)
                else:
                    for k in extra_result.keys():
                        if k in result:
                            print('Updating {}: was {}'.format(k,repr(result[k])))
                            result[k].extend(extra_result[k])
            else:
                extra_result = self.duplicate_datanames(cifdata,sc,target_category,skip_names=new_ids)
                if len(extra_result)>0 or source_ids[0] in cifdata:  #something is present
                    result[target_key].extend(cifdata[source_ids[0]])
                    for k in extra_result.keys():
                        if k in result:
                            print('Reverse filter: Updating {}: was {}'.format(k,repr(result[k])))
                            result[k].extend(extra_result[k])
                        else:
                            result[k]=extra_result[k]
    # Bonus derivation if there is a singleton filter
                    if self[sc]['_category_construct_local.type'] == 'Filter':
                        int_filter = self[sc].get('_category_construct_local.integer_filter',None)
                        text_filter = self[sc].get('_category_construct_local.text_filter',None)
                        if int_filter is not None:
                            filter_values = int_filter
                        else:
                            filter_values = text_filter
                        if len(filter_values)==1:    #a singleton
                            extra_dataname = self[sc]['_category_construct_local.components'][0]
                            if int_filter is not None:
                                new_value = [int(filter_values[0])] * len(cifdata[source_ids[0]])
                            else:
                                new_value = filter_values * len(cifdata[source_ids[0]])
                            if extra_dataname not in result:
                                result[extra_dataname] = new_value
                            else:
                                result[extra_dataname].extend(new_value)
                    else:
                        raise ValueError('Unexpected category construct type' + self[sc]['_category_construct_local.type'])
            first_time = False
        # check for sanity - all dataname lengths must be identical
        datalen = len(set([len(a) for a in result.values()]))
        if datalen != 1:
            raise AssertionError('Failed to construct equal-length category items,'+ repr(result))
        if store_value:
            print('Now storing ' + repr(result))
            self.store_new_cat_values(cifdata,result,target_category)
        return result

    def duplicate_datanames(self,cifdata,from_category,to_category,key_vals=None,skip_names=[]):
        """Copy across datanames for which the from_category key equals [[key_vals]]"""
        result = {}
        s_names_in_cat = set(self.names_in_cat(from_category,names_only=True))
        t_names_in_cat = set(self.names_in_cat(to_category,names_only=True))
        can_project = s_names_in_cat & t_names_in_cat
        can_project -= set(skip_names)  #already dealt with
        source_key = self[from_category]['_category.key_id']
        print('Source dataname set: ' + repr(s_names_in_cat))
        print('Target dataname set: ' + repr(t_names_in_cat))
        print('Projecting through following datanames from {} to {}'.format(from_category,to_category) + repr(can_project))
        for project_name in can_project:
            full_from_name = self.cat_obj_lookup_table[(from_category.lower(),project_name.lower())][0]
            full_to_name = self.cat_obj_lookup_table[(to_category.lower(),project_name.lower())][0]
            if key_vals is None:
                try:
                    result[full_to_name] = cifdata[full_from_name]
                except StarFile.StarDerivationError:
                    pass
            else:
                all_key_vals = cifdata[source_key]
                filter_pos = [all_key_vals.index(a) for a in key_vals]
                try:
                    all_data_vals = cifdata[full_from_name]
                except StarFile.StarDerivationError:
                    pass
                result[full_to_name] = [all_data_vals[i] for i in filter_pos]
        return result

    # Storing category results.  dREL allows 'category methods', which initialise an entire
    # category.  The dREL system that we have written returns a dictionary of lists, with the
    # dictionary keys being item names.  It is sufficient for us to extract each of these names
    # and pass them to our normal storage routine. If some of the values in the category key
    # are duplicated, we bail, as we may overwrite previous values.  We also bail if we
    # do not have exactly the same datanames available, as we are too lazy to insert 'unknown'
    # in the non-matching positions.                                          
    #                                                                         
    #                                                                         
    # <Storing a whole new dREL-derived category>=                            
    def store_new_cat_values(self,cifdata,result,the_category):
        """Store the values in [[result]] into [[cifdata]]"""
        the_key = [a for a in result.keys() if self[a].get('_type.purpose','')=='Key']
        double_names = [a for a in result.keys() if a in cifdata]
        if len(double_names)>0:
            already_present = [a for a in self.names_in_cat(the_category) if a in cifdata]
            if set(already_present) != set(result.keys()):
                print("Category {} not updated, mismatched datanames: {}".format(the_category, repr(set(already_present)^set(result.keys()))))
                return
            #check key values
            old_keys = set(cifdata[the_key])
            common_keys = old_keys & set(result[the_key])
            if len(common_keys)>0:
                print("Category {} not updated, key values in common:".format(common_keys))
                return
            #extend result values with old values
            for one_name,one_value in result.items():
                result[one_name].extend(cifdata[one_name])
        for one_name, one_value in result.items():
            try:
                self.store_new_looped_value(one_name,cifdata,one_value,False)
            except StarFile.StarError:
                print('{}: Not replacing {} with calculated {}'.format(one_name,repr(cifdata[one_name]),repr(one_value)))
        #put the key as the first item
        print('Fixing item order for {}'.format(repr(the_key)))
        for one_key in the_key:  #should only be one
            cifdata.ChangeItemOrder(one_key,0)


    # If a key is missing, we may sometimes fill in default values for it, for example,
    # a missing atom type may be assumed to have a number in cell of 0.       
    #                                                                         
    #                                                                         
    # <Generating default packets>=                                           
    def generate_default_packet(self,catname,catkey,keyvalue):
        """Return a StarPacket with items from ``catname`` and a key value
        of ``keyvalue``"""
        newpack = StarPacket()
        for na in self.names_in_cat(catname):
            def_val = self[na].get("_enumeration.default","")
            if def_val:
                final_val = self.change_type(na,def_val)
                newpack.extend(final_val)
                setattr(newpack,na,final_val)
        if len(newpack)>0:
            newpack.extend(keyvalue)
            setattr(newpack,catkey,keyvalue)
        return newpack


    # In the single case of executing dREL methods, we wish to return numpy   
    # Arrays from our __getitem__ so that the mathematical operations proceed 
    # as expected for matrix etc. objects. This needs to be reimplimented:    
    # currently numpy must be installed for 'numerification' to work.         
    #                                                                         
    #                                                                         
    # <Switch on numpy arrays>=                                               
    def switch_numpy(self,to_val):
        pass

    # This function converts the string-valued items returned from the parser into
    # types that correspond to the dictionary specifications.  For DDLm it must also
    # deal with potentially complex structures containing both strings and numbers. We
    # have tried to avoid introducing a dependence on Numpy in general for PyCIFRW,
    # but once we get into the realm of DDLm we require Numpy arrays in order to
    # handle the various processing tasks.  This routine is the one that will 
    # create the arrays from the StarList types, so needs access to numpy.  However,
    # this routine is only called if a DDLm dictionary has been provided, so we
    # should still have no Numpy dependence for non DDLm cases                
    #                                                                         
    # For safety, we check that our object is really string-valued.  In practice,
    # this means that it is either a string, a list of strings, or a list of  
    # StarLists as these are the only datastructures that an as-parsed file will
    # contain.                                                                
    #                                                                         
    #                                                                         
    # <Convert string to appropriate type>=                                   
    def change_type(self,itemname,inval):
        if inval == "?": return inval
        change_function = convert_type(self[itemname])
        if isinstance(inval,list) and not isinstance(inval,StarFile.StarList):   #from a loop
            newval = list([change_function(a) for a in inval])
        else:
            newval = change_function(inval)
        return newval

    # \section{Validation}                                                    
    #                                                                         
    # A DDL provides lots of information that can be used to check a datafile or dictionary
    # for consistency.  Currently, the DDL-appropriate routines are installed at initialisation
    # time.                                                                   
    #                                                                         
    #                                                                         
    # <Validation routines>=                                                  
    # Each dictionary has a set of validation functions associated with it based
    # on the information contained in the DDL. The following function is called
    # on initialisation.                                                      
    #                                                                         
    #                                                                         
    # <Install validation functions>=                                         
    def install_validation_functions(self):
        """Install the DDL-appropriate validation checks"""
        if self.diclang != 'DDLm':
            # functions which check conformance
            self.item_validation_funs = [
                self.validate_item_type,
                self.validate_item_esd,
                self.validate_item_enum,
                self.validate_enum_range,
                self.validate_looping
            ]
            # functions checking loop values
            self.loop_validation_funs = [
                self.validate_loop_membership,
                self.validate_loop_key,
                self.validate_loop_references
            ]

            # Ensure that loop id tags are unique, more functions may be added
            # in the future
            self.loop_id_uniqueness_funs = [
                self.validate_loop_key_uniqueness
            ]

            # where we need to look at other values
            self.global_validation_funs = [
                self.validate_exclusion,
                self.validate_parent,
                self.validate_child,
                self.validate_dependents,
                self.validate_uniqueness
            ]
            # where only a full block will do
            self.block_validation_funs = [
                self.validate_mandatory_category
            ]
            # removal is quicker with special checks
            self.global_remove_validation_funs = [
                self.validate_remove_parent_child
            ]
        elif self.diclang == 'DDLm':
            self.item_validation_funs = [
                self.validate_item_enum,
                self.validate_item_esd_ddlm,
                ]
            self.loop_validation_funs = [
                self.validate_looping_ddlm,
                self.validate_loop_key_ddlm,
                self.validate_loop_membership
                ]
            self.loop_id_uniqueness_funs = [
                self.validate_loop_key_uniqueness_ddlm
            ]
            self.global_validation_funs = []
            self.block_validation_funs = [
                self.check_mandatory_items,
                self.check_prohibited_items
                ]
            self.global_remove_validation_funs = []
        self.optimize = False        # default value
        self.done_parents = []
        self.done_children = []
        self.done_keys = []

    # Some things are independent of where an item occurs in the file; we     
    # check those things here.  All functions are expected to return a        
    # dictionary with at least one key: "result", as well as optional         
    # keys depending on the type of error.                                    
    #                                                                         
    #                                                                         
    # <Item-level validation>=                                                
    # Validate the type of an item                                            
    #                                                                         
    # We use the expressions for type that we have available to check that    
    # the type of the item passed to us matches up.  We may have a list of    
    # items, so be aware of that.  We define a tiny matching function so      
    # that we do not have to do a double match to catch the non-matching      
    # case, which returns None and thus an attribute error if we immediately  
    # try to get a group.                                                     
    #                                                                         
    # Note also that none of the extant dictionaries use the 'none' or 'seq'  
    # values for type.  The seq value in particular would complicate matters. 
    #                                                                         
    #                                                                         
    # <Validate the type of an item (DDL1/2)>=                                
    def validate_item_type(self,item_name,item_value):
        def mymatch(m,a):
            res = m.match(a)
            if res != None: return res.group()
            else: return ""
        target_type = self[item_name].get(self.type_spec)
        if target_type == None:          # e.g. a category definition
            return {"result":True}                  # not restricted in any way
        matchexpr = self.typedic[target_type]
        item_values = listify(item_value)
        #for item in item_values:
            #print("Type match " + item_name + " " + item + ":",)
        #skip dots and question marks
        check_all = [a for a in item_values if a !="." and a != "?"]
        check_all = [a for a in check_all if mymatch(matchexpr,a) != a]
        if len(check_all)>0: return {"result":False,"bad_values":check_all}
        else: return {"result":True}

    # DDLm types are far more nuanced, and we are not provided with prepacked 
    # regular expressions in order to check them.  We have identified the following
    # checks: that the type is in the correct container; that the contents are as
    # described in _type.contents; that 'State' purpose datanames have a list of
    # enumerated states; that 'Link' purpose datanames have '_name.linked_item_id'
    # in the same definition; that 'SU' purpose datanames also has the above. 
    #                                                                         
    #                                                                         
    # <Validate the type of an item (DDLm)>=                                  
    def decide(self,result_list):
        """Construct the return list"""
        if len(result_list)==0:
               return {"result":True}
        else:
               return {"result":False,"bad_values":result_list}

    def validate_item_container(self, item_name,item_value):
        container_type = self[item_name]['_type.container']
        item_values = listify(item_value)
        if container_type == 'Single':
           okcheck = [a for a in item_values if not isinstance(a,(int,float,long,unicode))]
           return self.decide(okcheck)
        if container_type in ('Multiple','List'):
           okcheck = [a for a in item_values if not isinstance(a,StarList)]
           return self.decide(okcheck)
        if container_type == 'Array':    #A list with numerical values
           okcheck = [a for a in item_values if not isinstance(a,StarList)]
           first_check = self.decide(okcheck)
           if not first_check['result']: return first_check
           #num_check = [a for a in item_values if len([b for b in a if not isinstance

    # Esds.  Numbers are sometimes not allowed to have esds appended.  The    
    # default is that esds are not OK, and we should also skip anything that  
    # has character type, as that is automatically not a candidate for esds.  
    #                                                                         
    # Note that we make use of the primitive type here; there are some        
    # cases where a string type looks like an esd, so unless we know          
    # we have a number we ignore these cases.                                 
    #                                                                         
    # DDLm requires an esd if _type.purpose is Measurand, and should not have an
    # esd if _type.purpose is Number.                                         
    #                                                                         
    #                                                                         
    # <Validate esd presence>=                                                
    def validate_item_esd(self,item_name,item_value):
        if self[item_name].get(self.primitive_type) != 'numb':
            return {"result":None}
        can_esd = self[item_name].get(self.esd_spec,"none") == "esd"
        if can_esd: return {"result":True}         #must be OK!
        item_values = listify(item_value)
        check_all = list([a for a in item_values if get_number_with_esd(a)[1] != None])
        if len(check_all)>0: return {"result":False,"bad_values":check_all}
        return {"result":True}

    def validate_item_esd_ddlm(self,item_name,item_value):
        if self[item_name].get('self.primitive_type') not in \
        ['Count','Index','Integer','Real','Imag','Complex','Binary','Hexadecimal','Octal']:
            return {"result":None}
        can_esd = True
        if self[item_name].get('_type.purpose') != 'Measurand':
            can_esd = False
        item_values = listify(item_value)
        check_all = [get_number_with_esd(a)[1] for a in item_values]
        check_all = [v for v in check_all if (can_esd and v == None) or \
                 (not can_esd and v != None)]
        if len(check_all)>0: return {"result":False,"bad_values":check_all}
        return {"result":True}

    # Enumeration ranges.  Our dictionary has been prepared as for a DDL2     
    # dictionary, where loops are used to specify closed or open ranges: if   
    # an entry exists where maximum and minimum values are equal, this means  
    # that this value is included in the range; otherwise, ranges are open.   
    # Our value is already numerical.                                         
    #                                                                         
    #                                                                         
    # <Validate enumeration range>=                                           
    def validate_enum_range(self,item_name,item_value):
        if "_item_range.minimum" not in self[item_name] and \
           "_item_range.maximum" not in self[item_name]:
            return {"result":None}
        minvals = self[item_name].get("_item_range.minimum",default = ["."])
        maxvals = self[item_name].get("_item_range.maximum",default = ["."])
        def makefloat(a):
            if a == ".": return a
            else: return float(a)
        maxvals = map(makefloat, maxvals)
        minvals = map(makefloat, minvals)
        rangelist = list(zip(minvals,maxvals))
        item_values = listify(item_value)
        def map_check(rangelist,item_value):
            if item_value == "?" or item_value == ".": return True
            iv,esd = get_number_with_esd(item_value)
            if iv==None: return None  #shouldn't happen as is numb type
            for lower,upper in rangelist:
                #check the minima
                if lower == ".": lower = iv - 1
                if upper == ".": upper = iv + 1
                if iv > lower and iv < upper: return True
                if upper == lower and iv == upper: return True
            # debug
            # print("Value %s fails range check %d < x < %d" % (item_value,lower,upper))
            return False
        check_all = [a for a in item_values if map_check(rangelist,a) != True]
        if len(check_all)>0: return {"result":False,"bad_values":check_all}
        else: return {"result":True}

    # Note that we must make a copy of the enum list, otherwise when we       
    # add in our ? and . they will modify the Cif in place, very sneakily,    
    # and next time we have a loop length check, e.g. in writing out, we      
    # will probably have a mismatch.                                          
    #                                                                         
    #                                                                         
    # <Validate an enumeration>=                                              
    def validate_item_enum(self,item_name,item_value):
        try:
            enum_list = self[item_name][self.enum_spec][:]
        except KeyError:
            return {"result":None}
        enum_list = [value.lower() for value in enum_list]
        enum_list.append(".")   #default value
        enum_list.append("?")   #unknown
        item_values = listify(item_value)
        #print("Enum check: {!r} in {!r}".format(item_values, enum_list))
        check_all = [a for a in item_values if a.lower() not in enum_list]
        if len(check_all)>0: return {"result":False,"bad_values":check_all}
        else: return {"result":True}

    # Check that something can be looped.  For DDL1 we have yes, no and both, 
    # For DDL2 there is no explicit restriction on looping beyond membership in
    # a category.  Note that the DDL1 language specifies a default value of 'no'
    # for this item,  so when not explicitly allowed by the dictionary, listing
    # is prohibited.  In DDLm, only members of 'Loop' categories allow looping.
    # As we transition the whole setup to DDLm-type data structures, the two  
    # calls below will merge and move to the looping checks rather than the single item
    # checks.                                                                 
    #                                                                         
    #                                                                         
    # <Validate looping properties>=                                          
    def validate_looping(self,item_name,item_value):
        try:
            must_loop = self[item_name][self.must_loop_spec]
        except KeyError:
            return {"result":None}
        if must_loop == 'yes' and isinstance(item_value,(unicode,str)): # not looped
            return {"result":False}      #this could be triggered
        if must_loop == 'no' and not isinstance(item_value,(unicode,str)):
            return {"result":False}
        return {"result":True}

    def validate_looping_ddlm(self,loop_names):
        """Check that all names are loopable"""
        truly_loopy = self.get_final_cats(loop_names)
        if len(truly_loopy)<len(loop_names):  #some are bad
            categories = [(a,self[a][self.cat_spec].lower()) for a in loop_names]
            not_looped = [a[0] for a in categories if a[1] not in self.parent_lookup.keys()]
            return {"result":False,"bad_items":not_looped}
        return {"result":True}


    # And some things are related to the group structure.  Note that these    
    # functions do not require knowledge of the item values.                  
    #                                                                         
    #                                                                         
    # <Loop-level validation>=                                                
    # Loop membership.                                                        
    # The most common constraints on a loop are that all items are from the same
    # category, and that loops of a certain category must contain a certain key to
    # be valid.  The latter test should be performed after the former test.   
    #                                                                         
    # DDLm allows nested loop categories, so an item from a child category can appear
    # in a parent category loop if both are from 'Loop' categories.           
    #                                                                         
    #                                                                         
    # <Validate loop membership>=                                             
    def validate_loop_membership(self,loop_names):
        final_cat = self.get_final_cats(loop_names)
        bad_items =  [a for a in final_cat if a != final_cat[0]]
        if len(bad_items)>0:
            return {"result":False,"bad_items":bad_items}
        else: return {"result":True}

    def get_final_cats(self,loop_names):
        """Return a list of the uppermost parent categories for the loop_names. Names
        that are not from loopable categories are ignored."""
        try:
            categories = [self[a][self.cat_spec].lower() for a in loop_names]
        except KeyError:       #category_id is mandatory
            raise ValidCifError( "{} missing from dictionary {} for item in loop containing {}".format(self.cat_spec,self.dicname,loop_names[0]))
        truly_looped = [a for a in categories if a in self.parent_lookup.keys()]
        return [self.parent_lookup[a] for a in truly_looped]

    # The items specified by [[_list_mandatory]] (DDL1) must be present in a loop
    # containing items of a given category (and it follows that only one loop 
    # in a given data block is available for any category containing such an  
    # item).  This has been explicitly described as a key in DDL2. In DDLm, any
    # key from a parent looped category is acceptable as well as the key of   
    # the given category itself.                                              
    #                                                                         
    #                                                                         
    # <Validate loop key>=                                                    
    def validate_loop_key(self,loop_names):
        category = self[loop_names[0]][self.cat_spec]
        # find any unique values which must be present
        key_spec = self[category].get(self.key_spec,[])
        for names_to_check in key_spec:
            if isinstance(names_to_check,unicode):   #only one
                names_to_check = [names_to_check]
            for loop_key in names_to_check:
                if loop_key not in loop_names:
                    #is this one of those dang implicit items?
                    if self[loop_key].get(self.must_exist_spec,None) == "implicit":
                        continue          #it is virtually there...
                    alternates = self.get_alternates(loop_key)
                    if alternates == []:
                        return {"result":False,"bad_items":loop_key}
                    for alt_names in alternates:
                        alt = [a for a in alt_names if a in loop_names]
                        if len(alt) == 0:
                            return {"result":False,"bad_items":loop_key}  # no alternates
        return {"result":True}

    #  Validating keys in DDLm. We move everything to the uppermost parent category, and
    # then lookup what keys can be used. If any of these are present, we are happy.  This
    # might miss some subtleties in mixed or unmixed loops?                   
    #                                                                         
    #                                                                         
    # <Validate loop key DDLm>=                                               
    def validate_loop_key_uniqueness(self, loop_names, block):
        '''
        Function to validate if the id tags of a loop are unique. Function for the DDL1 dictionaries.
        Tags that have a category in self.black_list_categories are ignored.
        '''

        loop_names_to_check = []
        for loop_name in loop_names:
            # Get the _list_mandatory tag value (empty if the loop does not have it)
            list_mandatory = self[loop_name].get(self.must_exist_spec, "")

            # Get the tag's category to check if has to be avoided or not
            category = self[loop_name].get(self.cat_spec, "")

            # Check if the tag actually is mandatory
            list_mandatory = list_mandatory == 'yes'

            # Only check the categories that ARE NOT in self.black_list_categories
            if list_mandatory and category not in self.black_list_categories:
                loop_names_to_check.append(loop_name)

        # No loop ids to check, the loop is valid
        if not loop_names_to_check:
            return {"result": True}

        # Group the tag values by the number of ids in the loop
        if len(loop_names_to_check) > 1:
            values_list = [block[loop_name] for loop_name in loop_names_to_check]
            values = list(zip(*values_list))

        else:
            loop_name = loop_names_to_check[0]

            values = block[loop_name]

        # The set only allows unique values
        set_values = set(values)

        # If the lengths are different, it means that there are repeated values
        if len(values) != len(set_values):
            repeated_values = [item for item, count in collections.Counter(values).items() if count > 1]
            return {"result":False, "bad_items":repeated_values}

        return {"result":True}

    def validate_loop_key_uniqueness_ddlm(self, loop_names, block):
        '''
        Function to validate if the id tags of a loop are unique. Function for the DDLm dictionaries.
        Tags that have a category in self.black_list_categories are ignored.
        '''
        # Get the final categories
        final_cats = self.get_final_cats(loop_names)

        # Get the category ids
        cat_keys = []
        for cat in final_cats:
            temp_cat_key = self[cat].get(self.unique_spec, "")
            if temp_cat_key not in cat_keys:
                cat_keys.append(temp_cat_key)

        # Only take into account the loop ids from our loop tags
        loop_names_to_check = [loop_name for loop_name in loop_names if loop_name in cat_keys]

        # There are no tags to check
        if not loop_names_to_check:
            return {"result":True}

        # Group the tag values by the number of ids in the group
        if len(loop_names_to_check) > 1:
            values_list = [block[loop_name] for loop_name in loop_names_to_check]
            values = list(zip(*values_list))

        else:
            loop_name = loop_names_to_check[0]
            values = block[loop_name]

        # The set only allows unique values
        set_values = set(values)

        # If the lengths are different, it means that there are repeated values
        if len(values) != len(set_values):
            repeated_values = [item for item, count in collections.Counter(values).items() if count > 1]
            return {"result":False, "bad_items":repeated_values}

        return {"result":True}

    def validate_loop_key_ddlm(self, loop_names):
        '''
        New version of the validation of the loop keys for the DDLm dictionaries.
        It checks if the _category_key.name of a given looped category appears.
        '''

        # Get the parent categories of the input loop names
        temp_final_cats = self.get_final_cats(loop_names)
        final_cats = [final_cat for final_cat in temp_final_cats if final_cat not in self.black_list_categories]

        if not final_cats:
            return {"result":True}

        poss_keys = self.cat_key_table[final_cats[0]]

        poss_keys_set = set()

        # As we want to validate CIF1.0 against DDLm dictionaries,
        # we have to take into account that the category keys may have
        # alias.
        # The input loop tags may also be CIF1.0 tags.
        # Retrieve those alias to make a more complete validation
        for poss_key in poss_keys:
            for temp in poss_key:
                if temp is None: continue
                key = temp
                key_alias = self[key].get(self.alias_spec, [])

                poss_keys_set.add(key.lower())

                if isinstance(key_alias, list):
                    for alias in key_alias:
                        poss_keys_set.add(alias.lower())

                else:
                    poss_keys_set.add(key_alias.lower())

        # If one of the tags exists, the loop is valid
        for loop_name in loop_names:
            if loop_name.lower() in poss_keys_set:
                return {"result":True}

        return {"result":False, "bad_items":poss_keys_set}

    # The [[_list_reference]] value specifies data names which must co-occur with the
    # defined data name.  We check that this is indeed the case for all items in the
    # loop.  We trace through alternate values as well.  In DDL1 dictionaries, a
    # name terminating with an underscore indicates that any(?) corresponding name
    # is suitable.                                                            
    #                                                                         
    #                                                                         
    # <Validate loop mandatory items>=                                        
        # Get the category keys

    def validate_loop_references(self,loop_names):
        must_haves = [self[a].get(self.list_ref_spec,None) for a in loop_names]
        must_haves = [a for a in must_haves if a != None]
        # build a flat list.  For efficiency we don't remove duplicates,as
        # we expect no more than the order of 10 or 20 looped names.
        def flat_func(a,b):
            if isinstance(b,unicode):
               a.append(b.lower())       #single name
            else:
               a.extend([a.lower() for a in b])       #list of names
            return a
        flat_mh = []
        [flat_func(flat_mh,a) for a in must_haves]
        group_mh = list(filter(lambda a:a[-1]=="_",flat_mh))
        single_mh = list(filter(lambda a:a[-1]!="_",flat_mh))
        res = [a for a in single_mh if a not in loop_names]
        def check_gr(s_item, name_list):
            nl = map(lambda a:a[:len(s_item)],name_list)
            if s_item in nl: return True
            return False
        res_g = [a for a in group_mh if check_gr(a,loop_names)]
        if len(res) == 0 and len(res_g) == 0: return {"result":True}
        # construct alternate list
        alternates = [(a,self.get_alternates(a)) for a in res]
        real_alternates = [a for a in alternates if len(a[1]) != 0]
        # next line purely for error reporting
        missing_alts = [a[0] for a in alternates if len(a[1]) == 0]
        if len(real_alternates) != len(res):
           return {"result":False,"bad_items":set(missing_alts)}   #short cut; at least one
                                                       #doesn't have an altern
        #loop over alternates
        for orig_name,alt_names in alternates:
             alt = [a for a in alt_names if a in loop_names]
             if len(alt) == 0: return {"result":False,"bad_items":orig_name}# no alternates
        return {"result":True}        #found alternates

    # A utility function to return a list of alternate names given a main name.
    # In DDL2 we have to deal with aliases.  Each aliased item appears in     
    # our normalised dictionary independently, so there is no need to resolve 
    # aliases when looking up a data name.  However, the original             
    # definition using DDL2-type names is simply copied to this aliased       
    # name during normalisation, so all references to other item names        
    # (e.g. _item_dependent) have to be resolved using the present function.  
    #                                                                         
    # These aliases are returned in any case, so if we had a data file        
    # which mixed DDL1 and DDL2 style names, it may turn out to be            
    # valid, and what's more, we wouldn't necessarily detect an error         
    # if a data name and its alias were present - need to ponder this.        
    #                                                                         
    # The exclusive_only option will only return items which must not         
    # co-exist with the item name in the same datablock.  This includes       
    # aliases, and allows us to do a check that items and their aliases       
    # are not present at the same time in a data file.                        
    #                                                                         
    #                                                                         
    # <Get alternative item names>=                                           
    def get_alternates(self,main_name,exclusive_only=False):
        if self.get(main_name, None) is None:
            return []
        alternates = self[main_name].get(self.related_func,None)
        alt_names = []
        if alternates != None:
            alt_names =  self[main_name].get(self.related_item,None)
            if isinstance(alt_names,unicode):
                alt_names = [alt_names]
                alternates = [alternates]
            together = zip(alt_names,alternates)
            if exclusive_only:
                alt_names = [a for a in together if a[1]=="alternate_exclusive" \
                                             or a[1]=="replace"]
            else:
                alt_names = [a for a in together if a[1]=="alternate" or a[1]=="replace"]
            alt_names = list([a[0] for a in alt_names])
        # now do the alias thing
        alias_names = listify(self[main_name].get("_item_aliases.alias_name",[]))
        alt_names.extend(alias_names)
        # print("Alternates for {}: {!r}".format(main_name, alt_names))
        return alt_names


    # Some checks require access to the entire data block.  These functions   
    # take both a provisional dictionary and a global dictionary; the         
    # provisional dictionary includes items which will go into the            
    # dictionary together with the current item, and the global               
    # dictionary includes items which apply to all data blocks (this is       
    # for validation of DDL1/2 dictionaries).                                 
    #                                                                         
    #                                                                         
    # <Cross-item validation>=                                                
    # DDL2 dictionaries introduce the "alternate exclusive" category for      
    # related items.  We also unilaterally include items listed in aliases    
    # as acting in this way.                                                  
    #                                                                         
    #                                                                         
    # <Validate exclusion rules>=                                             
    def validate_exclusion(self,item_name,item_value,whole_block,provisional_items={},globals={}):
       alternates = [a.lower() for a in self.get_alternates(item_name,exclusive_only=True)]
       item_name_list = [a.lower() for a in whole_block.keys()]
       item_name_list.extend([a.lower() for a in provisional_items.keys()])
       bad = [a for a in alternates if a in item_name_list]
       if len(bad)>0:
           if self.verbose_validation:
                print("Bad: {}, alternates {}".format(repr(bad),repr(alternates)))
           return {"result":False,"bad_items":bad}
       else: return {"result":True}

    # When validating parent/child relations, we check the parent link to the 
    # children, and separately check that parents exist for any children present.
    # Switching on optimisation will remove the redundancy in this procedure, but
    # only if no changes are made to the relevant data items between the two  
    # checks.                                                                 
    #                                                                         
    # It appears that DDL2 dictionaries allow parents to be absent if children
    # take only unspecified values (i.e. dot or question mark).  We catch this
    # case.                                                                   
    #                                                                         
    # The provisional items dictionary includes items that are going to be    
    # included with the present item  (in a single loop structure) so the     
    # philosophy of inclusion must be all or nothing.                         
    #                                                                         
    # When validating DDL2 dictionaries themselves, we are allowed access to  
    # other definition blocks in order to resolve parent-child pointers.      
    # We will be able to find                                                 
    # these save frames inside the globals dictionary (they will in this case 
    #  be collected inside a CifBlock object).                                
    #                                                                         
    # When removing, we look at the item to make sure that no child items require
    # it to be present.                                                       
    #                                                                         
    #                                                                         
    # <Validate parent child relations>=                                      
    # validate that parent exists and contains matching values
    def validate_parent(self,item_name,item_value,whole_block,provisional_items={},globals={}):
        parent_item = self[item_name].get(self.parent_spec)
        if not parent_item: return {"result":None}   #no parent specified
        if isinstance(parent_item,list):
            parent_item = parent_item[0]
        if self.optimize:
            if parent_item in self.done_parents:
                return {"result":None}
            else:
                self.done_parents.append(parent_item)
                print("Done parents {}".format(repr(self.done_parents)))
        # initialise parent/child values
        if isinstance(item_value,unicode):
            child_values = [item_value]
        else: child_values = item_value[:]    #copy for safety
        # track down the parent
        # print("Looking for {} parent item {} in {!r}".format(item_name, parent_item, whole_block))
        # if globals contains the parent values, we are doing a DDL2 dictionary, and so
        # we have collected all parent values into the global block - so no need to search
        # for them elsewhere.
        # print("Looking for {!r}".format(parent_item))
        parent_values = globals.get(parent_item)
        if not parent_values:
            parent_values = provisional_items.get(parent_item,whole_block.get(parent_item))
        if not parent_values:
            # go for alternates
            namespace = whole_block.keys()
            namespace.extend(provisional_items.keys())
            namespace.extend(globals.keys())
            alt_names = filter_present(self.get_alternates(parent_item),namespace)
            if len(alt_names) == 0:
                if len([a for a in child_values if a != "." and a != "?"])>0:
                    return {"result":False,"parent":parent_item}#no parent available -> error
                else:
                    return {"result":None}       #maybe True is more appropriate??
            parent_item = alt_names[0]           #should never be more than one??
            parent_values = provisional_items.get(parent_item,whole_block.get(parent_item))
            if not parent_values:   # check global block
                parent_values = globals.get(parent_item)
        if isinstance(parent_values,unicode):
            parent_values = [parent_values]
        #print("Checking parent %s against %s, values %r/%r" % (parent_item,
        #                                          item_name, parent_values, child_values))
        missing = self.check_parent_child(parent_values,child_values)
        if len(missing) > 0:
            return {"result":False,"bad_values":missing,"parent":parent_item}
        return {"result":True}

    def validate_child(self,item_name,item_value,whole_block,provisional_items={},globals={}):
        try:
            child_items = self[item_name][self.child_spec][:]  #copy
        except KeyError:
            return {"result":None}    #not relevant
        # special case for dictionaries  -> we check parents of children only
        if item_name in globals:  #dictionary so skip
            return {"result":None}
        if isinstance(child_items,unicode): # only one child
            child_items = [child_items]
        if isinstance(item_value,unicode): # single value
            parent_values = [item_value]
        else: parent_values = item_value[:]
        # expand child list with list of alternates
        for child_item in child_items[:]:
            child_items.extend(self.get_alternates(child_item))
        # now loop over the children
        for child_item in child_items:
            if self.optimize:
                if child_item in self.done_children:
                    return {"result":None}
                else:
                    self.done_children.append(child_item)
                    if self.verbose_validation:
                        print("Done children {}".format(repr(self.done_children)))
            if child_item in provisional_items:
                child_values = provisional_items[child_item][:]
            elif child_item in whole_block:
                child_values = whole_block[child_item][:]
            else:  continue
            if isinstance(child_values,unicode):
                child_values = [child_values]
                # print("Checking child %s against %s, values %r/%r" % (child_item,
                #       item_name, child_values, parent_values))
            missing = self.check_parent_child(parent_values,child_values)
            if len(missing)>0:
                return {"result":False,"bad_values":missing,"child":child_item}
        return {"result":True}       #could mean that no child items present

    #a generic checker: all child vals should appear in parent_vals
    def check_parent_child(self,parent_vals,child_vals):
        # shield ourselves from dots and question marks
        pv = parent_vals[:]
        pv.extend([".","?"])
        res =  [a for a in child_vals if a not in pv]
        #print("Missing: %s" % res)
        return res

    def validate_remove_parent_child(self,item_name,whole_block):
        try:
            child_items = self[item_name][self.child_spec]
        except KeyError:
            return {"result":None}
        if isinstance(child_items,unicode): # only one child
            child_items = [child_items]
        for child_item in child_items:
            if child_item in whole_block:
                return {"result":False,"child":child_item}
        return {"result":True}

    # The DDL2 [[_item_dependent]] attribute at first glance appears to be the
    # same as [[_list_reference]], however the dependent item does not have to appear
    # in a loop at all, and neither does the other item name.  Perhaps this   
    # behaviour was intended to be implied by having looped [[_names]] in DDL1
    # dictionaries, but we can't be sure and so don't implement this yet.     
    #                                                                         
    #                                                                         
    # <Validate presence of dependents>=                                      
    def validate_dependents(self,item_name,item_value,whole_block,prov={},globals={}):
        try:
            dep_items = self[item_name][self.dep_spec][:]
        except KeyError:
            return {"result":None}    #not relevant
        if isinstance(dep_items,unicode):
            dep_items = [dep_items]
        actual_names = whole_block.keys()
        actual_names.extend(prov.keys())
        actual_names.extend(globals.keys())
        missing = [a for a in dep_items if a not in actual_names]
        if len(missing) > 0:
            alternates = map(lambda a:[self.get_alternates(a),a],missing)
            # compact way to get a list of alternative items which are
            # present
            have_check = [(filter_present(b[0],actual_names),
                                       b[1]) for b in alternates]
            have_check = list([a for a in have_check if len(a[0])==0])
            if len(have_check) > 0:
                have_check = [a[1] for a in have_check]
                return {"result":False,"bad_items":have_check}
        return {"result":True}

    # The [[_list_uniqueness]] attribute permits specification of a single or 
    # multiple items which must have a unique combined value.  Currently it is only
    # used in the powder dictionary to indicate that peaks must have a unique 
    # index and in the core dictionary to indicate the a publication section name
    # with its label must be unique; however it would appear to implicitly apply
    # to any index-type value in any dictionary.  This is used precisely once 
    # in the cif_core dictionary in a non-intuitive manner, but we code for   
    # this here.  The value of the [[_list_uniqueness]] attribute can actually
    # refer to another data name, which together with the defined name must   
    # be unique.                                                              
    #                                                                         
    # DDL2 dictionaries do away with separate [[_list_mandatory]] and [[_list_uniqueness]]
    # attributes, instead using a [[_category_key]].  If multiple keys are specified,
    # they must be unique in combination, in accordance with standard relational
    # database behaviour.                                                     
    #                                                                         
    #                                                                         
    # <Validate list uniqueness>=                                             
    def validate_uniqueness(self,item_name,item_value,whole_block,provisional_items={},
                                                                  globals={}):
        category = self[item_name].get(self.cat_spec)
        if category == None:
            if self.verbose_validation:
                print("No category found for {}".format(item_name))
            return {"result":None}
        # print("Category {!r} for item {}".format(category, item_name))
        # we make a copy in the following as we will be removing stuff later!
        unique_i = self[category].get("_category_key.name",[])[:]
        if isinstance(unique_i,unicode):
            unique_i = [unique_i]
        if item_name not in unique_i:       #no need to verify
            return {"result":None}
        if isinstance(item_value,unicode):  #not looped
            return {"result":None}
        # print("Checking %s -> %s -> %s ->Unique: %r" % (item_name,category,catentry, unique_i))
        # check that we can't optimize by not doing this check
        if self.optimize:
            if unique_i in self.done_keys:
                return {"result":None}
            else:
                self.done_keys.append(unique_i)
        val_list = []
        # get the matching data from any other data items
        unique_i.remove(item_name)
        other_data = []
        if len(unique_i) > 0:            # i.e. do have others to think about
           for other_name in unique_i:
           # we look for the value first in the provisional dict, then the main block
           # the logic being that anything in the provisional dict overrides the
           # main block
               if other_name in provisional_items:
                   other_data.append(provisional_items[other_name])
               elif other_name in whole_block:
                   other_data.append(whole_block[other_name])
               elif self[other_name].get(self.must_exist_spec)=="implicit":
                   other_data.append([item_name]*len(item_value))  #placeholder
               else:
                   return {"result":False,"bad_items":other_name}#missing data name
        # ok, so we go through all of our values
        # this works by comparing lists of strings to one other, and
        # so could be fooled if you think that '1.' and '1' are
        # identical
        for i in range(len(item_value)):
            #print("Value no. %d" % i, end=" ")
            this_entry = item_value[i]
            for j in range(len(other_data)):
                this_entry = " ".join([this_entry,other_data[j][i]])
            #print("Looking for {!r} in {!r}: ".format(this_entry, val_list))
            if this_entry in val_list:
                return {"result":False,"bad_values":this_entry}
            val_list.append(this_entry)
        return {"result":True}


    # <Block-level validation>=                                               
    # DDL2 introduces a new idea, that of a mandatory category, items of      
    # which must be present.  We check only this particular fact, and         
    # leave the checks for mandatory items within the category, keys etc.     
    # to the relevant routines.  This would appear to be applicable to        
    # dictionaries only.                                                      
    #                                                                         
    # Also, although the natural meaning for a DDL2 dictionary would be that  
    # items from these categories must appear in every definition block, this is not what
    # happens in practice, as category definitions do not have anything from the
    # (mandatory) _item_description category.  We therefore adopt the supremely
    # useless meaning that mandatory categories in a dictionary context mean only
    # that somewhere, maybe in only one save frame, an item from this category
    # exists.  This interpretation is forced by using the "fake_mand" argument,
    # which then assumes that the alternative routine will be used to set the 
    # error information on a dictionary-wide basis.                           
    #                                                                         
    #                                                                         
    # <Validate category presence>=                                           
    def validate_mandatory_category(self,whole_block):
        mand_cats = [self[a]['_category.id'] for a in self.keys() if self[a].get("_category.mandatory_code","no")=="yes"]
        if len(mand_cats) == 0:
            return {"result":True}
        # print("Mandatory categories - {!r}".format(mand_cats)
        # find which categories each of our datanames belongs to
        all_cats = [self[a].get(self.cat_spec) for a in whole_block.keys()]
        missing = set(mand_cats) - set(all_cats)
        if len(missing) > 0:
            return {"result":False,"bad_items":repr(missing)}
        return {"result":True}

    #  Processing DDLm mandatory categories/items                             
    #                                                                         
    # DDLm manages mandatory items by providing a table in the DDLm           
    # dictionary which classifies datanames into                              
    # mandatory/recommended/prohibited for dictionary, category or item       
    # scopes. Note that the following check might fail for categories and     
    # dictionaries if '_definition.scope' or '_dictionary.title' is missing.  
    #                                                                         
    #                                                                         
    # <Process DDLm mandatory information>=                                   
    def check_mandatory_items(self,whole_block,default_scope='Item'):
        """Return an error if any mandatory items are missing"""
        if len(self.scopes_mandatory)== 0: return {"result":True}
        if default_scope == 'Datablock':
            return {"result":True}     #is a data file
        scope = whole_block.get('_definition.scope',default_scope)
        if '_dictionary.title' in whole_block:
           scope = 'Dictionary'
        missing = list([a for a in self.scopes_mandatory[scope] if a not in whole_block])
        if len(missing)==0:
            return {"result":True}
        else:
            return {"result":False,"bad_items":missing}

    # <Process DDLm prohibited information>=                                  
    def check_prohibited_items(self,whole_block,default_scope='Item'):
        """Return an error if any prohibited items are present"""
        if len(self.scopes_naughty)== 0: return {"result":True}
        if default_scope == 'Datablock':
            return {"result":True}     #is a data file
        scope = whole_block.get('_definition.scope',default_scope)
        if '_dictionary.title' in whole_block:
           scope = 'Dictionary'
        present = list([a for a in self.scopes_naughty[scope] if a in whole_block])
        if len(present)==0:
            return {"result":True}
        else:
            return {"result":False,"bad_items":present}


    # These validation checks are intended to be called externally.  They return
    # a dictionary keyed by item name with value being a list of the          
    # results of the check functions.  The individual functions return a      
    # dictionary which contains at least the key "result", and in case of error
    # relevant keys relating to the error.                                    
    #                                                                         
    #                                                                         
    # <Run validation tests>=                                                 
    def run_item_validation(self,item_name,item_value):
        return {item_name:list([(f.__name__,f(item_name,item_value)) for f in self.item_validation_funs])}

    def run_loop_validation(self,loop_names):
        return {loop_names[0]:list([(f.__name__,f(loop_names)) for f in self.loop_validation_funs])}

    def run_loop_id_uniqueness(self, loop_names, block):
        return {loop_names[0]:list([(f.__name__, f(loop_names, block)) for f in self.loop_id_uniqueness_funs])}

    def run_global_validation(self,item_name,item_value,data_block,provisional_items={},globals={}):
        results = list([(f.__name__,f(item_name,item_value,data_block,provisional_items,globals)) for f in self.global_validation_funs])
        return {item_name:results}

    def run_block_validation(self,whole_block,block_scope='Item'):
        results = list([(f.__name__,f(whole_block)) for f in self.block_validation_funs])
        # fix up the return values
        return {"whole_block":results}

    # Optimization: the dictionary validation routines normally retain no history
    # of what has been checked, as they are executed on a per-item basis.  This
    # leads to duplication of the uniqueness check, when there is more than one
    # key, and duplication of the parent-child check, once for the parent and 
    # once for the child.  By switching on optimisation, a record is kept and 
    # these checks will not be repeated.  This is safe only if none of the    
    # relevant items is altered while optimisation is on, and optimisation    
    # should be switched off as soon as all the checks are finished.          
    #                                                                         
    #                                                                         
    # <Optimisation on/off>=                                                  
    def optimize_on(self):
        self.optimize = True
        self.done_keys = []
        self.done_children = []
        self.done_parents = []

    def optimize_off(self):
        self.optimize = False
        self.done_keys = []
        self.done_children = []
        self.done_parents = []



# We provide some functions for straight validation.  These serve as an   
# example of the use of the CifDic class with the CifFile class.          
#                                                                         
#                                                                         
# <Top-level functions>=                                                  
# A convenient wrapper class for dealing with the structure returned by   
# validation.  Perhaps a more elegant approach would be to return one of  
# these objects from validation rather than wrap the validation routines inside.
#                                                                         
#                                                                         
# <ValidationResult class>=                                               
class ValidationResult:
    """Represents validation result. It is initialised with """
    def __init__(self,results):
        """results is return value of validate function"""
        self.valid_result, self.no_matches = results

    def report(self,use_html):
        """Return string with human-readable description of validation result"""
        return validate_report((self.valid_result, self.no_matches),use_html)

    def is_valid(self,block_name=None):
        """Return True for valid CIF file, otherwise False"""
        if block_name is not None:
            block_names = [block_name]
        else:
            block_names = self.valid_result.keys()
        for block_name in block_names:
            if not self.valid_result[block_name] == (True,{}):
                valid = False
                break
            else:
                valid = True
        return valid

    def has_no_match_items(self,block_name=None):
        """Return true if some items are not found in dictionary"""
        if block_name is not None:
            block_names = [block_name]
        else:
            block_names = self.no_matches.iter_keys()
        for block_name in block_names:
            if self.no_matches[block_name]:
                has_no_match_items = True
                break
            else:
                has_no_match_items = False
        return has_no_match_items

def get_no_matches_warning(checkfile, block, fulldic):
    no_matches = [a for a in checkfile[block].keys() if a not in fulldic]
    return no_matches

def get_obsolete_tags_warning_ddl1(checkfile, block, fulldic):
    result = {}
    for tag, tag_value in checkfile[block].items():
        dict_tag_entry = fulldic.get(tag, None)
        if dict_tag_entry is None:
            continue

        if dict_tag_entry.get(fulldic.related_func, "") == "replace":
            related_tag = fulldic.get(tag, None).get(fulldic.related_item)
            result[tag] = related_tag

    return result

def get_obsolete_tags_warning_ddlm(checkfile, block, fulldic):
    result = {}
    for tag, tag_value in checkfile[block].items():
        dict_tag_entry = fulldic.get(tag, None)
        if dict_tag_entry is None:
            continue

        new_tags = dict_tag_entry.get(fulldic.related_func, [])
        if new_tags:
            result[tag] = new_tags

    return result

def get_case_sensitive_warning(checkfile, block, fulldic):
    result = {}
    for tag, tag_value in checkfile[block].items():
        dict_tag_entry = fulldic.get(tag, None)
        # The tag is not found in the dictionary
        if dict_tag_entry is None:
            continue

        enum_values = dict_tag_entry.get(fulldic.enum_spec, [])
        temp_result = []

        # The tag has not any enumeration values
        if enum_values is None or not enum_values:
            continue

        if isinstance(tag_value, list):
            for temp_tag_value in tag_value:
                if temp_tag_value not in enum_values and temp_tag_value.lower() in enum_values:
                    temp_result.append(temp_tag_value)

        else:
            if tag_value not in enum_values and tag_value.lower() in enum_values:
                temp_result.append(tag_value)

        if temp_result:
            result[tag] = temp_result

    return result

def get_blacklist_warning(checkfile, block, fulldic):
    result = []
    for tag, tag_value in checkfile[block].items():
        if tag in fulldic.black_list_categories:
            result.append(tag)

    return result

def get_warnings(checkfile, block, fulldic):
    warnings = {}
    warnings["no_matches"] = get_no_matches_warning(checkfile, block, fulldic)
    warnings["blacklist"] = get_blacklist_warning(checkfile, block, fulldic)
    warnings["case_sensitive"] = get_case_sensitive_warning(checkfile, block, fulldic)

    if fulldic.diclang == "DDL1":
        warnings["obsolete"] = get_obsolete_tags_warning_ddl1(checkfile, block, fulldic)

    else:
        warnings["obsolete"] = get_obsolete_tags_warning_ddlm(checkfile, block, fulldic)

    return warnings


# We provide a function to do straight validation, using the built-in     
# methods of the dictionary type.  We need to create a single dictionary  
# from the multiple dictionaries we are passed, before doing our          
# check. Also, we allow validation of dictionaries themselves, by         
# passing a special flag [[isdic]].  This should only be used for         
# DDL2/DDLm dictionaries, and simply makes save frames visible as         
# ordinary blocks. DDL1 dictionaries validate OK if (any) global block    
# is deleted.                                                             
#                                                                         
#                                                                         
# <Validate against the given dictionaries>=                              
def Validate(ciffile,dic = "", diclist=[],mergemode="replace",isdic=False):
    """Validate the `ciffile` conforms to the definitions in `CifDic` object `dic`, or if `dic` is missing,
    to the results of merging the `CifDic` objects in `diclist` according to `mergemode`.  Flag
    `isdic` indicates that `ciffile` is a CIF dictionary meaning that save frames should be
    accessed for validation and that mandatory_category should be interpreted differently for DDL2."""
    if not isinstance(ciffile,CifFile):
        check_file = CifFile(ciffile)
    else:
        check_file = ciffile
    if not dic:
        fulldic = merge_dic(diclist,mergemode)
    else:
        fulldic = dic

    no_matches = {}
    warnings = {}
    valid_result = {}

    if isdic:          #assume one block only
        check_file.scoping = 'instance' #only data blocks visible
        top_level = check_file.keys()[0]
        check_file.scoping = 'dictionary'   #all blocks visible
        # collect a list of parents for speed
        if fulldic.diclang == 'DDL2':
            poss_parents = fulldic.get_all("_item_linked.parent_name")
            for parent in poss_parents:
                curr_parent = listify(check_file.get(parent,[]))
                new_vals = check_file.get_all(parent)
                new_vals.extend(curr_parent)
                if len(new_vals)>0:
                    check_file[parent] = new_vals
                print("Added {} (len {})".format(parent,len(check_file[parent])))
    # now run the validations
    for block in check_file.keys():
        if isdic and block == top_level:
           block_scope = 'Dictionary'
        elif isdic:
           block_scope = 'Item'
        else:
           block_scope = 'Datablock'
        warnings[block] = get_warnings(check_file, block, fulldic)
        # remove non-matching items
        if fulldic.verbose_validation:
            print()
            print("The following tags were not found in the dictionary: " + str(warnings[block]["no_matches"]))
            print("The following tags are obsolete: " + str(warnings[block]["obsolete"]))
            print("The following tags have not been taken into account for validation: " + str(warnings[block]["blacklist"]))
            print("The followings tags' values have a case-sensitive match failure: " + str(warnings[block]["case_sensitive"]))
            print()
        for nogood in warnings[block]["no_matches"]:
             del check_file[block][nogood]
        if fulldic.verbose_validation:
            print("Validating block {}, scope {}".format(block,block_scope))
        valid_result[block] = run_data_checks(check_file[block],fulldic,block_scope=block_scope)
    return valid_result, warnings

def validate_report(val_result,use_html=False):
    valid_result,warnings = val_result
    outstr = StringIO()
    if use_html:
        outstr.write("<h2>Validation results</h2>")
    else:
        outstr.write( "\nValidation results\n")
        outstr.write( "------------------\n")
    if len(valid_result) > 10:
        suppress_valid = True         #don't clutter with valid messages
        if use_html:
           outstr.write("<p>For brevity, valid blocks are not reported in the output.</p>")
    else:
        suppress_valid = False

    dict_summary = {}
    dict_summary['blocks'] = {}
    cif_is_valid = True
    cif_has_warnings = False
    for block in valid_result.keys():
        block_result = valid_result[block]

        dict_summary['blocks'][block] = {}
        dict_summary['blocks'][block]['is_valid'] = block_result[0]
        dict_summary['blocks'][block]['warnings'] = {}
        dict_summary['blocks'][block]['has_warnings'] = False
        dict_summary['blocks'][block]['errors'] = {}

        dict_summary['blocks'][block]['output_str'] = ""
        dict_summary['blocks'][block]['error_str'] = ""
        dict_summary['blocks'][block]['warning_str'] = ""

        if not dict_summary['blocks'][block]['is_valid']:
            cif_is_valid = False

        if block_result[0]:
            out_line = "Block '{}' is VALID".format(block)
        else:
            out_line = "Block '{}' is INVALID".format(block)
        if use_html:
            if (block_result[0] and (not suppress_valid or len(warnings[block])>0)) or not block_result[0]:
                outstr.write( "<h3>{}</h3><p>".format(out_line))
        else:
                outstr.write( "\n{} \n".format(out_line))

        warning_table = {
            'no_matches':'Warning: The following items were not found in the dictionary.',
            'obsolete':'Warning: Obsolete definitions found. Obsolete tags should be replaced by their related tags.',
            'case_sensitive':'Warning: Case-sensitive match failure for enumeration values.',
            'blacklist':'Warning: The following tags can cause validation problems so they have not been taken into account for validation.'
        }

        warnings_str, warning_dict = get_warning_report(warnings.get(block), warning_table)

        if warnings_str:
            outstr.write(warnings_str)
            cif_has_warnings = True
            dict_summary['blocks'][block]['warnings'] = warning_dict
            dict_summary['blocks'][block]['has_warnings'] = True

        # now organise our results by type of error, not data item...
        error_type_dic = {}
        for error_item, error_list in block_result[1].items():
            for func_name,bad_result in error_list:
                bad_result.update({"item_name":error_item})
                try:
                    error_type_dic[func_name].append(bad_result)
                except KeyError:
                    error_type_dic[func_name] = [bad_result]
        # make a table of test name, test message
        info_table = {\
        'validate_item_type':\
            "Error: The following data items had badly formed values",
        'validate_item_esd':\
            "Error: The following data items should not have esds appended",
        'validate_enum_range':\
            "Error: The following data items have values outside permitted range",
        'validate_item_enum':\
            "Error: The following data items have values outside permitted set",
        'validate_looping':\
            "Error: The following data items violate looping constraints",
        'validate_loop_membership':\
            "Error: The following looped data names are of different categories to the first looped data name",
        'validate_loop_key':\
            "Error: A required dataname for this category is missing from the loop\n containing the dataname",
        'validate_loop_key_ddlm':\
            "Error: A loop key is missing for the category containing the dataname",
        'validate_loop_key_uniqueness':\
            "Error: There are repeated values for a _list_mandatory type tag",
        'validate_loop_references':\
            "Error: A dataname required by the item is missing from the loop",
        'validate_parent':\
            "Error: A parent dataname is missing or contains different values",
        'validate_child':\
            "Error: A child dataname contains different values to the parent",
        'validate_uniqueness':\
            "Error: One or more data items do not take unique values",
        'validate_dependents':\
            "Error: A dataname required by the item is missing from the data block",
        'validate_exclusion': \
            "Error: Both dataname and exclusive alternates or aliases are present in data block",
        'validate_mandatory_category':\
            "Error: A required category is missing from this block",
        'check_mandatory_items':\
            "Error: A required data attribute is missing from this block",
        'check_prohibited_items':\
            "Error: A prohibited data attribute is present in this block"}

        block_validation_str = "\n" + out_line + " \n" + warnings_str + "\n"
        block_warning_str = "\n" + out_line + "\n" + warnings_str + "\n"
        block_error_str = "\n" + out_line + "\n"
        for test_name,test_results in error_type_dic.items():
           if use_html:
               outstr.write(html_error_report(test_name,info_table[test_name],test_results))
           else:
               temp_str = error_report(test_name,info_table[test_name],test_results)
               outstr.write(temp_str)
               outstr.write("\n\n")

               block_error_str += temp_str + "\n\n"
               block_validation_str += temp_str + "\n\n"
               dict_summary['blocks'][block]['errors'][test_name] = temp_str

               #outstr.write(error_report(test_name,info_table[test_name],test_results))
               #outstr.write("\n\n")

        dict_summary['blocks'][block]["error_str"] = block_error_str
        dict_summary['blocks'][block]["warning_str"] = block_warning_str
        dict_summary['blocks'][block]["output_str"] = block_validation_str

    dict_summary['cif_has_warnings'] = cif_has_warnings
    dict_summary['cif_is_valid'] = cif_is_valid

    return outstr.getvalue(), dict_summary

def warning_report_no_matches(no_matches_warnings, warning_table):
    if not no_matches_warnings:
        return ""

    warning_header = "\n" + warning_table.get('no_matches')
    table = PrettyTable()

    field_names = ["Tags not found in the dictionaries"]

    table.field_names = field_names
    table.align["Tags not found in the dictionaries"] = "l"

    for idx, tag_name in enumerate(no_matches_warnings):
        table.add_row([tag_name])

    table_str = table.get_string() + "\n"

    return "\n".join((warning_header, table_str))


def warning_report_obsolete(obsolete_tags, warning_table):
    if not obsolete_tags:
        return ""

    warning_header = "\n" + warning_table.get('obsolete')
    table = PrettyTable()

    field_names = ["Obsolete tags", "Related tags"]

    table.field_names = field_names
    table.align["Obsolete tags"] = "l"
    table.align["Related tags"] = "l"

    for obsolete_tag, related_tag in obsolete_tags.items():
        row = [obsolete_tag, related_tag]
        table.add_row(row)

    table_str = table.get_string() + "\n"

    return "\n".join((warning_header, table_str))

def warning_report_case_sensitive(case_sensitive_tags, warning_table):
    if not case_sensitive_tags:
        return ""

    warning_header = "\n" + warning_table.get('case_sensitive')
    table = PrettyTable()

    field_names = ["Tag name", "Case sensitive value"]

    table.field_names = field_names
    table.align["Tag name"] = "l"
    table.align["Case sensitive value"] = "l"

    for tag, wrong_values in case_sensitive_tags.items():
        row = [tag, wrong_values]
        table.add_row(row)

    table_str = table.get_string() + "\n"

    return "\n".join((warning_header, table_str))

def warning_report_blacklist(blacklist_tags, warning_table):
    if not blacklist_tags:
        return ""

    warning_header = warning_table.get('blacklist') + "\n"
    table = PrettyTable()

    field_names = ["Tags in the black list"]

    table.field_names = field_names
    table.align["Tags in the black list"] = "l"

    for idx, blacklist_tag in enumerate(blacklist_tags):
        table.add_row([blacklist_tag])

    table_str = table.get_string() + "\n"

    return "\n".join((warning_header, table_str))

def get_warning_report(warnings, warning_table):
    out_str = ""
    out_dict = {}

    no_matches_str = warning_report_no_matches(warnings.get('no_matches'), warning_table)
    obsolete_str = warning_report_obsolete(warnings.get('obsolete'), warning_table)
    case_sensitive_str = warning_report_case_sensitive(warnings.get('case_sensitive'), warning_table)
    blacklist_str = warning_report_blacklist(warnings.get('blacklist'), warning_table)

    out_dict['no_matches'] = no_matches_str
    out_dict['obsolete'] = obsolete_str
    out_dict['case_sensitive_str'] = case_sensitive_str
    out_dict['blacklist_str'] = blacklist_str

    out_str = "".join((
                no_matches_str, obsolete_str,
                case_sensitive_str, blacklist_str
            ))

    return out_str, out_dict

# A function to lay out a single error report.  We are passed
# the name of the error (one of our validation functions), the
# explanation to print out, and a dictionary with the error
# information.  We print no more than 50 characters of the item

def error_report(error_name,error_explanation,error_dics):
   retstring = "\n\n" + error_explanation + ":\n\n"
   headstring = "{}".format("Item name, ")
   bodystring = ""

   table = PrettyTable()
   field_names = ["Wrong item name"]

   if "bad_values" in error_dics[0]:
      headstring += "{}".format("Bad value(s)")
      field_names.append("Wrong value(s)")
   if "bad_items" in error_dics[0]:
      headstring += "{}".format("Bad dataname(s)")
      field_names.append("Bad dataname(s)")
   if "child" in error_dics[0]:
      headstring += "{}".format("Child")
      field_names.append("Child")
   if "parent" in error_dics[0]:
      headstring += "{}".format("Parent")
      field_names.append("Parent")
   headstring +="\n"

   table.field_names = field_names

   for field_name in table.field_names:
       table.align[field_name] = "l"

   for error in error_dics:
      bodystring += "\n{}".format(error["item_name"])
      row = [error["item_name"]]
      if "bad_values" in error:
          max_items = 8
          if len(error["bad_values"]) > max_items:
              out_vals = []
              for i in range(max_items):
                  out_vals.append(error["bad_values"][i])

              out_vals.append("...")
          else:
            out_vals = [repr(a)[:50] for a in error["bad_values"]]
          row.append(out_vals)
          bodystring += "{}".format(out_vals)
      if "bad_items" in error:
          bodystring += "{}".format(repr(error["bad_items"]))
          row.append(repr(error["bad_items"]))
      if "child" in error:
          bodystring += "{}".format(repr(error["child"]))
          row.append(repr(error["child"]))
      if "parent" in error:
          bodystring += "{}".format(repr(error["parent"]))
          row.append(repr(error["parent"]))

      table.add_row(row)

   bodystring = table.get_string()
   return retstring + bodystring

#  This lays out an HTML error report

def html_error_report(error_name,error_explanation,error_dics,annotate=[]):
   retstring = "<h4>" + error_explanation + ":</h4>"
   retstring = retstring + "<table cellpadding=5><tr>"
   headstring = "<th>Item name</th>"
   bodystring = ""
   if "bad_values" in error_dics[0]:
      headstring += "<th>Bad value(s)</th>"
   if "bad_items" in error_dics[0]:
      headstring += "<th>Bad dataname(s)</th>"
   if "child" in error_dics[0]:
      headstring += "<th>Child</th>"
   if "parent" in error_dics[0]:
      headstring += "<th>Parent</th>"
   headstring +="</tr>\n"
   for error in error_dics:
      bodystring += "<tr><td><tt>{}</tt></td>".format(error["item_name"])
      if "bad_values" in error:
          bodystring += "<td>{}</td>".format(error["bad_values"])
      if "bad_items" in error:
          bodystring += "<td><tt>{}</tt></td>".format(error["bad_items"])
      if "child" in error:
          bodystring += "<td><tt>{}</tt></td>".format(error["child"])
      if "parent" in error:
          bodystring += "<td><tt>{}</tt></td>".format(error["parent"])
      bodystring += "</tr>\n"
   return retstring + headstring + bodystring + "</table>\n"

# This function executes validation checks provided in the CifDic.  The   
# validation calls create a dictionary containing the test results for each
# item name.  Each item has a list of (test name,result) tuples.  After running
# the tests, we contract these lists to contain only false results, and then
# remove all items containing no false results.                           
#                                                                         
#                                                                         
# <Run dictionary validation checks>=                                     
def run_data_checks(check_block,fulldic,block_scope='Item'):
    v_result = {}
    for key in check_block.keys():
        update_value(v_result, fulldic.run_item_validation(key,check_block[key]))
        update_value(v_result, fulldic.run_global_validation(key,check_block[key],check_block))
    for loopnames in check_block.loops.values():
        update_value(v_result, fulldic.run_loop_validation(loopnames))
        update_value(v_result, fulldic.run_loop_id_uniqueness(loopnames, check_block))
    update_value(v_result,fulldic.run_block_validation(check_block,block_scope=block_scope))
    # return false and list of baddies if anything didn't match
    all_keys = list(v_result.keys())
    for test_key in all_keys:
        v_result[test_key] = [a for a in v_result[test_key] if a[1]["result"]==False]
        if len(v_result[test_key]) == 0:
            del v_result[test_key]
    # if even one false one is found, this should trigger
    # print("Baddies: {!r}".format(v_result))
    isvalid = len(v_result)==0
    return isvalid,v_result


# <Utility functions>=                                                    
# This support function uses re capturing to work out the number's value. The
# re contains 7 groups: group 0 is the entire expression; group 1 is the overall
# match in the part prior to esd brackets; group 2 is the match with a decimal
# point, group 3 is the digits after the decimal point, group 4 is the match
# without a decimal point.  Group 5 is the esd bracket contents, and      
# group 6 is the exponent.                                                
#                                                                         
# The esd should be returned as an independent number.  We count the number
# of digits after the decimal point, create the esd in terms of this, and then,
# if necessary, apply the exponent.                                       
#                                                                         
#                                                                         
# <Extract number and esd>=                                               
def get_number_with_esd(numstring):
    numb_re = '((-?(([0-9]*[.]([0-9]+))|([0-9]+)[.]?))([(][0-9]+[)])?([eEdD][+-]?[0-9]+)?)|(\\?)|(\\.)'
    our_match = re.match(numb_re,numstring)
    if our_match:
        a,base_num,b,c,dad,dbd,esd,exp,q,dot = our_match.groups()
        # print("Debug: {} -> {!r}".format(numstring, our_match.groups()))
    else:
        return None,None
    if dot or q: return None,None     #a dot or question mark
    if exp:          #has exponent
       exp = exp.replace("d","e")     # mop up old fashioned numbers
       exp = exp.replace("D","e")
       base_num = base_num + exp
    # print("Debug: have %s for base_num from %s" % (base_num,numstring))
    base_num = float(base_num)
    # work out esd, if present.
    if esd:
        esd = float(esd[1:-1])    # no brackets
        if dad:                   # decimal point + digits
            esd = esd * (10 ** (-1* len(dad)))
        if exp:
            esd = esd * (10 ** (float(exp[1:])))
    return base_num,esd

# We may be passed float values which have esds appended.  We catch this case
# by searching for an opening round bracket                               
#                                                                         
# <Convert value to float, ignore esd>=                                   
def float_with_esd(inval):
    if isinstance(inval,unicode):
        j = inval.find("(")
        if j>=0:  return float(inval[:j])
    return float(inval)



#  For dREl operations we require that all numerical types actually appear
# as numerical types rather than strings.  This function takes a datablock
# and a dictionary and converts all the datablock contents to numerical   
# values according to the dictionary specifications.                      
#                                                                         
# Note that as written we are happy to interpret a floating point string as
# an integer.  We are therefore assuming that the value has been validated.
#                                                                         
#                                                                         
# <Conversions to dictionary types>=                                      
#  Instead of returning a value, we return a function that can be used    
# to convert the values. This saves time reconstructing the conversion    
# function for every value in a loop.                                     
#                                                                         
#                                                                         
# <Overall conversion>=                                                   
def convert_type(definition):
    """Convert value to have the type given by definition"""
    #extract the actual required type information
    container = definition['_type.container']
    dimension = definition.get('_type.dimension','[]')
    dimension = ast.literal_eval(dimension)
    structure = interpret_structure(definition['_type.contents'])
    if container == 'Single':   #a single value to convert
        return convert_single_value(structure)
    elif container == 'List':   #lots of the same value
        return convert_list_values(structure,dimension)
    elif container == 'Multiple': #no idea
        return None
    elif container in ('Array','Matrix'): #numpy array
        return convert_matrix_values(structure)
    return lambda a:a    #unable to convert

# <Convert a single value>=                                               
def convert_single_value(type_spec):
    """Convert a single item according to type_spec"""
    if type_spec == 'Real':
        return float_with_esd
    if type_spec in ('Count','Integer','Index','Binary','Hexadecimal','Octal'):
        return int
    if type_spec == 'Complex':
        return complex
    if type_spec == 'Imag':
        return lambda a:complex(0,a)
    if type_spec in ('Code','Name','Tag'):  #case-insensitive -> lowercase
        return lambda a:a.lower()
    return lambda a:a   #can't do anything numeric

# Convert a whole DDLm list.  A 'List' type implies a repetition of       
# the types given in the 'type.contents' entry.  We get all fancy and     
# build a function to decode each entry in our input list.  This          
# function is then mapped over the List, and in the case of looped List   
# values, it can be mapped over the dataname value as well.  However, in  
# the case of a single repetition, files are allowed to drop one level    
# of enclosing brackets.  We account for that here by detecting a         
# one-element list and *not* mapping the conversion function.  TODO:      
# Note that we do not yet handle the case that we are supposed to         
# convert to a Matrix, rather than a list. TODO: handle arbitrary         
# dimension lists, rather than special-casing the character sequence      
# '[1]'.                                                                  
#                                                                         
#                                                                         
# <Convert a list value>=                                                 
class convert_simple_list(object):

    """\
    Callable object that converts values in a simple list according
    to the specified element structure.
    """

    def __init__(self, structure):
        self.converters = [convert_single_value(tp) for tp in structure]
        return

    def __call__(self, element):
        if len(element) != len(self.converters):
            emsg = "Expected iterable of {} values, got {}.".format(
                (len(self.converters), len(element)))
            raise ValueError(emsg)
        rv = [f(e) for f, e in zip(self.converters, element)]
        return rv

# End of class convert_single_value

def convert_list_values(structure, dimension):
    """Convert the values according to the element
       structure given in [[structure]]"""
    # simple repetition
    print("Converting {} of dimensions {}".format(structure, dimension))
    if isinstance(structure, (unicode, str)):
        fcnv = convert_single_value(structure)
    # assume structure is a list of types
    else:
        fcnv = convert_simple_list(structure)
    rv = fcnv
    # setup nested conversion function when dimension differs from 1.
    if len(dimension) > 0 and int(dimension[0]) != 1:
        rv = lambda args : [fcnv(a) for a in args]
    return rv

#  When storing a matrix/array value as a result of a calculation, we remove the
# numpy information and instead store as a StarList.  The following routine will
# work transparently for either string or number-valued Star Lists, so we do not
# have to worry.                                                          
#                                                                         
#                                                                         
# <Convert a matrix value>=                                               
def convert_matrix_values(valtype):
    """Convert a dREL String or Float valued List structure to a numpy matrix structure"""
    # first convert to numpy array, then let numpy do the work
    try:
        import numpy
    except ImportError:
        return lambda a:a   #cannot do it
    if valtype == 'Real':
        dtype = float
    elif valtype == 'Integer':
        dtype = int
    elif valtype == 'Complex':
        dtype = complex
    else:
        raise ValueError('Unknown matrix value type')
    fcnv = lambda a : numpy.asarray(a, dtype=dtype)
    return fcnv

#  DDLm specifies List element composition using a notation of form 'cont(el,el,el...)'
# where 'cont' refers to a container constructor (list or matrix so far) and 'el' is a simple
# element type. If 'cont' is missing, the sequence of elements is a sequence of elements in
# a simple list.  We have written a simple parser to interpret this.      
#                                                                         
#                                                                         
# <Parse the structure specification>=                                    
def interpret_structure(struc_spec):
    """Interpret a DDLm structure specification"""
    from . import TypeContentsParser as t
    p = t.TypeParser(t.TypeParserScanner(struc_spec))
    return getattr(p,"input")()


# <Append update>=                                                        
# A utility function to append to item values rather than replace them
def update_value(base_dict,new_items):
    for new_key in new_items.keys():
        if new_key in base_dict:
            base_dict[new_key].extend(new_items[new_key])
        else:
            base_dict[new_key] = new_items[new_key]

# <Transpose data>=                                                       
#Transpose the list of lists passed to us
def transpose(base_list):
    new_lofl = []
    full_length = len(base_list)
    opt_range = range(full_length)
    for i in range(len(base_list[0])):
       new_packet = []
       for j in opt_range:
          new_packet.append(base_list[j][i])
       new_lofl.append(new_packet)
    return new_lofl

# listify strings - used surprisingly often
def listify(item):
    if isinstance(item,(unicode,str)): return [item]
    else: return item

# given a list of search items, return a list of items
# actually contained in the given data block
def filter_present(namelist,datablocknames):
    return [a for a in namelist if a in datablocknames]

# Make an item immutable, used if we want a list to be a key
def make_immutable(values):
    """Turn list of StarList values into a list of immutable items"""
    if not isinstance(values[0],StarList):
        return values
    else:
        return [tuple(a) for a in values]

# This uses the  [[CifFile]] merge method to merge a list of filenames,   
# with an initial check to determine DDL1/DDL2 merge style.  In one       
# case we merge save frames in a single block, in another case we         
# merge data blocks.  These are different levels.                         
#                                                                         
# Note that the data block name is passed to specify the parts of each object
# to be merged, rather than the objects themselves (not doing this was a bug
# that was caught a while ago).                                           
#                                                                         
#                                                                         
# <Merge dictionaries as CIFs>=                                           
# merge ddl dictionaries.  We should be passed filenames or CifFile
# objects
def merge_dic(diclist,mergemode="replace",ddlspec=None, verbose_import=True, verbose_validation=True):
    dic_as_cif_list = []
    for dic in diclist:
        if not isinstance(dic,CifFile) and \
           not isinstance(dic,(unicode,str)):
               raise TypeError("Require list of CifFile names/objects for dictionary merging")
        if not isinstance(dic,CifFile): dic_as_cif_list.append(CifFile(dic))
        else: dic_as_cif_list.append(dic)
    # we now merge left to right
    basedic = dic_as_cif_list[0]
    if "on_this_dictionary" in basedic:   #DDL1 style only
        for dic in dic_as_cif_list[1:]:
           basedic.merge(dic,mode=mergemode,match_att=[], idblock="on_this_dictionary")
    elif len(basedic.keys()) == 1:                     #One block: DDL2/m style
        old_block = basedic[basedic.keys()[0]]
        for dic in dic_as_cif_list[1:]:
           new_block = dic[dic.keys()[0]]
           basedic.merge(dic,mode=mergemode,
                         single_block=[basedic.keys()[0],dic.keys()[0]],
                         match_att=["_item.name"],match_function=find_parent)
    final_dic = CifDic(basedic, do_dREL=False, verbose_import=verbose_import, verbose_validation=verbose_validation)

    # Add all the alias blocks once the dictionary is fully formed
    if final_dic.diclang == "DDLm":
        final_dic = final_dic.add_alias_blocks()

    return final_dic

# Find the main item from a parent-child list.  We are asked to find the  
# topmost parent in a ddl2 definition block containing multiple item.names.
# We use the insight that the parent item will be that item which is not in
# the list of children as well.  If there are no item names, that means   
# that we are dealing with something like a category -can they be merged??
#                                                                         
#                                                                         
# <Get topmost parent>=                                                   
def find_parent(ddl2_def):
    if "_item.name" not in ddl2_def:
       return None
    if isinstance(ddl2_def["_item.name"],unicode):
        return ddl2_def["_item.name"]
    if "_item_linked.child_name" not in ddl2_def:
        raise CifError("Asked to find parent in block with no child_names")
    if "_item_linked.parent_name" not in ddl2_def:
        raise CifError("Asked to find parent in block with no parent_names")
    result = list([a for a in ddl2_def["_item.name"] if a not in ddl2_def["_item_linked.child_name"]])
    if len(result)>1 or len(result)==0:
        raise CifError("Unable to find single unique parent data item")
    return result[0]

# Utility routine for use by callers who have captured parsing results instead
# of raising an error immediately.

import CifFile.yapps3_compiled_rt as yappsrt

def print_cif_syntax_error(parsing_result, cif_file_name):
    """ For use when parsing results have been captured instead of raising an error
    immediately. See ReadStarWithError."""
    
    error = parsing_result[1]

    # parsing_result[0] == -1
    if isinstance(error, yappsrt.YappsSyntaxError):
        parser = parsing_result[2]
        Y = parsing_result[3]

        scanner = parser._scanner
        input = parser._scanner.input
        pos = error.charpos

        line_number = scanner.get_line_number_with_pos(pos)

        out_str = "\n"
        out_str += "======================================================================\n"
        out_str += "\n"
        out_str += "SYNTAX ERROR AT LINE " + str(line_number) + " WHEN PARSING INPUT FILE:" + str(cif_file_name) + ":\n"
        out_str += str(error.msg) + "\n"
        out_str += "\n"
        out_str += "ERROR NEAR THE FOLLOWING INPUT TEXT:\n"

        text_error = Y.yappsrt.print_line_with_pointer(input, pos)

        out_str += text_error
        print(out_str)

        return out_str

    # parsing_result[0] == -2
    if isinstance(error, CifSyntaxError):
        print(error.value)

        return error.value

# Reading in a file.  We use the STAR grammar parser.  Note that the blocks returned
# will be locked for changing ([[overwrite=False]]) and can be unlocked by setting
# block.overwrite to True.                                                
#
# Provide access to rich error information with alternate function that makes use
# of the ReadStarWithError function.
#                                                                         
# <Read in a CIF file>=                                                   
def ReadCifWithErrors(filename,grammar='auto',scantype='standard',scoping='instance',standard='CIF',
            permissive=False):
    """ Read in a CIF file, returning a (`CifFile`, error_result) tuple. `error_result`
    is a list [error_val, Exception, Parser, ParserModule] which can be used for
    detailed error reporting. If `error_val` is less than 0, an error has occurred
    and the contents of `CifFile` will be incomplete and/or incorrect.

    * `filename` may be a URL, a file
    path on the local system, or any object with a `read` method.

    Keyword meanings are as for `ReadCif`"""

    finalcif = CifFile(scoping=scoping,standard=standard)
    return StarFile.ReadStarWithErrors(filename,prepared=finalcif,grammar=grammar,scantype=scantype,
                             permissive=permissive)

def ReadCif(filename, grammar='auto', scantype='standard', scoping='instance', standard='CIF',
            permissive = False):
    """ Read in a CIF file, returning a `CifFile` object and raising an exception
    on failure.

    * `filename` may be a URL, a file
    path on the local system, or any object with a `read` method.
    
    * `grammar` chooses the CIF grammar variant. `1.0` is the original 1992 grammar and `1.1`
    is identical except for the exclusion of square brackets as the first characters in
    undelimited datanames. `2.0` will read files in the CIF2.0 standard, and `STAR2` will
    read files according to the STAR2 publication.  If grammar is `None`, autodetection
    will be attempted in the order `2.0`, `1.1` and `1.0`. This will always succeed for
    properly-formed CIF2.0 files.  Note that only Unicode characters in the basic multilingual
    plane are recognised (this will be fixed when PyCIFRW is ported to Python 3).

    * `scantype` can be `standard` or `flex`.  `standard` provides pure Python parsing at the
    cost of a factor of 10 or so in speed.  `flex` will tokenise the input CIF file using
    fast C routines, but is not available for CIF2/STAR2 files.  Note that running PyCIFRW in
    Jython uses native Java regular expressions
    to provide a speedup regardless of this argument (and does not yet support CIF2).

    * `scoping` is only relevant where nested save frames are expected (STAR2 only).
    `instance` scoping makes nested save frames
    invisible outside their hierarchy, allowing duplicate save frame names in separate
    hierarchies. `dictionary` scoping makes all save frames within a data block visible to each
    other, thereby restricting all save frames to have unique names.
    Currently the only recognised value for `standard` is `CIF`, which when set enforces a
    maximum length of 75 characters for datanames and has no other effect.
    """

    finalcif = CifFile(scoping=scoping,standard=standard)
    return StarFile.ReadStar(filename, prepared=finalcif, grammar=grammar, scantype=scantype,
                  permissive = permissive)
    
# \section{Cif Loop block class}                                          
#                                                                         
# With the removal (by PyCIFRW) of nested loops, this class is now unnecessary. It is now
# simply a pointer to StarFile.LoopBlock.                                 
#                                                                         
#                                                                         
# <CifLoopBlock class>=                                                   
class CifLoopBlock(StarFile.LoopBlock):
    def __init__(self,data=(),**kwargs):
        super(CifLoopBlock,self).__init__(data,**kwargs)

# <API documentation flags>=                                              
#No documentation flags

