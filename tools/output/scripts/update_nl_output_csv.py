#!/usr/bin/env python3
# ---------------------------------------------------------------------------------------------------
#                           D E S C R I P T I O N
# ---------------------------------------------------------------------------------------------------
#
#  Author: Johannes Fjeldså
#
#  Date: 2025-04-23
#
#  This program will update the overview of output variables for a given history flag.
#
#  NOTE: It is assumed that the provided history file contains output variables that are
#        controlled by one history flag only.
#
#  License: ...
#
# ---------------------------------------------------------------------------------------------------

# -------------------
# Import libraries
# -------------------
import os
import warnings
import argparse
import pandas as pd
import xarray as xr
from pathlib import Path
from typing import Union, Optional
from utils import (
    dict2string,
    tuple2string,
    timed_input,
    robust_compare
)

# -------------------------
# Handle directory paths
# -------------------------
script_path = Path(__file__).resolve()
script_dir = script_path.parent
os.chdir(script_dir)
relative_path_alwaysoutputtedcsv = os.path.join(
    os.pardir,  # CAM/tools/output/
    'output_overview',  # CAM/tools/output/nl_output_overview/
    'alwaysoutputted.csv'
)
alwaysoutputtedcsv_path = Path(
    script_dir.joinpath(relative_path_alwaysoutputtedcsv)
).resolve()
nl_output_overview_path = alwaysoutputtedcsv_path.parent

# -------------------
# Helper functions
# -------------------
def extract_data_vars_info(
    hist_file_path: Optional[Union[Path, str]] = None,
    hist_file: Optional[xr.Dataset] = None
) -> pd.DataFrame:
    """Extract data variables information from a history file.

    Parameters
    ----------
    hist_file_path : Optional[Union[Path, str]], optional
        The path to the history file, by default None.
    hist_file : Optional[xr.Dataset], optional
        An open xarray dataset of the history file, by default None
        If provided, hist_file_path will be ignored.

    exits
    -----
    SystemExit
        If both hist_file and hist_file_path are None.
        If no history file is provided or if the file does not exist or is not a NetCDF file.

    warnings
    --------
    UserWarning
        If both hist_file and hist_file_path are provided, hist_file will be used.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing information about the data variables in the history file.
        The columns are: 'Name', 'Dimensions', 'Size', 'Data Type', 'Attributes'.
    """

    # check if the history file (path) is provided
    # if both are none, exit the program
    # if both are provided, use the xarray hist_file
    # if only hist_file_path is provided, check if the file exists
    # and if it is a NetCDF file
    # if not, exit the program
    if hist_file is None and hist_file_path is None:
        print("Error: No history file provided.")
        exit(1)
    elif hist_file is not None and hist_file_path is not None:
        warnings.warn(
            "Both hist_file and hist_file_path are provided. Using xarray hist_file."
        )
    elif hist_file_path is not None:
        if not os.path.exists(hist_file_path):
            print(f"Error: The history file {hist_file_path} does not exist.")
            exit(1)
        if not hist_file_path.endswith('.nc'):
            print(f"Error: The file {hist_file_path} is not a NetCDF file.")
            exit(1)
        hist_file = xr.open_dataset(hist_file_path)

    data_vars_info = pd.DataFrame({
        'Name': hist_file.data_vars.keys(),
        'Dimensions': [tuple2string(hist_file[var].dims) for var in hist_file.data_vars.keys()],
        'Size': [tuple2string(hist_file[var].shape) for var in hist_file.data_vars.keys()],
        'DataType': [hist_file[var].dtype for var in hist_file.data_vars.keys()],
        'Attributes': [dict2string(hist_file[var].attrs) for var in hist_file.data_vars.keys()]
    })

    return data_vars_info

