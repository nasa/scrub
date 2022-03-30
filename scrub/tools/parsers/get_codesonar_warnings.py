import sys
import xml.etree.ElementTree
import os
import re
import logging


def find_table_indices(input_file):
    """This function finds the proper table instances for warning attributes.

    Inputs:
        - input_file: Absolute path to the raw warning file for the CodeSonar Hub [string]

    Outputs:
        - indices: List of indices for the desired warning values [list of int]
    """

    # Initialize the variables
    indices = [None, None, None, None]

    # Import the input data
    codesonar_data = xml.etree.ElementTree.parse(input_file).getroot()

    # Iterate through the output file to find the column name data
    for table in codesonar_data.findall('table'):
        # Check the name of the table
        if table.attrib['name'] == 'Warnings':
            index = 0
            for header in table.findall('column'):

                # Find the header indices
                if header.attrib['name'] == 'Path':
                    indices[0] = index
                elif header.attrib['name'] == 'Line':
                    indices[1] = index
                elif header.attrib['name'] == 'Class':
                    indices[2] = index
                elif header.attrib['name'] == 'Procedure':
                    indices[3] = index

                # Increment the index
                index = index + 1

    return indices


def get_hub_location(input_file):
    """This function returns the CodeSonar Hub location from the raw results file.

    Inputs:
        - input_file: Absolute path to the raw warning file for the CodeSonar Hub [string]

    Outputs:
        - codesonar_hub_location: The CodeSonar Hub location found in the raw results file. [string]
    """

    # Initialize variables
    codesonar_hub_location = None

    # Import the input data
    codesonar_data = xml.etree.ElementTree.parse(input_file).getroot()

    # Iterate through the output file to find the column name data
    for text in codesonar_data.findall('text'):
        if text.attrib['class'] == 'Title1':
            codesonar_hub_location = text.attrib['value']
            break

    return codesonar_hub_location


