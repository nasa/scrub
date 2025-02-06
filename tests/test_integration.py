import os
import re
import sys
import pytest
import pathlib
import traceback
import shutil
from scrub import scrub_cli
from scrub.tools.parsers import get_codesonar_warnings
from scrub.tools.parsers import get_coverity_warnings
from scrub.tools.parsers import get_gbuild_warnings
from scrub.tools.parsers import get_gcc_warnings
from scrub.tools.parsers import get_javac_warnings
from scrub.tools.parsers import get_pylint_warnings
from scrub.tools.parsers import get_sonarqube_warnings
from scrub.tools.parsers import translate_results
from scrub import utils


# Initialize variables
test_root = os.path.abspath(os.path.dirname(__file__))
log_dir = os.path.join(test_root, 'log_files')

# Make the log directory if necessary
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

# Set the test directories
# c_testcase = os.path.abspath('./tests/integration_tests/c_testcase')
# java_testcase = os.path.abspath('./tests/integration_tests/java_testcase')
# javascript_testcase = os.path.abspath('./tests/integration_tests/javascript_testcase')
# python_testcase = os.path.abspath('./tests/integration_tests/python_testcase')
# multi_lang_testcase = os.path.abspath('./tests/integration_tests/multi_lang_testcase')
# diff_testcase = os.path.abspath('./tests/integration_tests/diff_testcase')
# raw_files = pathlib.Path('./tests/integration_tests/parsers').resolve().glob('*')
c_testcase = pathlib.Path(__file__).parent.joinpath('integration_tests/c_testcase')
java_testcase = pathlib.Path(__file__).parent.joinpath('integration_tests/java_testcase')
javascript_testcase = pathlib.Path(__file__).parent.joinpath('integration_tests/javascript_testcase')
python_testcase = pathlib.Path(__file__).parent.joinpath('integration_tests/python_testcase')
multi_lang_testcase = pathlib.Path(__file__).parent.joinpath('integration_tests/multi_lang_testcase')
diff_testcase = pathlib.Path(__file__).parent.joinpath('integration_tests/diff_testcase')
raw_files = pathlib.Path(__file__).parent.joinpath('integration_tests/parsers').glob('*')
parser_config_data = utils.scrub_utilities.parse_common_configs(c_testcase.joinpath('scrub.cfg'), None)

@pytest.mark.parametrize("raw_file", raw_files)
def test_parser(raw_file, capsys):
    output_file = raw_file.parent.joinpath(raw_file.stem + '_output.scrub')

    if 'codesonar' in raw_file.stem and raw_file.suffix == '.xml':
        get_codesonar_warnings.parse_warnings(pathlib.Path(__file__).parent.joinpath('integration_tests/parsers'),
                                              parser_config_data, raw_file, output_file)
    elif raw_file.suffix == '.sarif':
        translate_results.perform_translation(raw_file, output_file, c_testcase, 'scrub')
    elif 'codeql' in raw_file.stem:
        translate_results.perform_translation(raw_file, output_file, pathlib.Path(c_testcase), 'scrub')
    elif 'coverity' in raw_file.stem:
        warnings = get_coverity_warnings.parse_json(raw_file)
        translate_results.create_scrub_output_file(warnings, output_file)
    elif 'gbuild' in raw_file.stem:
        get_gbuild_warnings.parse_warnings(pathlib.Path(__file__).parent.joinpath('integration_tests/parsers'),
                                          parser_config_data, raw_file, output_file)
    elif 'gcc' in raw_file.stem:
        get_gcc_warnings.parse_warnings(pathlib.Path(__file__).parent.joinpath('integration_tests/parsers'),
                                        parser_config_data, raw_file, output_file)
    elif 'java' in raw_file.stem:
        get_javac_warnings.parse_warnings(pathlib.Path(__file__).parent.joinpath('integration_tests/parsers'),
                                          parser_config_data, raw_file, output_file)
    elif 'pylint' in raw_file.stem:
        get_pylint_warnings.parse_warnings(pathlib.Path(__file__).parent.joinpath('integration_tests/parsers'),
                                          parser_config_data, raw_file, output_file)
    elif 'sonarqube' in raw_file.stem:
        get_sonarqube_warnings.parse_warnings(raw_file, parser_config_data, output_file)

    # Verify output
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    output_file.unlink()

