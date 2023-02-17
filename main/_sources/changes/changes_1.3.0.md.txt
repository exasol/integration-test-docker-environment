# Integration-Test-Docker-Environment 1.3.0, released 2023-02-17

## Summary

In version 1.3.0 of the ITDE we added new supported versions up to 7.0.20 and 7.1.17 respectively.

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.17

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime

## Refactoring:

- Removed docker health checks from ITDE starter script
- Fixed broken/outdated import path
- Added itde cli entry point to project configuration
