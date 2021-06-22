import re
import os
import subprocess
import sys
import glob
import shutil


# Initialize variables
scrub_root = os.path.abspath(os.path.dirname(__file__) + '/..')
test_root = scrub_root + '/tests'
log_dir = test_root + '/log_files'
module_list = ['scrub.tools.compiler.do_gbuild',  'scrub.tools.compiler.do_gcc', 'scrub.tools.compiler.do_javac',
               'scrub.tools.coverity.do_coverity', 'scrub.tools.custom.do_custom', 'scrub.tools.klocwork.do_klocwork',
               'scrub.tools.semmle.do_semmle', 'scrub.tools.codeql.do_codeql', 'scrub.tools.codesonar.do_codesonar']
versioned_tools = ['codeql', 'semmle', 'coverity', 'codesonar', 'klocwork']
custom_flag_tools = ['codeql', 'semmle', 'coverity', 'codesonar', 'klocwork']

# Initialize C variables
c_test_dir = test_root + '/integration_tests/c_testcase'
filtering_log_file = c_test_dir + '/.scrub/log_files/filtering.log'
c_conf_file = test_root + '/test_data/configuration_files/c/scrub_c.cfg'
c_custom_conf_file = test_root + '/test_data/configuration_files/c/scrub_c_custom.cfg'
c_exclude_queries_file = test_root + '/test_data/configuration_files/c/SCRUBExcludeQueries_c'
c_regex_filtering_file = test_root + '/test_data/configuration_files/c/SCRUBFilters_c'
module_list_c = ['scrub.tools.compiler.do_gcc', 'scrub.tools.compiler.do_gbuild', 'scrub.tools.coverity.do_coverity',
                 'scrub.tools.semmle.do_semmle', 'scrub.tools.codesonar.do_codesonar',
                 'scrub.tools.klocwork.do_klocwork', 'scrub.tools.codeql.do_codeql', 'scrub.tools.custom.do_custom']

# Initialize java variables
java_test_dir = test_root + '/integration_tests/java_testcase'
java_custom_conf_file = test_root + '/test_data/configuration_files/java/scrub_java_custom.cfg'
java_conf_file = test_root + '/test_data/configuration_files/java/scrub_java.cfg'
java_exclude_queries_file = test_root + '/test_data/configuration_files/java/SCRUBExcludeQueries_java'
java_regex_filtering_file = test_root + '/test_data/configuration_files/java/SCRUBFilters_java'
module_list_java = ['scrub.tools.compiler.do_javac', 'scrub.tools.coverity.do_coverity', 'scrub.tools.semmle.do_semmle',
                    'scrub.tools.codesonar.do_codesonar', 'scrub.tools.codeql.do_codeql']


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


def init_codebase(source_root, conf_data, tag):
    # Initialize variables
    start_dir = os.getcwd()

    # Change to the directory of interest
    os.chdir(source_root)

    # Write out the conf data
    create_conf_file(isolate_tool(conf_data.copy(), tag), source_root + '/scrub.cfg')

    # Run scrubme
    os.system('python3 ./../../../scrubme.py >> /dev/null 2>&1')

    # Change back to the starting directory
    os.chdir(start_dir)


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


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as input_fh:
        conf_data = input_fh.readlines()

    # update_tag(conf_data, sys.argv[2], sys.argv[3])
    # disable_all_tools(conf_data)
    # isolate_tool(conf_data, sys.argv[2])
    get_tool_list('/Users/lbarner/Desktop/Projects/SCRUB_dev/Rel2.4')
