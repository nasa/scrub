import re
import sys
import json
import pathlib
import logging
import traceback
from sarif import loader

WARNING_LINE_REGEX = r'^[a-z]+[0-9]+ <.*>.*:.*:.*:'
CODE_FLOW_REGEX = r'    <.*>.*:.*:.*:'


def create_code_flow(file, line, description):
    """This function creates an internal representation of a code flow to be used by the

    Inputs:
        - file: Absolute path to the source file referenced by the finding [string]
        - line: Line number of the source file being referenced by the findings [int]
        - description: Finding description [list of strings]

    Outputs:
        - code_flow: Dictionary of code flow data [dict]

    """

    code_flow = {'file': file,
                 'line': line,
                 'description': description}

    return code_flow


def create_warning(scrub_id, file, line, description, tool, priority='Low', query='', suppress=False, code_flow=None):
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
        - code_flows: List of code flows related to the finding [list of dict]

    Outputs:
        - scrub_warning: Dictionary of warning data [dict]
    """

    # Do some type checking
    if code_flow is None:
        code_flow = []
    if type(description) is not list:
        description = [description]

    # Create the warning
    scrub_warning = {'id': scrub_id,
                     'file': file,
                     'line': line,
                     'description': description,
                     'tool': tool,
                     'priority': priority,
                     'query': query,
                     'suppress': suppress,
                     'code_flow': code_flow}

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

    # Add the code flow
    if len(warning.get('code_flow')) > 0:
        code_flow_description = '    Code flow data:\n'
        for flow_step in warning.get('code_flow'):
            code_flow_description = code_flow_description + '    {}\n    {}:{}\n'.format(flow_step.get('description'),
                                                                                         flow_step.get('file'),
                                                                                         flow_step.get('line'))
    else:
        code_flow_description = ''

    # Add the description
    scrub_warning = scrub_warning + description + code_flow_description + '\n'

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

    # Find all the warnings in the file
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
        code_flow_data = []
        for i in range(1, len(warning_lines)):
            description_line = warning_lines[i].rstrip().lstrip('    ')

            # Parse code flow data if it exists
            if description_line.lower() == 'code flow data:':
                code_flow_line = i + 1

                # Parse out the code flow if it exists
                for j in range(code_flow_line, len(warning_lines), 2):
                    code_flow_description = warning_lines[j].rstrip().lstrip('    ')
                    code_flow_file = pathlib.Path(warning_lines[j + 1].strip().split(':')[0])
                    code_flow_line = int(warning_lines[j + 1].strip().split(':')[-1])

                    # Generate the code flow object
                    code_flow_data.append(create_code_flow(code_flow_file, code_flow_line, code_flow_description))

                break
            else:
                # Otherwise add the line to the description
                warning_description.append(description_line)

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
        warning_list.append(create_warning(warning_id, warning_file.resolve(), warning_line, warning_description,
                                           warning_tool, warning_priority, warning_query, code_flow=code_flow_data))

    return warning_list


def format_sarif_for_upload(input_file, output_file, source_root, upload_format):
    """This function pre-processes SARIF files in preparation for import into various tools.

    Inputs:
        - input_file: Absolute path to the SARIF input file to be parsed [string]
        - output_file: Absolute path to output file to be created [string]
        - upload_format: Format of the SARIF output file [string]
    """

    # Initialize variables
    formatted_results = []
    tool_name = input_file.stem

    # Import the SARIF results
    unformatted_results = parse_sarif(input_file, source_root)

    if upload_format == 'sonarqube':
        for warning in unformatted_results:
            if input_file.stem == 'codesonar':
                # warning['description'] = [warning['query'] + " - (" +
                #                           warning['description'][0].split('Server Location: ')[-1] + ")"]
                warning['description'] = [warning['query'] + " - (" + warning['description'][-1] + ")"]
                formatted_results.append(warning)
            elif input_file.stem == 'coverity':
                warning['description'] = [warning['description'][0]]
                formatted_results.append(warning)

        create_sarif_output_file(formatted_results, '2.1.0', output_file, source_root, tool_name)
    elif upload_format == 'codesonar':
        # shutil.copyfile(input_file, output_file)
        for warning in unformatted_results:
            # Add a prefix to the tool name to allow for filtering
            warning['tool'] = 'external-' + warning['tool']
            warning['query'] = warning['tool'].title() + ' ' + warning['query']
            formatted_results.append(warning)
        create_sarif_output_file(formatted_results, '2.1.0', output_file, source_root, tool_name)


def parse_sarif(sarif_filename, source_root):
    """This function parses all the SARIF results into the dictionary list of results.

    NOTE: This function depends on the open-source SARIF parsing library "sarif-tools"
          https://github.com/microsoft/sarif-tools/tree/main

    Inputs:
        - sarif_filename: Absolute path to the SARIF file to be parsed [string]
        - source_root: Absolute path to source root directory [string]

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
        if sarif_data.get_distinct_tool_names():
            tool_name = sarif_data.get_distinct_tool_names()[0].lower()
        else:
            print("ERROR: No run data found for results file {}".format(sarif_filename))
            raise Exception

        # Update the source root if it can be found in the SARIF data
        if "originalUriBaseIds" in sarif_data.data['runs'][0]:
            # Parse the CodeSonar format
            if 'SRCROOT0' in sarif_data.data['runs'][0]['originalUriBaseIds']:
                source_root = pathlib.Path(sarif_data.data['runs'][0]['originalUriBaseIds']['SRCROOT0']['uri']
                                           .replace('file://', '')).resolve()

        # Iterate through every finding
        for finding in sarif_data.get_results():
            # Set the warning ID
            warning_id = tool_name + str(warning_count).zfill(3)

            # Get the rule ID
            warning_query = finding.get('ruleId')

            # Check if the warning should be suppressed
            if 'suppressions' in finding.keys() and finding.get("suppressions") != []:
                suppress_warning = True
            else:
                suppress_warning = False

            # Get the warning file
            if finding.get('locations'):
                location_data = finding.get('locations')[0].get('physicalLocation')
                warning_file = location_data.get('artifactLocation').get('uri')
                if warning_file.startswith('/'):
                    warning_file = pathlib.Path(warning_file)
                else:
                    warning_file = pathlib.Path(source_root).joinpath(warning_file)

                # Get the line number
                if location_data.get('region'):
                    warning_line = int(location_data.get('region').get('startLine', 0))
                else:
                    warning_line = 0
            else:
                print('WARNING: Location data missing. Could not parse finding {}'.format(warning_query))
                continue

            # Get the warning description
            if finding.get('message').get('text'):
                warning_description = [(finding.get('message').get('text').replace('\n', ''))]
                if finding.get('hostedViewerUri'):
                    # warning_description.append('Server Location: ' + finding.get('hostedViewerUri'))
                    warning_description.append(finding.get('hostedViewerUri'))
            else:
                print('WARNING: Description data missing. Could not parse finding {}'.format(warning_query))
                continue

            # Get any code flow information that exists
            code_flow = []
            if finding.get('codeFlows'):
                for flow in finding.get('codeFlows'):
                    if flow.get('message'):
                        warning_description.append(flow.get('message').get('text'))
                    for thread_location in flow.get('threadFlows')[0].get('locations'):
                        if thread_location.get('location').get('message'):
                            code_flow_file = pathlib.Path(thread_location.get('location')
                                                          .get('physicalLocation').get('artifactLocation').get('uri'))
                            code_flow_line = (thread_location.get('location').get('physicalLocation').get('region')
                                              .get('startLine'))
                            code_flow_description = thread_location.get('location').get('message').get('text')
                            code_flow.append(create_code_flow(code_flow_file, code_flow_line, code_flow_description))

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

            # Add to the warning dictionary
            results.append(create_warning(warning_id, warning_file.resolve(), warning_line, warning_description,
                                          tool_name, ranking, warning_query, suppress_warning, code_flow))

            # Update the warning count
            warning_count = warning_count + 1

    except:      # lgtm [py/catch-base-exception]
        raise Exception

    return results


