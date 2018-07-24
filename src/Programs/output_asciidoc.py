# A program to produce an Ascii-doc ready presentation of a CIF dictionary
#
from CifFile import CifDic,CifFile
from CifFile.StarFile import CIFStringIO
import cStringIO,os,re

def make_asciidoc(indic):
    """Make a nice asciidoc document from a CIF dictionary"""
    template_files = {}
    base_directory = os.path.dirname(indic)  #for later
    sem_dic = CifDic(indic,grammar="2.0",do_imports="Contents",do_dREL=False)
    dep_dics = analyse_deps(sem_dic,in_directory=base_directory)
    blockorder = sem_dic.get_full_child_list()
    outstring = CIFStringIO()
    categories = sem_dic.get_categories()
    # The first block is the one with the dictionary information
    top_block = sem_dic.master_block
    dicname = top_block['_dictionary.title']
    dicversion = top_block['_dictionary.version']
    dicdate = top_block['_dictionary.date']
    dicdes = prepare_text(top_block['_description.text'])
    outstring.write(":toc-placement: manual\n")
    outstring.write(":toc:\n")
    outstring.write("= " + dicname + "\n")
    outstring.write(":date: " + dicdate + "\n")
    outstring.write(":version: " + dicversion + "\n\n")
    outstring.write(dicdes + "\n\n")
    if len(dep_dics)>0:
        outstring.write("This dictionary builds on definitions found in ")
        for pos,one_dic in enumerate(dep_dics):
            outstring.write(one_dic.master_block["_dictionary.title"])
            if pos < len(dep_dics)-2:
                outstring.write(", ")
            elif pos == len(dep_dics)-2:
                outstring.write(" and ")
            else:
                outstring.write(".")
    outstring.write("\n\n")
    outstring.write("Generated from %s, version {version}\n\n" % indic)
    outstring.write("""
Categories that may have more than one row are called loop categories.
Datanames making up the keys for these categories have a dot suffix.""")
    outstring.write("\n\n");
    outstring.write("toc::[]\n")  #only works if toc2 removed
    # store a list of ids for us to reference later
    section_ids = map(make_id,blockorder[1:])
    for adef in blockorder[1:]:
        onedef = sem_dic[adef]
        def_type = onedef.get('_definition.scope','Item')
        def_text = onedef.get('_description.text','Empty')
        out_def_header = def_header = onedef.get('_definition.id','None')
        def_id = make_id(def_header)
        aliases = onedef.get('_alias.definition_id',[])
        cat_id = onedef.get('_name.category_id',None)
        if def_header in aliases:
            aliases.remove(def_header)
        alternates = onedef.get('_enumeration_set.state',[])
        alt_defs = [prepare_text(a,section_ids) for a in onedef.get('_enumeration_set.detail',[])]
        if len(alt_defs) != len(alternates):
            # definitions omitted as obvious?
            alt_defs = [None]*len(alternates)
        # Any examples we should know about?
        examples = onedef.get('_description_example.case',[])
        example_explanation = onedef.get('_description_example.detail',[])
        if len(example_explanation) != len(examples):   # no explanations
            example_explanation = ['']*len(examples)
        all_examples = zip(examples,example_explanation)
        if def_type == 'Category':
            outstring.write("[[%s]]\n== " % def_id)
            current_cat = def_header
            out_def_header = def_header.upper()
        elif def_type == 'Item':
            if cat_id.lower() != current_cat.lower():
                #from an external source
                # find external source
                dic_source = locate_category(dep_dics,cat_id)
                outstring.write("\n== " + cat_id.upper() + " (Original category from: %s) \n" % dic_source)
                outstring.write("This category is defined in external dictionary %s\n" % dic_source)
                current_cat = cat_id
            outstring.write("[[%s]]\n=== " % def_id)
            if is_key(sem_dic,def_header):
                out_def_header = def_header + r"&#8226;"
        else:
            continue
        outstring.write(out_def_header + "\n")
        if def_text == 'Empty': #check for template
            def_text = get_template_text(onedef,indic,template_files)
        else:
            def_text = prepare_text(def_text,section_ids)
        outstring.write("\n"+def_text+"\n")
        # further information for item definitions
        if len(alternates)>0:
            # check for default
            default = onedef.get('_enumeration.default',None)
            outstring.write("\n.Possible values")
            if default is not None:
                outstring.write('(default in bold)')
            outstring.write(":\n\n[horizontal]\n*****\n")
            for n,d in zip(alternates,alt_defs):
                if n == default:
                    outstring.write("*"+vb_text(n)+"*")
                else:
                    outstring.write(vb_text(n))
                outstring.write("::\n\n")
                if d is not None:
                    outstring.write(d+"\n")
            outstring.write("*****\n")
        if len(aliases)>0:
            outstring.write("\n.Aliases\n*****\n")
            for a in aliases:
                outstring.write("`"+a+"` +\n")
            outstring.write("*****\n")
        if len(all_examples)>0:
            for e,caption in all_examples:
                outstring.write("\n.Example:%s\n----\n" % prepare_text(caption))
                # Catch actual values by formatting them first
                if def_type == 'Item':  #only deal with single values
                    onedef.format_value(e,outstring)
                else:
                    outstring.write(e)
                outstring.write("\n----\n\n")
    outfile = open(indic+".adoc","w")
    outfile.write(outstring.getvalue())

