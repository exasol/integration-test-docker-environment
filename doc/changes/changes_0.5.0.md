# Integration-Test-Docker-Environment 0.5.0, released 2021-10-07

Code name: Add support for new docker-db versions

## Summary

This release adds support for new docker-db versions 6.2.17, 7.0.13 and 7.1.1

### Supported Exasol Versions

* **6.2**: up to 6.2.17
* **7.0**: up to 7.0.13
* **7.1**: up to 7.1.1

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

- #34 :Test container does not get restarted if it gets rebuild and reuse is activated

## Features / Enhancements:

- #106: Add support for docker-db 7.1.0-d1
- #111: Add docker-db version 6.2.16 and 7.0.12
- #116: Add docker-db 7.0.13, 6.2.17-d1 and 7.1.1 

## Refactoring:

n/a