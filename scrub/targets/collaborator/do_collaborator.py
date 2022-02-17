import re
import os
import logging
import pwd
import traceback
import shutil
import subprocess
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
    with open(scrub_file, 'r') as fh:
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

            if 'p10' in os.path.basename(scrub_file):
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


def create_batch_xml_file_upload(output_file, file_list, review_id, url, username, source_root):
    """This function creates the XML file that is used to upload review files to Collaborator.

    Inputs:
        - output_file: Absolute path to the desired XML output file location [string]
        - file_list: List of files to be uploaded to Collaborator [list of strings]
        - review_id: ID of review to upload files [string]
        - url: URL of the Collaborator server [string]
        - username: Username for the Collaborator user [string]
        - source_root: Absolute path to the source code root directory [string]
    """

    with open(output_file, 'w') as output_fh:
        # Start the XML
        output_fh.write('<batch-commands>\n')

        # Write out the global options
        output_fh.write('{}'.format(construct_xml_global_options(url, username)))

        # Write out all of the file upload commands
        output_fh.write('    <addfiles>\n')
        output_fh.write('        <review>{}</review>\n'.format(review_id))
        output_fh.write('        <relative-to>{}</relative-to>\n'.format(source_root))
        output_fh.write('        <upload-comment>Initial SCRUB upload</upload-comment>\n')

        for file in file_list:
            output_fh.write('        <file-path>{}</file-path>\n'.format(file.strip()))

        output_fh.write('    </addfiles>\n')

        # Close out the file
        output_fh.write('</batch-commands>\n')


def create_batch_xml_defect_upload(output_file, file_list, defect_list, review_id, finding_level, url, username):
    """This function creates the XML file that is used to upload review defects to Collaborator.

    Inputs:
        - output_file: Absolute path to the desired XML output file location [string]
        - defect_list: List of defects to be uploaded to the Collaborator review [list of dicts]
        - review_id: ID of review to upload files [string]
        - finding_level: Should findings be uploaded as comments or defects? ['comment'/'defect']
        - url: URL of the Collaborator server [string]
        - username: Username for the Collaborator user [string]
    """

    with open(output_file, 'w') as output_fh:
        # Start the XML
        output_fh.write('<batch-commands>\n')

        # Write out the global options
        output_fh.write('{}'.format(construct_xml_global_options(url, username)))
        
        # Track if we're including any warnings
        uploaded_warnings = False

        # Write out every defect for files of interest
        for defect in defect_list:
            if defect.get('file') in file_list:
                uploaded_warnings = True
                if finding_level.lower() == 'defect':
                    # Parse the priority level
                    if defect.get('priority') == 'High':
                        severity = 'Major'
                    elif defect.get('priority') == 'Med':
                        severity = 'Moderate'
                    else:
                        severity = 'Minor'

                    output_fh.write('    <admin_review_defect_create>\n')
                    output_fh.write('        <custom-field>Severity={}</custom-field>\n'.format(severity))
                else:
                    output_fh.write('    <admin_review_comment_create>\n')

                output_fh.write('        <review>{}</review>\n'.format(review_id))
                output_fh.write('        <file>{}</file>\n'.format(defect.get('file')))

                # Check for a line number
                if int(defect.get('line')) > 0:
                    output_fh.write('        <line-number>{}</line-number>\n'.format(defect.get('line')))

                output_fh.write('        <comment>{}</comment>\n'.format(defect.get('description')))

                if finding_level.lower() == 'defect':
                    output_fh.write('    </admin_review_defect_create>')
                else:
                    output_fh.write('    </admin_review_comment_create>\n')

        # Add a general comment if there are no uploaded warnings
        if not uploaded_warnings:
            output_fh.write('    <admin_review_comment_create>\n')
            output_fh.write('        <review>{}</review>\n'.format(review_id))
            output_fh.write('        <comment>No warnings were found to include in this review.</comment>\n')
            output_fh.write('    </admin_review_comment_create>\n')
                    
        # Close out the file
        output_fh.write('</batch-commands>\n')


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
    files_xml = tool_conf_data.get('scrub_analysis_dir') + '/collaborator_review_' + str(review_id) + '_files.xml'
    comments_xml = tool_conf_data.get('scrub_analysis_dir') + '/collaborator_review_' + str(review_id) + '_comments.xml'
    tool_conf_data.update({'collaborator_review_xml_files': files_xml})
    tool_conf_data.update({'collaborator_review_xml_comments': comments_xml})

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
        for root, dirs, files in os.walk(tool_conf_data.get('scrub_analysis_dir')):
            for filename in files:
                if filename.endswith('.scrub') and 'raw' not in filename:
                    tool_name = filename[0:-6]
                    tool_defect_types.append(tool_name)

    # Get the defects
    for tool_name in tool_defect_types:
        scrub_file = os.path.normpath(tool_conf_data.get('scrub_analysis_dir') + '/' + tool_name + '.scrub')

        # Add the defects to the review
        defect_list = defect_list + get_defects(scrub_file)

    # Create XML batch file for uploading files
    create_batch_xml_file_upload(tool_conf_data.get('collaborator_review_xml_files'), file_list,
                                 tool_conf_data.get('collaborator_review_id'),
                                 tool_conf_data.get('collaborator_server'), tool_conf_data.get('collaborator_username'),
                                 tool_conf_data.get('source_dir'))

    # Create the XML batch file for uploading defects
    create_batch_xml_defect_upload(tool_conf_data.get('collaborator_review_xml_comments'), file_list, defect_list,
                                   tool_conf_data.get('collaborator_review_id'),
                                   tool_conf_data.get('collaborator_finding_level'),
                                   tool_conf_data.get('collaborator_server'),
                                   tool_conf_data.get('collaborator_username'))

    # Find the xml files of interest
    xml_files = [tool_conf_data.get('collaborator_review_xml_files'),
                 tool_conf_data.get('collaborator_review_xml_comments')]

    # Perform all the batch commands
    for xml_file in xml_files:
        subcommand = ('admin batch ' + xml_file)
        execute_ccollab(tool_conf_data.get('collaborator_ccollab_location'), subcommand)


