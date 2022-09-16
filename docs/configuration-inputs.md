# Detailed Configuration

The information below provides a detailed description of each `scrub.cfg` input. A blank `scrub.cfg` file containing all of these values can be generated using the command:  

    scrub generate-conf

Each table below represents a portion of the complete `scrub.cfg` file.

**Note**: The use of environment variables is supported in `scrub.cfg` is supported. Environment variables will be resolved when the configuration file is read.

**Note**: All variables ending with `_PATH` will automatically be converted in absolute paths.


## Source Code Attributes

| Variable Name     | Format | Required? | Description                                                                    | Default Value       |
| ----------------- | ------ | --------- | ------------------------------------------------------------------------------ | ------------------- |
| SOURCE_DIR        | String | Yes       | Define the root location of the source code                                    | N/A                 |
| SOURCE_LANG       | String | Yes       | Comma-separated list of languages to be analyzed                               | N/A                 |
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
| CODEQL_BUILD_CMD             | String     | Optional  | Command to build the source code for CodeQL analysis         | N/A           |
| CODEQL_CLEAN_CMD             | String     | Optional  | Command to clean the source code for CodeQL analysis         | N/A           |
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
| COVERITY_BUILD_CMD             | String     | Optional  | Command to build the source code for Coverity analysis     | N/A           |
| COVERITY_CLEAN_CMD             | String     | Optional  | Command to clean the source code for Coverity analysis     | N/A           |
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
| CODESONAR_RESULTS_TEMPLATE* | Int        | Optional  | CodeSonar results template to use for results export          | ''            |
| CODESONAR_BUILD_DIR         | String     | Optional  | Relative path (to `SOURCE_DIR`) to the build directory        | `SOURCE_DIR`  |
| CODESONAR_BUILD_CMD         | String     | Optional  | Command to build the source code for CodeSonar analysis       | N/A           |
| CODESONAR_CLEAN_CMD         | String     | Optional  | Command to clean the source code for CodeSonar analysis       | N/A           |
| CODESONAR_BASELINE_ANALYSIS | True/False | Yes       | Should baseline CodeSonar analysis be performed?              | True          |
| CODESONAR_P10_ANALYSIS      | True/False | Yes       | Should CodeSonar P10 analysis be performed?                   | True          |
| CODESONAR_BUILD_FLAGS       | String     | Optional  | Flags to be passed into `codesonar build` command             | ''            |
| CODESONAR_ANALYZE_FLAGS     | String     | Optional  | Flags to be passed into `codesonar analyze` command           | ''            |
| CODESONAR_GET_FLAGS         | String     | Optional  | Flags to be passed into `codesonar get` command               | ''            |

\* The default behavoir is to export results as SARIF, but some instances required pulling results in an XML format. If a template is specified, SCRUB will retrieve XML results instead of SARIF.

**Note**: For more information on generating CodeSonar certificates and keys, please refer to the CodeSonar documentation.

### SonarQube Variables

| Variable Name               | Format     | Required? | Description                                                   | Default Value |
| --------------------------- | ---------- | --------- | ------------------------------------------------------------- | ------------- |
| SONARQUBE_WARNINGS          | True/False | Yes       | Should SonarQube analysis be performed?                       | False         |
| SONARQUBE_PATH              | String     | Optional  | Absolute path to the bin directory of SonarQube               | Check `PATH`  |
| SONARQUBE_WRAPPER_PATH      | String     | Optional  | Absolute path to the SonarQube build wrappers for C/C++       | Check `PATH`  |
| SONARQUBE_SERVER            | String     | Yes       | Address of the SonarQube server for results upload            | N/A           |
| SONARQUBE_TOKEN             | String     | Yes       | Access token for server authentication                        | N/A           |
| SONARQUBE_PROJECT           | String     | Yes       | Project key where results will stored on server               | N/A           |
| SONARQUBE_BUILD_DIR         | String     | Optional  | Relative path (to `SOURCE_DIR`) to the build directory        | `SOURCE_DIR`  |
| SONARQUBE_BUILD_CMD         | String     | Optional  | Command to build the source code for SonarQube analysis       | N/A           |
| SONARQUBE_CLEAN_CMD         | String     | Optional  | Command to clean the source code for SonarQube analysis       | N/A           |
| SONARQUBE_SCANNER_FLAGS     | String     | Optional  | Flags to be passed into the `sonar-scanner` command           | ''            |
| SONARQUBE_CURL_FLAGS        | String     | Optional  | Flags to be passed into the `curl` command                    | ''            |

