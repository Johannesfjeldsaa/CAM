# /usr/bin/env python3
# ---------------------------------------------------------------------------------------------------
#                           D E S C R I P T I O N
# ---------------------------------------------------------------------------------------------------
#
#  Author: Johannes Fjeldså
#
#  Date: 2025-04-28
#
#  The main function yields input on how to setup the history part of your `user_nl_cam` 
#  file for a given set of wanted-outputs.
#
#  License: ...
#
# ---------------------------------------------------------------------------------------------------

# -------------------
# Import libraries
# -------------------
import os
import argparse
import pandas as pd
from typing import Union
from pathlib import Path
from utils import (
    list2string,
    make_concat_nl_output_overview,
    get_reference_minus_intersection
)

# ---------------
# Handle Paths
# ---------------
script_dir = Path(__file__).resolve().parent
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

def fill_in_output_information(
    df:         Union[pd.DataFrame, pd.Series],
    verbose:    int = 0
) -> tuple(pd.DataFrame, list):
    """Add information from nl_output_overview to df. The common column 'Name' must be present.

    Parameters
    ----------
    df : pd.DataFrame or pd.Series
        DataFrame or Series to add information to. Must contain 'Name' column.
    verbose : int, optional
        Verbosity level, by default 0.
            If nonzero, print if variables are not found.
            If two or larger, print all variables that are found as well.

    Returns
    -------
    tuple(pd.DataFrame, list)
        The modified DataFrame with information and a list of variables that were not found.
    """

    # If df is a Series, convert it to a DataFrame
    if isinstance(df, pd.Series):
        df = df.to_frame()

    df_winfo = df.copy()
    # get the nl_output_overview DataFrame
    nl_output_overview = make_concat_nl_output_overview()

    # iterate over the rows of df and add the corresponding information from nl_output_overview
    # if the variable does not exist in nl_output_overview, add it to not_found
    not_found = []
    for row_indx, row in df_winfo.iterrows():
        # Get the variable name
        var_name = row['Name']

        # Check if the variable name exists in the nl_output_overview DataFrame
        if var_name in nl_output_overview['Name'].values:

            # check if the variable name is controlled by multiple flags
            histflags = nl_output_overview.loc[nl_output_overview['Name'] == var_name]['HistFlag'].tolist()
            histflags = list2string(histflags)

            # Get the corresponding row from nl_output_overview
            matching_row = nl_output_overview[nl_output_overview['Name'] == var_name]

            df_winfo.loc[row_indx, 'Dimensions'] = matching_row['Dimensions'].values[0]
            df_winfo.loc[row_indx, 'Size'] = matching_row['Size'].values[0]
            df_winfo.loc[row_indx, 'Attributes'] = matching_row['Attributes'].values[0]
            df_winfo.loc[row_indx, 'HistFlag'] = histflags

            if verbose >= 2:
                print(f"Found variable '{var_name}' in nl_output_overview.")

        else:
            if verbose != 0:
                print(f"Variable '{var_name}' not found in nl_output_overview.")
            not_found.append(var_name)

    return df_winfo, not_found

def all_used_historyflags(
    df_winfo: pd.DataFrame
) -> list:
    """Create a list of all history flags that govern output variables contained in df_winfo.
    Assums 'HistFlag' column exists and that if multiple flags are used for a variable, they are comma-separated.

    Parameters
    ----------
    df_winfo : pd.DataFrame
        DataFrame containing variable information. Assumes 'HistFlag' column exists.

    Returns
    -------
    list
        List of all history flags that govern output variables.
    """
    # Get all unique flag values from the 'HistFlag' column, splitting comma-separated entries
    all_flags = set()
    for flag in df_winfo['HistFlag'].unique():
        if isinstance(flag, str):
            # Split by comma and strip whitespace
            for f in flag.split(','):
                all_flags.add(f.strip())

    return list(all_flags)

