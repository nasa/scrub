# Release Checklist
The purpose of this document is to establish a process and checklist for new SCRUB releases. The process assumes that
all code changes have been completed and is ready for testing and subsequent release

## Preparation
- [ ] Make code changes associated with issues assigned to milestone
- [ ] Perform unit testing for affected modules
- [ ] Make sure that any branched code and pending pull requests have been merged
- [ ] Update [setup.cfg](https://github.com/nasa/scrub/blob/master/setup.cfg) for new release
- [ ] Draft new release

## Checklist
- [ ] Review [CodeQL results](https://github.com/nasa/scrub/security/code-scanning)
    - [ ] Check for commented out/debugging code
    - [ ] Make necessary code changes based on findings
- [ ] Make updates to the integration test suite, if necessary
- [ ] Run integration test suite
- [ ] Run performance test case
    - [ ] Analyze and compare metrics to previous releases
- [ ] Make any necessary updates to the [SCRUB documentation](https://nasa.github.io/scrub)


## Publish Release
- [ ] Publish the release on [GitHub](https://github.com/nasa/scrub/releases)
    - [ ] Ensure successful completion of GitHub Action to push release to [PyPi](https://pypi.org/project/nasa-scrub/)
- [ ] Update this release checklist as necessary
