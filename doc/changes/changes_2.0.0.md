# Integration-Test-Docker-Environment 2.0.0, released t.b.d.

## Summary

Version 2.0.0 of ITDE comes with breaking changes as public API class `DatabaseInfo` has been changed.  Former separate attributes `database_port_forward`and `bucketfs_port_forward` have been replaced by a single attribute `port` set to an instance of `PortForwarding` with attributes `database`, `bucketfs`, and `ssh`.

T.B.D.

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.17

If you need further versions, please open an issue.

## Internal

## Changes

* #329: Added CLI option `--ssh-port-forward` to forward SSH port