def inform_on_outputs(
    df:                     Union[pd.DataFrame, pd.Series],
    verbose_suggestions:    bool = True
) -> pd.DataFrame:
    """Print information about how to ensure that all output variables contained in df are written to CAM history file.
    Also return a DataFrame with additional information on the output variables contained in df.

    Parameters
    ----------
    df : Union[pd.DataFrame, pd.Series]
        DataFrame or Series containing output variables, must contain 'Name' column.
    verbose_suggestions : bool, optional
        Print reasoning behind suggestions for fincl and fexcl, by default True. If set to False, the output will be more compact.

    Returns
    -------
    pd.DataFrame
        DataFrame with added information on the output variables contained in the database.
    """

    # ensure consistent lineshifts and tabs
    lineshift = '\n'
    tab = '   '

    # Get the overview of the default settings for history flags
    historyflags_df = pd.read_csv(
        historyflagscsv_path
    )

    # Get the information about the output fields
    if isinstance(df, pd.Series):
        df = df.to_frame()
    df_winfo, not_found = fill_in_output_information(
        df,
        verbose=0
    )

    # Check that all fields are found
    if len(not_found) > 0:
        print(
            ' *****************', lineshift,
            '*** NOT FOUND ***', lineshift,
            '*****************', lineshift
        )
        print(
            "These variables were not found in nl_output_overview:", lineshift,
            tab, list2string(not_found), lineshift,
            "Check the spelling of the variable names and search the database using `python display_output.py`",
            lineshift*2
            )

    # get all the history flags that is affected
    all_flags = all_used_historyflags(df_winfo)

    # Find the best option wrt user_nl_cam and inform on settings
    all_finclvars = set()
    all_fexclvars = set()
    flag_settings = ''

    print(
        ' *****************', lineshift,
        '*** MAIN INFO ***', lineshift,
        '*****************', lineshift
    )
    for flag in all_flags:

        fincl_print = False
        fexcl_print = False

        flag_df_winfo = df_winfo.loc[df_winfo['HistFlag'] == flag]
        if len(flag_df_winfo) > 0:

            fincl_list = flag_df_winfo['Name'].to_list()
            fincl_str = list2string(
                fincl_list,
                max_length=100
            )
            fexcl_list = get_reference_minus_intersection(
                reference_df=make_concat_nl_output_overview(include_files=f'{flag}.csv'),
                df=flag_df_winfo
            )["Name"].to_list()
            fexcl_str = list2string(
                fexcl_list,
                max_length=100
            )

            print(
                f"These variables are controlled by the {flag} flag:", lineshift,
                tab, fincl_str
            )
            if flag == 'aerocom':
                print(
                    "To enable calculation of these variables make sure that `CAM_AEROCOM` is set to True.",
                    "Check by running ", lineshift, "`./xmlquery CAM_AEROCOM` >>> <output>", lineshift,
                    "within the case directory. If it is FALSE, eddit by running", lineshift, "`./xmlchange CAM_AEROCOM=TRUE`.",
                    lineshift
                )
                fexcl_print = True
                flag_settings += 'run ./xmlchange CAM_AEROCOM=TRUE \n'

            elif flag == 'cosp':
                print(
                    "To enable calculation of these variables make sure that `CAM_CONFIG_OPTS` contains `-cosp`.",
                    "Check by running ", lineshift, "`./xmlquery CAM_CONFIG_OPTS`  >>> <output>", lineshift,
                    "within the case directory. If it is not present, eddit by running", lineshift,
                    "`./xmlchange CAM_CONFIG_OPTS='<output> -cosp'`.",
                    lineshift
                )
                fexcl_print = True
                flag_settings += 'add -cosp to CAM_CONFIG_OPTS \n'

            else:
                flag_default = historyflags_df[historyflags_df['Name'] == flag]['Default'].values[0]
                valid_values = historyflags_df[historyflags_df['Name'] == flag]['Valid'].values[0]
                if len(fexcl_str) <= len(fincl_str):
                    setting = 'true' if '.true.' in valid_values.split(', ') else 'all'
                    print(
                        f'fexcl is shorter => ensure {flag} = {setting} in user_nl_cam.', lineshift,
                        tab, 'Default; ', flag_default, lineshift,
                        tab, 'Valid; ', valid_values
                    )
                    fexcl_print = True

                else:

                    setting  = '.false.' if '.false.' in valid_values.split(', ') else 'none'
                    print(
                        f'fincl is shorter => ensure {flag} = {setting} in user_nl_cam.', lineshift,
                        tab, 'Default; ', flag_default, lineshift,
                        tab, 'Valid; ', valid_values
                    )
                    fincl_print = True

                flag_settings += f'{flag} = {setting}\n'

            if fexcl_print:
                all_fexclvars.update(set(fexcl_list))

                if verbose_suggestions:
                    print(
                        'To avoid unneccesarry output fexcl:', lineshift,
                        tab, fexcl_str,
                        lineshift*2
                    )
            elif fincl_print:
                all_finclvars.update(set(fincl_list))

                if verbose_suggestions:
                    print(
                        f'To get the intented output fincl:', lineshift,
                        tab, fincl_str,
                        lineshift*2
                    )
    print(
        ' ***************', lineshift,
        '*** SUMMARY ***', lineshift,
        '***************', lineshift,
    )
    print(
        'fincl', lineshift, tab, list2string(list(all_finclvars), max_length=100), lineshift,
        'fexcl', lineshift, tab, list2string(list(all_fexclvars), max_length=100), lineshift,
    )
    print(
        'flag settings', lineshift, tab, flag_settings
    )

    return df_winfo

def __main__():
    """Inform on output settings needed for a set of output fields.
    Takes one to two command line arguments:
    * output_fields_csv: Path to the overview of required output fields as a .csv.
    Note that there must be a header row containing "Name".
    * verbose_suggestions: Print reasoning behind suggestions for fincl and fexcl, default: True.
    If set to False, the output will be more compact.

    Raises
    ------
    ValueError
        If the parsed output_fields_csv does not contain a column named 'Name'.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'output_fields_csv',
        help='Path to the overview of required output fields as a .csv. Note that there must be a header row containing "Name".'
    )
    parser.add_argument(
        '--verbose_suggestions',
        default=True,
        help='Print reasoning behind suggestions for fincl and fexcl, default: True.'
    )

    args = parser.parse_args()

    outputfields = pd.read_csv(args.output_fields_csv)
    if 'Name' not in outputfields.columns:
        raise ValueError(
            f"The CSV file {args.output_fields_csv} does not contain a column named 'Name'."
            "Please add a header row containing 'Name' as header for the output field names."
        )

    inform_on_outputs(
        outputfields,
        verbose_suggestions=args.verbose_suggestions
    )

if __name__ == '__main__':

    __main__()