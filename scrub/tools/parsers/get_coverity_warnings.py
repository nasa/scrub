import re
import json
import gzip
import pathlib
import xml.etree.ElementTree
from scrub.tools.parsers import translate_results

ID_PREFIX = 'coverity'
warning_count = 1


def parse_cc(raw_input_file, threshold):
    """ This function parses Coverity metrics data to look for functions with high cyclomatic complexity.

    Inputs:
        - raw_input_file: Absolute path to raw Coverity function metrics file [string]
        - threshold: Cyclomatic complexity threshold for identifying violations [int]
        - warning_count: Starting point for warning identifiers [int]

    Outputs:
        - coverity_cc_findings: List of SCRUB formatted findings that violate the CC threshold [list of SCRUB]
    """

    # Initialize variables
    global warning_count
    coverity_cc_findings = []

    # Import the metrics file data
    with gzip.open(raw_input_file, 'rb') as input_fh:
        raw_metrics_data = xml.etree.ElementTree.fromstring('<root>' + str(input_fh.read()) + '</root>')

    # Gather the CC data
    for function_metrics in raw_metrics_data.findall('fnmetric'):
        # Get the file path
        file_path = function_metrics.find('file').text

        # Get the function name
        function_name = function_metrics.find('names').text.split(':')[-1].replace(';', '')

        # Get the metrics data
        function_metrics_data = function_metrics.find('metrics').text.split(';')
        cyclomatic_complexity = int(function_metrics_data[6].split(':')[-1])

        # Check the cyclomatic complexity value
        if cyclomatic_complexity > threshold:
            with open(file_path, 'r') as input_fh:
                for line_number, line in enumerate(input_fh):
                    if re.search(function_name + ".*\(.*\)", line.strip()):
                        warning_id = '%s%03d' % (ID_PREFIX, warning_count)
                        warning_file = pathlib.Path(file_path)
                        ranking = 'LOW'
                        warning_checker = 'SCRUB.HIGH_CC'
                        warning_description = ['High cyclomatic complexity found in function: %s' % function_name,
                                               'Cyclomatic complexity of function is %d, '
                                               'which exceeds the defined threshold of %d. '
                                               'Refactor this function to lower the cyclomatic complexity.' %
                                               (cyclomatic_complexity, threshold)]

                        coverity_cc_findings.append(translate_results.create_warning(warning_id, warning_file,
                                                                                     line_number, warning_description,
                                                                                     'coverity', ranking,
                                                                                     warning_checker))

                        # Increment the warning count
                        warning_count = warning_count + 1
                        break

    return coverity_cc_findings


def parse_json(raw_input_file):
    """This function parses the Coverity internal JSON results format into SCRUB formatted results.

    Inputs:
        - raw_input_file: Absolute path to the file containing raw Coverity warnings [string]

    Outputs:
        - coverity_issues: List of SCRUB formatted Coverity issues [list of SCRUB]
    """

    # Initialize variables
    global warning_count
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
        warning_description = issue['checkerProperties']['subcategoryLongDescription'].encode("unicode_escape").decode("utf-8")
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
                event_description = '{}: {}'.format(event['eventTag'],
                                                    event['eventDescription']).encode("unicode_escape").decode("utf-8")

                # Add to the code flow
                warning_code_flow.append(translate_results.create_code_flow(event_file, event_line, event_description))

        coverity_issues.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                warning_description, 'coverity', ranking,
                                                                warning_checker, code_flow=warning_code_flow))

        # Increment the warning count
        warning_count = warning_count + 1

    return coverity_issues


# def parse_warnings(coverity_results_file, coverity_metrics_file, cc_threshold, parsed_output_file):
def parse_warnings(analysis_dir, tool_config_data):
    """This function handles the parsing of Coverity data to generate a SCRUB formatted output file.

    Inputs:
        - coverity_results_file:
        - coverity_metrics_file:
        - cc_threshold:
        - parsed_output_file:
    """

    # Initialize variables
    cc_threshold = int(tool_config_data.get('coverity_cc_threshold'))
    coverity_metrics_file = analysis_dir.joinpath('output/FUNCTION.metrics.xml.gz')
    parsed_output_file = tool_config_data.get('raw_results_dir').joinpath('coverity_raw.scrub')

    # Select the correct parser
    if tool_config_data.get('coverity_json'):
        # Parse the JSON Coverity results
        coverity_findings = parse_json(analysis_dir.joinpath('coverity.json'))
    else:
        # Parse the SARIF Coverity results
        coverity_findings = translate_results.parse_sarif(analysis_dir.joinpath('coverity.sarif'),
                                                          tool_config_data.get('source_dir'))

    # Parse the metrics file, if necessary
    if cc_threshold >= 0:
        coverity_findings = coverity_findings + parse_cc(coverity_metrics_file, cc_threshold)

    # Create the output file
    translate_results.create_scrub_output_file(coverity_findings, parsed_output_file)