def create_filtering_files(tool_conf_data):
    """This function creates the filtering files needed for Collaborator upload.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Print a status message
    logging.info('\t>> Checking analysis filtering output file.')

    # Determine if the baseline filtering list exists, or should be created
    if not os.path.exists(tool_conf_data.get('filtering_output_file')):
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


def run_analysis(baseline_conf_data, override=False):
    """This function runs this module based on input from the scrub.cfg file

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
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
    attempt_analysis = tool_conf_data.get('collaborator_upload') or override

    # Determine if Collaborator upload can be run
    if attempt_analysis:
        try:
            # Create the logging file, if it doesn't already exist
            scrub_utilities.create_logger(tool_conf_data.get('collaborator_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform Collaborator upload...')

            # Prepare for the upload
            initialize_upload(tool_conf_data)

            # Perform the upload
            perform_upload(tool_conf_data)

            # Set the exit code
            collaborator_exit_code = 0

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('Collaborator upload could not be performed. Please see log file %s for more information.',
                            tool_conf_data.get('collaborator_log_file'))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            collaborator_exit_code = 1

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.warning('Collaborator upload could not be performed. Please see log file %s for more information.',
                            tool_conf_data.get('collaborator_log_file'))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            collaborator_exit_code = 100

        finally:
            # Delete the review if necessary
            if (collaborator_exit_code > 0) and (tool_conf_data.get('collaborator_review_id') > 0):
                subcommand = ('admin review delete ' + str(tool_conf_data.get('collaborator_review_id')))
                execute_ccollab(tool_conf_data.get('collaborator_ccollab_location'), subcommand)

            # Close the loggers
            logging.getLogger().handlers = []

            # Update the permissions of the log file if it exists
            if os.path.exists(tool_conf_data.get('collaborator_log_file')):
                os.chmod(tool_conf_data.get('collaborator_log_file'), 438)

                # Move the log file to line up with the review id, if it exists
                if tool_conf_data.get('collaborator_review_id') > 0:
                    shutil.move(tool_conf_data.get('collaborator_log_file'),
                                tool_conf_data.get('scrub_log_dir') + '/collaborator_' +
                                str(tool_conf_data.get('collaborator_review_id')) + '.log')

    # Return the exit code
    return collaborator_exit_code


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    current_user = pwd.getpwuid(os.getuid()).pw_name
    collaborator_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/collaborator_' +
                                             current_user + '.log')
    collaborator_filtering_output_file = os.path.normpath(tool_conf_data.get('scrub_analysis_dir') +
                                                          '/SCRUBCollaboratorFilteringList')

    # Add derived values to the dictionary
    tool_conf_data.update({'collaborator_log_file': collaborator_log_file})
    tool_conf_data.update({'collaborator_filtering_output_file': collaborator_filtering_output_file})
    tool_conf_data.update({'collaborator_review_id': 0})

    # Set the username if necessary
    if tool_conf_data.get('collaborator_username') == '':
        tool_conf_data.update({'collaborator_username': current_user})

    # Determine if Collaborator can be run
    if not (tool_conf_data.get('collaborator_server')):
        # Update the analysis flag if necessary
        if tool_conf_data.get('collaborator_upload'):
            tool_conf_data.update({'collaborator_upload': False})

            # Print a status message
            print('\nWARNING: Unable to perform Collaborator upload. Required configuration inputs are missing.\n')
