# Integration-Test-Docker-Environment 2.0.0, released t.b.d.

## Summary

Version 2.0.0 of ITDE comes with breaking changes as public API class `DatabaseInfo` has been changed.  Former separate attributes `database_port_forward`and `bucketfs_port_forward` have been replaced by a single attribute `port` set to an instance of `PortForwarding` with attributes `database`, `bucketfs`, and `ssh`.

Up to version 1.6.0 ITDE used `docker_exec` to access the Docker Container, e.g. to analyze the content of logfiles or execute some shell commands. With version 8 of Exasol database the format of the Docker Containers might change so that `docker_exec` is no longer possible. Instead ITDE will then need to use SSH access.

The current release therefore enhances ITDE to enable to access the Docker Container via SSH.  The user can select the docker access method with command line option `--db-os-access` and can specify a port number to which ITDE forwards the SSH port of the Docker Container, see User Guide.

Additionally the directory for storing the randomly generated SSH keys has been moved to `~/.cache/exasol/itde/`. By that ITDE can restrict file permissions allowing access only by the current user.

T.B.D.

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.17

If you need further versions, please open an issue.

## Internal

## Changes

* #301: Added commandline option `--db-os-access`
* #302: Added support to create an SSH key for accessing Docker Container
* #241: Renamed environment variable for test execution from `GOOGLE_CLOUD_BUILD` to `RUN_SLC_TESTS_WITHIN_CONTAINER`
* #190: Added support for the Exasol 8.0 Docker-DB prerelease version
* #326: Changed folder for SSH keys to `~/.cache/exasol/itde/`
* #303: Added authorized_keys to Docker Container for SSH access
* #329: Added CLI option `--ssh-port-forward` to forward SSH port
