# Integration-Test-Docker-Environment 0.12.0, released TBD

Code name: TBD

## Summary
TBD


### Supported Exasol Versions

* **7.0**: up to 7.0.19, **except 7.0.5**
* **7.1**: up to 7.1.12

If you need further versions, please open an issue.

### Tested Docker Runtimes
TBD


## Bug Fixes:
- #228: Fixed graph plot generator
- #230: Fixed default value of click option external-exasol-xmlrpc-port should be int
- #211: Fixed output of test DockerTestEnvironmentDockerRuntimeInvalidRuntimeGivenTest
- #244: Fixed bug in generate graph plot if task uses luigi.ListParameter
- #249: Fixed bug of calculation of hash value of docker images when using volatile absolute paths

## Features / Enhancements:

- #221:  Add support for exasol 7.1.10
- #223:  Updated docker-db versions

## Refactoring:

- #235: Moved implementations of all click commands in separate methods
- #240: Created more integation tests for api calls and implemented return values
- #251: Updated Poetry

## Documentation:
- TBD

## Security:

n/a
