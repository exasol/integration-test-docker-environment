# Integration-Test-Docker-Environment 0.5.0, released t.b.d.

Code name: Fix index out-of-range in FileDirectoryListHasher

## Summary

This release fixes an index-out-of-range bug in the FileDirectoryListHasher which occurs for single character file or directory names.

### Supported Exasol Versions

* **6.2**: up to 6.2.15
* **7.0**: up to 7.0.11
* **7.1**: 7.1.0-d1

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

n/a

## Features / Enhancements:

- #106: Add support for docker-db 7.1.0-d1  

## Refactoring:

n/a  

