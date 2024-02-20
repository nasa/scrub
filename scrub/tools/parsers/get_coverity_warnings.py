import sys
import json
import pathlib
from scrub.tools.parsers import translate_results

ID_PREFIX = 'coverity'


def parse_json(raw_input_file, parsed_output_file):
    """This function parses the Coverity internal JSON results format into SCRUB formatted results.

    Inputs:
        - raw_input_file: Absolute path to the file containing raw Coverity warnings [string]

    Outputs:
        - coverity_issues: List of SCRUB formatted Coverity issues [list of SCRUB]
    """

    # Initialize variables
    warning_count = 1
    coverity_issues = []

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
        warning_description = issue['checkerProperties']['subcategoryLongDescription']
        warning_code_flow = []

        if issue['checkerProperties']['impact'].lower() == 'high':
            ranking = 'High'
        elif issue['checkerProperties']['impact'].lower() == 'medium':
            ranking = 'Med'
        elif issue['checkerProperties']['impact'].lower() == 'low':
            ranking = 'Low'
        elif issue['checkerProperties']['impact'].lower() == 'audit':
            ranking = 'Low'
        else:
            ranking = 'Low'

        # Get the warning description
        for event in issue['events']:
            if event['eventTag'] != 'caretline':
                event_file =event['strippedFilePathname']
                event_line = event['lineNumber']
                event_description = '{}: {}'.format(event['eventTag'], event['eventDescription'])
                # warning_description.append('{}:{}:'.format(event_file, event_line))
                # warning_description.append(event_description)

                # Add to the code flow
                warning_code_flow.append(translate_results.create_code_flow(event_file, event_line, event_description))

        coverity_issues.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                warning_description, 'coverity', ranking,
                                                                warning_checker, code_flow=warning_code_flow))

        # Increment the warning count
        warning_count = warning_count + 1

    # Create the output file
    translate_results.create_scrub_output_file(coverity_issues, parsed_output_file)


if __name__ == '__main__':
    parse_json(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
