import os
import re
import sys
import shutil
import traceback
from scrub import scrubme
from tests import helpers


def test_command_execution_error(capsys):
    # Initialize variables
    start_dir = os.getcwd()
    test_log_file = helpers.log_dir + '/test-errors-command_execution.log'
    conf_file = helpers.c_conf_file
    codebase = helpers.c_test_dir

    # Make a copy of the test code
    if os.path.exists(helpers.test_tmp_dir):
        shutil.rmtree(helpers.test_tmp_dir)
    shutil.copytree(codebase, helpers.test_tmp_dir)

    # Import the configuration data
    with open(conf_file, 'r') as input_fh:
        conf_data = input_fh.readlines()

    # Create the conf file
    conf_data = helpers.update_tag(conf_data, 'GCC_BUILD_CMD', 'exit 1')
    conf_data = helpers.update_tag(conf_data, 'COLLABORATOR_UPLOAD', 'False')
    helpers.create_conf_file(conf_data, helpers.test_tmp_dir + '/scrub.cfg')

    # Run the test
    try:
        os.chdir(helpers.test_tmp_dir)
        sys.argv = ['/opt/project/scrub/scrub_cli.py', 'run', '--tool', 'gcc', '--config', './scrub.cfg']
        scrubme.parse_arguments()

    except SystemExit:
        # Get the exit code
        sys_exit_text = traceback.format_exc()
        exit_code = int(list(filter(None, re.split('\n|:', sys_exit_text)))[-1])

        # There should be no system exit
        assert exit_code > 0

    finally:
        # Write results to the output log file
        with open(test_log_file, 'w') as output_fh:
            system_output = capsys.readouterr()
            output_fh.write(system_output.err)
            output_fh.write(system_output.out)

        # Navigate to the start directory
        os.chdir(start_dir)


def test_missing_substitution(capsys):
    # Initialize variables
    start_dir = os.getcwd()
    test_log_file = helpers.log_dir + '/test-errors-missing_substitution.log'
    conf_file = helpers.c_conf_file
    codebase = helpers.c_test_dir

    # Make a copy of the test code
    if os.path.exists(helpers.test_tmp_dir):
        shutil.rmtree(helpers.test_tmp_dir)
    shutil.copytree(codebase, helpers.test_tmp_dir)

    # Import the configuration data
    with open(conf_file, 'r') as input_fh:
        conf_data = input_fh.readlines()

    # Create the conf file
    conf_data = helpers.update_tag(conf_data, 'GCC_CLEAN_CMD', '${{DUMMY_SUB}}')
    conf_data = helpers.update_tag(conf_data, 'COLLABORATOR_UPLOAD', 'False')
    helpers.create_conf_file(conf_data, helpers.test_tmp_dir + '/scrub.cfg')

    # Run the test
    try:
        os.chdir(helpers.test_tmp_dir)
        sys.argv = ['/opt/project/scrub/scrub_cli.py', 'run', '--tool', 'gcc', '--config', './scrub.cfg']
        scrubme.parse_arguments()

    except SystemExit:
        # Get the exit code
        sys_exit_text = traceback.format_exc()
        exit_code = int(list(filter(None, re.split('\n|:', sys_exit_text)))[-1])

        # Read in the contents of the log file
        with open(helpers.test_tmp_dir + '/.scrub/log_files/gcc.log', 'r') as log_fh:
            log_data = log_fh.read()

        # There should be no system exit
        # assert exit_code == 0
        assert 'bad substitution' in log_data

    finally:
        # Write results to the output log file
        with open(test_log_file, 'w') as output_fh:
            system_output = capsys.readouterr()
            output_fh.write(system_output.err)
            output_fh.write(system_output.out)

        # Navigate to the start directory
        os.chdir(start_dir)


def test_missing_config(capsys):
    # Initialize variables
    start_dir = os.getcwd()
    test_log_file = helpers.log_dir + '/test-errors-missing_config.log'
    codebase = helpers.c_test_dir

    # Make a copy of the test code
    if os.path.exists(helpers.test_tmp_dir):
        shutil.rmtree(helpers.test_tmp_dir)
    shutil.copytree(codebase, helpers.test_tmp_dir)

    # Remove configuration file if it exists
    if os.path.exists(helpers.test_tmp_dir + '/scrub.cfg'):
        os.remove(helpers.test_tmp_dir + '/scrub.cfg')

    # Run the test
    try:
        os.chdir(helpers.test_tmp_dir)
        sys.argv = ['/opt/project/scrub/scrub_cli.py', 'run', '--config', './scrub.cfg']
        scrubme.parse_arguments()

    except SystemExit:
        # Get the exit code
        sys_exit_text = traceback.format_exc()
        exit_code = list(filter(None, re.split('\n', sys_exit_text)))[-1]

        # There should be no system exit
        assert exit_code == 'SystemExit: ERROR: Configuration file ./scrub.cfg does not exist.'

    finally:
        # Write results to the output log file
        with open(test_log_file, 'w') as output_fh:
            system_output = capsys.readouterr()
            output_fh.write(system_output.err)
            output_fh.write(system_output.out)

        # Navigate to the start directory
        os.chdir(start_dir)
