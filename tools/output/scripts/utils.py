#!/usr/bin/env python3
# ---------------------------------------------------------------------------------------------------
#                           D E S C R I P T I O N
# ---------------------------------------------------------------------------------------------------
#
#  Author: Johannes Fjeldså
#
#  Date: 2025-04-24
#
#  This file holds utility functions for the scripts in this directory.
#
# ---------------------------------------------------------------------------------------------------

# -------------------
# Import libraries
# -------------------
import os
import sys
import time
import select
import subprocess
import pandas as pd
from pathlib import Path
from typing import Union, Optional

# --------
# Paths
# --------
script_dir = Path(__file__).resolve().parent

# ------------
# Functions
# ------------

def dict2string(dictionary: dict) -> str:
    """Convert a dictionary to a string representation.

    Parameters
    ----------
    dictionary : dict
        The dictionary to convert.

    Returns
    -------
    str
        The string representation of the dictionary.
    """
    return ', '.join([f"{key}: {value}" for key, value in dictionary.items()])

def tuple2string(tup: tuple) -> str:
    """Convert a tuple to a string representation.

    Parameters
    ----------
    tup : tuple
        The tuple to convert.

    Returns
    -------
    str
        The string representation of the tuple.
    """
    return ', '.join([str(item) for item in tup])

def list2string(lst: list, max_length: int = None) -> str:
    """
    Convert a list to a string representation with optional max line length.
    Each line will contain only full entries from the list.

    Parameters
    ----------
    lst : list
        The list to convert.
    max_length : int, optional
        Maximum number of characters per line. If None, no limit.

    Returns
    -------
    str
        The string representation of the list, wrapped to the specified line length.
    """
    if max_length is None:
        return ', '.join(str(item) for item in lst)

    lines = []
    current_line = ''
    for item in lst:
        item_str = str(item)
        # Determine if adding this item would exceed the max_length
        if current_line:
            # +2 for ', '
            next_length = len(current_line) + 2 + len(item_str)
        else:
            next_length = len(item_str)
        if next_length > max_length:
            if current_line:
                lines.append(current_line)
            current_line = item_str
        else:
            if current_line:
                current_line += ', ' + item_str
            else:
                current_line = item_str
    if current_line:
        lines.append(current_line)
    return '\n'.join(lines)


def timed_input(
    prompt: str,
    timeout: int = 15,
    default_output: Union[str, None] = None
    ) -> Union[str, None]:
    """Get user input with timeout

    Parameters
    ----------
    prompt : str
        Text to prompt user.
    timeout : int, optional
        Timeout in seconds, by default 15.
    default_output : str, optional
        Default output to return if timeout occurs, by default None.

    Returns
    -------
    Union[str, None]
        User input, or default_output if timeout.
    """
    print(prompt, end='', flush=True)
    start_time = time.time()

    if sys.stdin.isatty():
        # Interactive mode
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            return sys.stdin.readline().strip()
    else:
        # Non-interactive mode
        while True:
            if time.time() - start_time > timeout:
                break
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.readline().strip()
            time.sleep(0.1)

    print('\nInput timed out')
    return default_output

def run_command(
    cmd:        str,
    error_msg:  str,
    cwd:        Optional[str]
):
    """Run command-line command via subprocess.run with error handling

    Parameters
    ----------
    cmd : str
        The command to run
    error_msg : str
        Error message to print.
    cwd : str, optional
        Working directory if command should be run in a different directory, by default None, i.e. the current directory is used.
    """
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd, executable="/bin/bash")
    except subprocess.CalledProcessError as error:
        print(f"ERROR ({error.returncode}): {error_msg}")
        exit(error.returncode)

def robust_compare(
    old_df:     pd.DataFrame,
    new_df:     pd.DataFrame,
    key_cols:   Union[list, str]=None
) -> dict:
    """Compare two DataFrames, ignoring index, focusing on new, removed, and changed rows.
    It is assumed that the DataFrames have the same columns, but not necessarily the same index.

    Parameters
    ----------
        old_df : pd.DataFrame
            The original DataFrame.
        new_df : pd.DataFrame
            The new DataFrame to compare against the original.
        key_cols : list or str, optional
            Column(s) to use as unique key(s). If None, uses intersection of columns.

    Returns
    -------
        dict: Dictionary with keys 'new_rows', 'removed_rows', 'changed_rows' and
        their corresponding DataFrames if any changes were found.
    """
    # Guess key columns if not provided
    if key_cols is None:
        common_cols = list(set(old_df.columns) & set(new_df.columns))
        if not common_cols:
            raise ValueError("No common columns to use as keys.")
        key_cols = common_cols

    # Ensure key_cols is a list
    if isinstance(key_cols, str):
        key_cols = [key_cols]

    # Find new and removed rows
    old_keys = old_df[key_cols].drop_duplicates()
    new_keys = new_df[key_cols].drop_duplicates()

    # New rows: keys in new_df but not in old_df
    new_rows = new_df.merge(old_keys, on=key_cols, how='left', indicator=True)
    new_rows = new_rows[new_rows['_merge'] == 'left_only'].drop('_merge', axis=1)

    # Removed rows: keys in old_df but not in new_df
    removed_rows = old_df.merge(new_keys, on=key_cols, how='left', indicator=True)
    removed_rows = removed_rows[removed_rows['_merge'] == 'left_only'].drop('_merge', axis=1)

    # Changed rows: keys in both, but other columns differ
    # Merge on keys, suffix columns
    merged = pd.merge(
        old_df, new_df, on=key_cols, how='inner', suffixes=('_old', '_new')
    )
    value_cols = [col for col in old_df.columns if col not in key_cols]
    changed_rows = pd.DataFrame()
    for col in value_cols:
        diff = merged[merged[f"{col}_old"] != merged[f"{col}_new"]]
        if not diff.empty:
            changed_rows = pd.concat([changed_rows, diff], axis=0)
    changed_rows = changed_rows.drop_duplicates(subset=key_cols)

    return {
        'new_rows': new_rows.reset_index(drop=True) if not new_rows.empty else None,
        'removed_rows': removed_rows.reset_index(drop=True) if not removed_rows.empty else None,
        'changed_rows': changed_rows.reset_index(drop=True) if not changed_rows.empty else None
    }

