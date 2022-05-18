import os
import re
import sys
import pytest
import traceback
from tests import verify_output
from scrub import scrub_cli


# Initialize variables
test_root = os.path.abspath(os.path.dirname(__file__))
log_dir = os.path.join(test_root, 'log_files')

# Make the log directory if necessary
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

# Set the test directories
c_testcase = os.path.abspath('./tests/integration_tests/c_testcase')
java_testcase = os.path.abspath('./tests/integration_tests/java_testcase')
javascript_testcase = os.path.abspath('./tests/integration_tests/javascript_testcase')
python_testcase = os.path.abspath('./tests/integration_tests/python_testcase')
# c_testcase = os.path.abspath('/root/c_testcase')
# java_testcase = os.path.abspath('/root/java_testcase')
# javascript_testcase = os.path.abspath('/root/javascript_testcase')
# python_testcase = os.path.abspath('/root/python_testcase')

# test_dirs = ['./tests/integration_tests/c_testcase',
#              './tests/integration_tests/java_testcase',
#              './tests/integration_tests/python_testcase',
#              './tests/integration_tests/javascript_testcase']
#
# # Set the flags
# cli_options = [['--clean', '--debug'],
#                ['--config', 'scrub_error.cfg', '--targets', 'scrub_gui'],
#                ['--tools', 'coverity', '--targets', 'scrub_gui', '--quiet']]

testcases = [[c_testcase, ['run', '--clean', '--debug']],                         # Testcase 0: Default C Execution
             [java_testcase, ['run', '--clean', '--debug', '--config']],          # Testcase 1: Default Java Execution
             [javascript_testcase, ['run', '--clean', '--debug']],                # Testcase 2: Default JavaScript Execution
             [python_testcase, ['run', '--clean', '--debug']],                    # Testcase 3: Default Python Execution
             [c_testcase, ['run', '--tools', 'filter']],                          # Testcase 4: Filtering Only Execution
             [c_testcase, ['run', '--quiet', '--tools', 'coverity']],             # Testcase 5: Individual Tool Execution
             [javascript_testcase, ['run', '--tools', 'coverity', 'sonarqube']],  # Testcase 6: Multiple Tool Execution
             [java_testcase, ['run', '--config', 'scrub_error.cfg']],             # Testcase 6: Tool Error
             [python_testcase, ['run', '--targets', 'collaborator']],             # Testcase 7: Collaborator Upload
             [c_testcase, ['run', 'targets', 'scrub_gui']]                        # Testcase 8: SCRUB GUI Distribution
             ]

@pytest.mark.parametrize("testcase", testcases)
def test_scrubme(testcase, capsys):
    # Create the log file
    test_log_file = os.path.join(log_dir, 'scrub-testcase-' + str(testcases.index(testcase)) + '.log')

    # Navigate to the test directory
    start_dir = os.getcwd()
    os.chdir(testcase[0])

    try:
        # Run scrub
        sys.argv = ['/opt/project/scrub/scrub_cli.py'] +testcase[1]
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
