import os
import re
import logging


def move_warnings(warning_file, source_dir):
    """This function moves warnings to be co-located with the source file of interest.

    Inputs:
        - warning_file: Full path to the file containing SCRUB-formatted warnings [string]
        - source_dir: Full path to the top-level directory of the source code [string]

    Outputs:
        - A series of .scrub directories and output files will be created as necessary
    """

    # Initialize the variables
    warning_type = warning_file.split(os.sep)[-1].strip()

    # Print a status message
    logging.info('')
    logging.info('\tMoving results...')
    logging.info('\t>> Executing command: move_warnings.move_warnings(%s, %s)', warning_file, source_dir)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Import the warning file
    with open(warning_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Update the source root to make it absolute
    source_dir = os.path.abspath(source_dir)

    # Iterate through every line of the file
    for i in range(0, len(input_data)):
        # Set the line
        line = input_data[i]

        # Check to see if the line contains a warning
        if re.search(r'<.*>.*:.*:.*:', line):
            # Add the line to the warning text
            warning = line

            # Get the warning file
            warning_file = line.split(":")[1].strip()
            warning_file_absolute = os.path.normpath(source_dir + '/' + warning_file)

            # Make sure the warning file is within the source root, but not at the source root
            if os.path.exists(warning_file_absolute) and (source_dir != os.path.dirname(warning_file_absolute)):
                # Get the rest of the warning text
                j = i + 1
                while input_data[j].strip() != '':
                    warning = warning + input_data[j]

                    # Increment the line
                    j = j + 1

                # Get the warning directory
                warning_directory = os.path.dirname(warning_file_absolute)

                # Create the scrub output paths
                local_scrub_directory = os.path.normpath(warning_directory + '/.scrub')
                local_scrub_warning_file = os.path.normpath(local_scrub_directory + '/' + warning_type)

                # Create a .scrub directory if it doesn't already exists
                if not os.path.exists(local_scrub_directory):
                    os.mkdir(local_scrub_directory)
                    os.chmod(local_scrub_directory, 511)

                # Write the warning to the output file
                with open(local_scrub_warning_file, 'a') as output_fh:
                    output_fh.write('%s\n' % (warning.replace(warning_file, os.path.basename(warning_file))))

                # Change the permissions of the output file
                os.chmod(local_scrub_warning_file, 438)
