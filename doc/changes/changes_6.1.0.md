# 6.1.0 - 2026-03-02

## Summary

This release allows to add arbitrary resources to the docker build. 
This is especially useful for the `exaslct` tool which needs to add a modified version of the package file to the docker image.

## Refactorings

 - #592: Added unit test for BuildContextHasher

## Features

 - #590: Added mechanism to add arbitrary resources to a docker build

## Internal

 - Relocked dependencies

## Dependency Updates

### `main`
* Updated dependency `click:8.3.0` to `8.3.1`
* Updated dependency `exasol-error-reporting:1.0.0` to `1.1.0`
* Updated dependency `gitpython:3.1.45` to `3.1.46`
* Updated dependency `luigi:3.6.0` to `3.7.3`
* Updated dependency `networkx:3.2.1` to `3.4.2`

### `dev`
* Updated dependency `dill:0.4.0` to `0.4.1`
* Updated dependency `joblib:1.5.2` to `1.5.3`
* Updated dependency `mypy:1.18.2` to `1.19.1`
* Updated dependency `pyexasol:1.2.0` to `2.0.0`
* Updated dependency `pyinstaller:6.16.0` to `6.19.0`
* Updated dependency `types-pyinstaller:6.16.0.20250918` to `6.19.0.20260215`
