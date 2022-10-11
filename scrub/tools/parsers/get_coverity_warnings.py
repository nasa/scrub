import sys
import json
import pathlib
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'coverity'


def parse_json(raw_input_file, parsed_output_file):
    """This function parses the Coverity internal JSON results format into SCRUB formatted results.

    Inputs:
        - raw_input_file: Absolute path to the file containing raw Coverity warnings [string]
        - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
    """

    # Initialize variables
    coverity_issues = []
    warning_count = 1

    # Read in the input file
    with open(raw_input_file, 'r') as input_fh:
        input_data = json.load(input_fh)

    # Iterate through every issue
    for issue in input_data['issues']:
        # Parse issue data
        warning_id = '%s%03d' % (ID_PREFIX, warning_count)
        warning_file = pathlib.Path(issue['mainEventFilePathname'])
        warning_line = int(issue['mainEventLineNumber'])
        warning_checker = issue['checkerName']
        warning_description = []

        # Get the warning description
        for event in issue['events']:
            if event['eventTag'] != 'caretline':
                warning_description.append('%s:%s:' % (event['strippedFilePathname'], event['lineNumber']))
                warning_description.append('%s: %s' % (event['eventTag'], event['eventDescription']))

        coverity_issues.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                warning_description, 'coverity', WARNING_LEVEL,
                                                                warning_checker))

        # Increment the warning count
        warning_count = warning_count + 1

    # Create the output file
    translate_results.create_scrub_output_file(coverity_issues, parsed_output_file)


if __name__ == '__main__':
    parse_json(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
