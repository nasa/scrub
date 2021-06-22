import sys
import os
import subprocess
import re
import logging
import traceback
import glob
import shutil
from scrub.utils import translate_results
from scrub.utils import scrub_utilities

VALID_TAGS = ['semmle', 'sem', 'sml']


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    semmle_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/semmle.log')
    semmle_analysis_dir = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/semmle_analysis')
    semmle_baseline_output_file = os.path.normpath(semmle_analysis_dir + '/semmle_baseline_raw.sarif')
    semmle_p10_output_file = os.path.normpath(semmle_analysis_dir + '/semmle_p10_raw.sarif')
    semmle_p10_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/semmle_p10_raw.scrub')
    semmle_p10_filtered_warning_file = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/p10.scrub')
    semmle_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/semmle_raw.scrub')
    semmle_filtered_warning_file = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/semmle.scrub')
    semmle_env = os.environ.copy()

    # Add derived values to the dictionary
    tool_conf_data.update({'semmle_log_file': semmle_log_file})
    tool_conf_data.update({'semmle_raw_warning_file': semmle_raw_warning_file})
    tool_conf_data.update({'semmle_filtered_warning_file': semmle_filtered_warning_file})
    tool_conf_data.update({'semmle_p10_raw_warning_file': semmle_p10_raw_warning_file})
    tool_conf_data.update({'semmle_p10_filtered_warning_file': semmle_p10_filtered_warning_file})
    tool_conf_data.update({'semmle_analysis_dir': semmle_analysis_dir})
    tool_conf_data.update({'semmle_baseline_output_file': semmle_baseline_output_file})
    tool_conf_data.update({'semmle_p10_output_file': semmle_p10_output_file})

    # Make sure the required inputs are present
    if not (tool_conf_data.get('semmle_build_cmd') and tool_conf_data.get('semmle_clean_cmd')):
        # Update the run flag if necessary
        if tool_conf_data.get('semmle_warnings'):
            tool_conf_data.update({'semmle_warnings': False})

            # Print a status message
            print('\nWARNING: Unable to perform Semmle analysis. Required configuration inputs are missing.\n')

    # Remove the analysis directory if it already exists
    if os.path.exists(semmle_analysis_dir):
        shutil.rmtree(semmle_analysis_dir)

    # Update the P10 flag if necessary
    if tool_conf_data.get('source_lang').lower() == 'j':
        tool_conf_data.update({'semmle_p10_analysis': False})

    # Make sure at least the baseline or P10 analysis will be run
    if not (tool_conf_data.get('semmle_baseline_analysis') or tool_conf_data.get('semmle_p10_analysis')):
        tool_conf_data.update({'semmle_warnings': False})

    # Update environment variables if necessary
    if tool_conf_data.get('semmle_path') != '':
        if 'ODASA_HOME' in semmle_env.keys():
            del semmle_env['ODASA_HOME']
        if 'SEMMLE_JAVA_HOME' in semmle_env.keys():
            del semmle_env['SEMMLE_JAVA_HOME']
        if 'SEMMLE_DIST' in semmle_env.keys():
            del semmle_env['SEMMLE_DIST']
        tool_conf_data.update({'semmle_env': semmle_env})