def prepare_text(textstring,link_ids=[]):
    """Transform text for better presentation"""
    # Make sure paragraphs are not set verbatim
    outstring = re.sub(r"\n +",r"\n",textstring.strip())
    # Try and catch some greek letters
    outstring = re.sub(r"\\alpha",r"&#945;",outstring)
    outstring = re.sub(r"\\\\a",r"&#945;",outstring)
    outstring = re.sub(r"\\a",r"&#945;",outstring)
    outstring = re.sub(r"\\b",r"&#946;",outstring)
    outstring = re.sub(r"\\\\q",r"&#952;",outstring)
    outstring = re.sub(r"\\q",r"&#952;",outstring)
    outstring = re.sub(r"\\l",r"&#955;",outstring)
    outstring = re.sub(r"\\\\m",r"&#956;",outstring)
    outstring = re.sub(r"\\\\n",r"&#957;",outstring)
    outstring = re.sub(r"\\n",r"&#957;",outstring)
    # Subscripting should just work
    # Assume underscores signal a dataname and format as literal
    # as well as linking
    outstring = re.sub(r"([\s(,]|^)(_[A-Za-z0-9.%_-]+)",match_to_id,outstring)
    # Assume that single apostrophes become double
    outstring = re.sub(r"'s",r"\'s",outstring)
    outstring = re.sub(r"'([\S])'",r'"\1"',outstring)
    # Also catch constructions of the form "*_" and "*_"
    outstring = re.sub(r"(\*_[\w]+|[\w]+_\*)",r"`\1`",outstring)
    # Asterisks are probably reciprocal space, not emphasis
    outstring = re.sub(r"\*(?!_)",r"\*",outstring)
    return outstring

def match_to_id(one_match):
    """ Used by prepare_text to format cross-references correctly"""
    to_id = make_id(one_match.group(2))
    return one_match.group(1)+"xref:"+to_id+"[`"+one_match.group(2)+"`]"

def vb_text(textstring):
    """Escape characters that might be interpreted by asciidoc"""
    import re
    outstring = re.sub(r"~(.+)",r"\~\1",textstring)
    return "+" + outstring + "+"

def make_id(textstring):
    """Convert the provided text into an ID for cross-referencing.
    Substitute all non-alphanumerics with underscore"""
    outstring = re.sub(r"\W","_",textstring)
    return outstring

def is_key(dic,name):
    """Check whether or not name is a key in its category"""
    cat_name = dic[name]['_name.category_id']
    cat_block = dic.get(cat_name)
    if cat_block is not None:
        cat_keys = cat_block.get('_category_key.name',[])
        single_key = cat_block.get('_category.key_id','')
        return name in cat_keys or name == single_key
    print 'Warning: no block found for %s' % cat_name
    return False

def get_template_text(onedef,mainfilename,template_cache={}):
    """Return some text stating that the definition comes from a template"""
    import os.path
    def_text = 'Empty'
    if onedef.has_key('_import.get'):
        filename = onedef['_import.get'][0]['file']
        blockname = onedef['_import.get'][0]['save']
        if filename not in template_cache:
            basename = os.path.join(os.path.dirname(mainfilename),filename)
            template_cache[filename] = CifFile(basename,grammar="2.0")
        def_text = '(Generic definition) '+ prepare_text(template_cache[filename][blockname]['_description.text'])
    else:
        print 'No import found'
    return def_text

def analyse_deps(indic,in_directory="."):
    """Determine which dictionaries this builds on by looking for imports in
    the top category"""
    import os
    cats = indic.get_categories()
    head_cat = [a for a in cats if indic[a].get('_definition.class',None)=='Head'][0]
    imports = indic[head_cat].get('_import.get')
    if imports is None:
        return []
    full_imports = [d['file'] for d in imports if d.get("mode") == 'Full']
    return [CifDic(os.path.join(in_directory,i),grammar="2.0",do_minimum=True) for i in full_imports]

def locate_category(diclist,catname):
    """Find out which dictionary has catname as a category"""
    found_id = [d for d in diclist if catname.lower() in d.get_categories()]
    found_id = [d.master_block['_dictionary.title'] for d in found_id]
    if len(found_id)==1:
        return found_id[0]
    elif len(found_id) == 0:
        return 'External category not found'
    else:
        return 'Ambiguous external dictionary'

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        indic = sys.argv[1]
        final_doc = make_asciidoc(indic)
    else:
        print 'Usage: output_asciidoc <dictionary_name>. Output file will be <dictionary_name>.adoc'
