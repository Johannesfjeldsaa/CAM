# CAM output controll

##  1. <a name='Readmecontent'></a>Readme content

<!-- vscode-markdown-toc -->
* 1. [Readme content](#Readmecontent)
* 2. [Prerequisits](#Prerequisits)
* 3. [Purpose](#Purpose)
* 4. [Directory description](#Directorydescription)
	* 4.1. [nl_output_oveview](#nl_output_oveview)
	* 4.2. [scripts](#scripts)
* 5. [Solving tasks](#Solvingtasks)
	* 5.1. [Get an overview of what output is available from CAM-OSLO](#GetanoverviewofwhatoutputisavailablefromCAM-OSLO)
	* 5.2. [Update the overview](#Updatetheoverview)
		* 5.2.1. [History output overview](#Historyoutputoverview)
		* 5.2.2. [History flags overview](#Historyflagsoverview)
	* 5.3. [Create the history part of user_nl_cam](#Createthehistorypartofuser_nl_cam)

<!-- vscode-markdown-toc-config
	numbering=true
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->

##  2. <a name='Prerequisits'></a>Prerequisits

An enviroment where python is available with the requirements is a prerequiste. To meet this run
```bash
python -m venv ~/.venvs/cam_output_venv 		# or <some_path_to_venv>
source ~/.venvs/cam_output_venv/bin/activate	# or <some_path_to_venv>/bin/activate
pip install -r requirements.txt
```

Note: this will put a virtual enviroment in your home directory ~200 Mb. If you want to remove it run
```bash
deactivate 										# if it is activated/sourced
rm -rf ~/.venvs/cam_output_venv 				# or <some_path_to_venv>
```

##  3. <a name='Purpose'></a>Purpose

This directory is meant as a tool to:

1. Get an overview of what output is available from CAM-OSLO.
2. Contain tools to update the overview.
3. Help create the history part of CAM's user namelist files (user_nl_cam) for a given set of outputs and guide other activations.

##  4. <a name='Directorydescription'></a>Directory description

To update Current content tables To update the overview run

```bash
echo "| filename | filesize |"
echo "| --- | --- |"
ls -lh | awk 'NR>1 {print "| " $9 " | " $5 " |"}'
```

inside of `nl_output_overview` and `script` directories, to get a print that can be pasted as replacement after updates in files.

###  4.1. <a name='nl_output_oveview'></a>nl_output_oveview

Holds .csv files with overview of which history flag governs what output. Togheter these files makes up an database of CAM-OSLO output. In addition it holds an overview of the default and valid values for these flags. See 4.1. [Get an overview of what output is available from CAM-OSLO](#GetanoverviewofwhatoutputisavailablefromCAM-OSLO) for a more in-debth description of file structures. Current content:

| filename | filesize |
| --- | --- |
| aerocom.csv | 21K |
| alwaysoutputted.csv | 1.8K |
| cosp.csv | 8.9K |
| diag_cnst_conv_tend-all.csv | 6.9K |
| do_circulation_diags.csv | 1.9K |
| fv_am_diag.csv | 1.7K |
| history_aero_optics.csv | 209 |
| history_aerosol_base.csv | 9.2K |
| history_aerosol.csv | 105K |
| history_aerosol_debug_output.csv | 718 |
| history_aerosol_decomposed.csv | 23K |
| history_aerosol_forcing.csv | 1.4K |
| history_aerosol_radiation.csv | 3.8K |
| history_amwg.csv | 18K |
| history_budget.csv | 25K |
| history_chemistry.csv | 14K |
| history_chemspecies_srf.csv | 4.4K |
| history_clubb.csv | 5.0K |
| history_dust.csv | 202 |
| historyflags.csv | 1020 |
| history_gas.csv | 2.1K |

###  4.2. <a name='scripts'></a>scripts

Holds scripts that allows you to performe all the tasks mentioned in 2. [Purpose](#Purpose). Current content:

| filename | filesize |
| --- | --- |
| display_output.py | 5.5K |
| inform_on_outputsettings.py | 10K |
| update_defaults_historyflagscsv.py | 8.0K |
| update_nl_output_csv.py | 17K |
| utils.py | 12K |

* `display_output.py`; the main function runs an interactive tabulate view of the output overview database. Run using
```bash
python scripts/display_output.py
```
See further description in 4.1. [Get an overview of what output is available from CAM-OSLO](#GetanoverviewofwhatoutputisavailablefromCAM-OSLO).

* `inform_on_outputsettings.py`; the main function yields input on how to setup the history part of your `user_nl_cam` file for a given set of wanted-outputs. The function expects one to two inputs:
  * `output_fields_csv`; string path to a csv of your wanted history. Must contain one column with the header name 'Name'.
  * `--verbose_suggestions`; bool used to regulate the print of reasoning behind suggestions.

Run using
```bash
python scripts/inform_on_outputsettings.py output_fields_csv --verbose_suggestions [True]/False
```
See further description in 4.3. [Create the history part of user_nl_cam](#Createthehistorypartofuser_nl_cam).

* `update_defaults_historyflagscsv.py`; the main function updates the `nl_output_overview/historyflags.csv` file based on the current namelist_definitions.xml file for CAM-OSLO. Run using 
```bash
python scripts/update_defaults_historyflagscsv.py
```
See further description in 4.2.2. [History flags overview](#Historyflagsoverview).

* `update_nl_output_csv.py`; An example use case is elaborated on in 4.2.1. [History output overview](#Historyoutputoverview).
* `utils.py`; Functions that are handy for the main scripts.

##  5. <a name='Solvingtasks'></a>Solving tasks

###  5.1. <a name='GetanoverviewofwhatoutputisavailablefromCAM-OSLO'></a>Get an overview of what output is available from CAM-OSLO

The output that is available in CAM-OSLO is stored as \*.csv files (excluding `historyflags.csv`) in `nl_output_overview`. All tables are formated with six columns:

* `Name`; the name of the outputfield e.g. 'AODDVIS', 'CLDMED', etc.
* `Dimensions`; the dimension names of the outputfield e.g. 'time', 'lat', etc.
* `Size`; the size of the dimensions e.g. 1, 96, ... .
* `DataType`; the datatype of the array as read by xarray in a standard simulation e.g. float32, float64.
* `Attributes`; description of the outputfield containing information such as 'units', 'long_name', etc. I.e. the information held by the history netcdf's .attrs.
* `HistFlag`; the history flag that governs wheter or not the outputfield is part of standard history output.

There are multiple ways to view the contents, however `scripts/display_output.py`provide a user-friendly interactive view of the whole database. To open this view:

1. Ensure that python is available (see prerequisits).
2. Run ```python scripts/display_output.py --rows_per_page 20``` where you can use `-r` or `--rows_per_page` followed by integer to adjust the numbers of rows shown in the table, by default 20.
3. Follow instructions.

###  5.2. <a name='Updatetheoverview'></a>Update the overview

####  5.2.1. <a name='Historyoutputoverview'></a>History output overview

The output tables are based on history output files. To update csv file(s) we run the `update_multiple_csvs(overview_hist, remove_alwaysoutputted)` python function. Here it is assumed that `overview_hist` is a pandas DataFrame object with columns:

* `HistFlag`; Name of the history flag that governs the output set e.g. 'history_aerosol', 'aerocom', etc.
* `HistFilePath`; Absolute file path to the history file that we will base the csv file on.
* `OutputCSV`; Absolute file path to the save location for the overview csv file.

Further `remove_alwaysoutputted` is a bool ([True], False) dictating whether or not the subset of history fields that are always outputted by CAM-Oslo ough to be removed. This, always outputted subset is kept in `nl_output_overview/alwaysoutputted.csv` and is updated similarly as the other output overviews but with all history flags turned off. An example of the update rutine is shown in `scripts/update_nl_output_csv.py`.

To make the prosess less manual create a script that are able to run and setup one case for each flag you want to update, then pass the `HistFilePath` from the runscripts to a similar setup as in `scripts/update_nl_output_csv.py`.

####  5.2.2. <a name='Historyflagsoverview'></a>History flags overview

In addition `nl_output_overview` holds an overview of the history flags `historyflags.csv` - a table of CAM-namelist flags, their default and valid values. This overview is based on the `cam/bld/namelist_definitions.xml` file. To update the overview run ```python update_defaults_historyflagscsv.py``` which will access the definitions files and update `historyflags.csv`. To add new flags to `historyflags.csv` write the flag name as a new entry in the csv file and run the python script. This will fill in default and valid values columns.

###  5.3. <a name='Createthehistorypartofuser_nl_cam'></a>Create the history part of user_nl_cam

The history from CAM-OSLO is gatekept by the history flags. Some which are activated via a bool statement in `user_nl_cam` and some which are activated by using `./xmlchange` commands. To get an overview of the settings that is needed for your wanted output create a csv file containing at least one column 'Name' with the history field names and save it at `output_fields_csv`. Additional information can be added to this csv but will not be used by the script. Next run

Run using
```bash
python scripts/inform_on_outputsettings.py output_fields_csv --verbose_suggestions [True]/False
```

which will inform on:
1. Variables that was not found in the database.
2. Which fields to include in fincl/fexcl.
3. Which history flags should have which bool.