def perform_analysis(tool_conf_data):
    """This function runs the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize variables
    initial_dir = os.getcwd()

    # Change directory if necessary
    if tool_conf_data.get('semmle_build_dir') != os.getcwd():
        # Navigate to the compilation directory
        logging.info('\tChanging directory: %s', os.path.abspath(tool_conf_data.get('semmle_build_dir')))
        os.chdir(tool_conf_data.get('semmle_build_dir'))

    # Perform a clean
    call_string = tool_conf_data.get('semmle_clean_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy())

    # Change back to the initial dir if necessary
    if os.getcwd() != initial_dir:
        logging.info('\tChanging directory: %s', initial_dir)
        os.chdir(initial_dir)

    # Initialize Semmle
    setup_odasa(tool_conf_data)

    # Create the Semmle project
    create_project(tool_conf_data)

    # Determine what suite file should be used
    if tool_conf_data.get('semmle_suite_file'):
        suite_file = tool_conf_data.get('semmle_suite_file')
    else:
        if tool_conf_data.get('source_lang') == 'c':
            queries = ['+ odasa-cpp-metrics/Files/FLinesOfCode.ql: /Metrics/Size',
                       '+ semmlecode-cpp-queries/Architecture/Refactoring Opportunities/CyclomaticComplexity.ql: /Metrics',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-2/Rule 12/EnumInitialization.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-2/Rule 07/ThreadSafety.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-4/Rule 22/UseOfUndef.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-4/Rule 30/FunctionPointerConversions.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-4/Rule 31/IncludesFirst.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-2/Rule 09/AvoidSemaphores.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-4/Rule 28/HiddenPointerDereferenceMacro.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-3/Rule 18/CompoundExpressions.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-4/Rule 25/FunctionSizeLimits.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-3/Rule 13/ExternDeclsInHeader.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-4/Rule 24/MultipleVarDeclsPerLine.ql: /JPL',
                       '+ semmlecode-cpp-queries/JPL_C/LOC-3/Rule 17/BasicIntTypes.ql: /JPL',
                       '+ semmlecode-cpp-queries/Likely Bugs/Conversion/LossyPointerCast.ql: /Correctness/Dangerous Conversions',
                       '+ semmlecode-cpp-queries/Best Practices/Likely Errors/Slicing.ql: /Correctness/Dangerous Conversions',
                       '+ semmlecode-cpp-queries/Likely Bugs/Arithmetic/BadCheckOdd.ql: /Correctness/Dangerous Conversions',
                       '+ semmlecode-cpp-queries/Likely Bugs/Arithmetic/IntMultToLong.ql: /Correctness/Dangerous Conversions',
                       '+ semmlecode-cpp-queries/Likely Bugs/Conversion/NonzeroValueCastToPointer.ql: /Correctness/Dangerous Conversions',
                       '+ semmlecode-cpp-queries/Likely Bugs/Conversion/ArrayArgSizeMismatch.ql: /Correctness/Dangerous Conversions',
                       '+ semmlecode-cpp-queries/Likely Bugs/InconsistentCheckReturnNull.ql: /Correctness/Consistent Use',
                       '+ semmlecode-cpp-queries/Likely Bugs/InconsistentCallOnResult.ql: /Correctness/Consistent Use',
                       '+ semmlecode-cpp-queries/Likely Bugs/Likely Typos/AssignWhereCompareMeant.ql: /Correctness/Common Errors',
                       '+ semmlecode-cpp-queries/Likely Bugs/Likely Typos/CompareWhereAssignMeant.ql: /Correctness/Common Errors',
                       '+ semmlecode-cpp-queries/Likely Bugs/Likely Typos/ExprHasNoEffect.ql: /Correctness/Common Errors',
                       '+ semmlecode-cpp-queries/Likely Bugs/Likely Typos/ShortCircuitBitMask.ql: /Correctness/Common Errors',
                       '+ semmlecode-cpp-queries/Likely Bugs/Likely Typos/MissingEnumCaseInSwitch.ql: /Correctness/Common Errors',
                       '+ semmlecode-cpp-queries/Likely Bugs/Arithmetic/FloatComparison.ql: /Correctness/Common Errors',
                       '+ semmlecode-cpp-queries/Likely Bugs/Arithmetic/BitwiseSignCheck.ql: /Correctness/Common Errors',
                       '+ semmlecode-cpp-queries/Likely Bugs/NestedLoopSameVar.ql: /Correctness/Common Errors',
                       '+ semmlecode-cpp-queries/Likely Bugs/Memory Management/SuspiciousCallToMemset.ql: /Correctness/Use of Libraries',
                       '+ semmlecode-cpp-queries/Likely Bugs/Memory Management/SuspiciousSizeof.ql: /Correctness/Use of Libraries',
                       '+ semmlecode-cpp-queries/Likely Bugs/Memory Management/UnsafeUseOfStrcat.ql: /Correctness/Use of Libraries',
                       '+ semmlecode-cpp-queries/Likely Bugs/Memory Management/SuspiciousCallToStrncat.ql: /Correctness/Use of Libraries',
                       '+ semmlecode-cpp-queries/Likely Bugs/Memory Management/StrncpyFlippedArgs.ql: /Correctness/Use of Libraries',
                       '+ semmlecode-cpp-queries/Likely Bugs/Format/WrongNumberOfFormatArguments.ql: /Correctness/Use of Libraries',
                       '+ semmlecode-cpp-queries/Likely Bugs/Format/WrongTypeFormatArguments.ql: /Correctness/Use of Libraries',
                       '+ semmlecode-cpp-queries/Likely Bugs/Format/NonConstantFormat.ql: /Correctness/Use of Libraries',
                       '+ semmlecode-cpp-queries/Best Practices/Magic Constants/MagicConstantsString.ql: /Maintainability/Declarations',
                       '+ semmlecode-cpp-queries/Best Practices/Magic Constants/MagicConstantsNumbers.ql: /Maintainability/Declarations',
                       '+ semmlecode-cpp-queries/Best Practices/Unused Entities/UnusedStaticFunctions.ql: /Useless Code',
                       '+ semmlecode-cpp-queries/Best Practices/Unused Entities/UnusedStaticVariables.ql: /Useless Code',
                       '+ semmlecode-cpp-queries/Best Practices/Unused Entities/UnusedLocals.ql: /Useless Code',
                       '+ semmlecode-cpp-queries/external/DuplicateFunction.ql: /Useless Code/Duplicate Code',
                       '+ semmlecode-cpp-queries/external/MostlyDuplicateClass.ql: /Useless Code/Duplicate Code',
                       '+ semmlecode-cpp-queries/external/MostlyDuplicateFile.ql: /Useless Code/Duplicate Code',
                       '+ semmlecode-cpp-queries/external/MostlyDuplicateFunction.ql: /Useless Code/Duplicate Code',
                       '+ semmlecode-cpp-queries/external/MostlySimilarFile.ql: /Useless Code/Duplicate Code',
                       '+ semmlecode-cpp-queries/AlertSuppression.ql']

        elif tool_conf_data.get('source_lang') == 'j':
            queries = ['@import ${odasa_queries}/customer/default/java',
                       '+ semmlecode-queries/AlertSuppression.ql']
        else:
            raise UserWarning()

        # Create the baseline suite file
        suite_file = tool_conf_data.get('semmle_analysis_dir') + '/baseline_queries'
        with open(suite_file, 'w') as suite_fh:
            for query in queries:
                suite_fh.write('{}\n'.format(query))

    # Examine the addSnapshot flag values
    required_addsnapshot_flags = '--project ' + tool_conf_data.get('semmle_analysis_dir')
    tool_conf_data.update({'semmle_addsnapshot_flags': tool_conf_data.get('semmle_addsnapshot_flags') + ' ' +
                           required_addsnapshot_flags})

    # Add the latest code snapshot to the project
    add_snapshot(tool_conf_data.get('semmle_env'), tool_conf_data.get('semmle_addsnapshot_flags'))

    # Examine the buildSnapshot flag values
    required_buildsnapshot_flags = ('--latest --verbose --overwrite --project ' +
                                    tool_conf_data.get('semmle_analysis_dir'))
    tool_conf_data.update({'semmle_buildsnapshot_flags': tool_conf_data.get('semmle_buildsnapshot_flags') + ' ' +
                           required_buildsnapshot_flags})

    # Build the latest code snapshot
    build_snapshot(tool_conf_data.get('semmle_env'), tool_conf_data.get('semmle_buildsnapshot_flags'))

    # Examine the analyzeSnapshot flag values
    required_analyzesnapshot_flags = ('--allow-recompiles --project ' + tool_conf_data.get('semmle_analysis_dir') +
                                      ' --latest --format sarifv2.1.0 --output-file ' +
                                      tool_conf_data.get('semmle_baseline_output_file') + ' --suite ' + suite_file)
    baseline_analyzesnapshot_flags = (tool_conf_data.get('semmle_analyzesnapshot_flags') + ' ' +
                                      required_analyzesnapshot_flags)

    # Perform the baseline analysis?
    if tool_conf_data.get('semmle_baseline_analysis'):
        analyze_snapshot(tool_conf_data.get('semmle_env'), baseline_analyzesnapshot_flags)

    # Perform P10 analysis?
    if tool_conf_data.get('source_lang').lower() == 'c' and tool_conf_data.get('semmle_p10_analysis'):
        # Set the P10 query list
        p10_queries= ['+ odasa-cpp-metrics/Files/FLinesOfCode.ql: /Metrics/Size',
                      '+ semmlecode-cpp-queries/AlertSuppression.ql',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 1/UseOfGoto.ql: /Power of 10/Rule 1',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 1/UseOfJmp.ql: /Power of 10/Rule 1',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 1/UseOfRecursion.ql: /Power of 10/Rule 1',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 2/BoundedLoopIterations.ql: /Power of 10/Rule 2',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 2/ExitPermanentLoop.ql: /Power of 10/Rule 2',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 3/DynamicAllocAfterInit.ql: /Power of 10/Rule 3',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 4/FunctionTooLong.ql: /Power of 10/Rule 4',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 4/OneStmtPerLine.ql: /Power of 10/Rule 4',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 5/AssertionDensity.ql: /Power of 10/Rule 5',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 5/AssertionSideEffect.ql: /Power of 10/Rule 5',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 5/ConstantAssertion.ql: /Power of 10/Rule 5',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 5/NonBooleanAssertion.ql: /Power of 10/Rule 5',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 6/GlobalCouldBeStatic.ql: /Power of 10/Rule 6',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 6/VariableScopeTooLarge.ql: /Power of 10/Rule 6',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 7/CheckArguments.ql: /Power of 10/Rule 7',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 7/CheckReturnValues.ql: /Power of 10/Rule 7',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 8/AvoidConditionalCompilation.ql: /Power of 10/Rule 8',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 8/PartialMacro.ql: /Power of 10/Rule 8',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 8/RestrictPreprocessor.ql: /Power of 10/Rule 8',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 8/UndisciplinedMacro.ql: /Power of 10/Rule 8',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 9/FunctionPointer.ql: /Power of 10/Rule 9',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 9/HiddenPointerIndirection.ql: /Power of 10/Rule 9',
                      '+ semmlecode-cpp-queries/Power of 10/Rule 9/PointerNesting.ql: /Power of 10/Rule 9']

        # Set the suite file path
        p10_suite_file = tool_conf_data.get('semmle_analysis_dir') + '/jpl_p10'

        # Create the suite file
        with open(p10_suite_file, 'w') as suite_fh:
            for query in p10_queries:
                suite_fh.write('{}\n'.format(query))

        # Examine the analyzeSnapshot flag values
        required_analyzesnapshot_flags = ('--allow-recompiles --project ' + tool_conf_data.get('semmle_analysis_dir') +
                                          ' --latest --format sarifv2.1.0 --output-file ' +
                                          tool_conf_data.get('semmle_p10_output_file') + ' --suite ' + p10_suite_file)
        p10_analyzesnapshot_flags = (tool_conf_data.get('semmle_analyzesnapshot_flags') + ' ' +
                                     required_analyzesnapshot_flags)

        # Perform P10 analysis
        analyze_snapshot(tool_conf_data.get('semmle_env'), p10_analyzesnapshot_flags)


def post_process_analysis(tool_conf_data):
    """This function post-processes results from the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize variables
    parse_exit_code = 0

    # Find all the results files to be parsed
    semmle_results_files = glob.glob(tool_conf_data.get('semmle_analysis_dir') + '/semmle*raw.sarif')

    # Iterate through the results files
    for semmle_results_file in semmle_results_files:
        # Initialize variables
        if 'baseline' in semmle_results_file:
            raw_output_file = tool_conf_data.get('semmle_raw_warning_file')
        else:
            raw_output_file = tool_conf_data.get('semmle_p10_raw_warning_file')

        # Post-process the data
        exit_code = translate_results.perform_translation(semmle_results_file, raw_output_file,
                                                          tool_conf_data.get('source_dir'), 'scrub')

        # Update the parse exit code
        parse_exit_code = parse_exit_code + exit_code

    return parse_exit_code


