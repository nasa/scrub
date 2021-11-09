# Detailed Configuration

The information below provides a detailed description of each `scrub.cfg` value. A blank `scrub.cfg` file containing all of these values can be generated using the command:  

    scrub generate-conf

Each table below represents a portion of the complete `scrub.cfg` file.

**Note**: The use of environment variables is supported in `scrub.cfg` is supported. Environment variables will be resolved when the configuration file is read.

**Note**: All variables ending with `_PATH` will automatically be converted in absolute paths.


## Source Code Attributes

| Variable Name     | Format | Required? | Description                                                                    | Default Value       |
| ----------------- | ------ | --------- | ------------------------------------------------------------------------------ | ------------------- |
| SOURCE_DIR        | String | Yes       | Define the root location of the source code                                    | N/A                 |
| SOURCE_LANG       | String | Yes       | Define the language of the source code                                         | N/A                 |
| SCRUB_WORKING_DIR | String | Optional  | Define the location of the SCRUB output files.                                 | `SOURCE_DIR/.scrub` |
| CUSTOM_TEMPLATES  | String | Optional  | Comma-separated list of custom templates to be executed during SCRUB execution | ''                  |


## Tool Variables

### GCC Compiler Variables

| Variable Name | Format     | Required? | Description                                              | Default Value |
| ------------- | ---------- | --------- | -------------------------------------------------------- | ------------- |
| GCC_WARNINGS  | True/False | Yes       | Should GCC analysis be performed?                        | False         |
| GCC_BUILD_DIR | String     | Optional  | Relative path (to `SOURCE_DIR`) to the build directory   | `SOURCE_DIR`  |
| GCC_BUILD_CMD | String     | Yes       | Build command used by the GCC compiler                   | N/A           |
| GCC_CLEAN_CMD | String     | Yes       | Clean command used by the GCC compiler                   | N/A           |


### JAVAC Compiler Variables

| Variable Name   | Format     | Required? | Description                                            | Default Value |
| --------------- | ---------- | --------- | ------------------------------------------------------ | ------------- |
| JAVAC_WARNINGS  | True/False | Yes       | Should JAVAC analysis be performed?                    | False         |
| JAVAC_BUILD_DIR | String     | Optional  | Relative path (to `SOURCE_DIR`) to the build directory | `SOURCE_DIR`  |
| JAVAC_BUILD_CMD | String     | Yes       | Build command used by the JAVAC compiler               | N/A           |
| JAVAC_CLEAN_CMD | String     | Yes       | Clean command used by the JAVAC compiler               | N/A           |


### GBUILD Compiler Variables

| Variable Name    | Format     | Required? | Description                                            | Default Value |
| ---------------- | ---------- | --------- | ------------------------------------------------------ | ------------- |
| GBUILD_WARNINGS  | True/False | Yes       | Should GBUILD analysis be performed?                   | False         |
| GBUILD_BUILD_DIR | String     | Optional  | Relative path (to `SOURCE_DIR`) to the build directory | `SOURCE_DIR`  |
| GBUILD_BUILD_CMD | String     | Yes       | Build command used by the GBUILD compiler              | N/A           |
| GBUILD_CLEAN_CMD | String     | Yes       | Clean command used by the GBUILD compiler              | N/A           |

**Note**: DoubleCheck analysis is included under gbuild compiler analysis. DoubleCheck must be enabled external to SCRUB.


### Pylint Variables

| Variable Name    | Format     | Required? | Description                            | Default Value |
| ---------------- | ---------- | --------- | -------------------------------------- | ------------- |
| PYLINT_WARNINGS  | True/False | Yes       | Should pylint analysis be performed?   | False         |
| PYLINT_FLAGS     | String     | Optional  | Optional flags to be passed to pylint  | ''            |


### CodeQL Variables

| Variable Name                | Format     | Required? | Description                                                  | Default Value |
| ---------------------------- | ---------- | --------- | ------------------------------------------------------------ | ------------- |
| CODEQL_WARNINGS              | True/False | Yes       | Should CodeQL analysis be performed?                         | False         |
| CODEQL_PATH                  | String     | Optional  | Absolute path to the directory of the CodeQL installation    | Check `PATH`  |
| CODEQL_QUERY_PATH            | String     | Yes       | Absolute path to the CodeQL query files                      | N/A           |
| CODEQL_BUILD_DIR             | String     | Optional  | Relative path (to `SOURCE_DIR`) to the build directory       | `SOURCE_DIR`  |
| CODEQL_BUILD_CMD             | String     | Yes       | Command to build the source code for CodeQL analysis         | N/A           |
| CODEQL_CLEAN_CMD             | String     | Yes       | Command to clean the source code for CodeQL analysis         | N/A           |
| CODEQL_BASELINE_ANALYSIS     | True/False | Yes       | Should baseline CodeQL analysis be performed?                | True          |
| CODEQL_P10_ANALYSIS          | True/False | Yes       | Should CodeQL P10 analysis be performed?                     | True          |
| CODEQL_DATABASECREATE_FLAGS  | String     | Optional  | Flags to be passed into 'codeql database create' command     | ''            |
| CODEQL_DATEBASEANALYZE_FLAGS | String     | Optional  | Flags to be passed into 'codeql database analyze' command    | ''            |


### Coverity Variables

