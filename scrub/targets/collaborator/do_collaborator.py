import re
import os
import logging
import pwd
import traceback
import shutil
import subprocess
import pathlib
from scrub.utils import scrub_utilities
from scrub.utils.filtering import create_file_list


def login(bin_dir, login_flags):
    """This function logs in users to Collaborator.

    Inputs:
        - bin_dir: Absolute path to the Collaborator ccollab client [string]
        - login_flags: Command flags to be passed to the Collaborator command 'ccollab login' [string]
    """

    # Construct the call string
    if bin_dir == '':
        call_string = 'ccollab --quiet login ' + login_flags
    else:
        call_string = bin_dir + '/ccollab --quiet login ' + login_flags

    # Execute the command
    scrub_utilities.execute_command(call_string, os.environ.copy(), None, True)


def check_login(bin_dir):
    """This function checks to see if a user is logged in to the Collaborator server.

    Inputs:
        - bin_dir: Absolute path to the Collaborator ccollab client [string]
    """

    # Construct the call string
    if bin_dir == '':
        call_string = 'ccollab info'
    else:
        call_string = bin_dir + '/ccollab info'

    # Execute the command
    proc = subprocess.Popen(call_string, shell=True, env=os.environ.copy(), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, encoding='utf-8')
    std_out, std_err = proc.communicate()

    # Check to see if a user is logged in
    if std_out.find('Connected as:') >= 0:
        authenticated = True
    else:
        authenticated = False

    return authenticated


def execute_ccollab(bin_dir, subcommand):
    """This function executes a given ccollab command.

    Inputs:
        - bin_dir: Absolute path to the Collaborator ccollab client [string]
        - subcommand: Command string and custom flags to be executed [string]
    """

    # Construct the call string
    if bin_dir == '':
        call_string = 'ccollab --no-browser --scm none ' + subcommand
    else:
        call_string = bin_dir + '/ccollab --no-browser --scm none ' + subcommand

    # Execute the command
    scrub_utilities.execute_command(call_string, os.environ.copy())


def get_review_id(log_file):
    """This function finds the review ID from the Collaborator log file.

    Inputs:
        - log_file: Absolute path to the Collaborator log file [string]

    Outputs:
        review_id: Review ID number found in the Collaborator log file [string]
    """

    # Initialize variables
    review_id = 0

    # Import the log data
    with open(log_file, 'r') as input_fh:
        review_id_data = input_fh.readlines()

    # Find the review ID
    for line in review_id_data:
        if 'Successfully created review' in line:
            review_id = re.split(' ', line.strip())[-1].replace('.', '')

    return review_id


def get_defects(scrub_file):
    """This function parses the input file and creates an internal dictionary of findings.

    Inputs:
        - scrub_file: Absolute path to the SCRUB-formatted results file [string]

    Outputs:
        defect_list: List of defects found within the results file [list of dict]
    """

    # Initialize variables
    special_chars_dict = {'"': "&quot;",
                          "'": "&apos;",
                          "<": "&lt;",
                          ">": "&gt;",
                          "&": "&amp;"}
    defect_list = []

    # Import the defects from the file of interest
    with open(scrub_file, 'r', encoding='UTF-8') as fh:
        results = fh.read()

    # Split the results into defects
    defects = results.split('\n\n')

    # Extract defect info
    for raw_defect in defects:
        if raw_defect:
            # Initialize the dict
            defect = {'id': None,
                      'file': None,
                      'line': None,
                      'priority': None,
                      'description': None,
                      'tool': None}

            # Replace any whitespace with single space
            raw_defect = re.sub(r'\s+', ' ', raw_defect)

            # Get tool abbrv, defect num, severity, file name, line num, description
            raw_defect = re.match(r'(\D+\d*\D+)(\d*) <(\D+)> :(\S+):(\d+): (.+)', raw_defect)

            if 'p10' in scrub_file.stem:
                defect.update({'tool': 'p10_' + raw_defect.group(1)})
            else:
                defect.update({'tool': raw_defect.group(1)})
            defect_num = raw_defect.group(2)

            defect.update({'id': defect.get('tool') + defect_num})
            defect.update({'priority': raw_defect.group(3)})
            defect.update({'file': raw_defect.group(4)})
            defect.update({'line': raw_defect.group(5)})
            defect.update({'description': raw_defect.group(6)})

            # Convert special chars in description
            for key in special_chars_dict.keys():
                defect.update({'description': defect.get('description').replace(key, special_chars_dict[key])})

            # Add the defect to the list
            defect_list.append(defect)

    return defect_list


