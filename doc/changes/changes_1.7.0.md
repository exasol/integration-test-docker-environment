# Integration-Test-Docker-Environment 1.7.0, released t.b.d.

## Summary

Up to version 1.6.0 ITDE used `docker_exec` to access the Docker Container, e.g. to analyze the content of logfiles or execute some shell commands. With version 8 of Exasol database the format of the Docker Containers might change so that `docker_exec` is no longer possible. Instead ITDE will then need to use SSH access.

The current release therefore enhances ITDE to enable to access the Docker Container via SSH.
The user can select the docker access method with command line option `--docker-access-method`, see User Guide.

T.B.D.

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.17

If you need further versions, please open an issue.

## Internal

## Changes

* #301: Added commanline option `--docker-access-method`
* #302: Added support to create an SSH key for accessing Docker Container
* #241: Renamed environment variable for test execution from `GOOGLE_CLOUD_BUILD` to `RUN_SLC_TESTS_WITHIN_CONTAINER`
* #190: Added Exasol 8.0 prerelease to list of tested database versions
