# this simply reports time taken to parse a file
import time
import CifFile
import profile
import pstats
testfiles = ['1YGG.cif','C13H22O3.cif','../dictionaries/cif_core.dic',
              '../dictionaries/mmcif_pdbx.dic']
#testfiles = []
cached_mmdic = CifFile.CifDic('../dictionaries/mmcif_pdbx.dic')
cached_core = CifFile.CifDic('../dictionaries/cif_core.dic')
valfiles = [ ('1YGG.cif',cached_mmdic), 
             ('C13H22O3.cif',cached_core)
           ]

for file in testfiles:
    start_time = time.time()
    jj = CifFile.ReadCif(file,scantype='flex')      # no profiling, approx usage
    finish_time = time.time()
    print "File %s: wallclock time %8.1f\n" % (file,finish_time - start_time)
    profile.run("jj = CifFile.ReadCif(file,scantype='flex') ","profout")
    p = pstats.Stats( "profout")
    p.strip_dirs().sort_stats("cumulative").print_stats()
    # try to validate  
for file,dic in valfiles:
    start_time = time.time()
    jj = CifFile.validate(file,dic=dic) 
    finish_time = time.time()
    print "Validate file %s: %8.1f\n" % (file,finish_time - start_time)
     