| Variable Name                  | Format     | Required? | Description                                                | Default Value |
| ------------------------------ | ---------- | --------- | ---------------------------------------------------------- | ------------- |
| COVERITY_WARNINGS              | True/False | Yes       | Should Coverity analysis be performed?                     | False         |
| COVERITY_PATH                  | String     | Optional  | Absolute path to `bin` directory of the Coverity           | Check `PATH`  |
| COVERITY_BUILD_DIR             | String     | Optional  | Relative path (to `SOURCE_DIR`) to the build directory     | `SOURCE_DIR`  |
| COVERITY_BUILD_CMD             | String     | Yes       | Command to build the source code for Coverity analysis     | N/A           |
| COVERITY_CLEAN_CMD             | String     | Yes       | Command to clean the source code for Coverity analysis     | N/A           |
| COVERITY_COVBUILD_FLAGS        | String     | Optional  | Flags to be passed into 'cov-build' command                | ''            |
| COVERITY_COVANALYZE_FLAGS      | String     | Optional  | Flags to be passed into the 'cov-analyze' command          | ''            |
| COVERITY_COVFORMATERRORS_FLAGS | String     | Optional  | Flags to be passed into the 'cov-format-errors' command    | ''            |


### CodeSonar Variables

| Variable Name               | Format     | Required? | Description                                                   | Default Value |
| --------------------------- | ---------- | --------- | ------------------------------------------------------------- | ------------- |
| CODESONAR_WARNINGS          | True/False | Yes       | Should CodeSonar analysis be performed?                       | False         |
| CODESONAR_PATH              | String     | Optional  | Absolute path to the bin directory of CodeSonar               | Check `PATH`  |
| CODESONAR_HUB               | String     | Yes       | `<hub location>:<port>`                                       | N/A           |
| CODESONAR_CERT              | String     | Yes       | Absolute path of the Hub certificate                          | N/A           |
| CODESONAR_KEY               | String     | Yes       | Absolute path of the user's private key                       | N/A           |
| CODESONAR_PROJ_NAME         | String     | Yes       | Project name provided by the Hub admin upon project creation  | N/A           |
| CODESONAR_BUILD_DIR         | String     | Optional  | Relative path (to `SOURCE_DIR`) to the build directory        | `SOURCE_DIR`  |
| CODESONAR_BUILD_CMD         | String     | Yes       | Command to build the source code for CodeSonar analysis       | N/A           |
| CODESONAR_CLEAN_CMD         | String     | Yes       | Command to clean the source code for CodeSonar analysis       | N/A           |
| CODESONAR_BASELINE_ANALYSIS | True/False | Yes       | Should baseline CodeSonar analysis be performed?              | True          |
| CODESONAR_P10_ANALYSIS      | True/False | Yes       | Should CodeSonar P10 analysis be performed?                   | True          |
| CODESONAR_ANALYZE_FLAGS     | String     | Optional  | Flags to be passed into 'codesonar analyze' command           | ''            |
| CODESONAR_GET_FLAGS         | String     | Optional  | Flags to be passed into 'codesonar get' command               | ''            |


## Output Target Variables

### Collaborator Variables

| Variable Name                 | Format         | Required? | Description                                             | Default Value                |
| ----------------------------- | -------------- | --------- | ------------------------------------------------------- | ---------------------------- |
| COLLABORATOR_UPLOAD           | True/False     | Yes       | Should Collaborator upload be performed?                | False                        |
| COLLABORATOR_SERVER           | String         | Yes       | URL of the Collaborator server                          | N/A                          |
| COLLABORATOR_CCOLLAB_LOCATION | String         | Optional  | Absolute path to `ccollab` directory                    | Check `PATH`                 |
| COLLABORATOR_USERNAME         | String         | Yes       | Collaborator username to be used to create the review   | Current user                 |
| COLLABORATOR_REVIEW_TITLE     | String         | Optional  | Optional title for the review                           | SCRUB Review                 |
| COLLABORATOR_REVIEW_GROUP     | String         | Optional  | Optional review group for the review                    | ''                           |
| COLLABORATOR_REVIEW_TEMPLATE  | String         | Optional  | Template to be used when creating review                | ''                           |
| COLLABORATOR_REVIEW_ACCESS    | String         | Optional  | Access level to be used or the review                   | ''                           |
| COLLABORATOR_FINDING_LEVEL    | comment/defect | Optional  | Level at which findings will be added to review         | comment                      |
| COLLABORATOR_FILTERS          | String         | Optional  | Absolute path to Collaborator upload regex file         | `./SCRUBCollaboratorFilters` |
| COLLABORATOR_SRC_FILES        | String         | Optional  | Comma separated list of results files to upload         | *                            |


### SCRUB GUI

| Variable Name    | Format         | Required? | Description                                             | Default Value |
| ---------------- | -------------- | --------- | ------------------------------------------------------- | ------------- |
| SCRUB_GUI_EXPORT | True/False     | Yes       | Should results be distributed for legacy SCRUB GUI?     | False         |


## Filtering Variables

| Variable Name         | Format     | Required? | Description                                                         | Default Value           |
| --------------------- | ---------- | --------- | ------------------------------------------------------------------- | ----------------------- |
| ENABLE_EXT_WARNINGS   | True/False | Yes       | Display warnings in directories outside of source root?             | False                   |
| ENABLE_MICRO_FILTER   | True/False | Yes       | Enable micro filtering?                                             | True                    |
| CUSTOM_FILTER_COMMAND | String     | Optional  | User-defined filtering command to perform specialty filtering       | ''                      |
| ANALYSIS_FILTERS      | String     | Optional  | Path to list of regex patterns to include/exclude source files      | `./SCRUBFilters`        |
| QUERY_FILTERS         | String     | Optional  | Absolute path to list of tool queries to exclude from results       | `./SCRUBExcludeQueries` |
