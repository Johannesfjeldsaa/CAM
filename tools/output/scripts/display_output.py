
# -----------------------------
# Import necessary libraries
# -----------------------------
import os
import shutil
import textwrap
import pandas as pd
from tabulate import tabulate
from utils import make_concat_nl_output_overview

# -----------------------
# hard-coded constants
# -----------------------
EXCLUDE_FILES = {"historyflags.csv"}
ROWS_RESERVED_FOR_UI = 10  # Space for instructions, prompts, etc.

# -------------------
# Helper functions
# -------------------
def get_terminal_height():
    """Get the height of the terminal window.
    This is used to determine how many rows can be displayed in the interactive table.
    The number of rows reserved for UI elements is subtracted from the total height.

    Returns
    -------
    int
        The number of rows available for displaying the table.
    """
    return shutil.get_terminal_size().lines - ROWS_RESERVED_FOR_UI


def display_page(
    df:             pd.DataFrame,
    page:           int,
    rows_per_page:  int,
    term_width:     int
):
    """Render a page of the DataFrame in a terminal-friendly format.
    This function clears the terminal and displays a portion of the DataFrame

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to display.
    page : int
        The current page number.
    rows_per_page : int
        The number of rows to display per page.
    term_width : int
        The width of the terminal window.
    """

    # Clear the terminal screen
    os.system('clear' if os.name == 'posix' else 'cls')

    # calculate which part of the DataFrame to display
    start = page * rows_per_page
    end = start + rows_per_page
    page_df = df.iloc[start:end].copy()

    # Wrap 'Attributes' column as it is often too wide to display
    attr_wrap_width = max(term_width // 4, 40)
    if 'Attributes' in page_df.columns:
        page_df['Attributes'] = page_df['Attributes'].apply(
            lambda val: textwrap.fill(str(val), width=attr_wrap_width) if pd.notnull(val) else ""
        )

    # print the portion of the DataFrame to the terminal with available commands
    print(f"\n🔢 Showing rows {start + 1} to {min(end, len(df))} of {len(df)}\n")
    print(tabulate(page_df, headers='keys', tablefmt='fancy_grid', showindex=False))
    print("\nCommands: [n]ext | [p]revious | [q]uit | [number] go to page | /search-term")

def interactive_table(
    df:                 pd.DataFrame,
    rows_per_page:      int=20
):
    """Make the DataFrame interactive in the terminal.
    This function allows the user to navigate through the DataFrame using
    commands. The user can search for terms, go to specific pages, and
    navigate through the DataFrame interactively.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to display.
    rows_per_page : int, optional
        The number of rows to display per page, by default 20
    """

    # Get the terminal size
    term_width = shutil.get_terminal_size().columns
    # keep track of the original DataFrame and filtered DataFrame
    full_df = df.copy()
    filtered_df = full_df.copy()
    # keep track of the current page
    page = 0
    # make it possible to search and then recover the original DataFrame
    just_searched = False

    while True:
        total_pages = max((len(filtered_df) - 1) // rows_per_page + 1, 1)
        page = max(0, min(page, total_pages - 1))  # Clamp within range

        display_page(filtered_df, page, rows_per_page, term_width)

        user_input = input("\nCommand: ").strip()

        if user_input.lower() == 'q':
            break
        elif user_input.lower() == 'n':
            page += 1
            just_searched = False
        elif user_input.lower() == 'p':
            if just_searched:
                filtered_df = full_df.copy()
                page = 0
                just_searched = False
            else:
                page -= 1
        elif user_input.startswith('/'):
            term = user_input[1:].strip().lower()
            if term:
                mask = full_df.apply(
                    lambda row: row.astype(str).str.lower().str.contains(term).any(), axis=1
                )
                filtered_df = full_df[mask].copy()
                page = 0
                just_searched = True
            else:
                print("Empty search. No filtering applied.")
                just_searched = False
        elif user_input.isdigit():
            page = int(user_input)
            just_searched = False
        else:
            print("Invalid command.")
            just_searched = False

def __main__():
    """Main function to run the script.
    This function handles the loading of CSV files, filtering based on user input,
    and displaying the interactive table.
    """

    df = make_concat_nl_output_overview()

    # Filter based on specific columns, only available in the beginning
    print(f"\nAvailable columns: {', '.join(df.columns)}")
    filters = {}
    while True:
        col = input("Filter column (or press Enter to continue): ").strip()
        if not col:
            break
        if col not in df.columns:
            print(f"❌ Column '{col}' not found.")
            continue
        val = input(f"Value (substring match) to search in '{col}': ").strip()
        filters[col] = val

    # Apply filters
    for col, val in filters.items():
        df = df[df[col].astype(str).str.contains(val, case=False, na=False)]

    # After filtering open the interactive table
    interactive_table(df)

if __name__ == "__main__":
    __main__()