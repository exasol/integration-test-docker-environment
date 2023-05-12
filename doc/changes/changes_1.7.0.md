# Integration-Test-Docker-Environment 1.7.0, released t.b.d.

## Summary

Up to version 1.6.0 ITDE used `docker_exec` to access the Docker Container, e.g. to analyze the content of logfiles or execute some shell commands. With version 8 of Exasol database the format of the Docker Containers might change so that `docker_exec` is no longer possible. Instead ITDE will then need to use SSH access.

The current release therefore enhances ITDE to enable to access the Docker Container via SSH.

t.b.d.

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.17

If you need further versions, please open an issue.

## Changes

* #302: Added support to create an SSH key for accessing Docker Container
