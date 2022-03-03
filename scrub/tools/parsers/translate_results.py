import re
import os
import sys
import json
import logging
import traceback

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
        - suppress: Has this finding been supressed? [bool]

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
    scrub_warning = (warning.get('id') + ' <' + warning.get('priority') + '> :' + warning.get('file') + ':' +
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

    # Change the permissions of the output file
    os.chmod(output_file, 438)


def verify_sarif(sarif_data):
    """This function checks the SARIF data for known errors.

    Inputs:
        - sarif_data: A list of dictionaries containing analysis results [list of dict]

    Outputs:
        - valid_results: Boolean value that indicates if the data is error free [bool]
    """

    # Initialize variables
    execution_status = True

    # Check to make sure the analysis completed successfully
    if "invocations" in sarif_data:
        invocations_data = sarif_data['invocations'][0]

        if "executionSuccessful" in invocations_data:
            execution_status = invocations_data['executionSuccessful']
        elif "toolExecutionSuccessful" in invocations_data:
            execution_status = invocations_data['toolExecutionSuccessful']

    # Return an error if the SARIF file cannot be parsed
    if not execution_status:
        raise Exception


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


def run_sarif_merge(sarif_file1, sarif_file2, output_filename, sarif_version='sarifv2.1.0'):
    """This function merges two SARIF files into a single set of results.

    Inputs:
        - sarif_file1: Relative path to the first .sarif file to merge [string]
        - sarif_file2: Relative path to the second .sarif file to merge [string]
        - output_filename: Relative path to the merged .sarif output file [string]
        - sarif_version: Version to use for merged .sarif file, defaults to latest [string]

    Outputs:
        - exit_code: Exit code that represents whether the module completed with errors [int]
                       1 - reports any kind of failure with the merge (i.e. read/write, and schema mismatch)
                       2 - reports any unexpected errors that are not caught by exception handling
    """

    # Initialize variables
    custom_exit_code = 2

    try:
        with open(sarif_file1, 'r') as sarif_one, open(sarif_file2, 'r') as sarif_two:
            sarif_data1 = json.loads(sarif_one.read())
            sarif_data2 = json.loads(sarif_two.read())

        if sarif_data1 and sarif_data2:
            sarif_version = sarif_version.strip('sarifv')

            if (sarif_data1['version'] != sarif_version) or (sarif_data2['version'] != sarif_version):
                logging.warning('SARIF versions mismatched, converting files to: ' + sarif_version)

            merged_sarif = {
                '$schema': sarif_data1['$schema'],
                'version': sarif_version,
                'runs': [
                    sarif_data1['runs'][0],
                    sarif_data2['runs'][0]
                ]
            }

            with open(output_filename, 'w') as sarif_output:
                sarif_output.write(json.dumps(merged_sarif))

            # Update the exit code
            custom_exit_code = 0

    except:     # lgtm [py/catch-base-exception]
        logging.warning('Failed to merge these SARIF results, check traceback error for more details.')
        logging.warning(traceback.format_exc())
        custom_exit_code = 1

    finally:
        return custom_exit_code


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
            warning_query = warning_info[-1].strip()
        else:
            warning_query = ''

        # Get the warning description
        warning_description = []
        for line in warning_lines[1:]:
            warning_description.append(line.rstrip())

        # Get the values of interest
        warning_id = warning_info[0].split()[0]
        warning_file = warning_info[1]
        warning_line = int(warning_info[2])
        warning_tool = re.sub(r'[0-9]', '', warning_id)
        warning_priority = re.sub('[<>]', '', warning_info[0].split()[-1])

        # Update the file path, if necessary
        if not warning_file.startswith('/'):
            warning_file = os.path.join(source_root, warning_file)
        warning_file = os.path.realpath(warning_file)

        # Add the warning to the dictionary
        warning_list.append(create_warning(warning_id, warning_file, warning_line, warning_description, warning_tool,
                                           warning_priority, warning_query))

    return warning_list


def parse_sarif(sarif_filename, source_root, id_prefix=None):
    """This function parses all the SARIF results into the dictionary list of results.

    NOTE: SARIF schema is dependent on version number, current supported version is 2.1.0, but changes may need to be
          made for future updates.

    Inputs:
        - sarif_filename: Absolute path to the SARIF file to be parsed [string]
        - id_prefix: the tool name to assign to warnings, overrides name from actual results file. [string]

    Outputs:
        - results: List of the dictionary items that represent each filtered analysis result [list of dict]
        - rules: Dictionary of extended descriptions for all of the analysis queries [dict]
        - updated_source_dir: Updated source root directory based on contents of SARIF file [string]
    """

    # Initialize variables
    results = []
    warning_count = 1

    try:
        # Initialize variables
        updated_source_dir = source_root

        # Import the SARIF data
        with open(sarif_filename, 'r') as sarif:
            sarif_data = json.loads(sarif.read())

        if sarif_data:
            # Create new dictionary item for each analysis result and append to results list
            schema_version = sarif_data['version']
            sarif_data = sarif_data.get('runs')[0]

            # Verify the results first
            verify_sarif(sarif_data)

            # Update the source root if it can be found in the SARIF data
            if "originalUriBaseIds" in sarif_data:
                for item in sarif_data.get("originalUriBaseIds").items():
                    updated_source_dir = os.path.realpath(item[-1]['uri'].replace('file://', ''))

            # TODO: replace key checks with booleans for all optional SARIF fields
            tool_name, analysis_rules, locations = '', [], []
            if schema_version == "2.1.0":
                tool_name = sarif_data.get('tool')['driver']['name'].split(' ')[0].lower()
                analysis_rules = {}
                # grab full descriptions for each analysis rule or query (only exists in current SARIF`` schema)
                if 'rules' in sarif_data['tool']['driver'].keys() and sarif_data['tool']['driver']['rules'] != []:
                    rules = sarif_data['tool']['driver']['rules']
                    for each in rules:
                        analysis_rules[each['id']] = each['fullDescription']['text']
                if 'artifacts' in sarif_data:
                    for file in sarif_data['artifacts']:
                        locations.append(file['location']['uri'])
            elif schema_version == "2.0.0":
                tool_name = sarif_data.get('tool')['name'].split(' ')[0].lower()
                # Get the list of file locations
                for file in sarif_data['files']:
                    if isinstance(file, dict):
                        locations.append(file['fileLocation']['uri'])  # TODO: duplicated code, modularize this task
                    else:
                        locations.append(file)
            if id_prefix:
                # prefer user defined tool name for scrub microfilter
                tool_name = id_prefix

            # Check to make sure there are results
            if 'results' in sarif_data.keys():
                # Iterate through the results
                for result in sarif_data['results']:
                    viewer_uri = ''
                    if 'suppressions' in result.keys() and result["suppressions"] != []:
                        suppress_warning = True
                    else:
                        suppress_warning = False

                    if result.get('hostedViewerUri') is not None:
                        viewer_uri = result['hostedViewerUri']

                    if 'ruleId' in result.keys():
                        warning_query = result['ruleId']

                    warning_description = [(result['message']['text'].replace('\n', ''))]
                    if 'codesonar' in tool_name.lower():
                        warning_description.append('Codesonar viewer: ' + viewer_uri)

                    location = result.get('locations')[0]['physicalLocation']  # this much is the same across versions
                    if schema_version == "2.1.0":
                        if 'rules' in sarif_data['tool']['driver'].keys() and sarif_data['tool']['driver']['rules'] != []:
                            if 'ruleId' in result.keys():
                                warning_description.append(analysis_rules[result['ruleId']].replace('\n', ''))

                        if 'uri' in location['artifactLocation'].keys() and location['artifactLocation']['uri'] != '':
                            warning_file = location['artifactLocation']['uri']
                        else:
                            file_index = result['locations'][0]['physicalLocation']['artifactLocation'].get('index')
                            warning_file = locations[file_index]
                        # TODO: use helper functions to do key checks? there are too many.
                    elif schema_version == "2.0.0":
                        if 'fileIndex' in location['fileLocation'].keys():
                            file_index = location['fileLocation']['fileIndex']  # mostly for CodeSonar compatibility
                            warning_file = locations[file_index]
                        else:
                            warning_file = location['fileLocation']['uri']

                    # Find the line number
                    if 'region' in location.keys():
                        warning_line = location['region']['startLine']
                    else:
                        warning_line = 0

                    # Fix the filepath
                    warning_file = warning_file.replace('file://', '')
                    if not warning_file.startswith('/'):
                        warning_file = os.path.join(updated_source_dir, warning_file)
                    warning_file = os.path.realpath(warning_file)

                    # Set the warning ID
                    warning_id = tool_name + str(warning_count).zfill(3)

                    # Add to the warning dictionary
                    results.append(create_warning(warning_id, warning_file, warning_line, warning_description, tool_name,
                                                  'Low', warning_query, suppress_warning))

                    # Update the warning count
                    warning_count = warning_count + 1

        else:
            results = []

    except UnboundLocalError:
        logging.warning('Failed to parse file. SARIF schema version does not match SCRUB supported versions.')
        logging.warning(traceback.format_exc())

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
        #result_item['level'] = warning['priority']
        result_item['level'] = 'warning'

        # Set the rule ID
        result_item['ruleId'] = warning['query']

        if warning.get('description') is not None:
            result_item['message'] = {
                'text': '\n'.join(warning['description'])
            }
        if sarif_version == '2.0.0':
            # TODO: CAREFUL USING 2.0.0, STRUCT IS NOT COMPLETELY DEPENDABLE, NEEDS WORK
            sarif_output['runs'][0]['resources'] = {'rules': rules_list}

            sarif_output['runs'][0]['tool'] = results_list[0]['toolName']
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
                        'uri': os.path.relpath(warning['file'], source_root),
                        'uriBaseId': source_root
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

    # Change the permissions of the output file
    os.chmod(output_file, 438)


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
        if input_file.endswith('.scrub'):
            parsed_results = parse_scrub(input_file, source_root)

        elif input_file.endswith('.sarif'):
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
    perform_translation(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
