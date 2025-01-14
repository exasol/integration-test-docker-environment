# Integration-Test-Docker-Environment 1.7.1, released 2023-06-19

## Summary

This release fixes the not working UDFs in Exasol Docker-DB 8.18.1. 

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.17
* **8**: 8.18.1

If you need further versions, please open an issue.

## Internal

## Changes

* #351: Added test for UDF with builtin Script-Language Container and fixed it for Docker-DB 8.18.1