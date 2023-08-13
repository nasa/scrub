import re
import sys
import json
import pathlib
import logging
import traceback
from sarif import loader

WARNING_LINE_REGEX = r'^[a-z]+[0-9]+ <.*>.*:.*:.*:'


def create_warning(scrub_id, file, line, description, tool, priority='Low', query='', suppress=False):
    """This function creates an internal representation of a warning t be used for processing.

    Inputs:
        - id: Finding identifier of the format <tool><count> [string]
        - file: Absolute path to the source file referenced by the finding [string]
        - line: Line number of the source file being referenced by the findings [int]
        - description: Finding description [list of strings]
        - tool: Tool that generated the finding [string]
        - priority: Priority marking for the finding [Low/Med/High]
        - query: Tool query name that generated the finding [string]
        - suppress: Has this finding been suppressed? [bool]

    Outputs:
        - scrub_warning: Dictionary of warning data [dict]
    """

    # Create the warning
    scrub_warning = {'id': scrub_id,
                     'file': file,
                     'line': line,
                     'description': description,
                     'tool': tool,
                     'priority': priority,
                     'query': query,
                     'suppress': suppress}

    return scrub_warning


def format_scrub_warning(warning):
    """This function takes an internal representation of a warning and converts it into a SCRUB-formatted string.

    Inputs:
        - warning: Dictionary of finding data [dict]

    Outputs:
        - scrub_warning: SCRUB-formatted warning that can be written to the output file [string]
    """

    # Format the warning
    scrub_warning = (warning.get('id') + ' <' + warning.get('priority') + '> :' + str(warning.get('file')) + ':' +
                     str(warning.get('line')) + ': ' + warning.get('query') + '\n')

    # Add the description
    description = ''
    for line in warning.get('description'):
        description = description + '    ' + line + '\n'
    scrub_warning = scrub_warning + description + '\n'

    return scrub_warning


def create_scrub_output_file(warnings, output_file):
    """This function writes out raw warnings to a SCRUB formatted output file.

    Inputs:
        - warnings: Dictionary of raw warnings [list of dict]
        - output_file: Absolute path to output file to be created [string]
    """

    # Create the output file
    with open(output_file, 'w', encoding='utf-8') as output_fh:
        # Iterate through every raw warning
        for warning in warnings:
            # Check that the warning isn't suppressed
            if not warning['suppress']:
                # Create the SCRUB formatted warning
                scrub_warning = format_scrub_warning(warning)

                # Write the warning to the output file
                output_fh.write(scrub_warning)


def get_rules_list(warnings):
    """This function gets a list of the rules contained in a set of warnings.

    Inputs:
        - warnings: List of warnings to be examined [list of dicts]

    Outputs:
        - rules_list: List of queries contained in the list of warnings [list of strings]
    """

    # Initialize variables
    rules_list = []

    # Iterate through every warning
    for warning in warnings:
        if warning['query'] not in rules_list and (warning['query'] != ''):
            rules_list.append(warning['query'])

    return rules_list


def parse_scrub(scrub_file, source_root):
    """This function parses a scrub input file and returns a dictionary of findings.

    Inputs:
        - scrub_file: Absolute path to the SCRUB formatted file to bee parsed [string]
        - source_root: Root directory of source code [string]

    Outputs:
        - warning_dict: Dictionary of static analysis findings [dict]
        - query_list: List of queries found in the SCRUB input file [list of strings]
    """

    # Initialize variables
    warning_list = []

    # Import the data
    with open(scrub_file, 'r', encoding='utf-8') as input_fh:
        scrub_data = input_fh.read()

    # Split the warnings
    raw_warnings = list(filter(None, re.split('\n\n', scrub_data)))

    # Find all of the warnings in the file
    for raw_warning in raw_warnings:
        warning_lines = list(filter(None, re.split('\n', raw_warning.strip())))

        # Get the location information
        warning_info = list(filter(None, re.split(':', warning_lines[0].strip())))

        # Get the query name if it exists
        if len(warning_info) > 3:
            warning_query = list(warning_lines[0].split(': '))[-1].strip()
        else:
            warning_query = ''

        # Get the warning description
        warning_description = []
        for line in warning_lines[1:]:
            warning_description.append(line.rstrip())

        # Get the values of interest
        warning_id = warning_info[0].split()[0]
        warning_file = pathlib.Path(warning_info[1])
        warning_line = int(warning_info[2])
        warning_tool = re.sub(r'[0-9]', '', warning_id)
        warning_priority = re.sub('[<>]', '', warning_info[0].split()[-1])

        # Update the file path, if necessary
        if warning_file.anchor != '/':
            warning_file = source_root.joinpath(warning_file).resolve()

        # Add the warning to the dictionary
        warning_list.append(create_warning(warning_id, warning_file.resolve(), warning_line, warning_description, warning_tool,
                                           warning_priority, warning_query))

    return warning_list