def construct_xml_global_options(url, username):
    """This function constructs the global options portion of the XML file.

    Inputs:
        - url: URL of the Collaborator server [string]
        - username: Username for the Collaborator user [string]

    Outputs:
        - global_options_string: A string containing the global options [string]
    """

    # Create the global options string
    global_options_string = ('    <global-options>\n' +
                             '        <no-browser/>\n' +
                             '        <scm>none</scm>\n' +
                             '        <url>{}</url>\n'.format(url) +
                             '        <user>{}</user>\n'.format(username) +
                             '    </global-options>\n')

    return global_options_string


def create_batch_xml_file_upload(file_list, review_id, source_root):
    """This function creates the XML file that is used to upload review files to Collaborator.

    Inputs:
        - file_list: List of files to be uploaded to Collaborator [list of strings]
        - review_id: ID of review to upload files [string]
        - source_root: Absolute path to the source code root directory [string]
    """

    # Initialize the variables
    file_upload_xml_batch = ('    <addfiles>\n' +
                             '        <review>{}</review>\n'.format(review_id) +
                             '        <relative-to>{}</relative-to>\n'.format(source_root) +
                             '        <upload-comment>Initial SCRUB upload</upload-comment>\n')

    # Iterate through every file and add it to the upload
    for file in file_list:
        file_upload_xml_batch = file_upload_xml_batch + '        <file-path>{}</file-path>\n'.format(file.strip())

    file_upload_xml_batch = file_upload_xml_batch + '    </addfiles>\n'

    return file_upload_xml_batch


def create_batch_xml_comment_upload(file_list, comment_list, review_id):
    """This function creates the XML snippet that is used to upload review comments to Collaborator.

    Inputs:
        - file_list: List of files that are present within the review [list of string]
        - defect_list: List of defects to be uploaded to the Collaborator review [list of dicts]
        - review_id: ID of review to upload files [string]
    """

    # Initialize variables
    comment_xml_list = ''

    # Write out every defect for files of interest
    for comment in comment_list:
        if comment.get('file') in file_list:
            # Construct the comment xml
            comment_xml = ('    <admin_review_comment_create>\n' +
                           '        <review>{}</review>\n'.format(review_id) +
                           '        <file>{}</file>\n'.format(comment.get('file')) +
                           '        <line-number>{}</line-number>\n'.format(comment.get('line')) +
                           '        <comment>{}: {}</comment>\n'.format(comment.get('tool'), comment.get('description')) +
                           '    </admin_review_comment_create>\n')

            # Add it to the list
            comment_xml_list = comment_xml_list + comment_xml

    return comment_xml_list


def create_batch_xml_defect_upload(file_list, defect_list, review_id):
    """This function creates the XML snippet that is used to upload review defects to Collaborator.

    Inputs:
        - file_list: List of files that are present within the review [list of string]
        - defect_list: List of defects to be uploaded to the Collaborator review [list of dicts]
        - review_id: ID of review to upload files [string]
    """

    # Initialize variables
    defect_xml_list = ''

    # Write out every defect for files of interest
    for defect in defect_list:
        if defect.get('file') in file_list:
            # Parse the priority level
            if defect.get('priority') == 'High':
                severity = 'Major'
            elif defect.get('priority') == 'Med':
                severity = 'Moderate'
            else:
                severity = 'Minor'

            # Create the defect XML
            defect_xml = ('    <admin_review_defect_create>\n'+
                                 '        <custom-field>Severity={}</custom-field>\n'.format(severity) +
                                 '        <review>{}</review>\n'.format(review_id) +
                                 '        <file>{}</file>\n'.format(defect.get('file')) +
                                 '        <line-number>{}</line-number>\n'.format(defect.get('line')) +
                                 '        <comment>{}: {}</comment>\n'.format(defect.get('tool'),
                                                                              defect.get('description')) +
                                 '    </admin_review_defect_create>\n')

            # Update the list of defects
            defect_xml_list = defect_xml_list + defect_xml

    return defect_xml_list


