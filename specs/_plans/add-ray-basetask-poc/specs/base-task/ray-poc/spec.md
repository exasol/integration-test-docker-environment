# Ray-backed BaseTask PoC

## Background

The current `BaseTask` implementation is Luigi-based and is used by inherited tasks that depend on a stable API, task creation shape, and dependency handling behavior. This proof of concept adds a Ray-backed clone in parallel to the existing implementation so the migration can proceed incrementally without breaking the current Luigi path.

## Scenarios

### Scenario: Preserve the existing BaseTask API

#### GIVEN
- existing tasks inherit from `BaseTask`
#### WHEN
- the Ray-backed clone is introduced
#### THEN
- the public API and class structure remain compatible with inherited code

### Scenario: Keep the Ray implementation parallel to the Luigi implementation

#### GIVEN
- the current Luigi-backed `BaseTask` is still required for comparison
#### WHEN
- the PoC is implemented
#### THEN
- the Ray-backed version is added in a separate file and the Luigi implementation remains intact

### Scenario: Implement the PoC bottom-up

#### GIVEN
- the PoC starts from the smallest `BaseTask` behavior surface
#### WHEN
- the Ray-backed version is implemented
#### THEN
- the work begins with return value handling, then common parameter propagation, then dependency creation

### Scenario: Support local Ray execution for the PoC

#### GIVEN
- the existing Luigi path uses local execution
#### WHEN
- the Ray-backed PoC is designed
#### THEN
- it targets local Ray execution only and does not require distributed cluster support

### Scenario: Cover the minimal compatibility test set

#### GIVEN
- the Ray-backed PoC must prove the core `BaseTask` contract
#### WHEN
- integration tests are selected for the first pass
#### THEN
- the minimal set is `test_common_run_task.py`, `test_common_parameter.py`, and `test_dependency_creation.py`
