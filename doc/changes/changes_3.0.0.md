# Integration-Test-Docker-Environment 3.0.0, released 2024-02-22

## Summary

Removed `pytest-itde` plugin.

### Supported Exasol Versions

* **7.1**: up to 7.1.17
* **8**: 8.18.1

### Breaking Changes

* Removed `pytest-itde` plugin See also

    Users which do rely on the plugin should consider moving to the standalone [pytest-itde](https://pypi.org/project/pytest-exasol-itde/) plugin.
    The related project can be found [here](https://github.com/exasol/pytest-plugins)
    

