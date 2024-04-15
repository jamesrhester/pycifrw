import unittest
from optparse import Values

from validate_cif import execute_with_options

'''
Input is given in the following format.

Args:
['./cif_files/992E7Z7oL.cif']

Options:
{'dirname': 'dic_files', 'dictnames': ['cif_core_2.4.5.dic', 'cif_ms_1.0.1.dic'],
'versions': None, 'iucr_names': None, 'store_flag': True, 'registry': 'file:cifdic.register',
'use_html': False, 'dict_flag': False}

NOTE:
ALL THE FUNCTIONS MUST START WITH test_*
'''

class TestPycifrwCIF1_0(unittest.TestCase):

    def test_992E7Z7oL(self):
        '''
        Function to test the basic .cif file. The cif file is CORRECT.

        Command:

        python3 validate_cif.py -d dics/DDL1 -f cif_core_2.4.5.dic -f cif_ms_1.0.1.dic -f cif_iucr.dic
        -f cif_pd-mod.dic -f cif_third_party-mod.dic -f cif_twinning.dic -f jana-mod.dic
        ./cif_files/cif_1_0/correct_cif/992E7Z7oL.cif
        '''

        args = ['./cif_files/cif_1_0/correct_cif/992E7Z7oL.cif']
        options = Values()

        options.dirname = 'dics/DDL1'
        options.dictnames = [
            'cif_core_2.4.5.dic',
            'cif_ms_1.0.1.dic',
            'cif_iucr.dic',
            'cif_pd-mod.dic',
            'cif_third_party-mod.dic',
            'cif_twinning.dic',
            'jana-mod.dic'
        ]
        options.versions = None
        options.iucr_names = None
        options.store_flag = True
        options.registry = 'file:cifdic.register'
        options.use_html = False
        options.dict_flag = False
        options.verbose_import = False
        options.verbose_validation = False

        cc, report_str = execute_with_options(options, args)

        valid_result, no_matches = cc

        result = True

        for block in valid_result.keys():
            block_result = valid_result[block]

            if not block_result[0]:
                result = False

        self.assertTrue(result)

    def test_Fxhs6DE1VaT(self):
        '''
        Function to test the Fxhs6DE1VaT. The cif file is CORRECT.

        Command:

        python3 validate_cif.py -d dics/DDL1 -f cif_core_2.4.5.dic -f cif_ms_1.0.1.dic -f cif_iucr.dic
        -f cif_pd-mod.dic -f cif_third_party-mod.dic -f cif_twinning.dic -f jana-mod.dic
        ./cif_files/cif_1_0/correct_cif/Fxhs6DE1Vat.cif
        '''

        args = ['./cif_files/cif_1_0/correct_cif/Fxhs6DE1VaT.cif']

        options = Values()

        options.dirname = 'dics/DDL1'
        options.dictnames = [
            'cif_core_2.4.5.dic',
            'cif_ms_1.0.1.dic',
            'cif_iucr.dic',
            'cif_pd-mod.dic',
            'cif_third_party-mod.dic',
            'cif_twinning.dic',
            'jana-mod.dic'
        ]
        options.versions = None
        options.iucr_names = None
        options.store_flag = True
        options.registry = 'file:cifdic.register'
        options.use_html = False
        options.dict_flag = False
        options.verbose_import = False
        options.verbose_validation = False

        cc, report_str = execute_with_options(options, args)

        valid_result, no_matches = cc

        result = True

        for block in valid_result.keys():
            block_result = valid_result[block]

            if not block_result[0]:
                result = False

        self.assertTrue(result)

    def test_z034DL74QTM(self):
        '''
        Function to test the z034DL74QTM. The cif file is CORRECT.

        Command:

        python3 validate_cif.py -d dics/DDL1 -f cif_core_2.4.5.dic -f cif_ms_1.0.1.dic -f cif_iucr.dic
        -f cif_pd-mod.dic -f cif_third_party-mod.dic -f cif_twinning.dic -f jana-mod.dic
        ./cif_files/cif_1_0/correct_cif/z034DL74QTM.cif
        '''

        args = ['./cif_files/cif_1_0/correct_cif/z034DL74QTM.cif']

        options = Values()

        options.dirname = 'dics/DDL1'
        options.dictnames = [
            'cif_core_2.4.5.dic',
            'cif_ms_1.0.1.dic',
            'cif_iucr.dic',
            'cif_pd-mod.dic',
            'cif_third_party-mod.dic',
            'cif_twinning.dic',
            'jana-mod.dic'
        ]
        options.iucr_names = None
        options.store_flag = True
        options.registry = 'file:cifdic.register'
        options.use_html = False
        options.dict_flag = False
        options.verbose_import = False
        options.verbose_validation = False

        cc, report_str = execute_with_options(options, args)

        valid_result, no_matches = cc

        result = True

        for block in valid_result.keys():
            block_result = valid_result[block]

            if not block_result[0]:
                result = False

        self.assertTrue(result)

    def test_992E7Z7oL_full(self):
        '''
        Function to test the 992E7Z7oL.cif.full file. The cif file is INCORRECT.

        Command:

        python3 validate_cif.py -d dics/DDL1 -f cif_core_2.4.5.dic -f cif_ms_1.0.1.dic -f cif_iucr.dic
        -f cif_pd-mod.dic -f cif_third_party-mod.dic -f cif_twinning.dic -f jana-mod.dic
        ./cif_files/cif_1_0/incorrect_cif/992E7Z7oL.cif.full
        '''

        args = ['./cif_files/cif_1_0/incorrect_cif/992E7Z7oL.cif.full']

        options = Values()

        options.dirname = 'dics/DDL1'
        options.dictnames = [
            'cif_core_2.4.5.dic',
            'cif_ms_1.0.1.dic',
            'cif_iucr.dic',
            'cif_pd-mod.dic',
            'cif_third_party-mod.dic',
            'cif_twinning.dic',
            'jana-mod.dic'
        ]
        options.versions = None
        options.iucr_names = None
        options.store_flag = True
        options.registry = 'file:cifdic.register'
        options.use_html = False
        options.dict_flag = False
        options.verbose_import = False
        options.verbose_validation = False

        cc, report_str = execute_with_options(options, args)

        valid_result, no_matches = cc

        result = True

        for block in valid_result.keys():
            block_result = valid_result[block]

            if not block_result[0]:
                result = False

        # Notice that the CIF file is not valid
        self.assertFalse(result)

    def test_a7JwDmTmunB(self):
        '''
        Function to test the a7JwDmTmunB.cif file. The cif file is INCORRECT.

        Command:

        python3 validate_cif.py -d dics/DDL1 -f cif_core_2.4.5.dic -f cif_ms_1.0.1.dic -f cif_iucr.dic
        -f cif_pd-mod.dic -f cif_third_party-mod.dic -f cif_twinning.dic -f jana-mod.dic
        ./cif_files/cif_1_0/incorrect_cif/a7JwDmTmunB.cif
        '''

        args = ['./cif_files/cif_1_0/incorrect_cif/a7JwDmTmunB.cif']
        options = Values()

        options.dirname = 'dics/DDL1'
        options.dictnames = [
            'cif_core_2.4.5.dic',
            'cif_ms_1.0.1.dic',
            'cif_iucr.dic',
            'cif_pd-mod.dic',
            'cif_third_party-mod.dic',
            'cif_twinning.dic',
            'jana-mod.dic'
        ]
        options.versions = None
        options.iucr_names = None
        options.store_flag = True
        options.registry = 'file:cifdic.register'
        options.use_html = False
        options.dict_flag = False
        options.verbose_import = False
        options.verbose_validation = False

        cc, report_str = execute_with_options(options, args)

        valid_result, no_matches = cc

        result = True

        for block in valid_result.keys():
            block_result = valid_result[block]

            if not block_result[0]:
                result = False

        # Notice that the CIF file is not valid
        self.assertFalse(result)

    def test_ferro_embedded(self):
        '''
        Function to test the ferro_embedded.cif file. The cif file is INCORRECT.

        Command:

        python3 validate_cif.py -d dics/DDL1 -f cif_core_2.4.5.dic -f cif_ms_1.0.1.dic -f cif_iucr.dic
        -f cif_pd-mod.dic -f cif_third_party-mod.dic -f cif_twinning.dic -f jana-mod.dic
        ./cif_files/cif_1_0/incorrect_cif/ferro_embedded.cif
        '''

        args = ['./cif_files/cif_1_0/incorrect_cif/ferro_embedded.cif']
        options = Values()

        options.dirname = 'dics/DDL1'
        options.dictnames = [
            'cif_core_2.4.5.dic',
            'cif_ms_1.0.1.dic',
            'cif_iucr.dic',
            'cif_pd-mod.dic',
            'cif_third_party-mod.dic',
            'cif_twinning.dic',
            'jana-mod.dic'
        ]
        options.versions = None
        options.iucr_names = None
        options.store_flag = True
        options.registry = 'file:cifdic.register'
        options.use_html = False
        options.dict_flag = False
        options.verbose_import = False
        options.verbose_validation = False

        cc, report_str = execute_with_options(options, args)

        valid_result, no_matches = cc

        result = True

        for block in valid_result.keys():
            block_result = valid_result[block]

            if not block_result[0]:
                result = False

        # Notice that the CIF file is not valid
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()