def create_sarif_output_file(results_list, sarif_version, output_file, source_root, tool_name):
    """This function creates a SARIF formatted output file.

    Inputs:
        - results_list: List of dictionaries representing each warning [list of dicts]
        - sarif_version:
        - output_file:
        - source_root: Absolute path of source root directory [string]
        - tool_name: Name of scanning tool [string]

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
                       'tool': {
                           'driver': {
                               'name': tool_name
                           },
                           'rules': []
                       },
                       'results': []
                   }
        ]
    }

    # Iterate through every warning
    for warning in results_list:
        file_index = 0

        # Set the priority level
        result_item['level'] = 'warning'

        # Set the file path
        warning_file = str(warning['file'])

        # Set the rule ID
        result_item['ruleId'] = warning['query']

        if warning.get('description') is not None:
            result_item['message'] = {
                'text': ' '.join(warning['description'])
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
            sarif_output['runs'][0]['tool']['rules'] = sarif_rules
            result_item['locations'] = [{
                'physicalLocation': {
                    'artifactLocation': {
                        'uri': warning_file,
                        'uriBaseId': str(source_root)
                    },
                    'region': {
                        'startLine': warning['line']
                    }
                }
            }]

            if len(warning.get('code_flow')) > 0:
                # Add the codeFlows data to the result
                result_item['codeFlows'] = [{
                                                'message': {
                                                    'text': "Code flow information from {}".format(warning.get('tool'))
                                                },
                                                'threadFlows': [
                                                    {
                                                        'locations': []
                                                    }
                                                ]
                                            }]

                # Get all the code flow data
                for code_flow_item in warning.get('code_flow'):
                    # if str(code_flow_item.get('file')).startswith('/'):
                    if source_root in code_flow_item.get('file').parents:
                        artifact_location = str(code_flow_item.get('file').relative_to(source_root))
                    else:
                        artifact_location = str(code_flow_item.get('file'))

                    location_item = {
                                        'location': {
                                            'message': {
                                                'text': code_flow_item.get('description')
                                            },
                                            'physicalLocation': {
                                                'artifactLocation': {
                                                    'uri': artifact_location
                                                },
                                                'region': {
                                                    'startLine': code_flow_item['line']
                                                }
                                            }
                                        }
                                    }

                    # locations_list.append(location_item)
                    result_item['codeFlows'][0]['threadFlows'][0]['locations'].append(location_item)

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
    tool_name = input_file.stem

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
            create_sarif_output_file(parsed_results, sarif_version, output_file, source_root, tool_name)

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
