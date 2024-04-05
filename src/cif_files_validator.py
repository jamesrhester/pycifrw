"""
Python class for validating many cif files at once.

Usage Example:

    from cif_files_validator import CifFilesValidator

    cif_files_validator = CifFilesValidator()
    cif_files_validator(
        input_path=input_path,
        input_type=input_type,
        output_path=output_path,
        output_type=output_type,
        print_output=print_output,
        only_print_errors=only_print_errors,
        output_multiple_files=output_multiple_files,
        verbose_validation=verbose_validation,
        verbose_import=verbose_import
    )

Created by the Bilbao Crystallographic Server.
"""

from zipfile import ZipFile
from pathlib import Path
from typing import Generator, Tuple, List

import os
import shutil
import tarfile
import logging
import CifFile
import CifFile.yapps3_compiled_rt as yappsrt

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class CifFilesValidator:
    """
    Class for validating many cif files at once.

    Attributes:
        self.input_type_methods (dict): Dictionary to store the functions that read
            the cif files in different formats.
        self.output_type_methods (dict): Dictionary to store the functions that
            write the validation result in different formats.
        self.logger (Logger): Logger for printing information about the process.
    """


    def __init__(self) -> None:

        # Add methods to open different types of files
        self.input_type_methods = {}
        self.input_type_methods['zip'] = self.__open_zip
        self.input_type_methods['targz'] = self.__open_targz
        self.input_type_methods['path'] = self.__open_path

        # Add methods to write the output to different types of files
        self.output_type_methods = {}
        self.output_type_methods['md'] = self.__write_md
        self.output_type_methods['err'] = self.__write_err

        self.logger = logging.getLogger('info_logger')
        self.logger.setLevel(logging.INFO)

    def __open_zip(
        self,
        path: Path
    ) -> Tuple[List, str]:
        """Auxiliary function to extract the input cif files from
        a zip file. It extracts all the cif files to a ./temp
        directory, and afterwards read them with self.__read_path().

        Args:
            path (Path): Path of the zip file.

        Raises:
            FileNotFoundError: If the given path for the zip file
                does not exist.
            IsADirectoryError: If the given path is a directory.
            ValueError: If the given path is not a zip file.

        Returns:
            Generator: Generator for the input cif files.
        """

        # Make sure that the zip file has the correct format
        if not path.exists():
            raise FileNotFoundError("The selected input path does not exist.")

        if path.is_dir():
            raise IsADirectoryError("The given input path is a directory.")

        if path.suffix != ".zip":
            raise ValueError("The given input file is not a .zip file.")

        filename = path.stem

        # Create a temporal file to store all the cif file contents
        if not os.path.exists("./temp"):
            os.mkdir("./temp")

        if not os.path.exists("./temp/" + filename):
            os.mkdir("./temp/" + filename)

        # Path to the extracted files
        zip_file_path = Path("./temp/" + filename)

        # Extract the files
        with ZipFile(path, "r") as zf:
            zf.extractall(zip_file_path)
            self.logger.info("Cifs succesfully extracted to path: %s", zip_file_path)

        filenames, input_path = self.__open_path(zip_file_path)

        return filenames, input_path

    def __open_targz(
        self,
        path: Path
    ) -> Tuple[List, str]:
        """Auxiliary function to extract the input cif files from
        a .tar.gz file. It extracts all the cif files to a ./temp
        directory, and afterwards read them with self.__read_path().

        Args:
            path (Path): Path of the .tar.gz file.

        Raises:
            FileNotFoundError: If the given path for the .tar.gz file
                does not exist.
            IsADirectoryError: If the given path is a directory.
            ValueError: If the given path is not a zip file.

        Returns:
            Generator: Generator for the input cif files.
        """

        # Make sure that the .tar.gz file has the correct format
        if not path.exists():
            raise FileNotFoundError("The selected input path does not exist.")

        if path.is_dir():
            raise IsADirectoryError("The given input path is a directory.")

        if path.suffixes != ['.tar', '.gz']:
            raise ValueError("The given input file is not a .tar.gz file.")

        # Create a temporal file to store all the zif file contents
        if not os.path.exists("./temp"):
            os.mkdir("./temp")

        tar_file = tarfile.open(path, encoding="utf-8")
        temp_filename = path.parts[-1]
        filename = temp_filename.split(".")[0]

        # Path to the extracted files
        targz_file_path = Path("./temp/" + filename)

        # Extract the files
        tar_file.extractall(targz_file_path)
        self.logger.info("Cifs successfully extracted to path: %s.", targz_file_path)

        filenames, input_path = self.__open_path(targz_file_path)

        return filenames, input_path

    def __open_path(
        self,
        path: Path
    )-> Tuple[List, str]:
        """Auxiliary function to read all the cif files inside of a path.
        It returns a generator with the cif files, in an arbitrary order.

        Args:
            path (Path): Path of the input cif files.

        Raises:
            FileNotFoundError: If the given path does not exist.
            NotADirectoryError: If the given path is not a directory.
            ValueError: If the given path is empty.

        Returns:
            Generator: Generator for the input cif files.
        """
        # Check the input file
        if not path.exists():
            raise FileNotFoundError("The selected input path does not exist.")

        if not path.is_dir():
            raise NotADirectoryError("The given input path is not a directory.")

        # Get the generator of the input files
        filenames = []


        for temp in path.iterdir():
            temp_path = Path(temp)

            if temp_path.is_dir():
                temp_files, temp_dir = self.__open_path(temp_path)
                filenames.extend(temp_files)

            else:
                filenames.append(temp)

        if not filenames:
            raise ValueError("The given input path does not have any cif file.")

        self.logger.info("Cif files successfully loaded.")

        return filenames, path

    def __get_output_path(
        self,
        input_file: str,
        output_type: str
    ) -> list:
        """Function for getting the output names of the validation
        results for a given input cif.

        Args:
            input_file (str): Name of the input cif file.
            output_type (str): Format of the validation result file.

        Returns:
            list: List with the output names:
                output_path[0] => Name for the error file.
                output_path[1] => Name for the warning file.
        """

        # Get the root of the cif file
        temp_path = os.path.split(input_file)
        base_name = temp_path[-1]
        root_name = base_name.split(".")[0]

        # Get the output names depeding on format
        if output_type == "err":
            root_name_err= ".".join((root_name, "err"))
            root_name_warn = ".".join((root_name, "warn"))

            output_path_err = os.path.join("./", root_name_err)
            output_path_warn = os.path.join("./", root_name_warn)

            output_path = [output_path_err, output_path_warn]

        else:
            root_name_err = "_".join((root_name, "err"))
            root_name_warn = "_".join((root_name, "warn"))

            root_name_err = ".".join((root_name_err, "md"))
            root_name_warn = ".".join((root_name_warn, "md"))

            output_path_err = os.path.join("./", root_name_err)
            output_path_warn = os.path.join("./", root_name_warn)

            output_path = [output_path_err, output_path_warn]

        return output_path

    def __get_warnings(
        self,
        validation_output: dict,
        only_print_errors: bool,
    ) -> dict:
        """
        Function for getting only the warnings from the general validation
        result.

        Args:
            validation_output (dict): Validation result of all the input cif
                files.
            only_print_errors (bool): Whether to print the blocks that have
                any warning or error. If only_print_errors == True, the blocks
                that does not have any warning or error are not taken into
                account.

        Returns:
            dict: Dictionary containing the warnings of the validation.
        """
        warnings = {}

        # Iterate over all the cif files
        for cif_name, cif_validation_dict in validation_output.items():
            warnings[cif_name] = {}

            # Iterate per block
            for block_name, block_result in cif_validation_dict.get("blocks").items():
                block_has_warnings = block_result.get("has_warnings", False)

                # Retrive all the warnings, even if the block has not any
                if not only_print_errors:
                    warnings[cif_name][block_name] = block_result["warning_str"]

                # Only get the blocks that have warnings
                if only_print_errors and block_has_warnings:
                    warnings[cif_name][block_name] = block_result["warning_str"]


        return warnings

    def __get_errors(
        self,
        validation_output:dict,
        only_print_errors: bool
    ) -> dict:
        """
        Function for getting only the errors from the general validation
        result.

        Args:
            validation_output (dict): Validation result of all the input cif
                files.
            only_print_errors (bool): Whether to print the blocks that have
                any warning or error. If only_print_errors == True, the blocks
                that does not have any warning or error are not taken into
                account.

        Returns:
            dict: Dictionary containing the errors of the validation.
        """
        errors = {}

        # Iterate over all the cif files
        for cif_name, cif_validation_dict in validation_output.items():
            errors[cif_name] = {}

            # Iterate per block
            for block_name, block_result in cif_validation_dict.get("blocks").items():
                block_is_valid = block_result.get("is_valid", False)

                # Retrive all the errors, even if the block has not any
                if not only_print_errors:
                    errors[cif_name][block_name] = block_result["error_str"]

                # Only get the blocks that have errors
                if only_print_errors and not block_is_valid:
                    errors[cif_name][block_name] = block_result["error_str"]

        return errors



    def __filter_errors(
        self,
        validation_output: dict
    ) -> dict:
        """Function for filtering the validation output dictionary to include only
        the cifs and data blocks that have errors or warnings.

        Args:
            validation_output (dict): Full validation output dictionary.

        Returns:
            dict: Dictionary containing only the datablocks that have errors or warnings.
        """

        only_error_validation_output = {}
        for cif_name, cif_validation_dict in validation_output.items():
            cif_is_valid = cif_validation_dict.get("cif_is_valid", False)
            cif_has_warnings = cif_validation_dict.get("cif_has_warnings", False)

            # Only continue checking if
            # the cif has any kind of error or warning
            if not cif_is_valid or cif_has_warnings:

                # Copy the contents of the cif
                only_error_validation_output[cif_name] = {}
                only_error_validation_output[cif_name]["cif_is_valid"] = cif_is_valid
                only_error_validation_output[cif_name]["cif_has_warnings"] = cif_has_warnings
                only_error_validation_output[cif_name]["output_str"] = \
                    cif_validation_dict.get("output_str", "")
                only_error_validation_output[cif_name]["blocks"] = {}

                # Iterate throught the cif block
                for block_name, block_result in cif_validation_dict.get("blocks").items():
                    block_is_valid = block_result.get("is_valid", False)
                    block_has_warnings = block_result.get("has_warnings", False)

                    # Only add a block if its information is not valid
                    if not block_is_valid or block_has_warnings:
                        only_error_validation_output[cif_name]["blocks"][block_name] = block_result

        return only_error_validation_output

    def __write_cifs_to_md(
        self,
        output_dict: dict,
        output_path: str,
    ) -> None:
        """
        Function for writing the validation result of all the input cif
        files in a single markdown file.

        Args:
            output_dict (dict): Filtered validation result. It can be
                a dictionary with the errors or warnings.
            output_path (str): Path of the output file to write the
                results.
        """

        # All the results are written in a single file
        with open(output_path, "w", encoding="utf-8") as file:
            for cif_name, cif_result_dict in output_dict.items():
                # The cif does not have errors or warnings
                if not cif_result_dict.values():
                    continue

                cif_header = "## " + cif_name + "\n"

                file.write(cif_header)
                file.write("```shell\n")

                for block_result in cif_result_dict.values():
                    file.write(block_result + "\n")

                file.write("```\n")

        self.logger.info("Validation result generated at: %s.", output_path)


    def __write_single_cif_to_md(
        self,
        output_dict: dict,
        write_errors: bool
    ):
        """Function for writing the result of each of the input
        cif files into a single markdown file. A markdown file per
        input cif is generated.

        Args:
            output_dict (dict): iltered validation result. It can be
                a dictionary with the errors or warnings.
            write_errors (bool): Whether the result being written are
                errors or warnings.
        """

        # The validation is stored at "./validation_result"
        if not os.path.exists("./validation_result"):
            os.mkdir("./validation_result")

        # Iterate through each input cif
        for cif_path, cif_result_dict in output_dict.items():
            head_tail = os.path.split(cif_path)
            cif_name = head_tail[1].split(".")[0]

            if write_errors:
                cif_name = cif_name + "_cif_error.md"
            else:
                cif_name = cif_name + "_cif_warn.md"

            # Output filename
            cif_md_filename = os.path.join("validation_result", cif_name)

            # Create a md file per input cif
            with open(cif_md_filename, "w", encoding="utf-8") as file:
                cif_header = "## " + cif_name + "\n"

                file.write(cif_header)
                file.write("```shell\n")

                for block_result in cif_result_dict.values():
                    file.write(block_result + "\n")

                file.write("```\n")
                self.logger.info("Validation result generated at: %s.", cif_md_filename)



    def __write_md(
        self,
        validation_output: dict,
        input_path: str,
        only_print_errors: bool = False,
        output_multiple_files: bool = False
    ):
        """Function to write the validation result to markdown format.

        Args:
            validation_output (dict): Validation result of the input cif
                files.
            input_path (str): Input path of the cif files.
            only_print_errors (bool, optional): Whether to filter out the blocks
                without errors or warnings. If only_print_errors == True,
                All the correct blocks are removed from the result dictionary.
                Defaults to False.
            output_multiple_files (bool, optional): Whether to otuput a markdown
                file per input cif file. Defaults to False.
        """

        # Remove the correct blocks from the validation result
        if only_print_errors:
            validation_output = self.__filter_errors(validation_output)

        # Write all the results to a single markdown file
        if not output_multiple_files:
            errors = self.__get_errors(validation_output, only_print_errors)
            warnings = self.__get_warnings(validation_output, only_print_errors)

            output_paths = self.__get_output_path(input_path, "md")

            error_path = output_paths[0]
            warning_path = output_paths[1]

            self.__write_cifs_to_md(errors, error_path)
            self.__write_cifs_to_md(warnings, warning_path)

        else:
            # Generate a Markdown file per input cif file
            errors = self.__get_errors(validation_output, only_print_errors)
            warnings = self.__get_warnings(validation_output, only_print_errors)

            self.__write_single_cif_to_md(errors, True)
            self.__write_single_cif_to_md(warnings, False)


    def __write_cifs_to_err(
        self,
        output_dict: dict,
        output_path: str
    ):
        """
        Function for writing the validation result of all the input cif
        files in a single .err or .warn file.

        Args:
            output_dict (dict): Filtered validation result. It can be
                a dictionary with the errors or warnings.
            output_path (str): Path of the output file to write the
                results.
        """
        # A single .err/.warn file will be generated
        with open(output_path, "w", encoding="utf-8") as file:
            for cif_name, cif_result_dict in output_dict.items():
                # The cif does not have errors or warnings
                if not cif_result_dict.values():
                    continue
                header = "VALIDATION FOR CIF: " + str(cif_name)

                file.write(header)

                for block_result in cif_result_dict.values():
                    file.write(block_result)

                file.write("=============================================\n\n")

        self.logger.info("Validation result generated at: %s.", output_path)

    def __write_single_cif_to_err(
        self,
        output_dict: dict,
        write_errors: bool
    ):
        """
        Function for writing the result of each of the input
        cif files into a .err/.warn file. A .err/.warn file per
        input cif is generated.

        Args:
            output_dict (dict): iltered validation result. It can be
                a dictionary with the errors or warnings.
            write_errors (bool): Whether the result being written are
                errors or warnings.
        """

        # The validation is stored at "./validation_result"
        if not os.path.exists("./validation_result"):
            os.mkdir("./validation_result")

        for cif_path, cif_result_dict in output_dict.items():
            head_tail = os.path.split(cif_path)
            cif_name = head_tail[1].split(".")[0]

            if write_errors:
                cif_name = cif_name + "_cif.err"
            else:
                cif_name = cif_name + "_cif.warn"

            # Create output file name
            cif_filename = os.path.join("validation_result", cif_name)

            # Create a .err/.warn file per input cif
            with open(cif_filename, "w", encoding="utf-8") as file:
                header = "VALIDATION FOR CIF: " + str(cif_path)
                file.write(header)

                for block_result in cif_result_dict.values():
                    file.write(block_result)

                self.logger.info("Validation result generated at: %s.", cif_filename)

    def __write_err(
        self,
        validation_output: dict,
        input_path: str,
        only_print_errors: bool = False,
        output_multiple_files: bool = False
    ):
        """Function to write the validation result to .err/.warn format.
        All the errors will appear in the .err file, and the warning in
        the .warn file.

        Args:
            validation_output (dict): Validation result of the input cif
                files.
            input_path (str): Input path of the cif files.
            only_print_errors (bool, optional): Whether to filter out the blocks
                without errors or warnings. If only_print_errors == True,
                All the correct blocks are removed from the result dictionary.
                Defaults to False.
            output_multiple_files (bool, optional): Whether to otuput a .err/.warn
                file per input cif file. Defaults to False.
        """

        # Remove all the correct blocks from the validation dict
        if only_print_errors:
            self.logger.info("Only print errors selected. Filtering out the correct cifs.")
            validation_output = self.__filter_errors(validation_output)

        # Generate a single output file
        if not output_multiple_files:
            errors = self.__get_errors(validation_output, only_print_errors)
            warnings = self.__get_warnings(validation_output, only_print_errors)

            output_paths = self.__get_output_path(input_path, "err")
            error_path = output_paths[0]
            warning_path = output_paths[1]

            self.__write_cifs_to_err(errors, error_path)
            self.__write_cifs_to_err(warnings, warning_path)

        else:
            # Generate an output file per input cif
            errors = self.__get_errors(validation_output, only_print_errors)
            warnings = self.__get_warnings(validation_output, only_print_errors)

            self.__write_single_cif_to_err(errors, True)
            self.__write_single_cif_to_err(warnings, False)

    def __check_dictionaries_path(
        self,
        dirname: str,
        dictnames: list
    ) -> list:
        """Function that checks if the provided dictionary paths are
        correct. If all the paths are correct, it returns a list with
        the paths of the dictionaries.

        Args:
            dirname (str): Directory where the dictionaries are stored.
            dictnames (list): Names of the dictionaries that are stored
                at dirname.

        Raises:
            NotADirectoryError: If dirname is not a directory.
            FileNotFoundError: If any of the dictnames does not correspond
                to a file.

        Returns:
            list: List with the joined paths.
        """

        if not os.path.isdir(dirname):
            raise NotADirectoryError(f"The given dictionary path ({dirname}) does not exist.")

        joined_dictnames = list(map(lambda a:os.path.join(dirname,a),dictnames))

        for idx, joined_dictname in enumerate(joined_dictnames):
            if not os.path.isfile(joined_dictname):
                raise FileNotFoundError(f"The given dictionary path({joined_dictname}) does not exist.")

        return joined_dictnames


    def __get_merged_dictionaries(
        self,
        dictnames1_0: list,
        dictnames2_0: list,
        dirname1_0: str,
        dirname2_0: str,
        verbose_import: bool=False,
        verbose_validation: bool=False
    ) -> tuple:
        """Function to get the DDL1 and DDLm dictionaries that are going
        to be used for validation. This function does the merging of DDL1
        dictionaries and the importation of the DDLm dictionaries.

        Args:
            dictnames1_0 (list): DDL1 dictionaries names.
            dictnames2_0 (list): DDLm dictionaries names.
            dirname1_0 (str): Directory name where the DDL1 dictionaries
                are stored.
            dirname2_0 (str): Directory name where the DDLm dictionaries
                are stored.
            verbose_import (bool, optional): Whether to show the dictionary
                importation logging messages or not. Defaults to False.
            verbose_validation (bool, optional): Whether to show the logging
                messages in validation or not. Defaults to False.

        Returns:
            tuple: Tuple containing the validation dictionaries:
                tuple[0] ==> DDL1 dictionary.
                tuple[1] ==> DDLm dictionary.
        """

        # Merge all the DDL1 dictionaries
        diclist1_0 = self.__check_dictionaries_path(dirname1_0, dictnames1_0)
        fulldic1_0 = CifFile.CifFile_module.merge_dic(
            diclist1_0, verbose_import=verbose_import, verbose_validation=verbose_validation
        )

        self.logger.info("DDL1 dictionaries merged: %s", dictnames1_0)

        # Import all the DDLm dictionaries
        # Notice that the imported dictionaries may be inside of the
        # dictionary itself
        diclist2_0 = self.__check_dictionaries_path(dirname2_0, dictnames2_0)
        fulldic2_0 = CifFile.CifFile_module.merge_dic(
            diclist2_0, verbose_import=verbose_import, verbose_validation=verbose_validation
        )

        self.logger.info(
            "DDLm dictionaries successfully loaded: %s. Check also for the possible imported dictionaries.", dictnames2_0
        )
        return fulldic1_0, fulldic2_0

    def __print_cif_syntax_error(
        self,
        parsing_result: list,
        cif_file_name: str
    ) -> str:
        """Function for returning a syntax error, in case this happens.

        Args:
            parsing_result (list): List with the objects for getting
                the parsing error.
            cif_file_name (str): Name of the cif file that has the
                parsing error.

        Returns:
            str: Parsing error string.
        """
        error = parsing_result[1]

        # error[0] == -1
        if isinstance(error, yappsrt.YappsSyntaxError):
            parser = parsing_result[2]
            Y = parsing_result[3]

            scanner = parser._scanner
            input = parser._scanner.input
            pos = error.charpos

            line_number = scanner.get_line_number_with_pos(pos)

            out_str = "\n"
            out_str += "======================================================================\n"
            out_str += "\n"
            out_str += "SYNTAX ERROR AT LINE " + str(line_number) + " WHEN PARSING INPUT FILE:" + str(cif_file_name) + ":\n"
            out_str += str(error.msg) + "\n"
            out_str += "\n"
            out_str += "ERROR NEAR THE FOLLOWING INPUT TEXT:\n"

            text_error = Y.yappsrt.print_line_with_pointer(input, pos)

            out_str += text_error
            print(out_str)

            return out_str

        # error[0] == -2
        if isinstance(error, CifFile.StarError):
            print(error.value)

            return error.value

    def __validate_cif(
        self,
        cif_input_path: Path,
        fulldic1_0: CifFile.CifDic,
        fulldic2_0: CifFile.CifDic
    ) -> tuple:
        """Function to validate a singe cif.

        Args:
            cif_input_path (Path): Path of the input cif file.
            fulldic1_0 (CifFile.CifDic): DDL1 dictionary.
            fulldic2_0 (CifFile.CifDic): DDLm dictionary.

        Returns:
            tuple: Validation result of the cif.
                tuple[0] ==> String representing the whole validation.
                tuple[1] ==> Dictionary that represents the result.
        """

        # Parse the input cif
        cf = CifFile.CifFile(str(cif_input_path), grammar="auto")
        result = cf.get_parsing_result()
        output_dict = {}

        # The cif has syntax errors
        if result[0] < 0:
            error_str = self.__print_cif_syntax_error(result, cif_input_path)
            output_dict["output_str"] = error_str
            return error_str, output_dict

        # Determine the cif version
        if cf.grammar in ["1.0", "1.1"]:
            fulldic = fulldic1_0

        else:
            fulldic = fulldic2_0

        # Validate the cif
        cc = CifFile.Validate(cf, dic=fulldic, isdic=False)
        repor_str, dict_summary = CifFile.validate_report(cc, use_html=False)

        # Store the result in a more general dictionary
        output_dict["output_str"] = repor_str

        output_dict["cif_is_valid"] = dict_summary["cif_is_valid"]
        output_dict["cif_has_warnings"] = dict_summary["cif_has_warnings"]
        output_dict["blocks"] = dict_summary["blocks"]

        return repor_str, output_dict


    def __validate_cif_files(
        self,
        cif_files: Generator,
        dictionaries: dict,
        print_output: bool=False,
        verbose_validation: bool=False,
        verbose_import: bool=False
    ) -> dict:
        """General function to validate all the input cifs.

        Args:
            cif_files (Generator): Generator for the input cif filenames.
            dictionaries (dict): Dictionary containing the names and the
                directories of the DDL1 and DDLm dictionaries that will be used
                for validation.
            print_output (bool, optional): Whether to print the validation output
                of each of the cifs. Defaults to False.
            verbose_validation (bool, optional): Whether to log information in
                the validation process. Defaults to False.
            verbose_import (bool, optional): Whether to log information when
                importing the dictionaries. Defaults to False.

        Returns:
            dict: Dictionary containing the validation results of all the input cifs.
        """
        # Get DDL1 and DDLm dictionaries
        fulldic1_0, fulldic2_0 = self.__get_merged_dictionaries(
            dictnames1_0=dictionaries.get("ddl1_dictionaries"),
            dictnames2_0=dictionaries.get("ddlm_dictionaries"),
            dirname1_0=dictionaries.get("ddl1_dir"),
            dirname2_0=dictionaries.get("ddlm_dir"),
            verbose_validation=verbose_validation,
            verbose_import=verbose_import
        )

        validation_result = {}

        # Validate the cif files
        for cif_file in cif_files:
            cif_file = str(cif_file)
            repor_str, dict_summary = self.__validate_cif(cif_file, fulldic1_0, fulldic2_0)
            if print_output:
                print(repor_str)

            validation_result[cif_file] = dict_summary

        return validation_result


    def __get_input_path_type(
        self,
        input_path: Path
    ) -> str:
        """Function to automatically infer the format of the input data.
        It returns the format so that the file can be opened later.

        Args:
            input_path (Path): Path of the input file.

        Raises:
            ValueError: If the input file is not a file, a .zip or .tar.gz file.

        Returns:
            str: Extension of the input file.
        """
        if input_path.is_dir():
            return "path"

        if input_path.suffix == '.zip':
            return "zip"

        if input_path.suffix == '.gz':
            return "targz"

        raise ValueError("ERROR: Invalid input format. Only path, .zip and .tar.gz are accepted.")

    def __call__(
        self,
        input_path: str,
        output_type: str = None,
        print_output: bool = False,
        only_print_errors: bool = False,
        dictionaries: dict = {},
        output_multiple_files: bool = False,
        verbose_validation: bool = False,
        verbose_import: bool = False
    ) -> None:
        """Function for validating the input cifs. It reads, validates
        and writes the result to the desired format.

        Args:
            input_path (str): Input path of the input cifs.
            output_type (str, optional): Format of the output file. Defaults to None.
            print_output (bool, optional): Whether to print the validation output
                of each of the cifs. Defaults to False.
            only_print_errors (bool, optional): Whether to filter out the blocks
                without errors or warnings. If only_print_errors == True,
                All the correct blocks are removed from the result dictionary.
                Defaults to False.
            dictionaries (dict, optional): Dictionary containing the names and the
                directories of the DDL1 and DDLm dictionaries that will be used
                for validation.
            output_multiple_files (bool, optional): _description_. Defaults to False.
            verbose_import (bool, optional): Whether to show the dictionary
                importation logging messages or not. Defaults to False.
            verbose_validation (bool, optional): Whether to show the logging
                messages in validation or not. Defaults to False.
        """

        # Construct Path objects
        input_path = Path(input_path)

        # Open data
        try:
            input_type = self.__get_input_path_type(input_path)

        except ValueError as e:
            print(e)
            return -1

        input_data_function = self.input_type_methods[input_type]

        # Read the input cifs
        input_cifs, input_dir = input_data_function(input_path)

        # Validating the input cifs
        self.logger.info("Starting validation process.")
        try:
            validation_output = self.__validate_cif_files(
                input_cifs, dictionaries, print_output ,verbose_validation, verbose_import
            )

        except Exception as e:
            print(e)
            return -1

        self.logger.info("Validation process finished.")

        try:
            output_data_function = self.output_type_methods[output_type]

        except KeyError:
            print("The selected output type is incorrect.")

        # Write the validation result
        output_data_function(
            validation_output,
            input_path,
            only_print_errors,
            output_multiple_files
        )

        # Remove the temporal directory
        if input_data_function != "path":
            if input_dir.is_relative_to('./temp'):
                shutil.rmtree('./temp')

            else:
                shutil.rmtree(input_dir)

            self.logger.info("Temporal directory %s has been removed.", input_dir)