def update_nl_output_csv(
    data_vars_info: pd.DataFrame,
    hist_flag: str,
    output_csv: Union[Path, str],
    remove_alwaysoutputted: bool = True
):
    """Update the overview of output variables for a given history flag.

    Parameters
    ----------
    data_vars_info : pd.DataFrame
        A DataFrame containing information about the data variables in the history file.
        If remove_alwaysoutputted is True, it is assumed that the DataFrame contains the 'Name' column.
    hist_flag : str
        The history flag to update the overview for.
    output_csv : Union[Path, str]
        The path to the output CSV file.
    remove_alwaysoutputted : bool, optional
        If True, remove the data variables that are not controlled by any history flag
        based on alwaysoutputtedcsv_path, by default True. If False, all data variables
        from data_vars_info will be included in the output CSV file.
    """

    # add the history flag to the data_vars_info DataFrame
    data_vars_info['HistFlag'] = hist_flag

    # remove the data variables that are not controlled by any history flag
    # base on alwaysoutputtedcsv_path
    if remove_alwaysoutputted:
        # remove the data variables that are always outputted
        # these are the ones that are not controlled by any history flag
        # and are not in the history file
        always_outputted_info = pd.read_csv(alwaysoutputtedcsv_path)
        for var in always_outputted_info['Name']:
            if var in data_vars_info['Name'].values:
                data_vars_info = data_vars_info[data_vars_info['Name'] != var]
        data_vars_info = data_vars_info.reset_index(drop=True)

    diff = None
    # check if the output CSV file exists
    # if it does not exist, create it
    # if it does exist, prompt the user to overwrite it
    if Path(output_csv).exists():

        overwrite = timed_input(
            f"The output CSV file {output_csv} already exists. \n Do you want to overwrite it? (y/n) [default: y]: ",
            timeout=15,
            default_output='y'
        )

        if overwrite.lower() != 'y':
            print("Exiting without overwriting the file.")
            exit(0)

        # if we are overwriting the file, we find the difference between the new and old data_vars_info
        old_data_vars_info = pd.read_csv(output_csv)

        diff = robust_compare(
            old_df=old_data_vars_info,
            new_df=data_vars_info,
            key_cols='Name'
        )

    data_vars_info.to_csv(output_csv, index=False)
    print(f'Saved data variables information to {output_csv}.')

    if diff is not None:
        print(f'Differences between old and new data_vars_info:')
        for key, value in diff.items():
            print(f'{key}: {value}')

def update_multiple_csvs(
    overview_hist: pd.DataFrame,
    remove_alwaysoutputted: bool = True
):
    """Update multiple CSV files with data variables information.

    Parameters
    ----------
    overview_csvs : pd.DataFrame
        A DataFrame containing the paths to the overview CSV files and the history flags.
    """

    for index, row in overview_hist.iterrows():
        hist_flag = row['HistFlag']
        output_csv = row['OutputCSV']
        hist_file_path = row['HistFilePath']

        data_vars_info = extract_data_vars_info(hist_file_path=hist_file_path)
        update_nl_output_csv(
            data_vars_info=data_vars_info,
            hist_flag=hist_flag,
            output_csv=output_csv,
            remove_alwaysoutputted=remove_alwaysoutputted
        )


