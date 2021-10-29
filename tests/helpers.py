import re
import os
import subprocess
import sys
import glob
import shutil


# Initialize variables
scrub_root = os.path.abspath(os.path.dirname(__file__) + '/..')
test_root = scrub_root + '/tests'
test_tmp_dir = test_root + '/integration_tests/tmp'
log_dir = test_root + '/log_files'
module_list = ['gbuild', 'gcc', 'javac', 'pylint', 'coverity', 'codeql', 'codesonar']
versioned_tools = ['codeql', 'coverity', 'codesonar', 'klocwork']
custom_flag_tools = ['codeql', 'coverity', 'codesonar']

# Initialize C variables
c_test_dir = test_root + '/integration_tests/c_testcase'
filtering_log_file = c_test_dir + '/.scrub/log_files/filtering.log'
c_conf_file = test_root + '/test_data/configuration_files/c/scrub_c.cfg'
c_custom_conf_file = test_root + '/test_data/configuration_files/c/scrub_c_custom.cfg'
c_exclude_queries_file = test_root + '/test_data/configuration_files/c/SCRUBExcludeQueries_c'
c_regex_filtering_file = test_root + '/test_data/configuration_files/c/SCRUBFilters_c'
module_list_c = ['gcc', 'gbuild', 'coverity', 'codesonar', 'codeql']

# Initialize java variables
java_test_dir = test_root + '/integration_tests/java_testcase'
java_custom_conf_file = test_root + '/test_data/configuration_files/java/scrub_java_custom.cfg'
java_conf_file = test_root + '/test_data/configuration_files/java/scrub_java.cfg'
java_exclude_queries_file = test_root + '/test_data/configuration_files/java/SCRUBExcludeQueries_java'
java_regex_filtering_file = test_root + '/test_data/configuration_files/java/SCRUBFilters_java'
module_list_java = ['javac', 'coverity', 'codesonar', 'codeql']

# Initialize python variables
#python_test_dir = test_root + '/integration_tests/python_testcase'
python_test_dir = scrub_root + '/scrub'
python_custom_conf_file = test_root + '/test_data/configuration_files/python/scrub_python_custom.cfg'
python_conf_file = test_root + '/test_data/configuration_files/python/scrub_python.cfg'
python_exclude_queries_file = test_root + '/test_data/configuration_files/python/SCRUBExcludeQueries_python'
python_regex_filtering_file = test_root + '/test_data/configuration_files/python/SCRUBFilters_python'
module_list_python = ['pylint', 'coverity', 'codesonar', 'codeql']


def init_testcase(conf_data, test_dir, init_state, log_dir):
    # Create the log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    # Initialize the codebase
    if init_state == 'clean':
        clean_codebase(test_dir, test_dir + '/src', 'make clean')
    elif init_state == 'dirty':
        clean_codebase(test_dir, test_dir + '/src', 'make clean')
        init_codebase(test_dir, conf_data, 'GCC_WARNINGS')
    elif init_state == 'empty':
        clean_codebase(test_dir, test_dir + '/src', 'make clean')
        os.mkdir(test_dir + '/.scrub')

    # Write out the conf data
    with open('scrub.cfg', 'w+') as output_fh:
        for line in conf_data:
            output_fh.write('%s' % line)


def clean_codebase(source_root, clean_dir, clean_cmd):
    # Initialize variables
    start_dir = os.getcwd()

    # Clean the code
    os.chdir(clean_dir)
    os.system(clean_cmd + ' >> /dev/null 2>&1')

    # Remove scrub artifacts
    os.chdir(source_root)
    if os.path.exists(source_root + '/CollaboratorFilters'):
        os.remove(source_root + '/CollaboratorFilters')
    if os.path.exists(source_root + '/SCRUBFilters'):
        os.remove(source_root + '/SCRUBFilters')

    scrub_list = glob.glob(source_root + '/**/.scrub', recursive=True)
    for scrub_item in scrub_list:
        shutil.rmtree(scrub_item)

    # Switch back to the start dir
    os.chdir(start_dir)


def create_conf_file(conf_data, output_file):
    # Write out the conf data
    with open(output_file, 'w+') as output_fh:
        for line in conf_data:
            output_fh.write('%s' % line)


def init_codebase(source_root, lang, state):
    # Create the SCRUB directory
    if os.path.exists(source_root + '/.scrub'):
        shutil.rmtree(source_root + '/.scrub')

    # os.mkdir(source_root + '/.scrub')
    if state == 'empty':
        os.mkdir(source_root + '/.scrub')
    elif state == 'dirty':
        # Copy the results
        if lang == 'c':
            shutil.copytree(test_root + '/test_data/sample_data/sample_c_results', source_root + '/.scrub')
        elif lang == 'j':
            shutil.copytree(test_root + '/test_data/sample_data/sample_java_results/*', source_root + '/.scrub')
        elif lang == 'p':
            shutil.copytree(test_root + '/test_data/sample_data/sample_python_results/*', source_root + '/.scrub')


def execute_command(call_string, my_env, output_file=None):
    # Initialize variables
    output_data = ''

    # Execute the call string and capture the output
    if output_file:
        proc = subprocess.Popen(call_string, shell=True, env=my_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                encoding='utf-8')

        # Write the output to the logging file
        for stdout_line in iter(proc.stdout.readline, ''):
            output_data = output_data + str(stdout_line)

        # Write results to the output file
        with open(output_file, 'w') as output_fh:
            output_fh.write(output_data)

    else:
        proc = subprocess.Popen(call_string, shell=True, env=my_env, encoding='utf-8')

        # Wait for the process to finish
        proc.wait(timeout=None)


def get_tool_list(root_dir):
    tool_list = []
    do_files = glob.glob(root_dir + '/tools/*/do*.py')

    for item in do_files:
        tool_list.append(os.path.relpath(item, root_dir).replace('/', '.').replace('.py', ''))

    return tool_list


def update_tag(conf_data, tag, new_value):
    # Update the line of interest
    for i in range(0, len(conf_data)):
        line = conf_data[i].strip()
        if tag in line and not line.startswith('#'):
            conf_data[i] = re.split(':', line)[0] + ': ' + new_value + '\n'
            break

    return conf_data


def isolate_tool(conf_data, tag):
    # Make a copy of the conf data
    updated_conf_data = conf_data.copy()

    # Update the line of interest
    for i in range(0, len(updated_conf_data)):
        line = updated_conf_data[i].strip()
        if ((tag not in line) and ('WARNINGS' in line or 'UPLOAD' in line) and (not line.startswith('#')) and
                (line.count('_') == 1)):
            updated_conf_data[i] = re.split(':', line)[0] + ': False\n'
        elif (tag in line) and (not line.startswith('#')):
            updated_conf_data[i] = re.split(':', line)[0] + ': True\n'

    return updated_conf_data


def disable_all_tools(conf_data):
    # Iterate through all lines
    for i in range(0, len(conf_data)):
        line = conf_data[i].strip()
        if ('WARNINGS' in line or 'UPLOAD' in line) and (not line.startswith('#')) and (line.count('_') == 1):
            conf_data[i] = re.split(':', line)[0] + ': False\n'

    return conf_data

