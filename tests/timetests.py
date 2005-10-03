# this simply reports time taken to parse a file
import time
import CifFile
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
    jj = CifFile.CifFile(file) 
    finish_time = time.time()
    print "File %s: %8.1f\n" % (file,finish_time - start_time)
    # try to validate  
for file,dic in valfiles:
    start_time = time.time()
    jj = CifFile.validate(file,dic=dic) 
    finish_time = time.time()
    print "Validate file %s: %8.1f\n" % (file,finish_time - start_time)
     