def parse_sarif(sarif_filename, source_root, id_prefix=None):
    """This function parses all the SARIF results into the dictionary list of results.

    NOTE: This function depends on the open-source SARIF parsing library "sarif-tools"
          https://github.com/microsoft/sarif-tools/tree/main

    Inputs:
        - sarif_filename: Absolute path to the SARIF file to be parsed [string]
        - source_root: Absolute path to source root directory [string]
        - id_prefix: the tool name to assign to warnings, overrides name from actual results file. [string]

    Outputs:
        - results: List of the dictionary items that represent each filtered analysis result [list of dict]
    """

    # Initialize variables
    results = []
    warning_count = 1

    try:
        # Import the SARIF file data
        sarif_data = loader.load_sarif_file(sarif_filename)

        # Get the tool name
        tool_name = sarif_data.get_distinct_tool_names()[0].lower()

        # Update the source root if it can be found in the SARIF data
        if "originalUriBaseIds" in sarif_data.data['runs'][0]:
            # Parse the CodeSonar format
            if 'SRCROOT0' in sarif_data.data['runs'][0]['originalUriBaseIds']:
                source_root = pathlib.Path(sarif_data.data['runs'][0]['originalUriBaseIds']['SRCROOT0']['uri'].replace('file://', '')).resolve()

        # Iterate through every finding
        for finding in sarif_data.get_results():
            # Set the warning ID
            warning_id = tool_name + str(warning_count).zfill(3)

            # Get the rule ID
            warning_query = finding.get('ruleId')

            # Get the warning file
            if finding.get('locations'):
                location_data = finding.get('locations')[0].get('physicalLocation')
                warning_file = location_data.get('artifactLocation').get('uri')
                if warning_file.startswith('/'):
                    warning_file = pathlib.Path(warning_file)
                else:
                    warning_file = pathlib.Path(source_root).joinpath(warning_file)

                # Get the line number
                warning_line = location_data.get('region').get('startLine')
                if warning_line:
                    warning_line = int(warning_line)
                else:
                    warning_line = 0
            else:
                print('WARNING: Could not parse finding {}'.format(warning_query))
                continue

            # Get the warning description
            warning_description = [(finding.get('message').get('text').replace('\n', ''))]
            if finding.get('hostedViewerUri'):
                warning_description.append('Server Location: ' + finding.get('hostedViewerUri'))

            # Set the ranking
            if 'rank' in finding.keys():
                if int(finding['rank']) > 56:
                    ranking = 'High'
                elif 21 < int(finding['rank']) <= 56:
                    ranking = 'Med'
                else:
                    ranking = 'Low'
            else:
                ranking = 'Low'

            # Check if the warning should be suppressed
            if 'suppressions' in finding.keys() and finding.get("suppressions") != []:
                suppress_warning = True
            else:
                suppress_warning = False

            # Add to the warning dictionary
            results.append(create_warning(warning_id, warning_file.resolve(), warning_line, warning_description,
                                          tool_name, ranking, warning_query, suppress_warning))

            # Update the warning count
            warning_count = warning_count + 1

    except:      # lgtm [py/catch-base-exception]
        raise Exception

    return results


