import os
import re
import pathlib
import logging


def parse_filtering_file(file_path):
    """This function parses a regex filtering file to obtain filtering options for SCRUB.

    Inputs:
        - file_path: Absolute path to regex filtering file [string]

    Outputs:
        - filtering_options: List of filtering options to be used [list of strings]
    """

    # Initialize variables
    filtering_options = []

    # Read in the default filtering options
    with open(file_path, 'r') as input_fh:
        # Iterate through every line of the file
        for line in input_fh.readlines():

            # Check to make sure the line is formatted correctly
            if len(line.strip()) > 2 and line.startswith(('-', '+')):
                # Append the filtering option
                if line[1] == ' ':
                    filtering_options.append((line[0], line.strip()[2:]))
            elif not line.startswith('#'):
                logging.warning('\tInvalid regex filtering line: {}'.format(line.strip()))

    return filtering_options


def create_file_list(source_root_dir, filtering_output_file, filtering_options_file, initial_filtering_list=''):
    """This function creates a list of the files that will be included in SCRUB analysis.

    Inputs:
        - source_root_dir: Absolute path to the source code root directory [string]
        - filtering_output_file: Absolute path to the output file containing a list of files to be included in analysis
                                 [string]
        - filtering_options_file: Absolute path to the filtering file to be used to create list of analysis files
                                  [string]
        - initial_filtering_list: Absolute path to the file containing an initial set of files [string]
    """

    # Print a status message
    logging.info('')
    logging.info('\tCreating analysis filtering list...')
    logging.info('\t>> Executing command: create_file_list.create_file_list(%s, %s, %s, %s)', source_root_dir,
                 filtering_output_file, filtering_options_file, initial_filtering_list)
    logging.info('\t>> From directory: %s', pathlib.Path.cwd())

    # Initialize the variables
    # filtering_options = []
    raw_file_list = []
    default_filtering_options_file = pathlib.Path(__file__).parent.joinpath('FilteringDefaults').resolve()

    # Create the list of all available files, if necessary
    if initial_filtering_list:
        # Read in the list
        with open(initial_filtering_list, 'r') as input_fh:
            raw_file_list = [pathlib.Path(line.strip()) for line in input_fh.readlines()]

    else:
        for item in source_root_dir.rglob('*'):
            if item.is_file():
                raw_file_list.append(item)

    # Read in the values from the filtering file and add them to the list
    if filtering_options_file.exists():
        # Print a status message
        logging.info('')
        logging.info('\tParsing input file.')

        # Parse the filtering file
        filtering_options = (parse_filtering_file(filtering_options_file) +
                             parse_filtering_file(default_filtering_options_file))

    else:
        # Print a warning message
        logging.info('')
        logging.info('\tNo filtering file was found or no filtering file was provided. Using default values.')

        # Parse the filtering file
        filtering_options = parse_filtering_file(default_filtering_options_file)

    # Modify the list based on the include and exclude options
    filtered_file_list = raw_file_list.copy()
    for filtering_option in filtering_options:
        for file_path in raw_file_list:
            if re.search(filtering_option[1], str(file_path)) and filtering_option[0] == '-' and file_path in filtered_file_list:
                filtered_file_list.remove(file_path)

            elif re.search(filtering_option[1], str(file_path)) and filtering_option[0] == '+' and file_path not in filtered_file_list:
                filtered_file_list.append(file_path)

    # Print the results to the output file
    with open(filtering_output_file, 'w') as output_fh:
        for filtered_file in filtered_file_list:
            if filtered_file.anchor == '/':
                relative_path = filtered_file.relative_to(source_root_dir)
            else:
                relative_path = filtered_file
            output_fh.write('%s\n' % relative_path)
