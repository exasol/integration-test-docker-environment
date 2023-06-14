# Integration-Test-Docker-Environment 1.7.0, released 2023-06-15

## Summary

This release added support for the Exasol Docker-DB 8.18.1. Furthermore, it adds the first features for accessing 
the Docker-DB container via SSH instead of `docker exec`. This is in preparation for later Exasol Docker-DB releases,
for which you can't access the operating system of the database with `docker exec`. However, the SSH access itself 
is not yet operational. Finally, this release fixes a bug in the reporting of task failures. The TaskRuntimeError 
didn't show the actual task failures if not caught explicitly.

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.17
* **8**: 8.18.1

If you need further versions, please open an issue.

## Internal

## Changes

* #301: Added commandline option `--db-os-access`
* #302: Added support to create an SSH key for accessing Docker Container
* #241: Renamed environment variable for test execution from `GOOGLE_CLOUD_BUILD` to `RUN_SLC_TESTS_WITHIN_CONTAINER`
* #190: Added support for the Exasol 8.0 Docker-DB prerelease version
* #326: Changed folder for SSH keys to `~/.cache/exasol/itde/`
* #303: Added authorized_keys to Docker Container for SSH access
* #337: Added Docker-DB 8.18.1
* #350: TaskRuntimeError will be raised as chained exception with all task failures.