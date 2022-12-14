# this simply reports time taken to parse a file
from __future__ import print_function
import time
from CifFile import ReadCif,Validate,CifDic
import cProfile
import pstats
testfiles = ['1wic.cif','ag03.cif','C13H22O3.cif','../dictionaries/cif_core.dic',
              '../dictionaries/mmcif_pdbx.dic','img2cif_packed.cif']
#cached_mmdic = CifDic('../dictionaries/mmcif_pdbx.dic',standard=None)
#cached_mmdic = CifDic('../dictionaries/mmcif_std_2.0.09.dic',standard=None)
cached_core = CifDic('../dictionaries/cif_core.dic')
#valfiles = [ ('ag03.cif',cached_mmdic),
#             ('C13H22O3.cif',cached_core)
valfiles = [
           ]

for file in testfiles:
    start_time = time.time()
    jj = ReadCif(file,scantype='flex',standard=None)      # no profiling, approx usage
    finish_time = time.time()
    print("File %s: wallclock time %8.1f\n" % (file,finish_time - start_time))
    cProfile.run("jj = ReadCif(file,scantype='flex',standard=None) ","profout")
    p = pstats.Stats( "profout")
    p.strip_dirs().sort_stats("cumulative").print_stats()
    # try to validate
for file,dic in valfiles:
    start_time = time.time()
    jj = Validate(file,dic=dic)
    finish_time = time.time()
    print("Validate file %s: %8.1f\n" % (file,finish_time - start_time))
