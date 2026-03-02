# 6.1.0 - 2026-03-02

## Summary

This release allows to add arbitrary resources to the docker build. 
This is especially useful for the `exaslct` tool which needs to add a modified version of the package file to the docker image.

## Refactorings

 - #592: Added unit test for BuildContextHasher

## Features

 - #590: Added mechanism to add arbitrary resources to a docker build
