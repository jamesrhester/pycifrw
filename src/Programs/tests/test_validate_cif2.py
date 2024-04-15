import unittest
from optparse import Values

from validate_cif import execute_with_options

class TestPycifrwCIF2_0(unittest.TestCase):


    def test_2212_stairlike_example(self):
        '''
        Function to test the  2212-stairlike-example.cif file. The cif file is CORRECT. The used dictionary imports
        cif_core, cif_ms and cif_twin.

        Command:

        python3 validate_cif.py -d dics/DDLm -f cif_mag.dic ./cif_files/cif_2_0/2212-stairlike-example.cif
        '''

        args = ['./cif_files/cif_2_0/correct_cif/2212-stairlike-example.cif']
        options = Values()

        options.dirname = 'dics/DDLm'
        options.dictnames = [
            'cif_mag.dic'
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

    def test_2212_cozn_example(self):
        '''
        Function to test the  Cozn-example.cif file. The cif file is CORRECT. The used dictionary imports
        cif_core, cif_ms and cif_twin.

        Command:

        python3 validate_cif.py -d dics/DDLm -f cif_mag.dic ./cif_files/cif_2_0/Cozn-example.cif
        '''

        args = ['./cif_files/cif_2_0/correct_cif/Cozn-example.cif']
        options = Values()

        options.dirname = 'dics/DDLm'
        options.dictnames = [
            'cif_mag.dic'
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

    def test_hexabrtellurate_example(self):
        '''
        Function to test the hexabrtellurate_example.cif file. The cif file is CORRECT. The used dictionary imports
        cif_core, cif_ms and cif_twin.

        Command:

        python3 validate_cif.py -d dics/DDLm -f cif_mag.dic ./cif_files/cif_2_0/hexabrtellurate_example.cif
        '''

        args = ['./cif_files/cif_2_0/correct_cif/hexabrtellurate-example.cif']
        options = Values()

        options.dirname = 'dics/DDLm'
        options.dictnames = [
            'cif_mag.dic'
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

    def test_levyclaudite_example(self):
        '''
        Function to test the levyclaudite_example.cif file. The cif file is CORRECT. The used dictionary imports
        cif_core, cif_ms and cif_twin.

        Command:

        python3 validate_cif.py -d dics/DDLm -f cif_mag.dic ./cif_files/cif_2_0/levyclaudite_example.cif
        '''

        args = ['./cif_files/cif_2_0/correct_cif/levyclaudite-example.cif']
        options = Values()

        options.dirname = 'dics/DDLm'
        options.dictnames = [
            'cif_mag.dic'
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

    def test_lillianite_example(self):
        '''
        Function to test the lillianite_example.cif file. The cif file is INCORRECT. The used dictionary imports
        cif_core, cif_ms and cif_twin.

        Command:

        python3 validate_cif.py -d dics/DDLm -f cif_mag.dic ./cif_files/cif_2_0/lillianite_example.cif
        '''

        args = ['./cif_files/cif_2_0/incorrect_cif/lillianite-example.cif']
        options = Values()

        options.dirname = 'dics/DDLm'
        options.dictnames = [
            'cif_mag.dic'
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

        self.assertFalse(result)

    def test_nepheline_example(self):
        '''
        Function to test the nepheline_example.cif file. The cif file is INCORRECT. The used dictionary imports
        cif_core, cif_ms and cif_twin.

        Command:

        python3 validate_cif.py -d dics/DDLm -f cif_mag.dic ./cif_files/cif_2_0/nepheline_example.cif
        '''

        args = ['./cif_files/cif_2_0/incorrect_cif/nepheline-example.cif']
        options = Values()

        options.dirname = 'dics/DDLm'
        options.dictnames = [
            'cif_mag.dic'
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

        self.assertFalse(result)


    def test_non_harmonic_adp_example(self):
        '''
        Function to test the lillianite_example.cif file. The cif file is INCORRECT. The used dictionary imports
        cif_core, cif_ms and cif_twin.

        Command:

        python3 validate_cif.py -d dics/DDLm -f cif_mag.dic ./cif_files/cif_2_0/Non-harmonic-ADP-example.cif
        '''

        args = ['./cif_files/cif_2_0/incorrect_cif/Non-harmonic-ADP-example.cif']
        options = Values()

        options.dirname = 'dics/DDLm'
        options.dictnames = [
            'cif_mag.dic'
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

        self.assertFalse(result)

    def test_sulfone_example(self):
        '''
        Function to test the lillianite_example.cif file. The cif file is INCORRECT. The used dictionary imports
        cif_core, cif_ms and cif_twin.

        Command:

        python3 validate_cif.py -d dics/DDLm -f cif_mag.dic ./cif_files/cif_2_0/sulfone-example.cif
        '''

        args = ['./cif_files/cif_2_0/incorrect_cif/sulfone-example.cif']
        options = Values()

        options.dirname = 'dics/DDLm'
        options.dictnames = [
            'cif_mag.dic'
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

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()