# Pull Request Checklist
The purpose of this document is to establish a process and checklist for new SCRUB releases. The process assumes that
all code changes have been completed and is ready for testing and subsequent release

## Checklist
- [ ] Rev the version information
    - [ ] Local VERSION file
    - [ ] PIP setup.cfg file   
- [ ] Review [CodeQL results](https://github.com/nasa/scrub/security/code-scanning)
    - [ ] Check for commented out/debugging code
    - [ ] Make necessary code changes based on findings
- [ ] Make updates to the regression test suite, if necessary
- [ ] Run regression test suite
- [ ] Make any necessary updates to the [SCRUB documentation](https://nasa.github.io/scrub)