# Testcase | Class       | Description            | Expected Outcome   |
# -------- + ----------- + ---------------------- + ------------------ |
# 0        | Error       | Missing config file    | Exit Code: 10      |
# 1        | Error       | Broken tool execution  | Exit code: 1       |
# 2        | Error       | Incorrect sub-command  | Exit code: 0       |
# 3        | Error       | Existing working dir   | Exit code: 10      |
# 4        | Integration | Help message           | Exit code: 0       |
# 5        | Integration | Generate scrub.cfg     | Exit code: 0       |
# 6        | Integration | Check version          | Exit code: 0       |
# 7        | Integration | Diff testcase          | Exit code: 0       |
# 8        | Integration | C integration          | Exit Code: 0       |
# 9        | Integration | C custom configs       | Exit Code: 0       |
# 10       | Integration | Java integration       | Exit Code: 0       |
# 11       | Integration | JavaScript integration | Exit Code: 0       |
# 12       | Integration | Python integration     | Exit Code: 0       |
# 13       | Integration | Filter only            | Exit Code: 0       |
# 14       | Integration | Single tool            | Exit Code: 0       |
# 15       | Integration | Multiple tools         | Exit Code: 0       |
# 16       | Integration | Single target          | Exit Code: 0       |
# 17       | Integration | Multiple targets       | Exit Code: 0       |
# 18       | Integration | Multilang integration  | Exit Code: 0       |
# 19       | Integration | Multilang subset       | Exit Code: 0       |


# testcases = [[java_testcase, ['run', '--config', 'missing_scrub.cfg'], 10],                          # Testcase 0
#              [c_testcase, ['run', '--clean', '--config', 'bad_scrub.cfg'], 1],                       # Testcase 1
#              [c_testcase, ['dummy'], 0],                                                             # Testcase 2
#              [c_testcase, ['run', '--config', 'bad_dir_scrub.cfg'], 10],                             # Testcase 3
#              [c_testcase, ['--help'], 0],                                                            # Testcase 4
#              [c_testcase, ['get-conf'], 0],                                                          # Testcase 5
#              [c_testcase, ['-version'], 0],                                                          # Testcase 6
#              [diff_testcase, ['diff', '--baseline-source', 'results1', '--baseline-scrub',           # Testcase 7
#                               'results1/.scrub', '--comparison-source', 'results2',
#                               '--comparison-scrub', 'results2/.scrub'], 0],
#              [c_testcase, ['run', '--clean', '--debug'], 0],                                         # Testcase 8
#              [c_testcase, ['run', '--clean', '--debug', '--config', 'scrub_custom.cfg'], 0],         # Testcase 9
#              [java_testcase, ['run', '--clean', '--debug'], 0],                                      # Testcase 10
#              [javascript_testcase, ['run', '--clean', '--debug'], 0],                                # Testcase 11
#              [python_testcase, ['run', '--clean', '--debug'], 0],                                    # Testcase 12
#              [c_testcase, ['run', '--tools', 'filter'], 0],                                          # Testcase 13
#              [c_testcase, ['run', '--quiet', '--tools', 'coverity'], 0],                             # Testcase 14
#              [javascript_testcase, ['run', '--tools', 'coverity', 'sonarqube'], 0],                  # Testcase 15
#              [python_testcase, ['run', '--tools', 'none', '--targets', 'collaborator'], 0],          # Testcase 16
#              [c_testcase, ['run', '--targets', 'collaborator', 'scrub_gui'], 0],                     # Testcase 17
#              [multi_lang_testcase, ['run', '--debug'], 0],                                           # Testcase 18
#              [multi_lang_testcase, ['run', '--debug', '--config', 'scrub_subset.cfg'], 0]           # Testcase 19

