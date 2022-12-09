import os
import re
import sys
import pytest
import pathlib
import traceback
from scrub import scrub_cli
from scrub.tools.parsers import get_codesonar_warnings
from scrub.tools.parsers import get_coverity_warnings
from scrub.tools.parsers import get_gbuild_warnings
from scrub.tools.parsers import get_gcc_warnings
from scrub.tools.parsers import get_javac_warnings
from scrub.tools.parsers import get_pylint_warnings
from scrub.tools.parsers import get_sonarqube_warnings
from scrub.tools.parsers import translate_results


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
multi_lang_testcase = os.path.abspath('./tests/integration_tests/multi_lang_testcase')
raw_files = pathlib.Path('./tests/integration_tests/parsers').resolve().glob('*')

@pytest.mark.parametrize("raw_file", raw_files)
def test_parser(raw_file, capsys):
    output_file = raw_file.parent.joinpath(raw_file.stem + '_output.scrub')

    if 'codesonar' in raw_file.stem and raw_file.suffix == '.xml':
        get_codesonar_warnings.parse_warnings(raw_file, output_file)
    elif 'codesonar' in raw_file.stem and raw_file.suffix == '.sarif':
        translate_results.perform_translation(raw_file, output_file, c_testcase, 'scrub')
    elif 'codeql' in raw_file.stem:
        translate_results.perform_translation(raw_file, output_file, pathlib.Path(c_testcase), 'scrub')
    elif 'coverity' in raw_file.stem:
        get_coverity_warnings.parse_json(raw_file, output_file)
    elif 'gbuild' in raw_file.stem:
        get_gbuild_warnings.parse_warnings(raw_file, output_file)
    elif 'gcc' in raw_file.stem:
        get_gcc_warnings.parse_warnings(raw_file, output_file)
    elif 'java' in raw_file.stem:
        get_javac_warnings.parse_warnings(raw_file, output_file)
    elif 'pylint' in raw_file.stem:
        get_pylint_warnings.parse_warnings(raw_file, output_file)
    elif 'sonarqube' in raw_file.stem:
        get_sonarqube_warnings.parse_warnings(raw_file.parent, output_file, pathlib.Path(c_testcase), os.getenv('SONARQUBE_SERVER'))

    # Verify output
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    output_file.unlink()

# Testcase | Class       | Description            | Expected Outcome   |
# -------- + ----------- + ---------------------- + ------------------ |
# 0        | Error       | Missing config file    | Exit Code: 10      |
# 1        | Error       | Broken tool execution  | Exit code: 1       |
# 2        | Error       | Incorrect sub-command  | Exit code: 0       |
# 3        | Error       | Existing working dir   | Exit code: 10
# 4        | Integration | Help message           | Exit code: 0       |
# 5        | Integration | Generate scrub.cfg     | Exit code: 0       |
# 6        | Integration | C integration          | Exit Code: 0       |
# 7        | Integration | C custom configs       | Exit Code: 0       |
# 8        | Integration | Java integration       | Exit Code: 0       |
# 9        | Integration | JavaScript integration | Exit Code: 0       |
# 10       | Integration | Python integration     | Exit Code: 0       |
# 11       | Integration | Filter only            | Exit Code: 0       |
# 12       | Integration | Single tool            | Exit Code: 0       |
# 13       | Integration | Multiple tools         | Exit Code: 0       |
# 14       | Integration | Single target          | Exit Code: 0       |
# 15       | Integration | Multiple targets       | Exit Code: 0       |
# 16       | Integration | Multilang integration  | Exit Code: 0       |


testcases = [[java_testcase, ['run', '--config', 'missing_scrub.cfg'], 10],                          # Testcase 0
             [c_testcase, ['run', '--clean', '--config', 'bad_scrub.cfg'], 1],                       # Testcase 1
             [c_testcase, ['dummy'], 0],                                                             # Testcase 2
             [c_testcase, ['run', '--config', 'bad_dir_scrub.cfg'], 10],                             # Testcase 3
             [c_testcase, ['--help'], 0],                                                            # Testcase 4
             [c_testcase, ['get-conf'], 0],                                                          # Testcase 5
             [c_testcase, ['run', '--clean', '--debug'], 0],                                         # Testcase 6
             [c_testcase, ['run', '--clean', '--debug', '--config', 'scrub_custom.cfg'], 0],         # Testcase 7
             [java_testcase, ['run', '--clean', '--debug'], 0],                                      # Testcase 8
             [javascript_testcase, ['run', '--clean', '--debug'], 0],                                # Testcase 9
             [python_testcase, ['run', '--clean', '--debug'], 0],                                    # Testcase 10
             [c_testcase, ['run', '--tools', 'filter'], 0],                                          # Testcase 11
             [c_testcase, ['run', '--quiet', '--tools', 'coverity'], 0],                             # Testcase 12
             [javascript_testcase, ['run', '--tools', 'coverity', 'sonarqube'], 0],                  # Testcase 13
             [python_testcase, ['run', '--tools', 'none', '--targets', 'collaborator'], 0],          # Testcase 14
             [c_testcase, ['run', '--targets', 'collaborator', 'scrub_gui'], 0],                     # Testcase 15
             [multi_lang_testcase, ['run', '--debug'], 0]                                            # Testcase 16
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