def create_sarif_output_file(results_list, sarif_version, output_file, source_root):
    """This function creates a SARIF formatted output file.

    Inputs:
        - results_list: List of dictionaries representing each warning [list of dicts]
        - sarif_version:
        - output_file:
        - source_root: Absolute path of source root directory [string]

    Returns:
        - output_file is created at the specified location
    """

    # Initialize variables
    result_item = {}
    rules_list = get_rules_list(results_list)
    sarif_output = {
        'version': sarif_version,
        '$schema': 'https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json',
        'runs': [
                   {
                       'results': []
                   }
        ]
    }

    # Iterate through every warning
    for warning in results_list:
        file_index = 0

        # Set the priority level
        result_item['level'] = 'warning'

        # Set the rule ID
        result_item['ruleId'] = warning['query']

        if warning.get('description') is not None:
            result_item['message'] = {
                'text': '\n'.join(warning['description'])
            }
        if sarif_version == '2.0.0':
            # TODO: CAREFUL USING 2.0.0, STRUCT IS NOT COMPLETELY DEPENDABLE, NEEDS WORK
            sarif_output['runs'][0].update({'resources': rules_list})

            sarif_output['runs'][0].update({'tool': results_list[0]['tool']})
            # TODO: get the logic right for deciding mime type... pass file_list like rules_list
            sarif_output['runs'][0]['files'] = [{
                "mimeType": "text/c",
                "fileLocation": {
                    "uri": results_list[0]['file']
                }
            }]
            result_item['locations'] = [
                {
                    'physicalLocation': {
                        'fileLocation': {
                            # TODO: get the logic right on properly indexing file paths (like with ruleIndex)
                            'fileIndex': file_index
                        },
                        'region': {
                            'startLine': warning['line']
                        }
                    }
                }
            ]
            file_index += 1
        elif sarif_version == '2.1.0':
            # Create the list of sarif rules
            sarif_rules = []
            for rule in rules_list:
                sarif_rules.append({
                    'id': rule,
                    'shortDescription': {
                        'text': rule
                    }
                })

            sarif_output['runs'][0]['tool'] = {
                'driver': {
                    'name': results_list[0]['tool'],
                    'rules': sarif_rules
                }
            }
            result_item['locations'] = [{
                'physicalLocation': {
                    'artifactLocation': {
                        'uri': str(warning['file'].relative_to(source_root)),
                        'uriBaseId': str(source_root)
                    },
                    'region': {
                        'startLine': warning['line']
                    }
                }
            }]

        # append fixed warnings to results list and clean dict object
        sarif_output['runs'][0]['results'].append(result_item)
        result_item = {}

    # Create the output file
    with open(output_file, 'w') as output_fh:
        # output_fh.write('{}'.format(json.dumps(sarif_output, indent=4)))
        json.dump(sarif_output, output_fh, indent=4)


def perform_translation(input_file, output_file, source_root, output_format):
    """This function takes in an analysis results file in legacy format (.scrub), then parses and converts the contents
       of each analysis result into the SARIF format.

    Inputs:
        - scrub_filename: The name of the .sarif file to parse and convert. [string]
        - output_filename: The filename to output parsed results to. [string]

    Outputs:
        - custom_exit_code: Exit code that represents whether the module completed with errors.
                            1 - reports any kind of failure with the parser (i.e. read/write, and schema mismatch)
    """

    # Initialize the variables
    exit_code = 1
    parsed_results = []

    try:
        # Parse the input file
        if input_file.suffix == '.scrub':
            parsed_results = parse_scrub(input_file, source_root)

        elif input_file.suffix == '.sarif':
            parsed_results = parse_sarif(input_file, source_root)

        else:
            # TODO: This should generate an exception
            logging.error('Unknown input file type.')

        # Generate the desired output file
        if output_format == 'scrub':
            create_scrub_output_file(parsed_results, output_file)

        elif output_format.startswith('sarif'):
            # Determine the SARIF version
            sarif_version = output_format.strip('sarifv')

            # Generate the output file
            create_sarif_output_file(parsed_results, sarif_version, output_file, source_root)

        else:
            # TODO: This should generate an exception
            logging.error('Unknown output format type.')

        # Update the exit code
        exit_code = 0

    except:     # lgtm [py/catch-base-exception]
        logging.error('Translation could not be performed.')
        logging.error(traceback.format_exc())

        # Update the exit code
        exit_code = 100

    finally:
        return exit_code


if __name__ == '__main__':
    perform_translation(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4])