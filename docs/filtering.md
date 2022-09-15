# Filtering

Filtering in SCRUB allows users to remove sets of warnings that they don't care about. The raw results of SCRUB analysis
are always stored, in addition to the filtered results. The two types of filtering available in SCRUB are described
below.

- [Macro Filtering](#macro-filtering)
- [Micro Filtering](#micro-filtering)
- [Custom Filtering](#custom-filtering)
- [Tool Based Filtering](#tool-based-filtering)


## Macro Filtering

For the purposes of SCRUB, macro filtering is defined as filtering out large portions of results based on the code's
location in the codebase. For example, say there is portion of the source code that is only used for testing purposes.
Macro filtering allows you to tell SCRUB to ignore results from this directory.


### Regex Filtering

SCRUB allows for two levels of regex filtering: analysis regex filtering and Collaborator regex filtering. Analysis
regex filtering is applied to the results from the analysis tools and Collaborator regex filtering is applied
subsequently, after the analysis regex filtering and before uploading results to Collaborator.

Regex include and exclude patterns can be supplied, one per line, using the following syntax::

    + <regex pattern>
    - <regex pattern>

A "+" symbol at the beginning of the line indicates a pattern for files that should be included. A "-" symbol at the
beginning of the line indicates a pattern for files that should be excluded.

The filtering mechanism first identifies all files located within `SOURCE_DIR`. The include patterns are then applied
to the initial list, followed by the exclude patterns to generate the final file list.


#### Analysis Regex Filtering

The location of the analysis regex filters file can be specified explicitly via the scrub.cfg file by using the
`ANALYSIS_FILTERS` variable. If this value is left blank, SCRUB will look for a filtering file called SCRUBFilters
that is co-located with the scrub.cfg configuration file. If this file does not exist/can not be found, no analysis
filtering will be performed.

The resulting set of files that will be included for analysis is printed to the output file
`<SOURCE_DIR>/.scrub/SCRUBAnalysisFilteringList`.


#### Collaborator Regex Filtering

The location of the analysis regex filters file can be specified explicitly via the scrub.cfg file by using the
**COLLABORATOR_FILTERS** variable. These regex filters are applied directly to the ``SCRUBAnalysisFilteringList``
results file. If this file does not exist/can not be found, no Collaborator filtering will be performed.

The resulting set of files that will be included for analysis is printed to the output file
`<SOURCE_DIR>/.scrub/SCRUBCollaboratorFilteringList`.


### Filtering External Warnings

SCRUB can automatically remove all warnings that are located in files outside of the **SOURCE_DIR** directory as
defined in the scrub.conf file. Filtering of external warnings can be enabled by setting the **ENABLE_EXT_WARNINGS**
variable in the scrub.conf file to *False*.


#### Filtering by Query

Similar to the directory filtering described above, queries can be filtered by user input. SCRUB determines which
queries to filter by reading from the file SCRUBExcludeQueries. This file should contain a list of queries to be
excluded, with one query listed per line. Query filters must conform to the following format::

    <Tool Name>:<Query Name>

**Tool Name**: the name of the tool as specified in the SCRUB output file ID prefix (e.g. if a warning has the ID `coverity005`, the tool name is `coverity`)  
**Query Name**: Full name of the query as reported in the corresponding SCRUB output file


## Micro Filtering

For the purposes of SCRUB, micro filtering is defined as filtering out individual warnings based on a developer's
assessment of correctness/usefulness. If a developer reviews a warning and deems it to be incorrect/not useful, they
can then edit the source code file associated with the warning so that it will not be shown in future runs of SCRUB
analysis.


### Filtering Individual Warnings

Adding a comment containing the string `SCRUB_IGNORE_WARNING_<warning_type>` (where 'warning_type' is the tool
identifier) to the line of source code called out by SCRUB will filter the warning from future analysis. Valid
`<warning_type>` values for each tool are shown in the table below.


| Tool Name | Suppression Value            |
| --------- | ---------------------------- |
| GBUILD    | gbuild, dblchck, doublecheck |
| GCC       | cmp, compiler, gcc           |
| JAVAC     | cmp, compiler, javac         |
| Coverity  | coverity, cov                |
| CodeSonar | codesonar, cdsnr             |
| CodeQL    | codeql                       |
| Pylint    | cmp, pylint                  |
| SonarQube | sonarqube                    |

**Note**: P10 warnings can be filtered by using the suppression value of the tool that generated the warning (Codesonar or CodeQL)

For example, say you have received the following warning from SCRUB:

    cmp002 <Low> :helloworld.c:9:
        ISO C90 forbids mixed declarations and code [-Wpedantic]


Adding the following comment to line 9 of the source code file would remove this warning from showing up in future runs
of SCRUB:

      1 #include<stdio.h>
      2
      3 main()
      4 {
      5     int  i, j, k;
      6     char x = 'x';
      7     printf("Hello World");
      8
      9    int sum = 17, count = 5; //SCRUB_IGNORE_WARNING_CMP
      10    double mean;
      11
      12    mean = (double) sum / count;
      13    printf("Value of mean : %f\n", mean );
      14
      15 }


### Legacy Filtering

SCRUB also supports the legacy SCRUB micro filtering format. See the code snippet below for an example of the legacy micro-filtering syntax:

      1 #include<stdio.h>
      2
      3 main()
      4 {
      5     int  i, j, k;
      6     char x = 'x';
      7     printf("Hello World");
      8
      9    int sum = 17, count = 5; //@suppress cmp
      10    double mean;
      11
      12    mean = (double) sum / count;
      13    printf("Value of mean : %f\n", mean );
      14
      15 }


## Custom Filtering

A custom, user-defined filtering command can be run after SCRUB defined filtering options have been executed. This command can implement any arbitrary filtering routine, but this command should only modify the existing SCRUB output files (`SOURCE_DIR/.scrub/<tool>.scrub`). These output files must remain in the same location and maintain valid SCRUB file formatting.

If any error occurs during execution, SCRUB execution will be halted and warning message will be printed. This command
is defined in scrub.cfg via the **CUSTOM_FILTER_CMD**.

Please see the [Utilities](utilities.md) page to see a detailed example using the SCRUB diff utility.


## Tool Based Filtering

SCRUB supports all filtering options that are supported internally within each static analysis tool. For more information on the usage of these filtering techniques, please refer to the tool documentation.