def setup_odasa(tool_conf_data):
    """This function initializes the Semmle setup variables.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the variables
    semmle_env = tool_conf_data.get('semmle_env')
    odasa_home = tool_conf_data.get('semmle_path')

    # Determine if the Semmle environment needs to be updated
    if odasa_home != '':
        # Create the derived variables
        odasa_tools = odasa_home + '/tools'
        java_home = odasa_home + '/tools/java'

        # Update the environment
        semmle_env.update({'PATH': odasa_tools + os.pathsep + semmle_env.get('PATH')})
        semmle_env.update({'ODASA_HOME': odasa_home})
        semmle_env.update({'SEMMLE_DIST': odasa_home})
        semmle_env.update({'SEMMLE_JAVA_HOME': java_home})
        tool_conf_data.update({'semmle_env': semmle_env})


def create_project(tool_conf_data):
    """This function creates the Semmle project based on user provided values.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the variables
    project_template = tool_conf_data.get('semmle_template_path')
    project_directory = tool_conf_data.get('semmle_analysis_dir')
    source_dir = tool_conf_data.get('source_dir')
    semmle_build_dir = tool_conf_data.get('semmle_build_dir')
    semmle_build_cmd = tool_conf_data.get('semmle_build_cmd')
    source_lang = tool_conf_data.get('source_lang')

    # Print a status message
    logging.info('')
    logging.info('\t>> Executing command: do_semmle.create_project(%s, %s, %s, %s)', project_directory,
                 source_dir, semmle_build_dir, semmle_build_cmd)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Create the project directory
    os.mkdir(project_directory)

    # Use a template if provided
    if project_template:
        # Copy the template, with modifications
        with open(project_template, 'r') as input_fh:
            template_data = input_fh.read()

        # Swap out the variables in the template
        template_data = template_data.replace("${source_root}", source_dir)
        template_data = template_data.replace("${build_dir}", semmle_build_dir)
        template_data = template_data.replace("${build_cmd}", semmle_build_cmd)

        # Write out the data to a the project file
        with open(os.path.normpath(project_directory + '/project'), 'w+') as output_fh:
            output_fh.write('%s' % template_data)

    else:
        # Write out the project data
        with open(project_directory + '/project', 'w+') as output_fh:
            # Write out the project file data
            if source_lang.lower() == 'c':
                output_fh.write('<project language="cpp">\n')
            else:
                output_fh.write('<project language="java">\n')

            output_fh.write('  <displayName>scrub_semmle_analysis</displayName>\n')
            output_fh.write('  <timeout>600</timeout>\n')
            output_fh.write('  <autoupdate>\n')

            if (sys.platform == 'darwin') and (source_lang.lower() == 'j'):
                output_fh.write('    <build export="JAVA_HOME" dir="{}">{}</build>\n'.format(semmle_build_dir,
                                                                                             semmle_build_cmd))

                # Write out the variables file
                with open(project_directory + '/variables') as variable_fh:
                    variable_fh.write('JAVA_HOME=${odasa_tools}/java-ext-odasa]\n')

            else:
                output_fh.write('    <build dir="{}" index="true">{}</build>\n'.format(semmle_build_dir, semmle_build_cmd))

            output_fh.write('    <build>odasa duplicateCode --ram 2048 --minimum-tokens 100</build>\n')
            output_fh.write('    <source-location>{}</source-location>\n'.format(source_dir))
            output_fh.write('  </autoupdate>\n')
            output_fh.write('</project>')


