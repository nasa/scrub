import sys
import xml.etree.ElementTree
import pathlib
import logging


def parse_warnings(input_file, output_file, codesonar_hub, exclude_p10=False):
    """This function parses the raw CodeSonar warnings into the SCRUB format.

    Inputs:
        - input_file: Full path to the file containing raw CodeSonar warnings [string]
        - output_file: Full path to the file where the parsed warnings will be stored [string]
        - codesonar_hub: Location of the CodeSonar Hub [string]

    Outputs:
        - output_file: All parsed warnings will be written to the output_file
    """

    # Print a status message
    logging.info('\t>> Executing command: get_codesonar_warnings.parse_warnings(%s, %s)', input_file, output_file)
    logging.info('\t>> From directory: %s', str(pathlib.Path().absolute()))

    # Initialize the variables
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
    if 'p10' in output_file.stem:
        p10_only = True

    # Import the input data
    codesonar_data = xml.etree.ElementTree.parse(input_file).getroot()

    # Create the output file
    with open(output_file, 'w+') as output_fh:
        # Find all the tables in the XML file
        for warning in codesonar_data.findall('warning'):
            # Parse the warning into SCRUB format
            warning_instance_id = warning.get("url").split('/')[-1].split('.')[0]
            warning_file = warning.findall("file_path")[0].text
            warning_line = int(warning.findall("line_number")[0].text)
            warning_class = warning.findall("class")[0].text
            if str(warning.findall("procedure")[0].text).lower() == 'none':
                warning_procedure = 'undefined procedure'
            else:
                warning_procedure = warning.findall("procedure")[0].text
            warning_summary = warning_class + ' found in ' + warning_procedure
            warning_link = codesonar_hub + '/warninginstance/' + warning_instance_id + '.html'

            # Get the ranking information
            if int(warning.findall("score")[0].text) > 56:
                warning_level = 'High'
            elif 21 < int(warning.findall("score")[0].text) <= 56:
                warning_level = 'Med'
            else:
                warning_level = 'Low'

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


if __name__ == '__main__':
    parse_warnings(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3])
