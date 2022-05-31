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

# Testcase | Class       | Description            | Expected Outcome   |
# -------- + ----------- + ---------------------- + ------------------ |
# 0        | Error       | Missing config file    | Exit Code: 10      |
# 1        | Error       | Broken tool execution  | Exit code: 1       |
# 2        | Error       | Incorrect sub-command  | Exit code: 0       |
# 3        | Integration | Help message           | Exit code: 0       |
# 4        | Integration | Generate scrub.cfg     | Exit code: 0       |
# 5        | Integration | C integration          | Exit Code: 0       |
# 6        | Integration | Java integration       | Exit Code: 0       |
# 7        | Integration | JavaScript integration | Exit Code: 0       |
# 8        | Integration | Python integration     | Exit Code: 0       |
# 9        | Integration | Filter only            | Exit Code: 0       |
# 10       | Integration | Single tool            | Exit Code: 0       |
# 11       | Integration | Multiple tools         | Exit Code: 0       |
# 12       | Integration | Single target          | Exit Code: 0       |
# 13       | Integration | Multiple targets       | Exit Code: 0       |
# 14       | Integration | Diff utility           | Exit Code: 0       |


testcases = [[java_testcase, ['run', '--config', 'missing_scrub.cfg'], 10],          # Testcase 0
             [c_testcase, ['run', '--clean', '--config', 'bad_scrub.cfg'], 1],       # Testcase 1
             [c_testcase, ['dummy'], 0],                                             # Testcase 2
             [c_testcase, ['--help'], 0],                                            # Testcase 3
             [c_testcase, ['get-conf'], 0],                                          # Testcase 4
             [c_testcase, ['run', '--clean', '--debug'], 0],                         # Testcase 5
             [java_testcase, ['run', '--clean', '--debug'], 0],                      # Testcase 6
             [javascript_testcase, ['run', '--clean', '--debug'], 0],                # Testcase 7
             [python_testcase, ['run', '--clean', '--debug'], 0],                    # Testcase 8
             [c_testcase, ['run', '--tools', 'filter'], 0],                          # Testcase 9
             [c_testcase, ['run', '--quiet', '--tools', 'coverity'], 0],             # Testcase 10
             [javascript_testcase, ['run', '--tools', 'coverity', 'sonarqube'], 0],  # Testcase 11
             [python_testcase, ['run', '--targets', 'collaborator'], 0],             # Testcase 12
             [c_testcase, ['run', '--targets', 'collaborator', 'scrub_gui'], 0]      # Testcase 13
             ]


@pytest.mark.parametrize("testcase", testcases)
def test_scrub(testcase, capsys):
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

        # Check the exit code or other condition
        assert exit_code == testcase[2]


    finally:
        # Navigate to the start directory
        os.chdir(start_dir)