def add_snapshot(semmle_env, semmle_addsnapshot_flags):
    """This function adds a snapshot of the code to the Semmle project using the command 'odasa addLatestSnapshot'

    Inputs:
        - semmle_env: Dictionary of Semmle environment settings [dict]
        - semmle_addsnapshot_flags: Command flags to be passed to the command [string]
    """

    # Add the latest snapshot
    call_string = 'odasa addLatestSnapshot ' + semmle_addsnapshot_flags
    scrub_utilities.execute_command(call_string, semmle_env)


def build_snapshot(semmle_env, semmle_buildsnapshot_flags):
    """This function builds the snapshot contained in the Semmle project.

    Inputs:
        - semmle_env: Dictionary of Semmle environment settings [dict]
        - semmle_buildsnapshot_flags: Command flags to be passed to the command 'odasa buildSnapshot' [string]
    """

    # Add the latest snapshot
    call_string = 'odasa buildSnapshot ' + semmle_buildsnapshot_flags
    scrub_utilities.execute_command(call_string, semmle_env)


def analyze_snapshot(semmle_env, semmle_analyzesnapshot_flags):
    """This function analyzes the Semmle build using the command 'odasa analyzeSnapshot'.

    Inputs:
        - semmle_env: Dictionary of Semmle environment settings [dict]
        - semmle_analyzesnapshot_flags: Command flags to be passed to the command [string]
    """

    # Perform the lint analysis
    call_string = 'odasa analyzeSnapshot ' + semmle_analyzesnapshot_flags
    scrub_utilities.execute_command(call_string, semmle_env)


