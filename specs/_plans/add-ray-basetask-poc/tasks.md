# Tasks: add-ray-basetask-poc

## Phase 1: Compatibility Boundaries
- [ ] 1.1 Define the Ray compatibility boundary for `BaseTask` API preservation [expert]
- [ ] 1.2 Map the Luigi behaviors used by `BaseTask` onto a minimal local Ray execution model [expert]

## Phase 2: Implementation
- [x] 2.1 Add a new Ray-backed base task module alongside the Luigi implementation
- [x] 2.2 Keep the existing Luigi `BaseTask` path intact for comparison
- [x] 2.3 Add or adapt `test_common_run_task.py`
- [x] 2.4 Add or adapt `test_common_parameter.py`
- [x] 2.5 Add or adapt `test_dependency_creation.py`

## Phase 3: Verification
- [ ] 3.1 Validate the active plan with `speq plan validate add-ray-basetask-poc`
- [x] 3.2 Run the targeted integration tests for the three PoC scenarios
- [ ] 3.3 Review the changed files for regressions and spec drift