**Note**: For more information on generating SonarQube access tokens, please refer to the SonarQube documentation.

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


## Sample Configuration File
The configuration file provided below is a sample configuration file for a C project.


    # Please refer to the SCRUB documentation for more detailed configuration information
    
    ###############################################################################
    ###############################################################################
    # SOURCE CODE VARIABLES
    ###############################################################################
    ###############################################################################
    [Source Code Variables]
    # VARIABLE           REQUIRED?    FORMAT
    # SOURCE_DIR         Yes          String
    # SOURCE_LANG        Yes          String
    # SCRUB_WORKING_DIR  No           String
    # CUSTOM_TEMPLATES   No           String
    #
    SOURCE_DIR: ./
    SOURCE_LANG: c
    SCRUB_WORKING_DIR: ~/scrub_analysis
    CUSTOM_TEMPLATES: ~/
    
    ###############################################################################
    ###############################################################################
    # TOOL VARIABLES
    ###############################################################################
    ###############################################################################
    
    # GCC compiler analysis variables
    # VARIABLE        REQUIRED?     FORMAT
    # GCC_WARNINGS    Yes           True/False
    # GCC_BUILD_DIR   No            String
    # GCC_BUILD_CMD   Yes           String
    # GCC_CLEAN_CMD   Yes           String
    #
    [GCC Variables]
    GCC_WARNINGS: True
    GCC_BUILD_DIR: src
    GCC_BUILD_CMD: make all
    GCC_CLEAN_CMD: make clean
    
    # JAVAC compiler analysis variables
    # VARIABLE          REQUIRED?   FORMAT
    # JAVAC_WARNINGS    Yes         True/False
    # JAVAC_BUILD_DIR   No          String
    # JAVAC_BUILD_CMD   Yes         String
    # JAVAC_CLEAN_CMD   Yes         String
    #
    [JAVAC Variables]
    JAVAC_WARNINGS: False
    JAVAC_BUILD_DIR:
    JAVAC_BUILD_CMD:
    JAVAC_CLEAN_CMD:
    
    # GBUILD compiler analysis variables
    # VARIABLE           REQUIRED?   FORMAT
    # GBUILD_WARNINGS    Yes         True/False
    # GBUILD_BUILD_DIR   No          String
    # GBUILD_BUILD_CMD   Yes         String
    # GBUILD_CLEAN_CMD   Yes         String
    #
    [GBUILD Variables]
    GBUILD_WARNINGS: False
    GBUILD_BUILD_DIR:
    GBUILD_BUILD_CMD:
    GBUILD_CLEAN_CMD:
    
    # PYLINT analysis variables
    # VARIABLE           REQUIRED?   FORMAT
    # PYLINT_WARNINGS    Yes         True/False
    # PYLINT_FLAGS       No          String
    #
    [PYLINT Variables]
    PYLINT_WARNINGS: False
    PYLINT_FLAGS:
    
    # CodeQL analysis variables
    # VARIABLE                          REQUIRED?   FORMAT
    # CODEQL_WARNINGS                   Yes         True/False
    # CODEQL_PATH                       No          String
    # CODEQL_QUERY_PATH                 Yes         String
    # CODEQL_BUILD_DIR                  No          String
    # CODEQL_BUILD_CMD                  Yes         String
    # CODEQL_CLEAN_CMD                  Yes         String
    # CODEQL_BASELINE_ANALYSIS          Yes         True/False
    # CODEQL_P10_ANALYSIS               Yes         True/False
    # CODEQL_DATABASECREATE_FLAGS       No          String
    # CODEQL_DATABASEANALYZE_FLAGS      No          String
    #
    [CodeQL Variables]
    CODEQL_WARNINGS: True
    CODEQL_PATH: /opt/local/codeql/codeql-cli
    CODEQL_QUERY_PATH: /opt/local/codeql/queries
    CODEQL_BUILD_DIR: src
    CODEQL_BUILD_CMD: make all
    CODEQL_CLEAN_CMD: make clean
    CODEQL_BASELINE_ANALYSIS: True
    CODEQL_P10_ANALYSIS: False
    CODEQL_DATABASECREATE_FLAGS:
    CODEQL_DATABASEANALYZE_FLAGS:
    
    # Coverity analysis variables
    # VARIABLE                         REQUIRED?   FORMAT
    # COVERITY_WARNINGS                Yes         True/False
    # COVERITY_PATH                    No          String
    # COVERITY_BUILD_DIR               No          String
    # COVERITY_BUILD_CMD               Yes         String
    # COVERITY_CLEAN_CMD               Yes         String
    # COVERITY_COVBUILD_FLAGS          No          String
    # COVERITY_COVANALYZE_FLAGS        No          String
    # COVERITY_COVFORMATERRORS_FLAGS   No          String
    #
    [Coverity Variables]
    COVERITY_WARNINGS: True
    COVERITY_PATH: /opt/local/coverity/bin
    COVERITY_BUILD_DIR: src
    COVERITY_BUILD_CMD: make all
    COVERITY_CLEAN_CMD: make clean
    COVERITY_COVBUILD_FLAGS: 
    COVERITY_COVANALYZE_FLAGS:
    COVERITY_COVFORMATERRORS_FLAGS:
    
    # CodeSonar analysis variables
    # VARIABLE                      REQUIRED?   FORMAT
    # CODESONAR_WARNINGS            Yes         True/False
    # CODESONAR_PATH                No          String
    # CODESONAR_HUB                 Yes         String
    # CODESONAR_CERT                Yes         String
    # CODESONAR_KEY                 Yes         String
    # CODESONAR_PROJ_NAME           Yes         String
    # CODESONAR_RESULTS_TEMPLATE    No          Integer
    # CODESONAR_BUILD_DIR           No          String
    # CODESONAR_BUILD_CMD           Yes         String
    # CODESONAR_CLEAN_CMD           Yes         String
    # CODESONAR_BASELINE_ANALYSIS   Yes         True/False
    # CODESONAR_P10_ANALYSIS        Yes         True/False
    # CODESONAR_BUILD_FLAGS         No          String
    # CODESONAR_ANALYZE_FLAGS       No          String
    # CODESONAR_GET_FLAGS           No          String
    #
    [CodeSonar Variables]
    CODESONAR_WARNINGS: True
    CODESONAR_PATH: /opt/local/codesonar/codesonar/bin
    CODESONAR_HUB: www.fake-codesonar-hub.com
    CODESONAR_CERT: /home/user/codesonar_cert.pem
    CODESONAR_KEY: /home/user/codesonar_key.pem
    CODESONAR_PROJ_NAME: /TestProject
    CODESONAR_RESULTS_TEMPLATE:
    CODESONAR_BUILD_DIR: src
    CODESONAR_BUILD_CMD: make all
    CODESONAR_CLEAN_CMD: make clean
    CODESONAR_BASELINE_ANALYSIS: True
    CODESONAR_P10_ANALYSIS: True
    CODESONAR_BUILD_FLAGS:
    CODESONAR_ANALYZE_FLAGS: 
    CODESONAR_GET_FLAGS:
    
    
    # SonarQube analysis variables
    # VARIABLE                 REQUIRED?   FORMAT
    # SONARQUBE_WARNINGS       Yes         True/False
    # SONARQUBE_PATH           No          String
    # SONARQUBE_SERVER         Yes         String
    # SONARQUBE_TOKEN          Yes         String
    # SONARQUBE_PROJECT        Yes         String
    # SONARQUBE_BUILD_DIR      No          String
    # SONARQUBE_BUILD_CMD      No          String
    # SONARQUBE_CLEAN_CMD      No          String
    # SONARQUBE_SCANNER_FLAGS  No          String
    # SONARQUBE_CURL_FLAGS     No          String
    #
    [SonarQube Variables]
    SONARQUBE_WARNINGS: True
    SONARQUBE_PATH: /opt/local/sonarqube/bin
    SONARQUBE_SERVER: www.fake-sonarqube-server.com
    SONARQUBE_TOKEN: $SONARQUBE_TOKEN
    SONARQUBE_PROJECT: scrub-analysis
    SONARQUBE_BUILD_DIR: src
    SONARQUBE_BUILD_CMD: make all
    SONARQUBE_CLEAN_CMD: make clean
    SONARQUBE_SCANNER_FLAGS:
    SONARQUBE_CURL_FLAGS:
    
    
    # Collaborator upload variables
    # VARIABLE                        REQUIRED?   FORMAT
    # COLLABORATOR_UPLOAD             Yes         True/False
    # COLLABORATOR_SERVER             Yes         String
    # COLLABORATOR_CCOLLAB_LOCATION   No          String
    # COLLABORATOR_USERNAME           No          String
    # COLLABORATOR_REVIEW_TITLE       No          String
    # COLLABORATOR_REVIEW_GROUP       No          String
    # COLLABORATOR_REVIEW_TEMPLATE    No          String
    # COLLABORATOR_REVIEW_ACCESS      No          String
    # COLLABORATOR_FINDING_LEVEL      No          String
    # COLLABORATOR_FILTERS            No          String
    # COLLABORATOR_SRC_FILES          No          String
    #
    [Collaborator Variables]
    COLLABORATOR_UPLOAD: True
    COLLABORATOR_SERVER: www.fake-collaborator.com
    COLLABORATOR_CCOLLAB_LOCATION: /opt/local/ccollab
    COLLABORATOR_USERNAME: userid
    COLLABORATOR_REVIEW_TITLE: 'My SCRUB Review'
    COLLABORATOR_REVIEW_GROUP:
    COLLABORATOR_REVIEW_TEMPLATE: 'The Best Template'
    COLLABORATOR_REVIEW_ACCESS:
    COLLABORATOR_FINDING_LEVEL: Defect
    COLLABORATOR_FILTERS:
    COLLABORATOR_SRC_FILES:
    
    # SCRUB GUI variables
    # VARIABLE     REQUIRED?   FORMAT
    # GUI_EXPORT   Yes         True/False
    #
    [SCRUB GUI Variables]
    SCRUB_GUI_EXPORT: True
    
    ###############################################################################
    ################################################################################
    ## FILTERING VARIABLES
    ################################################################################
    ################################################################################
    # SCRUB analysis filtering variables
    # VARIABLE              REQUIRED?   FORMAT
    # ENABLE_EXT_WARNINGS   Yes         True/False
    # ENABLE_MICRO_FILTER   Yes         True/False
    # CUSTOM_FILTER_CMD     No          String
    # ANALYSIS_FILTERS      No          String
    # QUERY_FILTERS         No          String
    #
    [Filtering Variables]
    ENABLE_EXT_WARNINGS: False
    ENABLE_MICRO_FILTER: True
    CUSTOM_FILTER_CMD:
    ANALYSIS_FILTERS:
    QUERY_FILTERS:
