# Docker-DB Test Environment Starter

**This repository is under development and might undergo breaking changes. 
Use it only, if you know what you are doing.**

Clone the repository

```
git clone https://github.com/exasol/integration-test-docker-environment
```

Starting the test environment:

```
./start-test-env spawn-test-environment --environment-name <NAME> --database-port-forward <PORT> --bucketfs-port-forward <PORT>
```

Shutdown of the test environment is currently done manual.
