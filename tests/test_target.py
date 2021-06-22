import os
import glob
import shutil
import pytest
from tests import helpers
from scrub.utils import do_clean
from scrub.utils import scrub_utilities


@pytest.mark.parametrize('operation', ['normal', 'tool_error', 'upload_error', 'invalid_config', 'custom_config'])
def test_collaborator(operation):
    # Import the modules
    import scrub.targets.collaborator.do_collaborator as do_collaborator

    # Initialize variables
    start_dir = os.getcwd()
    log_file = helpers.log_dir + '/collaborator-' + operation + '.log'

    # Change directory
    os.chdir(helpers.c_test_dir)

    # Remove any existing results
    do_clean.clean_directory(helpers.c_test_dir)

    # Copy the test data into the directory
    shutil.copytree(helpers.test_root + '/test_data/sample_data/sample_results_c', './.scrub')

    # Get the configuration data
    if operation == 'tool_error':
        conf_data = scrub_utilities.parse_common_configs(helpers.c_conf_file)
        conf_data.update({'collaborator_review_group': 'bad review group'})
    elif operation == 'custom_config':
        conf_data = scrub_utilities.parse_common_configs(helpers.c_custom_conf_file)
        os.environ['PATH'] = conf_data.get('collaborator_ccollab_location') + os.pathsep + os.environ['PATH']
        conf_data.update({'collaborator_ccollab_location': ''})
    elif operation == 'invalid_config':
        conf_data = scrub_utilities.parse_common_configs(helpers.c_conf_file)
        conf_data.update({'collaborator_server': ''})
    else:
        conf_data = scrub_utilities.parse_common_configs(helpers.c_conf_file)

    # Create an upload failure
    if operation == 'upload_error':
        with open(helpers.c_test_dir + '/.scrub/SCRUBAnalysisFilteringList', 'a') as output_fh:
            output_fh.write('dummy_file.c')

    # Perform the upload
    collaborator_exit_code = do_collaborator.run_analysis(conf_data)

    # Copy the log file
    if operation != 'invalid_config':
        collaborator_log_file = glob.glob(helpers.c_test_dir + '/.scrub/log_files/collaborator*.log')[0]
        shutil.copyfile(collaborator_log_file, log_file)

    # Change back to the start directory
    os.chdir(start_dir)

    # Examine the output
    if operation == 'tool_error' or operation == 'upload_error':
        assert collaborator_exit_code == 1
    elif operation == 'invalid_config':
        assert collaborator_exit_code == 2
    else:
        assert collaborator_exit_code == 0
