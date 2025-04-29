#!/usr/bin/env python3
# ---------------------------------------------------------------------------------------------------
#                           D E S C R I P T I O N
# ---------------------------------------------------------------------------------------------------
#
#  Author: Johannes Fjeldså
#
#  Date: 2025-04-23
#
#  This program will update the nl_output_overview/historyflags.csv file Default column
#  based on CAM/bld/namelist_files/namelist_definition.xml.
#  To get default values for new history flags add the new history flag to the
#  nl_output_overview/historyflags.csv file with empty Default and run this script.
#
#  License: ...
#
# ---------------------------------------------------------------------------------------------------

# -------------------
# Import libraries
# -------------------
import os
import pandas as pd
from pathlib import Path
from utils import robust_compare

# -------------------------
# Handle directory paths
# -------------------------
script_path = Path(__file__).resolve()
script_dir = script_path.parent
os.chdir(script_dir)
namelist_definition_path = Path(
    script_dir.joinpath(
        os.pardir, # CAM/tools/output/
        os.pardir, # CAM/tools/
        os.pardir, # CAM/
        'bld', # CAM/bld/
        'namelist_files', # CAM/bld/namelist_files/
        'namelist_definition.xml'
    )
).resolve()
historyflagscsv_path = Path(
    script_dir.joinpath(
        os.pardir, # CAM/tools/output/
        'nl_output_overview', # CAM/tools/output/nl_output_overview/
        'historyflags.csv'
    )
).resolve()

# -------------------
# Helper functions
# -------------------
def get_default_from_namelist_definition(
    namelist_definition_path: str,
    flag_name: str
) -> str:
    """Extract default from the namelist definition XML file.

    Parameters
    ----------
    namelist_definition_path : str
        Path to the namelist definition XML file.
    flag_name : str
        The name of the flag to look for in the XML file.

    Returns
    -------
    str
        The default value of the variable as a string ('.true.', '.false.' etc).
    """

    # Check if the file exists
    if not os.path.exists(namelist_definition_path):
        print(f"Error: The file {namelist_definition_path} does not exist.")
        exit(1)

    # str to look for in namelist_definition
    lookup_str = f'<entry id="{flag_name}"'
    # symbols to clean up the default value
    clean_up_symbols = ['<', '>', ' ', '/', ',', '"', "'"]

    # Read the XML file and extract default value
    with open(namelist_definition_path, 'r') as file:
        lines = file.readlines()

    for line_numb, line in enumerate(lines):
        # Check if the line contains the entry for the flag
        if lookup_str in line:

            # find the linenumber for Default line
            line_with_default_numb = line_numb
            next_numb = line_numb + 1

            while line_with_default_numb == line_numb:
                # Check if the line contains the 'Default: ' str
                if 'Default: ' in lines[next_numb]:
                    line_with_default_numb = next_numb

                next_numb += 1

            line_with_default = lines[line_with_default_numb]
            default = line_with_default.split(' ')[1].strip()
            # Clean up the default value
            for symbol in clean_up_symbols:
                default = default.replace(symbol, '')

    return default

def get_valid_values_from_namelist_definition(
    namelist_definition_path:   str,
    flag_name:                  str,
    assume_valid_if_empty:      list = ['.true.','.false.']
) -> list:
    """Get valid values from the namelist definition XML file.
    If no valid values are found, return a list of assumed valid values.

    Parameters
    ----------
    namelist_definition_path : str
        Path to the namelist definition XML file.
    flag_name : str
        The name of the flag to look for in the XML file.
    assume_valid_if_empty : list, optional
        List of valid values assumed if no valid values are found for entries, by default ['.true.','.false.']

    Returns
    -------
    list
        The valid values for a given namelist option.
    """

    # Check if the file exists
    if not os.path.exists(namelist_definition_path):
        print(f"Error: The file {namelist_definition_path} does not exist.")
        exit(1)

    # str to look for in namelist_definition
    lookup_str = f'<entry id="{flag_name}"'
    # symbols to clean up the default value
    clean_up_symbols = ['<', '>', ' ', '/', ',', '"', "'"]

    # Read the XML file and extract default value
    with open(namelist_definition_path, 'r') as file:
        lines = file.readlines()

    for line_numb, line in enumerate(lines):
        # Check if the line contains the entry for the flag
        if lookup_str in line:

            # the valid_values format is 'valid_values="value1, value2, value3"'
            # so we need to isolate the string between the quotes. There
            # might be multiple quotes in the line, so we need to find the
            # one following the valid_values=" string
            # find the linenumber for Default line
            line_with_validvalues_numb = line_numb
            next_numb = line_numb + 1

            while line_with_validvalues_numb == line_numb:
                # Check if the line contains the 'Default: ' str
                if 'valid_values=' in lines[next_numb]:
                    line_with_validvalues_numb = next_numb

                next_numb += 1
            line_with_validvalues = lines[line_with_validvalues_numb]

            start_index = line_with_validvalues.index('valid_values="') + len('valid_values="')
            end_index = line_with_validvalues.index('"', start_index)
            valid_values_str = line_with_validvalues[start_index:end_index]

            if len(valid_values_str) == 0:
                # if the valid values are empty, we use assume_valid_if_empty
                return assume_valid_if_empty

            # split the string into a list of values
            valid_values = valid_values_str.split(',')
            # clean up the values
            for i in range(len(valid_values)):
                valid_values[i] = valid_values[i].strip()
                for symbol in clean_up_symbols:
                    valid_values[i] = valid_values[i].replace(symbol, '')

    return valid_values

def __main__():
    """Open the historyflags.csv file and update the Default column using the namelist_definition.xml file.
    The function reads the historyflags.csv file, extracts the default values from the namelist_definition.xml file,
    and updates the Default column in the historyflags.csv file. The updated CSV file is then saved.
    The function also prints a message if updating the CSV file was successful and what is different.
    """

    # open the historyflags.csv file
    historyflags = pd.read_csv(historyflagscsv_path)

    # loop through the historyflags.csv file
    # and get the default value as well as valid values from the namelist_definition.xml file
    new_csv = historyflags.copy()
    for entry in historyflags.itertuples():
        default = get_default_from_namelist_definition(
            namelist_definition_path,
            entry.Name
        )

        valid_values = get_valid_values_from_namelist_definition(
            namelist_definition_path,
            entry.Name,
            assume_valid_if_empty=['.true.','.false.']
        )

        new_csv.loc[
            new_csv['Name'] == entry.Name,
            'Default'
        ] = default
        new_csv.loc[
            new_csv['Name'] == entry.Name,
            'Valid'
        ] = ', '.join(valid_values)

    # Save the new CSV file
    if not new_csv.equals(historyflags):
        try:
            new_csv.to_csv(historyflagscsv_path, index=False)
            print(f"Updated {historyflagscsv_path} with new default values.")
            diff = robust_compare(
                old_df=historyflags,
                new_df=new_csv,
                key_cols=['Name']
            )
            print(f'Differences between old and new historyflags.csv:')
            for key, value in diff.items():
                print(f'{key}: {value}')
        except Exception as error:
            print(f"Error: Could not save the updated CSV file. {error}")
            exit(1)
    else:
        print("No changes made to the CSV file. The default values are already up to date.")
        exit(0)


if __name__ == "__main__":
    # Run the main function to get the updated historyflags.csv file

    __main__()
