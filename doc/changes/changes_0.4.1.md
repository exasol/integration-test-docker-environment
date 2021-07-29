# Integration-Test-Docker-Environment 0.4.1, released 2021-07-29

Code name: Fix index out-of-range in FileDirectoryListHasher

## Summary

This release fixes an index-out-of-range bug in the FileDirectoryListHasher which occurs for single character file or directory names.

### New supported Exasol Versions

* **6.2**: 6.2.14, 6.2.15,
* **7.0**: 7.0.4, 7.0.5, 7.0.6, 7.0.7, 7.0.8, 7.0.9, 7.0.10, 7.0.11

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