testcases = [
                {
                    "name": "missing-configuration-file",
                    "location": java_testcase,
                    "subcommand": "run",
                    "parameters": ['--clean', '--config', 'bad_scrub.cfg'],
                    "exit-code": 10
                },
                {
                    "name": "bad-config-file",
                    "location": c_testcase,
                    "subcommand": "run",
                    "parameters": ['--clean', '--config', 'bad_scrub.cfg'],
                    "exit-code": 1
                },
                {
                    "name": "bad-subcommand",
                    "location": c_testcase,
                    "subcommand": "dummy",
                    "parameters": [],
                    "exit-code": 0
                },
                {
                    "name": "bad-working-dir",
                    "location": c_testcase,
                    "subcommand": "run",
                    "parameters": ['--config', 'bad_dir_scrub.cfg'],
                    "exit-code": 10
                },
                {
                    "name": "help-message",
                    "location": c_testcase,
                    "subcommand": "",
                    "parameters": ['--help'],
                    "exit-code": 0
                },
                {
                    "name": "generate-config",
                    "location": c_testcase,
                    "subcommand": "get-conf",
                    "parameters": [],
                    "exit-code": 0
                },
                {
                    "name": "check-version",
                    "location": c_testcase,
                    "subcommand": "",
                    "parameters": ['-version'],
                    "exit-code": 0
                },
                {
                    "name": "diff-test",
                    "location": diff_testcase,
                    "subcommand": "diff",
                    "parameters": ['--baseline-source', 'results1', '--baseline-scrub', 'results1/.scrub',
                                   '--comparison-source', 'results2', '--comparison-scrub', 'results2/.scrub'],
                    "exit-code": 0
                },
                {
                    "name": "c-testcase",
                    "location": c_testcase,
                    "subcommand": "run",
                    "parameters": ['--clean', '--debug'],
                    "exit-code": 0
                },
                {
                    "name": "c-custom-testcase",
                    "location": c_testcase,
                    "subcommand": "run",
                    "parameters": ['--clean', '--debug', '--config', 'scrub_custom.cfg'],
                    "exit-code": 0
                },
                {
                    "name": "java-testcase",
                    "location": java_testcase,
                    "subcommand": "run",
                    "parameters": ['--clean', '--debug'],
                    "exit-code": 0
                },
                {
                    "name": "javascript-testcase",
                    "location": javascript_testcase,
                    "subcommand": "run",
                    "parameters": ['--clean', '--debug'],
                    "exit-code": 0
                },
                {
                    "name": "python-testcase",
                    "location": python_testcase,
                    "subcommand": "run",
                    "parameters": ['--clean', '--debug'],
                    "exit-code": 0
                },
                {
                    "name": "filter-only-testcase",
                    "location": c_testcase,
                    "subcommand": "run",
                    "parameters": ['--tools', 'filter'],
                    "exit-code": 0
                },
                {
                    "name": "single-tool-testcase",
                    "location": c_testcase,
                    "subcommand": "run",
                    "parameters": ['--quiet', '--tools', 'coverity'],
                    "exit-code": 0
                },
                {
                    "name": "multi-tool-testcase",
                    "location": javascript_testcase,
                    "subcommand": "run",
                    "parameters": ['--tools', 'coverity', 'sonarqube'],
                    "exit-code": 0
                },
                {
                    "name": "collaborator-upload-testcase",
                    "location": python_testcase,
                    "subcommand": "run",
                    "parameters": ['--tools', 'none', '--targets', 'collaborator'],
                    "exit-code": 0
                },
                {
                    "name": "multi-target-testcase",
                    "location": c_testcase,
                    "subcommand": "run",
                    "parameters": ['--targets', 'collaborator', 'scrub_gui'],
                    "exit-code": 0
                },
                {
                    "name": "multi-language-testcase",
                    "location": multi_lang_testcase,
                    "subcommand": "run",
                    "parameters": ['--debug'],
                    "exit-code": 0
                },
                {
                    "name": "multi-language-subset-testcase",
                    "location": multi_lang_testcase,
                    "subcommand": "run",
                    "parameters": ['--debug', '--config', 'scrub_subset.cfg'],
                    "exit-code": 0
                }
             ]


@pytest.mark.parametrize("testcase", testcases)
def test_scrub(testcase, capsys):
    # Create the log file
    # test_log_file = os.path.join(log_dir, 'scrub-testcase-' + str(testcases.index(testcase)) + '.log')
    test_log_file = os.path.join(log_dir, testcase['name'] + '.log')

    # Navigate to the test directory
    start_dir = os.getcwd()
    # os.chdir(testcase[0])
    os.chdir(testcase['location'])

    try:
        # Run scrub
        # sys.argv = ['/opt/project/scrub/scrub_cli.py'] + testcase[1]
        sys.argv = ['/opt/project/scrub/scrub_cli.py', testcase['subcommand']] + testcase['parameters']
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
        # assert exit_code == testcase[2]
        assert exit_code == testcase['exit-code']


    finally:
        # Navigate to the start directory
        os.chdir(start_dir)