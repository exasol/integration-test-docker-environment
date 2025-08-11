# 4.2.0 - 2025-07-01

## Security

 - #488: Fixed vulnerabilities by updating dependencies
  * CVE-2025-47287 in transitive productive dependency `tornado` via `luigi` by updating `tornado` to version `6.5.1`
  * CVE-2025-47273 in transitive dev dependency `setuptools` via `exasol-toolbox`, `bandit`, `stevedore` by updating `setuptools` to version `80.9.0`
 - #494: Fixed vulnerabilities by updating dependencies
   * CVE-2025-50182 and CVE-2025-50181 in transitive productive dependency `urllib3` via `docker` and `requests` by updating `urllib3` to version `2.5.0`
   * CVE-2024-47081 in productive dependency `requests` by updating `requests` to version `2.32.4`

## Feature
 - 442: Adding feature to show the default DB version and Adding a nox task to update the default DB version all over the repository at relevant places.
