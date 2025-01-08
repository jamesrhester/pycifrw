# A program to check CIFs against dictionaries.
#
# Usage: validate_cif [-d dictionary_dir] -f dictionary file cifname
#
# We need option parsing:
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# Python 2,3 compatibility
try:
    from urllib2 import urlopen         # for arbitrary opening
    from urllib.parse import url2pathname
except:
    from urllib.request import urlopen,url2pathname

# Option parsing
from optparse import OptionParser
# We need our cif library:
import CifFile
import os
import urllib
import traceback

#
# return a CifFile object from an FTP location
def cif_by_ftp(ftp_ptr,store=True,directory="."):
    # print "Opening %s" % ftp_ptr
    if store:
        new_fn = os.path.split(url2pathname(ftp_ptr))[1]
        target = os.path.abspath(os.path.join(directory,new_fn))
        if target != ftp_ptr:
            response = urlopen(ftp_ptr)
            contents = response.read()
            open(target,"wb").write(contents)
            print("Stored {} as {}".format(ftp_ptr,target))
        print('Reading ' + target)
        ret_cif = CifFile.CifFile(target)
    else:
        ret_cif = CifFile.ReadCif(ftp_ptr)
    return ret_cif

# get a canonical CIF dictionary given name and version
# we use the IUCr repository file, perhaps stored locally

def locate_dic(dicname,dicversion,regloc="cifdic.register",store_dir = "."):
    register = cif_by_ftp(regloc,directory=store_dir)
    good_gen = register["validation_dictionaries"]
    dataloop = good_gen.GetLoop("_cifdic_dictionary.version")
    matches = [a for a in dataloop if getattr(a,"_cifdic_dictionary.name")==dicname and \
               getattr(a,"_cifdic_dictionary.version")==dicversion]
    if len(matches)==0:
        print( "Unable to find any matches for {} version {}".format(dicname,dicversion))
        return ""
    elif len(matches)>1:
        print( "Warning: found more than one candidate, choosing first.")
        print( map(str,matches))
    return getattr(matches[0],"_cifdic_dictionary.URL")    # the location

def parse_options():
    # define our options
    op = OptionParser(usage="%prog [options] ciffile", version="%prog 0.7")
    op.add_option("-d","--dict_dir", dest = "dirname", default = ".",
                  help = "Directory where locally stored dictionaries are located")
    op.add_option("-f","--dict_file", dest = "dictnames",
                  action="append",
                  help = "A dictionary name stored locally")
    op.add_option("-u","--dict-version", dest = "versions",
                  action="append",
                  help = "A dictionary version")
    op.add_option("-n","--name", dest = "iucr_names",action="append",
                  help = "Dictionary name as registered by IUCr")
    op.add_option("-s","--store", dest = "store_flag",action="store_true",
                  help = "Store this dictionary locally", default=True)
    op.add_option("-c","--canon-reg", dest = "registry",action="store_const",
                  const = "ftp://ftp.iucr.org/pub/cifdics/cifdic.register",
                  help = "Fetch and use canonical dictionary registry from IUCr")
    op.add_option("-m","--markup", dest = "use_html",action="store_true",
                  help = "Output result in HTML",default=False)
    op.add_option("-t","--is_dict", dest = "dict_flag", action="store_true",default=False,
                  help = "CI    y")
    op.add_option("-r","--registry-loc", dest = "registry",
                  default = "file:cifdic.register",
                  help = "Location of global dictionary registry (see also -c option)")
    op.add_option("-v", "--verbose_validation", action="store_true", default=False,
                    help="Log information in the validation process.")
    op.add_option("-w", "--verbose_import", action="store_true", default=False,
                    help="Log information in the dictionary importing process.")
    (options,args) = op.parse_args()
    # our logic: if we are given a dictionary file using -f, the dictionaries
    # are all located locally; otherwise, they are all located externally, and
    # we use the IUCr register to locate them.
    # create the dictionary file names

    import sys
    if len(sys.argv) <= 1:
        print( "No arguments given: use option --help to get a help message\n")
        exit

    return options,args


def execute_with_options(options,args):
    print(args)
    print()
    print(options)

    verbose_import = options.verbose_import
    verbose_validation = options.verbose_validation

    if options.dictnames:
        diclist = list(map(lambda a:os.path.join(options.dirname,a),options.dictnames))
        print( "Using following local dictionaries to validate:")
        for dic in diclist: print( "{}".format(dic))
        #fulldic = CifFile.CifFile_module.merge_dic(diclist,mergemode='overlay')
        fulldic = CifFile.CifFile_module.merge_dic(diclist, verbose_import=verbose_import, verbose_validation=verbose_validation)
    else:
        # print( "Locating dictionaries using registry at %s" % options.registry)
        dics = zip(options.iucr_names,options.versions)
        dicurls = map(lambda a:locate_dic(a[0],a[1],regloc=options.registry,store_dir=options.dirname),dics)
        diccifs = map(lambda a:cif_by_ftp(a,options.store_flag,options.dirname),dicurls)
        fulldic = CifFile.CifFile_module.merge_dic(diccifs, verbose_import=verbose_import, verbose_validation=verbose_validation)
        diclist = dicurls  # for use in reporting later

    f = CifFile.CifFile(fulldic)

    cif_file_name = args[0]
    # open the cif file
    with open(cif_file_name, "r") as f:
        cif_text = f.read()

    cf = CifFile.CifFile(cif_text,grammar="auto", from_str=True)

    cf_json = cf.to_json()
    print(cf_json)

    result = cf.get_parsing_result()

    # Some kind of parsing error occurred
    # Parsing errors are identified with negative codes
    if result[0] < 0:
        error_str = CifFile.print_cif_syntax_error(result, cif_file_name)
        cc = (False, None)

        return cc, error_str


    output_header(options.use_html,args[0],diclist)

    cc = CifFile.Validate(cf,dic= fulldic,isdic=options.dict_flag)
    report_str, dict_summary =  CifFile.validate_report(cc,use_html=options.use_html)

    print(report_str)
    output_footer(options.use_html)

    return cc, report_str

#
#  Headers and footers for HTML/ASCII output
#

def output_header(use_html,filename,dictionaries):
    prog_info =  "Validate_cif version 0.7, Copyright ANSTO 2005-2020\n"
    if use_html:
        print( "<html><head><title>PyCIFRW validation report</title></head>")
        print( '<style type="text/css">')
        print( " body {font-family: verdana, sans-serif;}")
        print( " body {margin-left: 5%; margin-right: 5%;}")
        print( " table{background: #f0f0f8;}")
        print( " h4 {background: #f0f8f0;}")
        print( "</style><body>")
        print( "<h1>Validation results for {}</h1>".format(filename))
        print( "<p>Validation performed by {}</p>".format(prog_info))
        print( "<p>Dictionaries used:<ul>")
        for one_dic in dictionaries:
            print( "<li>{}".format(one_dic))
        print( "</ul>")
    else:
        print( "Validation results for {}\n".format(filename))
        print( "Validation performed by {}".format(prog_info))
        print( "File validated against following dictionaries:")

        for one_dic in dictionaries:
            print( "    {}".format(one_dic))

def output_footer(use_html):
    if use_html:
        print( "</body></html>")

def main ():
    execute_with_options(*parse_options())

if __name__ == "__main__":
    main()
