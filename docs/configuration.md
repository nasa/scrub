# Configuration

Configuration of SCRUB analysis is handled almost entirely via the configuration file `scrub.cfg`.

## Completing scrub.cfg

Setting up you `scrub.cfg` file can be broken up into several key steps.

### 1. Determine which analysis tools you would like to use.
Determine which analysis tools you would like to use will determine which sections of the configuration file will be necessary for your project. This decision depends on the tools that are available to your organization, the coding languages supported by each tool, and the preference of the user.

### 2. Determine which output targets, if any, you would like to use
By default, SCRUB analysis will be output into the custom SCRUB file format. This is a human-readable output format designed for performing iterative analysis. Other tools such as Collaborator are suitable for performing more formalized peer reviews. As above, the selection of output targets will determine the relevant sections of the configuration file.

### 3. Determine the languages you would like to analyze.
Occasionally, the codebase of interest may contain more than a single language. SCRUB supports analysis of multiple languages as part of a single analysis. Interpreted languages will be recognized automatically\* by each of the analysis tools and no special action is needed\**. Compiled languages must be built during analysis by specifying the `<tool>_BUILD_CMD` configuration value (e.g. `COVERITY_BUILD_CMD: make all`).

*\*CodeSonar analysis requires the use of a pass-through command to capture Java, Python, and C#. Multiple commands can be specified as part of a single build capture. Please refer to the CodeSonar manual for more information.*

*\**Coverity requires a pre-configuration step to be performed in order to properly recognized interpreted languages. Please refer to the Coverity manual for more information.*

### 4. If desired, customize optional analysis parameters
By default, SCRUB will perform a default analysis based on the languages that have been selected. Configuration values marked as optional on the [detailed configuration](configuration-inputs.md) page can modified to perform a project specific analysis. Many of these configuration values act as pass-through commands into the underlying analysis tool commands. Users should refer to the tool-specific documentation for more information about valid input values. Some common examples are shown below.

## Command Line Configurations
There are several flags that can be used to modify the execution of SCRUB without modifying `scrub.cfg` itself. These options are outlined in detail in the [usage](usage.md) section of this document.

## External Configurations
SCRUB supports the use of all standard shell environment configuration values as well as analyzer specific configuration options. Please refer to the tool's documentation for more specific information.