def parse_warnings(input_file, output_file, exclude_p10=False):
    """This function parses the raw CodeSonar warnings into the SCRUB format.

    Inputs:
        - input_file: Full path to the file containing raw CodeSonar warnings [string]
        - output_file: Full path to the file where the parsed warnings will be stored [string]

    Outputs:
        - output_file: All parsed warnings will be written to the output_file
    """

    # Print a status message
    logging.info('\t>> Executing command: get_codesonar_warnings.parse_warnings(%s, %s)', input_file, output_file)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Initialize the variables
    warning_level = 'Low'
    warning_count = 1
    id_prefix = 'codesonar'
    p10_only = False
    filter_list = ["Goto Statement",  # P10: Rule 1
                   "Recursion",  # P10: Rule 1
                   "Use of < setjmp.h >",  # P10: Rule 1
                   "Use of longjmp",  # P10: Rule 1
                   "Use of setjmp",  # P10: Rule 1
                   "Potential Unbounded Loop",  # P10: Rule 2
                   "Dynamic Allocation After Initialization",  # P10: Rule 3
                   "Function Too Long",  # P10: Rule 4
                   "Not Enough Assertions",  # P10: Rule 5
                   "Scope Could Be File Static",  # P10: Rule 6
                   "Scope Could Be Local Static",  # P10: Rule 6
                   "Ignored Return Value",  # P10: Rule 7
                   "Unchecked Parameter Dereference",  # P10: Rule 7
                   "## Follows # Operator",  # P10: Rule 8
                   "Conditional Compilation",  # P10: Rule 8
                   "Macro Does Not End With } or )",  # P10: Rule 8
                   "Macro Does Not Start With { or (",  # P10: Rule 8
                   "Macro Name is C Keyword",  # P10: Rule 8
                   "Macro Uses # Operator",  # P10: Rule 8
                   "Macro Uses ## Operator",  # P10: Rule 8
                   "Non-Boolean Preprocessor Expression",  # P10: Rule 8
                   "Preprocessing Directives in Macro Argument",  # P10: Rule 8
                   "Recursive Macro",  # P10: Rule 8
                   "Unbalanced Parenthesis",  # P10: Rule 8
                   "Use of <stdio.h> Input/Output Macro",  # P10: Rule 8
                   "Use of <wchar.h> Input/Output Macro",  # P10: Rule 8
                   "Variadic Macro",  # P10: Rule 8
                   "Function Pointer",  # P10: Rule 9
                   "Macro Uses [] Operator",  # P10: Rule 9
                   "Macro Uses -> Operator",  # P10: Rule 9
                   "Macro Uses Unary * Operator",  # P10: Rule 9
                   "Pointer Type Inside Typedef",  # P10: Rule 9
                   "Too Many Dereferences",  # P10: Rule 9
                   "Not All Warnings Are Enabled",  # P10: Rule 10
                   "Warnings Not Treated As Errors"]  # P10: Rule 10

    # Determine if the output is P10 results
    if 'p10' in os.path.basename(output_file).lower():
        p10_only = True

    # Get the header indices
    header_indices = find_table_indices(input_file)

    # Get the CodeSonar hub location
    codesonar_hub_location = get_hub_location(input_file)

    # Set the indices for retrieving data
    path_index = header_indices[0]
    line_index = header_indices[1]
    class_index = header_indices[2]
    procedure_index = header_indices[3]

    # Import the input data
    codesonar_data = xml.etree.ElementTree.parse(input_file).getroot()

    # Create the output file
    with open(output_file, 'w+') as output_fh:
        # Find all the tables in the XML file
        for table in codesonar_data.findall('table'):
            # Check the name of the table
            if table.attrib['name'] == 'Warnings':
                # Iterate through all the warnings in the table
                for warning in table.findall('row'):
                    # Parse the warning into SCRUB format
                    warning_instance_id = re.split('\.', warning[0].text)[-1]
                    warning_file = warning[path_index].text
                    warning_line = int(warning[line_index].text)
                    warning_class = warning[class_index].text
                    if str(warning[procedure_index].text).lower() == 'none':
                        warning_procedure = 'undefined procedure'
                    else:
                        warning_procedure = warning[procedure_index].text
                    warning_summary = warning_class + ' found in ' + warning_procedure
                    warning_link = codesonar_hub_location + '/warninginstance/' + warning_instance_id + '.html'

                    # Check to see if the warnings should be filtered for P10 results
                    if p10_only:
                        # Check to see if the warning class is associated with P10 warnings
                        if warning_class.strip() in filter_list:
                            # Write the warnings to the output file
                            output_fh.write('%s%03d <%s> :%s:%d: %s\n\tCodeSonar P10 Warning: %s\n\t%s\n\n' %
                                            (id_prefix, warning_count, warning_level, warning_file, warning_line,
                                             warning_class, warning_summary, warning_link))

                            # Increase the warning_count
                            warning_count = warning_count + 1

                    elif exclude_p10:
                        # Check to see if the warning class is associated with P10 warnings
                        if warning_class.strip() not in filter_list:
                            # Write the warnings to the output file
                            output_fh.write('%s%03d <%s> :%s:%d: %s\n\t%s\n\t%s\n\n' %
                                            (id_prefix, warning_count, warning_level, warning_file, warning_line,
                                             warning_class, warning_summary, warning_link))

                            # Increase the warning_count
                            warning_count = warning_count + 1

                    else:
                        # Write the warnings to the output file
                        output_fh.write('%s%03d <%s> :%s:%d: %s\n\t%s\n\t%s\n\n' %
                                        (id_prefix, warning_count, warning_level, warning_file, warning_line,
                                         warning_class, warning_summary, warning_link))

                        # Increase the warning_count
                        warning_count = warning_count + 1

    # Update the permissions of the output file
    os.chmod(output_file, 438)


if __name__ == '__main__':
    # Store input variables
    codesonar_file = sys.argv[1]
    scrub_file = sys.argv[2]

    parse_warnings(codesonar_file, scrub_file)