def get_version_number(tool_conf_data):
    """This function determines the Semmle version number.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]

    Outputs:
        - version_number: The version number of the Semmle instance being tested [string]
    """

    # Initialize variables
    version_number = None
    semmle_path = tool_conf_data.get('semmle_path')
    semmle_env = tool_conf_data.get('semmle_env')

    try:
        # Set the path, if necessary
        if semmle_path == '':
            call_string = 'which odasa'
            proc = subprocess.Popen(call_string, shell=True, env=semmle_env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            semmle_path = os.path.dirname(os.path.normpath(os.path.dirname(proc.communicate()[0].strip())))

        # Run the Semmle version command
        call_string = semmle_path + '/tools/odasa selfTest'
        proc = subprocess.Popen(call_string, shell=True, env=semmle_env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, encoding='utf-8')
        std_out, std_err = proc.communicate()

        # Get the line with the version number
        version_line = re.split('\n', std_out)[0]

        # Iterate through every item and find the one with numbers
        for item in re.split(' ', version_line):
            if any(char.isdigit() for char in item):
                version_number = item.strip()
                break

    except:     # lgtm [py/catch-base-exception]
        version_number = 'Unknown'

    return version_number


def run_analysis(baseline_conf_data, override=False):
    """This function calls Semmle to perform analysis.

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
        - override: Force tool execution? [optional] [bool]

    Outputs:
        - semmle_analysis: Directory containing Semmle intermediary analysis files
        - log_file/semmle.log: SCRUB log file for the Semmle analysis
        - raw_results/semmle_raw.scrub: SCRUB-formatted results file containing raw Semmle results
        - raw_results/semmle_raw.sarif: SARIF-formatted results file containing raw Semmle results
        - raw_results/semmle_p10_raw.scrub: SCRUB-formatted results file containing raw Semmle P10 results
        - raw_results/semmle_p10_raw.sarif: SARIF-formatted results file containing raw Semmle P10 results
    """

    # Import the config data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize variables
    attempt_analysis = tool_conf_data.get('semmle_warnings') or override
    initial_dir = os.getcwd()
    semmle_exit_code = 2

    # Run the baseline analysis, if required
    if attempt_analysis:
        try:
            # Create the logger
            scrub_utilities.create_logger(tool_conf_data.get('semmle_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform Semmle analysis...')
            logging.info('\tPerform Semmle baseline analysis: ' + str(tool_conf_data.get('semmle_baseline_analysis')))
            logging.info('\tPerform Semmle P10 analysis: ' + str(tool_conf_data.get('semmle_p10_analysis')))

            # Get the version number
            version_number = get_version_number(tool_conf_data)
            logging.info('\tSemmle Version: %s', version_number)

            # Perform the analysis
            perform_analysis(tool_conf_data)

            # Post-process the analysis
            parse_exit_code = post_process_analysis(tool_conf_data)

            # Set the exit code
            semmle_exit_code = parse_exit_code

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('Semmle analysis could not be performed. Please see log file {} for '
                            'more information.'.format(tool_conf_data.get('semmle_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            semmle_exit_code = 1

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.error('A SCRUB error has occurred. Please see log file {} for more '
                          'information.'.format(tool_conf_data.get('semmle_log_file')))

            # Print the exception traceback
            logging.error(traceback.format_exc())

            # Set the exit code
            semmle_exit_code = 100

        finally:
            # Change back to the initial dir if necessary
            if os.getcwd() != initial_dir:
                logging.info('\tChanging directory: %s', initial_dir)
                os.chdir(initial_dir)

            # Close the loggers
            logging.getLogger().handlers = []

    # Return the exit code
    return semmle_exit_code
