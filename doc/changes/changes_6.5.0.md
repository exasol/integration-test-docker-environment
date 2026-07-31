# 6.5.0 - 2026-07-31

## Summary

This release fixes a bug in Docker image tagging when `build_name` is provided.

The image is now published with both the hashsum-suffixed tag and the `build_name` tag, so clients that rely on the hashsum tag, such as exaslct image caching, continue to work.

At the same time, the simpler `build_name` tag is still generated for release-oriented workflows.

Also there were some internal improvements.

## Security Issues

This release fixes vulnerabilities by updating dependencies:

| Dependency | Vulnerability | Affected | Fixed in |
|------------|---------------|----------|----------|
| gitpython | GHSA-2f96-g7mh-g2hx | 3.1.50 | 3.1.51 |
| gitpython | GHSA-v396-v7q4-x2qj | 3.1.50 | 3.1.51 |
| gitpython | GHSA-956x-8gvw-wg5v | 3.1.50 | 3.1.51 |
| gitpython | GHSA-3rp5-jjmw-4wv2 | 3.1.50 | 3.1.53 |
| gitpython | GHSA-fjr4-x663-mwxc | 3.1.50 | 3.1.54 |
| gitpython | GHSA-6p8h-3wgx-97gf | 3.1.50 | 3.1.54 |
| gitpython | GHSA-r9mr-m37c-5fr3 | 3.1.50 | 3.1.54 |
| gitpython | GHSA-94p4-4cq8-9g67 | 3.1.50 | 3.1.55 |
| setuptools | PYSEC-2026-3447 | 82.0.1 | 83.0.0 |
| setuptools | PYSEC-2026-3447 | 82.0.1 | 83.0.0 |

## Refactoring

* #630: Updated to exasol-toolbox 10.2.1 and restored check-workflows in checks.yml
* #662: Updated to exasol-toolbox 10.4.0 and updated dependencies

## Bugs

* #639: Fixed quirks with build_name during image build

## Dependency Updates

### `main`

* Updated dependency `docker:7.1.0` to `7.2.0`
* Updated dependency `gitpython:3.1.50` to `3.1.57`

### `dev`

* Updated dependency `exasol-toolbox:10.0.0` to `10.4.0`
* Updated dependency `pyexasol:2.2.2` to `2.3.0`