def initialize_upload(tool_conf_data):
    """This function prepares to upload review data to Collaborator.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Create the filtering files
    create_filtering_files(tool_conf_data)

    # Check to see if a user is logged in
    if not check_login(tool_conf_data.get('collaborator_ccollab_location')):
        # Prompt user to log in
        login_flags = tool_conf_data.get('collaborator_server') + ' ' + tool_conf_data.get('collaborator_username')
        login(tool_conf_data.get('collaborator_ccollab_location'), login_flags)

    # Create the review
    subcommand = ('admin review create --creator ' + tool_conf_data.get('collaborator_username') +
                  ' --restrict-access \"' + tool_conf_data.get('collaborator_review_access') + '\" --template \"' +
                  tool_conf_data.get('collaborator_review_template') + '\" --title \"' +
                  tool_conf_data.get('collaborator_review_title') + '\"')
    if tool_conf_data.get('collaborator_review_group'):
        subcommand = (subcommand + ' --group \"' + tool_conf_data.get('collaborator_review_group') + '\"')
    execute_ccollab(tool_conf_data.get('collaborator_ccollab_location'), subcommand)

    # Get the review ID and add it to the configuration data
    review_id = get_review_id(tool_conf_data.get('collaborator_log_file'))
    tool_conf_data.update({'collaborator_review_id': int(review_id)})

    # Set the review xml file path
    batch_command_file = tool_conf_data.get('collaborator_upload_dir').joinpath('collaborator_review_' +
                                                                                str(review_id) + '_batch.xml')
    tool_conf_data.update({'batch_command_file': batch_command_file})
    # tool_conf_data.update({'collaborator_review_xml_comments': comments_xml})

    # Set the author of the review
    subcommand = ('admin review set-participants ' + review_id + ' --participant author=' +
                  tool_conf_data.get('collaborator_username'))
    execute_ccollab(tool_conf_data.get('collaborator_ccollab_location'), subcommand)


def perform_upload(tool_conf_data):
    """This function uploads review data to the Collaborator review.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize variables
    tool_defect_types = []
    defect_list = []

    # Get a list of the source code files to be uploaded
    with open(tool_conf_data.get('collaborator_filtering_output_file'), 'r') as fh:
        file_list = list(filter(None, re.split('\n', fh.read())))

    # Check if any files specified
    if tool_conf_data.get('collaborator_src_files'):
        for results_file in tool_conf_data.get('collaborator_src_files').split(','):
            tool_name = results_file[0:-6]
            tool_defect_types.append(tool_name)
    else:
        for filename in tool_conf_data.get('scrub_analysis_dir').glob('*.scrub'):
            if 'raw' not in filename.stem:
                tool_name = filename.stem
                tool_defect_types.append(tool_name)

    # Get the defects
    for tool_name in tool_defect_types:
        scrub_file = tool_conf_data.get('scrub_analysis_dir').joinpath(tool_name + '.scrub')

        # Add the defects to the review
        defect_list = defect_list + get_defects(scrub_file)

    # Create XML data for uploading files
    file_xml_data = create_batch_xml_file_upload(file_list, tool_conf_data.get('collaborator_review_id'),
                                                 tool_conf_data.get('source_dir'))

    if tool_conf_data.get('collaborator_finding_level').lower() == 'defect':
        finding_xml_data = create_batch_xml_defect_upload(file_list, defect_list,
                                                          tool_conf_data.get('collaborator_review_id'))
    else:
        finding_xml_data = create_batch_xml_comment_upload(file_list, defect_list,
                                                           tool_conf_data.get('collaborator_review_id'))

    # Add a generic comment if the finding upload list is empty
    if finding_xml_data == '':
        finding_xml_data = ('    <admin_review_comment_create>\n' +
                            '        <review>{}</review>\n'.format(tool_conf_data.get('collaborator_review_id')) +
                            '        <comment>No findings were found to include in this review.</comment>\n' +
                            '    </admin_review_comment_create>\n')

    # Create the XML batch file
    with open(tool_conf_data.get('batch_command_file'), 'w+') as output_fh:
        output_fh.write('<batch-commands>\n')
        output_fh.write('{}'.format(construct_xml_global_options(tool_conf_data.get('collaborator_server'),
                                                                 tool_conf_data.get('collaborator_username'))))
        output_fh.write('{}'.format(file_xml_data))
        output_fh.write('{}'.format(finding_xml_data))
        output_fh.write('</batch-commands>')

    # Perform the upload
    subcommand = ('admin batch ' + str(tool_conf_data.get('batch_command_file')))
    execute_ccollab(tool_conf_data.get('collaborator_ccollab_location'), subcommand)


