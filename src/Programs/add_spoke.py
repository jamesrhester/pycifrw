# This program adds a dataname to every category that is a child
# dataname of the nominated category for the provided dictionary
# All spoke categories are then linked via the hub category.

from __future__ import print_function
from CifFile import CifDic

def update_one_category(dic,cat_name,hub_id,obj_id,extra_text=""):
    """Add a dataname <cat_name.obj_id> to category cat_name which is
    a child_item of category hub_id and an additional key for cat_name"""
    blockname = dic.block_from_catname(cat_name)
    hub_blockname = dic.block_from_catname(hub_id)
    hub_keyname = dic[hub_blockname]['_category_key.name'][0]
    def_text = "This dataname indicates which member of the " + hub_id.upper()
    def_text += \
""" category a member of this category belongs to. It does not need to be
explicitly included in datafiles if the key for the """ + hub_id + \
""" category takes a single (or default) value. """ + extra_text
    new_bname = dic.add_definition(obj_id,blockname,def_text)
    dic[new_bname]['_name.linked_item_id'] = hub_keyname
    dic[new_bname]['_type.purpose'] = 'Link'
    # now update the category information as well
    current_keys = dic[blockname].get('_category_key.name',[])
    dic[blockname]['_category_key.name'] = current_keys + ["_"+new_bname]
    dic[blockname].CreateLoop(['_category_key.name'])
    return new_bname

def add_spoke(sem_dic,hub_cat,specific_cats = set(),extra_text=''):
    all_cats = set([a.get('_definition.id','').lower() for a in sem_dic if a.get('_definition.scope','Item'=='Category') and a.get('_definition.class','') != 'Head'])
    if specific_cats is None:
        specific_cats = all_cats
    actual_cats = (all_cats & set(specific_cats)) - set([hub_cat])
    print('Will update categories in following list')
    print(repr(actual_cats))
    for one_cat in actual_cats:
        print('Updating %s' % one_cat)
        new_bname = update_one_category(sem_dic,one_cat,hub_cat,hub_cat+'_id',extra_text)
        print('New definition:\n')
        print(str(sem_dic[new_bname]))

def add_hub(indic,hub_cat,key_id,extra_text=''):
    """Add a hub category with hub key id <key_id>"""
    def_text = \
    """This category is a central category for logically connecting together a
    group of categories."""
    blockname = indic.add_category(hub_cat)
    indic[blockname].overwrite = True
    indic[blockname]['_description.text'] = def_text
    indic[blockname]['_definition.class'] = 'Loop'
    indic[blockname]['_category_key.name'] = ['_'+hub_cat.lower()+"."+key_id]
    indic[blockname].CreateLoop(['_category_key.name'])
    # add the single entry for the key
    new_def_text = """This dataname must have a unique value for each distinct
row in this category. As a default value is defined, it need not explicitly
appear in datafiles unless there is more than entry in the category."""
    new_def = indic.add_definition(key_id,hub_cat,new_def_text)
    indic[new_def]['_enumeration.default'] = "."

def add_hub_spoke(indic,hub_cat,only_cats=None,force=False):
    """Edit <indic> to add a new hub category, with linked ids in all
    other categories, unless only_cats is specified"""
    sem_dic = CifDic(indic,grammar="2.0",do_minimum=True)
    if hub_cat.lower() not in sem_dic.cat_map.keys() or force==True:
        print(hub_cat + ' not found in dictionary, adding')
        add_hub(sem_dic, hub_cat, 'id')
    add_spoke(sem_dic,hub_cat,only_cats)
    outfile = indic + '.updated'
    outfile = open(outfile,"w")
    outfile.write(str(sem_dic))
    return sem_dic

if __name__ == '__main__':
    import sys
    if len(sys.argv)>2:
        indic = sys.argv[1]
        hub_cat = sys.argv[2].lower()
        if len(sys.argv)>3:
            all_cats = [a.lower() for a in sys.argv[3:]]
        else:
            all_cats = None
        new_dic = add_hub_spoke(indic,hub_cat,all_cats)
    else:
        print('Usage: add_spoke <dic name> <hub category name> <category name> ...')
