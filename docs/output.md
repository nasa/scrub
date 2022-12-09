# Output

## SCRUB Output File Format

All SCRUB files that store analysis results must adhere to the following format for the contents of the file:

    [tool][count] <[severity]> :[path to file]:[line number]: [query name]
        [warning description]
        [warning description continued]

- Tool: A string indicator for the specific tool reporting the warnings
- Count: The numeric count of the warning for the given tool
- Severity: A severity assignment for the warning. Valid values are Low/Med/High
- Path to file: The path to the file being referenced by the warning
- Line number: The line number of the file being referenced by the warning
- Query name [optional]: If applicable, the tool query name that generated the warning
- Warning description: A detailed description of the warning. May be more than one line

**Note**: For analysis tools that include a web component for viewing analysis results, the warning description section will also include a URL where the detailed warning results may be viewed

Some important notes about the format:

- The [path to file] value should be **absolute** for ``raw_results/<tool>_raw.scrub`` (pre-filtering) output files and should **relative** for `<tool>.scrub` (post-filtering) output files. The location should be relative to the `SOURCE_DIR` location as specified in `scrub.cfg`.
- Each line of the warning description should be proceeded by 4 spaces, not a tab
- Each individual warning should be separated by a single blank line

An example of a set of two warnings that adhere to this format:

**Pre-Filtering (raw_results/codeql_raw.scrub)**:

    codeql021 <Low> :/Users/lbarner/Desktop/scrub/test/c_testcase/testcasesupport/std_thread.c:57: Unchecked function argument
        Functions should check their arguments before their first use.
        This use of parameter thread has not been checked.

    codeql022 <Low> :/Users/lbarner/Desktop/scrub/test/c_testcase/testcasesupport/std_thread.c:112: Unchecked function argument
        Functions should check their arguments before their first use.
        This use of parameter thread has not been checked.

**Post-Filtering (codeql.scrub)**:

    codelql021 <Low> :testcasesupport/std_thread.c:57: Unchecked function argument
        Functions should check their arguments before their first use.
        This use of parameter thread has not been checked.

    codeql022 <Low> :testcasesupport/std_thread.c:112: Unchecked function argument
        Functions should check their arguments before their first use.
        This use of parameter thread has not been checked.


## List of Output Files

The following section provides a description of the structure of the .scrub output directory located at `SOURCE_DIR` as specified in the `scrub.cfg` configuration file:

    .scrub
    |  VERSION                          (Version of SCRUB that generated results)
    |  scrub.cfg                        (Copy of user-provided configuration file)
    |  SCRUBAnalysisFilteringList       (List of source files that will be included in analysis)
    |  SCRUBCollaboratorFiltering List  (List of source files that will be uploaded to Collaborator)
    |  compiler.scrub                   (Filtered, aggregate results from all compilers)
    |  p10.scrub                        (Filtered, aggregate results from all P10 analysis engines)
    |  [tool].scrub                     (Filtered results file for each tool)
    |  ...
    |
    |--raw_results                      (Directory containing unfiltered, SCRUB-formatted results)
    |    [tool]_p10_raw.scrub           (Unfiltered, SCRUB-formatted P10 results for each tool)
    |    [tool]_raw.scrub               (Unfiltered, SCRUB-formatted results for each tool)
    |    ...
    |
    |--log_files                        (Directory containing log files generated during SCRUB execution)
    |    filtering.log                  (Log file for results filtering post-processing step)
    |    [tool].log                     (Log file for analysis tool execution)
    |
    |--[tool]_analysis                  (Directory containing intermediary files generated during tool analysis)
    |    intermediary files
    |
    |--analysis_scripts                 (Directory containing parsed tool analysis scripts)
    |    [tool].sh

