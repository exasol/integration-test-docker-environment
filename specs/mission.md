# Mission: integration-test-docker-environment

> A Python CLI and API layer that starts a standard Exasol Docker-DB test environment, so developers, contributors, and customers can run Exasol-backed integration tests or simple local database setups without assembling the container stack manually.

## Problem Statement

Developers and contributors need a repeatable way to start an Exasol database environment for integration testing in other projects. Customers also need a simple wrapper around the Exasol Docker-DB image so they can start and inspect a working test environment without wiring up the container details themselves. The project exists to hide the setup, configuration, startup, and health checks that would otherwise have to be managed manually.

## Target Users

| Persona | Goal | Key Workflow |
|---------|------|--------------|
| Developer / contributor | Start a predictable Exasol-backed test environment for local or CI-driven integration tests | Install the tool, check `health`, then run `spawn-test-environment` or the API layer from another project |
| Customer / user | Use a simple wrapper around Exasol Docker-DB | Start the environment with a small set of command-line options and connect to the forwarded services |

## Core Capabilities

1. **Start an Exasol Docker-DB environment** — launch a standard Exasol database container from the Docker image with sensible defaults.
2. **Attach an optional test container** — create a second container in the same Docker network so tests can run next to the database.
3. **Configure the environment** — customize DB memory, disk size, image version, runtime, nameservers, port forwards, environment variables, and extra DB parameters.
4. **Support operational tasks** — check host health, print default DB settings, manage certificates, and expose host-accessible ports for the database and BucketFS.
5. **Support advanced execution modes** — reuse SSH access where needed and enable GPU-backed setups for supported Exasol versions.

## Out of Scope

- Windows support.
- Managing Docker-DB itself as a product or replacing the upstream Exasol Docker image.
- Java-focused Testcontainers-style lifecycle integration.
- Full database administration beyond what is needed to start and use a test environment.
- Any workflow that does not depend on Docker.

## Domain Glossary

| Term | Definition |
|------|------------|
| Docker-DB | The Exasol database container image that ITDE starts and configures. |
| BucketFS | The Exasol file service exposed by the environment for uploads and access. |
| EXAConf | The database configuration file used by the environment setup. |
| Test container | An optional client-controlled container that runs on the same Docker network as the database. |
| `docker_exec` | A container access method that executes commands inside the database container. |
| SSH access | An alternative way to access the database operating system when `docker_exec` is not suitable. |
| Accelerator | NVIDIA GPU passthrough support for the Docker-DB container. |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Language | Python | Main implementation language |
| Runtime | Python 3.10 to 3.14 | Supported execution environment from `pyproject.toml` |
| Framework | Click, Luigi, nox | CLI commands, task orchestration, and development sessions |
| Database | Exasol Docker-DB | Database container managed by the tool |
| Testing | pytest | Unit and integration testing |

## Commands

```bash
# Build a standalone binary
poetry run -- nox -s build-standalone-binary -- --executable-name "itde_linux_x86-64"

# Run tests
poetry run -- nox -s run-all-tests -- --db-version default --test-set default

# Lint & Format
poetry run -- nox -s format:fix

# Gather Code Coverage
poetry run -- nox -s test:unit
```

## Project Structure

```
integration-test-docker-environment/
├── exasol_integration_test_docker_environment/  # CLI, API layer, orchestration logic, templates, and runtime helpers
├── test/                                         # Unit and integration tests
├── doc/                                          # User guide, developer guide, API docs, and changelog
├── docker_db_config_template/                    # Versioned Docker-DB configuration templates
├── scripts/                                      # Helper shell scripts
└── vagrant/                                      # Vagrant and provisioning support
```

## Architecture

The project uses a layered Python design:

- The `itde` CLI exposes user-facing commands such as `health`, `environment`, and `spawn-test-environment`.
- The CLI delegates to an API layer, which coordinates environment creation and health checks.
- The API layer drives Luigi-based task orchestration for database setup, test container setup, container networking, port forwarding, certificate handling, and related preparation steps.
- Supporting modules handle logging, resource management, configuration, Docker registry access, and test-environment utilities.

Data flow starts with the CLI or API request, moves through validation and task construction, and ends with a configured Docker-DB environment plus optional test-container artifacts and host-side connection information.

## Constraints

- **Technical**: Requires Docker; Windows is not supported; Linux and Mac OS X on Intel are supported.
- **Technical**: Docker must run with privileged mode, and GPU usage requires NVIDIA-compatible Docker support.
- **Technical**: The environment stores generated state and connection details on disk, including cache and output directories.
- **Business**: The tool is a wrapper around Exasol Docker-DB, not a replacement for upstream container images or other ecosystem tools.
- **Performance**: The environment needs at least 2 GiB RAM and roughly 15 GB free disk space for practical use.

## External Dependencies

| Service | Purpose | Failure Impact |
|---------|---------|----------------|
| Docker daemon | Runs the database and test containers | The environment cannot start |
| Exasol Docker Hub image | Supplies the Docker-DB base image | The database container cannot be created |
| NVIDIA container support | Enables GPU-backed database runs | GPU scenarios cannot run |
| Optional Docker registry credentials | Pull and push cached build stages | Image reuse and stage publishing may fail |
