# Plan: add-ray-basetask-poc

## Intent

Create a proof of concept that keeps the existing `BaseTask` API stable while cloning the implementation into a new Ray-backed variant in parallel to the Luigi-based path.

## User Goals

- Preserve the public `BaseTask` API so inherited task classes continue to work.
- Keep the Ray work bottom-up and incremental.
- Start with the smallest compatible surface area: `BaseTask` behavior, then the three smallest integration tests.
- Leave the current Luigi implementation untouched for comparison.

## Scope

### In scope

- Add a new Ray-backed `BaseTask` implementation in a separate file.
- Keep the class structure and child-task creation shape close to the existing Luigi version.
- Preserve the current API surface used by inherited code.
- Add or adapt the minimum integration coverage needed for:
  - return value handling
  - common parameter propagation
  - dependency creation

### Out of scope

- Replacing the existing Luigi implementation.
- Distributed Ray cluster support.
- Broad refactors of unrelated task helpers.
- Expanding the test matrix beyond the minimal PoC set.

## Proposed Approach

1. [expert] Define the compatibility boundary for the Ray clone: constructor signature, inheritance shape, dependency registration, result handling, cleanup, and child task creation.
2. [expert] Map the Luigi behaviors used by `BaseTask` onto a minimal Ray execution model suitable for local PoC execution only.
3. Add a new Ray-backed base task file alongside the existing Luigi version.
4. Keep the existing Luigi code path intact so tests can compare behavior and the migration remains incremental.
5. Add the minimal integration tests first, in this order:
   - `test_common_run_task.py`
   - `test_common_parameter.py`
   - `test_dependency_creation.py`
6. Validate the Ray-backed path against the current compatibility expectations before expanding further.

## Test Strategy

- Use the return-value test to validate the most basic task execution contract.
- Use the common-parameter test to validate inherited task compatibility and parameter propagation.
- Use the dependency-creation test to validate static and dynamic dependency creation/execution in the new path.

## Risks

- Ray may not match Luigi semantics one-to-one for dependency handling or result propagation.
- The inherited task hierarchy may rely on implicit Luigi behavior that needs to be preserved explicitly in the Ray clone.
- If the Ray PoC diverges too early from the existing class structure, downstream inherited code may stop working.

## Validation

- The active plan must validate with `speq plan validate add-ray-basetask-poc`.
- The plan should contain a delta file under the active plan tree and a `plan.md` summary.

## Output Files

- `specs/_plans/add-ray-basetask-poc/plan.md`
- `specs/_plans/add-ray-basetask-poc/specs/base-task/ray-poc/spec.md`
