# Unreleased

## Refactorings

 - #417: Replaced Ubuntu 18.04 and Ubuntu 20.04 Docker images with Ubuntu 22.04
 - #430: Splitted up api/common.py which changes the imports for its parts in breaking way
 - #443: Added GH workflow which validates that the Exaconf files in the package are up-to-date
 - #445: Fixed Type hints in BaseTask and FlavorBaseTask