import os
import re
import sys
import pytest
import traceback
from scrub import scrub_cli


# Initialize variables
test_root = os.path.abspath(os.path.dirname(__file__))
log_dir = os.path.join(test_root, 'log_files')

# Make the log directory if necessary
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

# Set the test directories
test_dirs = ['./tests/integration_tests/c_testcase',
             './tests/integration_tests/java_testcase',
             './tests/integration_tests/python_testcase',
             './tests/integration_tests/javascript_testcase']

# Set the flags
cli_options = [['--clean', '--debug'],
               ['--config', 'scrub_custom.cfg', '--targets', 'scrub_gui'],
               ['--tools', 'coverity', '--targets', 'scrub_gui', '--quiet']]


@pytest.mark.parametrize("test_dir", test_dirs)
@pytest.mark.parametrize("config_file", ['scrub.cfg', 'scrub_custom.cfg'])
@pytest.mark.parametrize("cli_flags", cli_options)
def test_scrubme(test_dir, config_file, cli_flags, capsys):
    # Initialize variables
    language = os.path.basename(os.path.basename(test_dir)).split('_')[0]
    if 'custom' in config_file:
        operation = 'custom'
    else:
        operation = 'nominal'

    # Create the log file
    test_log_file = os.path.join(log_dir, 'scrub-run-' + language + '-' + operation + '_flags' +
                                 str(cli_options.index(cli_flags)) + '.log')

    # Navigate to the test directory
    start_dir = os.getcwd()
    os.chdir(test_dir)

    try:
        # Run scrubme
        sys.argv = ['/opt/project/scrub/scrub_cli.py', 'run']
        scrub_cli.main()

    except SystemExit:
        # Write results to the output log file
        with open(test_log_file, 'w') as output_fh:
            system_output = capsys.readouterr()
            output_fh.write(system_output.err)
            output_fh.write(system_output.out)

        # Get the exit code
        sys_exit_text = traceback.format_exc()
        exit_code = int(list(filter(None, re.split('\n|:', sys_exit_text)))[-1])

        # There should be no system exit
        assert exit_code == 0

    finally:
        # Navigate to the start directory
        os.chdir(start_dir)
