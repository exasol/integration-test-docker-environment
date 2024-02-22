# Integration-Test-Docker-Environment 2.1.0, released 2024-02-22

## Summary

This release addresses dependencies updates and dependency issues.

### Supported Exasol Versions

* **7.1**: up to 7.1.17
* **8**: 8.18.1

## Dependencies

* Constrain docker dependency to `>= 4.0.0, < 7.0.0`, for further details see [docker/docker-py#3223](https://github.com/docker/docker-py/issues/3223)

## Internal

* #184: Streamlined error messages
  * Added exasol-error-reporting library