if __name__ == "__main__":

    # make an overview of the history files and the corresponding output CSV files
    overview_hist_dict = {
        'HistFlag': [],
        'HistFilePath': [],
        'OutputCSV': []
    }

    #  clubb_history
    #overview_hist_dict['HistFlag'].append('clubb_history')
    #overview_hist_dict['HistFilePath'].append()
    #overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('clubb_history.csv'))
    #  clubb_rad_history
    #overview_hist_dict['HistFlag'].append('clubb_rad_history')
    #overview_hist_dict['HistFilePath'].append()
    #overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('clubb_rad_history.csv'))
    #  history_aero_optics
    overview_hist_dict['HistFlag'].append('history_aero_optics')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test14/atm/hist/NF1850norbc_f19_f19_20250313_test14.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_aero_optics.csv'))
    #  history_aerosol
    overview_hist_dict['HistFlag'].append('history_aerosol')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test12/atm/hist/NF1850norbc_f19_f19_20250313_test12.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_aerosol.csv'))
    #  history_amwg
    overview_hist_dict['HistFlag'].append('history_amwg')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250424_history_amwg/atm/hist/NF1850norbc_f19_f19_20250424_history_amwg.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_amwg.csv'))
    #  history_budget
    overview_hist_dict['HistFlag'].append('history_budget')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test15/atm/hist/NF1850norbc_f19_f19_20250313_test15.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_budget.csv'))
    #  history_chemistry
    overview_hist_dict['HistFlag'].append('history_chemistry')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test16/atm/hist/NF1850norbc_f19_f19_20250313_test16.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_chemistry.csv'))
    #  history_chemspecies_srf
    overview_hist_dict['HistFlag'].append('history_chemspecies_srf')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test17/atm/hist/NF1850norbc_f19_f19_20250313_test17.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_chemspecies_srf.csv'))
    #  history_clubb
    overview_hist_dict['HistFlag'].append('history_clubb')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test18/atm/hist/NF1850norbc_f19_f19_20250313_test18.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_clubb.csv'))
    #  history_dust
    overview_hist_dict['HistFlag'].append('history_dust')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test19/atm/hist/NF1850norbc_f19_f19_20250313_test19.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_dust.csv'))
    #  history_eddy
    #overview_hist_dict['HistFlag'].append('history_eddy')
    #overview_hist_dict['HistFilePath'].append()
    #overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_eddy.csv'))
    #  history_vdiag
    #overview_hist_dict['HistFlag'].append('history_vdiag')
    #overview_hist_dict['HistFilePath'].append()
    #overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_vdiag.csv'))
    #  history_waccm
    #overview_hist_dict['HistFlag'].append('history_waccm')
    #overview_hist_dict['HistFilePath'].append()
    #overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_waccm.csv'))
    #  history_waccmx
    #overview_hist_dict['HistFlag'].append('history_waccmx')
    #overview_hist_dict['HistFilePath'].append()
    #overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_waccmx.csv'))
    #  history_aerosol_base
    overview_hist_dict['HistFlag'].append('history_aerosol_base')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250425_history_aerosol_base/atm/hist/NF1850norbc_f19_f19_20250425_history_aerosol_base.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_aerosol_base.csv'))
    #  history_aerosol_decomposed
    overview_hist_dict['HistFlag'].append('history_aerosol_decomposed')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250425_history_aerosol_decomposed/atm/hist/NF1850norbc_f19_f19_20250425_history_aerosol_decomposed.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_aerosol_decomposed.csv'))
    #  history_gas
    overview_hist_dict['HistFlag'].append('history_gas')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250425_history_gas/atm/hist/NF1850norbc_f19_f19_20250425_history_gas.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_gas.csv'))
    #  history_aerosol_forcing
    overview_hist_dict['HistFlag'].append('history_aerosol_forcing')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250425_history_aerosol_forcing/atm/hist/NF1850norbc_f19_f19_20250425_history_aerosol_forcing.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_aerosol_forcing.csv'))
    #  history_aerosol_radiation
    overview_hist_dict['HistFlag'].append('history_aerosol_radiation')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250425_history_aerosol_radiation/atm/hist/NF1850norbc_f19_f19_20250425_history_aerosol_radiation.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_aerosol_radiation.csv'))
    #  history_aerosol_debug_output
    overview_hist_dict['HistFlag'].append('history_aerosol_debug_output')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250425_history_aerosol_debug_output/atm/hist/NF1850norbc_f19_f19_20250425_history_aerosol_debug_output.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('history_aerosol_debug_output.csv'))
    #  diag_cnst_conv_tend
    overview_hist_dict['HistFlag'].append('diag_cnst_conv_tend-all')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test24/atm/hist/NF1850norbc_f19_f19_20250313_test24.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('diag_cnst_conv_tend-all.csv'))
    #  do_circulation_diags
    overview_hist_dict['HistFlag'].append('do_circulation_diags')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test22/atm/hist/NF1850norbc_f19_f19_20250313_test22.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('do_circulation_diags.csv'))
    #  fv_am_diag
    overview_hist_dict['HistFlag'].append('fv_am_diag')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test23/atm/hist/NF1850norbc_f19_f19_20250313_test23.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('fv_am_diag.csv'))
    #  cosp
    overview_hist_dict['HistFlag'].append('cosp')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250314_test10/atm/hist/NF1850norbc_f19_f19_20250314_test10.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('cosp.csv'))
    #  aerocom
    overview_hist_dict['HistFlag'].append('aerocom')
    overview_hist_dict['HistFilePath'].append('/cluster/work/users/johannef/archive/NF1850norbc_f19_f19_20250313_test13/atm/hist/NF1850norbc_f19_f19_20250313_test13.cam.h0.0001-01.nc')
    overview_hist_dict['OutputCSV'].append(nl_output_overview_path.joinpath('aerocom.csv'))

    update_multiple_csvs(
        overview_hist=pd.DataFrame(overview_hist_dict),
        remove_alwaysoutputted=True
    )
