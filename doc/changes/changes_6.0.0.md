# 6.0.0 - 2026-02-24

This release adds support for docker db version 2025.1.8 and also adds support to build platform specific docker images.
The latter is a breaking change, because the docker image tag format has changed.
Additionally, the release fixes a bug when building the binary, where the "certificate_resources" folder was missing, 
a bug for the default values of some of the CLI parameters, and also a bug for serialization of class ImageInfo. 
Furthermore there were some internal improvements.

## Features

 - #558: Added docker-db 2025.1.8
 - #583: Added platform support for managed docker images 

## Bugs

 - #565: Added folder certificate_resources to binary
 - #588: Set missing default values for click parameter
 - #589: Fixed serialization of ImageInfo



## Internal

 - #568: Used automatic formatting tools to upgrade typing to Python 3.10 and remove unused imports
 - #568: Updated exasol-toolbox to 4.0.0
 - #580: Updated exasol-toolbox to 5.1.1 and re-locked poetry.lock

## Dependency Updates

### `main`
* Removed dependency `importlib-resources:6.5.2`

### `dev`
* Updated dependency `exasol-toolbox:1.10.0` to `5.1.1`
