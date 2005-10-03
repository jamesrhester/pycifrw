# A program to check CIFs against dictionaries.  
#
# Usage: check_cif [-d dictionary_dir] -f dictionary file cifname
#
# We need option parsing:
from optparse import OptionParser
# We need our cif library:
import CifFile
import os
import urllib
#
# return a CifFile object from an FTP location
def cif_by_ftp(ftp_ptr,store=True,directory="."):
    print "Opening %s" % ftp_ptr
    if store:
	new_fn = os.path.split(urllib.url2pathname(ftp_ptr))[1]
	target = os.path.join(directory,new_fn)
	if target != ftp_ptr:
            urllib.urlretrieve(ftp_ptr,target)
	    print "Stored %s as %s" % (ftp_ptr,target)
	ret_cif = CifFile.CifFile(target)
    else:
        ret_cif = CifFile.CifFile()
        raw_data = urllib.urlopen(ftp_ptr) 
        ret_cif.ReadCif(raw_data)
        raw_data.close()
    return ret_cif

# get a canonical CIF dictionary given name and version
# we use the IUCr repository file, perhaps stored locally

def locate_dic(dicname,dicversion,regloc="cifdic.register",store_dir = "."):
    register = cif_by_ftp(regloc,directory=store_dir)
    good_gen = register["validation_dictionaries"]
    versions = good_gen["_cifdic_dictionary.version"]
    names = good_gen["_cifdic_dictionary.name"]
    locations = good_gen["_cifdic_dictionary.URL"]
    together = map(None,names,versions,locations)
    matches = filter(lambda a:a[0]==dicname and a[1]==dicversion,together)
    if len(matches)==0 or len(matches)>1:
	print "Unable to unambiguously locate %s version %s" % (dicname,dicversion)
	exit()
    return matches[0][2]    # the location
    
def main ():
    # define our options
    op = OptionParser(usage="%prog [options] ciffile", version="%prog 0.5")
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
    op.add_option("-r","--registry-loc", dest = "registry",
		  default = "./cifdic.register",
		  help = "Location of global dictionary registry (see also -c option)")
    (options,args) = op.parse_args()
    # print a header
    print "Validate_cif version 0.5, Copyright ASRP 2005-\n"      
    # our logic: if we are given a dictionary file using -f, the dictionaries 
    # are all located locally; otherwise, they are all located externally, and
    # we use the IUCr register to locate them. 
    # create the dictionary file names
    if options.dictnames: 
        diclist = map(lambda a:os.path.join(options.dirname,a),options.dictnames)
	print "Using following local dictionaries to validate:"
	for dic in diclist: print "%s" % dic
	fulldic = CifFile.merge_dic(diclist)
    else:
	print "Locating dictionaries using registry at %s" % options.registry
	dics = map(None,options.iucr_names,options.versions)
        dicurls = map(lambda a:locate_dic(a[0],a[1],regloc=options.registry,store_dir=options.dirname),dics) 
	diccifs = map(lambda a:cif_by_ftp(a,options.store_flag,options.dirname),dicurls)
	fulldic = CifFile.merge_dic(diccifs)
    # open the cif file
    cf = CifFile.CifFile(args[0])
    print "\n"
    print CifFile.validate_report(CifFile.validate(cf,dic= fulldic))


if __name__ == "__main__":
    main()