def make_concat_nl_output_overview(
    include_files: Optional[list] = None,
    exclude_files: Optional[list] = None
)-> pd.DataFrame:
    """Make a concatenated DataFrame from all CSV files in the nl_output_overview directory.
    This function reads all CSV files in the nl_output_overview directory, excluding
    specified files, and concatenates them into a single DataFrame. The resulting DataFrame
    serves as a comprehensive overview of the output files.

    Parameters
    ----------
    include_files : Optional[list], optional
        The files to include in the overview, if default None is used, all files are included except those in exclude_files.
        If a list is provided, only those files will be included.
    exclude_files : Optional[list], optional
        The files to exclude from the overview, if default None is used, the following files are excluded:
        'nl_output_overview.csv', 'nl_output_overview_*.csv', 'historyflags.csv'.

    If there is an overlap between include_files and exclude_files, a warning is printed and the user is prompted for action.

    Returns
    -------
    pd.DataFrame
        The concatenated DataFrame.
    """

    # handle directories and paths
    csv_dir = script_dir.joinpath(
        os.pardir,              # CAM/tools/output/
        'nl_output_overview'    # CAM/tools/output/nl_output_overview/
    ).resolve()

    # Set defaults for optional parameters
    include_files = csv_dir.glob(include_files) if include_files is not None else csv_dir.glob("*.csv")
    if not isinstance(include_files, list):
        include_files = list(include_files)
    exclude_files = exclude_files if exclude_files is not None else [
        'nl_output_overview.csv',
        'nl_output_overview_*.csv',
        'historyflags.csv'
    ]
    if not isinstance(exclude_files, list):
        exclude_files = list(exclude_files)

    if any(file in include_files for file in exclude_files):
        print("Warning: There is an overlap between include_files and exclude_files.")
        user_input = timed_input(
            "Which files do you want to keep? (include/exclude) [default: include]: ",
            timeout=60,
            default_output='include'
        )
        if user_input.lower() == 'exclude':
            include_files = [file for file in include_files if file not in exclude_files]
        else:
            if user_input.lower() != 'include':
                print("Invalid input. Using default (include_files).")

            exclude_files = [file for file in exclude_files if file in include_files]

    # Load and merge CSV files (ignore EXCLUDE_FILES)
    nl_output_overview = pd.concat([
        pd.read_csv(file) for file in include_files
        if file.name not in exclude_files
    ], ignore_index=True)

    return nl_output_overview

def get_intersection(
    reference_df: pd.DataFrame,
    df: pd.DataFrame,
    column: str = 'Name'
) -> pd.DataFrame:
    """Returns the intersection of two DataFrames based on a specified column.

    Parameters
    ----------
    reference_df : pd.DataFrame
        The reference DataFrame.
    df : pd.DataFrame
        The DataFrame to compare with the reference.
    column : str, optional
        The column name to use for intersection, by default 'Name'.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing rows from the intersection of both DataFrames
        based on the specified column.
    """
    return pd.merge(reference_df, df, on=column, how='inner')

def get_reference_minus_intersection(
    reference_df:   pd.DataFrame,
    df:             pd.DataFrame,
    column:         str='Name'
) -> pd.DataFrame:
    """Returns rows from reference_df where 'column' values are NOT present in other_df.

    Parameters
    ----------
    reference_df : pd.DataFrame
        The reference DataFrame.
    df : pd.DataFrame
        The DataFrame to compare with the reference.
    column : str, optional
        The column name to use for reference minus intersection, by default 'Name'.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing rows from reference_df where 'column' values
        are NOT present in df.
    """
    return reference_df[~reference_df[column].isin(df[column])].reset_index(drop=True)