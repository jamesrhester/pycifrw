"""
The CifFile module provides classes and methods for interacting with Crystallographic
Information Format (CIF) files.
"""
from __future__ import absolute_import
# print("Name is " + repr(__name__))
from .StarFile import StarError,ReadStar,StarList,apply_line_folding,apply_line_prefix
from .yapps3_compiled_rt import YappsSyntaxError as CifSyntaxError
from .CifFile_module import CifDic,CifError, CifBlock,ReadCif,ValidCifError,Validate,CifFile
from .CifFile_module import get_number_with_esd,convert_type,validate_report
from .CifFile_module import print_cif_syntax_error
from .StarFile import remove_line_prefix,remove_line_folding
from .StarFile import check_stringiness

__all__ = [ReadCif, CifFile, CifBlock, CifDic, CifError, ValidCifError, get_number_with_esd]