def create_filtering_files(tool_conf_data):
    """This function creates the filtering files needed for Collaborator upload.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Print a status message
    logging.info('\t>> Checking analysis filtering output file.')

    # Determine if the baseline filtering list exists, or should be created
    if not tool_conf_data.get('filtering_output_file').exists():
        # Print a status message
        logging.info('\t>> No analysis filtering output was found. Creating output now.')

        # Create the output file
        create_file_list.create_file_list(tool_conf_data.get('source_dir'),
                                          tool_conf_data.get('filtering_output_file'),
                                          tool_conf_data.get('analysis_filters'))

    # Create the file list based on filtering options
    create_file_list.create_file_list(tool_conf_data.get('source_dir'),
                                      tool_conf_data.get('collaborator_filtering_output_file'),
                                      tool_conf_data.get('collaborator_filters'),
                                      tool_conf_data.get('filtering_output_file'))


def run_analysis(baseline_conf_data, console_logging=logging.INFO, override=False):
    """This function runs this module based on input from the scrub.cfg file

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
        - console_logging: Level of console logging information to print to console [optional] [enum]
        - override: Force tool execution? [optional] [bool]

    Outputs:
        - collaborator.log: Log file for the Collaborator upload, where uid is the user ID
        - review.xml: XML file containing appropriate Collaborator commands to upload source code and SCRUB results
        - stdout and stderr data will be directed to log_file
    """

    # Import the config file data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize variables
    collaborator_exit_code = 2
    attempt_analysis = tool_conf_data.get('collaborator_export') or override

    # Determine if Collaborator upload can be run
    if attempt_analysis:
        try:
            # Create the logging file, if it doesn't already exist
            scrub_utilities.create_logger(tool_conf_data.get('collaborator_log_file'), console_logging)

            # Print a status message
            logging.info('')
            logging.info('Perform Collaborator export...')

            # Prepare for the upload
            initialize_upload(tool_conf_data)

            # Perform the upload
            perform_upload(tool_conf_data)

            # Set the exit code
            collaborator_exit_code = 0

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('Collaborator export could not be performed. Please see log file %s for more information.',
                            str(tool_conf_data.get('collaborator_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            collaborator_exit_code = 1

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.warning('Collaborator export could not be performed. Please see log file %s for more information.',
                            str(tool_conf_data.get('collaborator_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            collaborator_exit_code = 100

        finally:
            # Delete the review if necessary
            if (collaborator_exit_code > 0) and (tool_conf_data.get('collaborator_review_id') > 0):
                subcommand = ('admin review delete ' + str(tool_conf_data.get('collaborator_review_id')))
                execute_ccollab(str(tool_conf_data.get('collaborator_ccollab_location')), subcommand)

            # Close the loggers
            logging.getLogger().handlers = []

            # Move the log file to line up with the review id, if it exists
            if tool_conf_data.get('collaborator_log_file').exists() and tool_conf_data.get('collaborator_review_id') > 0:
                shutil.move(tool_conf_data.get('collaborator_log_file'),
                            tool_conf_data.get('scrub_log_dir').joinpath('collaborator_' + str(tool_conf_data.get('collaborator_review_id')) + '.log'))

    # Return the exit code
    return collaborator_exit_code


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    current_user = pwd.getpwuid(os.getuid()).pw_name
    collaborator_upload_dir = tool_conf_data.get('scrub_analysis_dir').joinpath('collaborator_upload')
    collaborator_log_file = tool_conf_data.get('scrub_log_dir').joinpath('collaborator_' + current_user + '.log')
    collaborator_filtering_output_file = collaborator_upload_dir.joinpath('SCRUBCollaboratorFilteringList')

    # Add derived values to the dictionary
    tool_conf_data.update({'collaborator_log_file': collaborator_log_file})
    tool_conf_data.update({'collaborator_upload_dir': collaborator_upload_dir})
    tool_conf_data.update({'collaborator_filtering_output_file': collaborator_filtering_output_file})
    tool_conf_data.update({'collaborator_review_id': 0})

    # Set the username if necessary
    if tool_conf_data.get('collaborator_username') == '':
        tool_conf_data.update({'collaborator_username': current_user})

    # Create the working directory if it doesn't already exist
    if not collaborator_upload_dir.exists():
        collaborator_upload_dir.mkdir()

    # Resolve the COLLABORATOR_FILTERS variable
    tool_conf_data.update({'collaborator_filters': pathlib.Path(tool_conf_data.get('collaborator_filters'))})

    # Determine if Collaborator can be run
    if not (tool_conf_data.get('collaborator_server')):
        # Update the analysis flag if necessary
        if tool_conf_data.get('collaborator_export'):
            tool_conf_data.update({'collaborator_export': False})

            # Print a status message
            print('\nWARNING: Unable to perform Collaborator export. Required configuration inputs are missing.')
            print('\tRequired inputs: COLLABORATOR_SERVER\n')
