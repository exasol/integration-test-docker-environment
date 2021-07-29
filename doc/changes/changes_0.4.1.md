# Integration-Test-Docker-Environment 0.4.1, released 2021-07-29

Code name: Fix index out-of-range in FileDirectoryListHasher

## Summary

This release fixes an index-out-of-range bug in the FileDirectoryListHasher which occurs for single character file or directory names.

### Supported Exasol Versions

* **6.2**: up to 6.2.15
* **7.0**: up to 7.0.11

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:
   - #103: Index out of range exception in FileDirectoryListHasher

## Features / Enhancements:
n/a  

## Refactoring:
n/a  

