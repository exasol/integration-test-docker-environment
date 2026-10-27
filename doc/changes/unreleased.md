# Unreleased

## Summary

Added SSH-ready Docker-DB fixture support for GitHub Actions
Added secure ConfD RPC port exposure and disposable Basic-auth credentials for Docker-DB integration tests

## Features

* #673: Add SSH-ready Docker-DB fixture support for GitHub Actions
* #676: Add secure ConfD RPC port exposure for Docker-DB integration tests
* #678: Provide documented ConfD credentials for disposable ITDE environments
* #682: Harden SSH Docker-DB readiness retries and acceptance coverage

## Refactorings

* #685: Refactor Docker-DB SSH and ConfD Endpoint Handling
* #687: Add json-rpc basic confd integration tests
* #689: Refactor Docker-DB SSH and ConfD Endpoint Handling Part 2
* #695: Removed support for Python 3.10 and updated to exasol-toolbox version 12.0.0

## Bugs

* #557: Docker pull returns unexpected messages
