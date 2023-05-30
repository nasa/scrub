import re
import os
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
        for line in input_fh:
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

    # Make sure the inputs are pathlib objects
    source_root_dir = pathlib.Path(source_root_dir)
    filtering_output_file = pathlib.Path(filtering_output_file)
    filtering_options_file = pathlib.Path(filtering_options_file)
    initial_filtering_list = pathlib.Path(initial_filtering_list)

    # Print a status message
    logging.info('')
    logging.info('\tCreating analysis filtering list...')
    logging.info('\t>> Executing command: create_file_list.create_file_list(%s, %s, %s, %s)', source_root_dir,
                 filtering_output_file, filtering_options_file, initial_filtering_list)
    logging.info('\t>> From directory: %s', pathlib.Path.cwd())

    # Initialize the variables
    raw_file_list = []
    default_filtering_options_file = pathlib.Path(__file__).parent.joinpath('FilteringDefaults').resolve()

    # Create the list of all available files, if necessary
    if initial_filtering_list.is_file():
        # Read in the list
        with open(initial_filtering_list, 'r') as input_fh:
            raw_input_data = input_fh.readlines()

        # Strip whitespace from each element
        raw_file_list = []
        for index in range(len(raw_input_data)):
            if raw_input_data[index] != '\n':
                raw_file_list.append(raw_input_data[index].strip())

    else:
        for root, dir_names, file_names, in os.walk(source_root_dir, topdown=True):
            dir_names[:] = [d for d in dir_names if d not in ['.scrub', 'scrub_results']]
            for file_name in file_names:
                raw_file_list.append(os.path.join(root, file_name))

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
        try:
            regex_option = re.compile(filtering_option[1]).search
            for file_path in list(filter(regex_option, raw_file_list)):
                # if filtering_option[0] == '-' and os.path.exists(file_path):
                if filtering_option[0] == '-' and file_path in filtered_file_list:
                    logging.debug('\tRemoving file from filtering list: %s', file_path)
                    filtered_file_list.remove(file_path)

                # elif filtering_option[0] == '+' and os.path.exists(file_path):
                elif filtering_option[0] == '+':
                    logging.debug('\tAdding file to filtering list: %s', file_path)
                    filtered_file_list.append(file_path)
        except:
            logging.warning("\tUnable to process regex filter: {} {}".format(filtering_option[0], filtering_option[1]))
            logging.warning("\t\tPlease ensure this is a valid regex format.")

    # Print the results to the output file
    filtered_file_list.sort()
    with open(filtering_output_file, 'w') as output_fh:
        for filtered_file in filtered_file_list:
            if pathlib.Path(filtered_file).anchor == '/':
                relative_path = pathlib.Path(filtered_file).relative_to(source_root_dir)
            else:
                relative_path = pathlib.Path(filtered_file)
            output_fh.write('%s\n' % relative_path)
