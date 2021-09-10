# Integration-Test-Docker-Environment 0.5.0, released t.b.d.

Code name: Add support for new docker-db versions

## Summary

This release adds support for new docker-db versions 6.2.16, 7.0.12 and 7.1.0-d1

### Supported Exasol Versions

* **6.2**: up to 6.2.16
* **7.0**: up to 7.0.12
* **7.1**: 7.1.0-d1

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

- #34 :Test container does not get restarted if it gets rebuild and reuse is activated

## Features / Enhancements:

- #106: Add support for docker-db 7.1.0-d1
- #111: Add docker-db version 6.2.16 and 7.0.12

## Refactoring:

n/a  

