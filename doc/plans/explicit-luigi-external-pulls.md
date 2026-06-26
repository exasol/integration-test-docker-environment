# Explicit Luigi Pull Tasks Plus Mixed-Reference Regression Coverage

## Summary
Replace Docker build's global `pull=True` behavior with explicit Luigi pull tasks for external images.

The implementation covers:
- unit tests for Dockerfile reference analysis and pull-task planning
- a fully mocked unit test that mocks Docker completely
- an integration regression test with a real local test registry and a multi-step build graph

Only missing external references should produce pull tasks. The actual Docker build should then run with `pull=False`.

## Implementation Changes
- Add Dockerfile reference analysis on rendered Dockerfile content, after Jinja substitution, to collect image references from:
  - `FROM <image>`
  - `COPY --from=<ref>`
- Classify references as:
  - ITDE dependency image from `image_info.depends_on_images`
  - stage alias from `FROM ... AS ...`
  - numeric stage index in `COPY --from=<n>`
  - `scratch`
  - external pullable image
- Add local-availability filtering so only missing external images produce pull tasks.
- Introduce explicit Luigi pull tasks for external references:
  - one task per concrete external image reference
  - task performs `docker pull <image>`
  - task is skipped logically when the image already exists locally
- Extend build-task execution so `DockerCreateImageTask` schedules:
  - existing ITDE build/load/pull tasks from `depends_on_images`
  - new explicit external-image pull tasks for missing external references
- Change `DockerBuildImageTask` to call `docker_client.api.build(..., pull=False, ...)`.
- Reuse existing Docker client and registry-auth configuration so external pull tasks behave consistently with current pull behavior.
- Deduplicate external pull tasks by exact rendered image reference.
- Keep build-context creation, dependency-image templating, and image hashing unchanged.

## Internal Interfaces / Behavior
- No CLI or public API signature changes.
- Internal Luigi graph changes:
  - image builds may now include explicit external pull-task dependencies
  - external pulls become visible in dependency graphs and logs
- External references in both `FROM` and `COPY --from` are handled consistently.
- Build-step references from prior Luigi tasks are never treated as pullable external images.

## Unit Tests
- Add unit tests for rendered-Dockerfile reference extraction:
  - external `FROM`
  - dependency `FROM {{ dep }}`
  - stage alias via `FROM ... AS builder`
  - `COPY --from=builder`
  - `COPY --from=0`
  - external `COPY --from=<image>`
  - mixed Dockerfile containing both dependency and external references
- Add a fully mocked unit test that mocks Docker completely:
  - mock Docker client access
  - mock local image existence checks
  - mock `docker_client.api.build`
  - mock explicit pull execution
  - verify that for a mixed Dockerfile:
    - only missing external references schedule pull tasks
    - build-step references do not
    - Docker build is invoked with `pull=False`

## Integration Regression Test
- Add an integration test near `test/integration/test_docker_build_base.py`, using the lower-level `DockerBuildBase` pattern to model a multi-step dependency graph.
- Define test-only `DockerAnalyzeImageTask` subclasses and one `DockerBuildBase` root task with a graph:
  - `build-step-base`: local build-step image used by `FROM`
  - `build-step-copy-source`: local build-step image used by `COPY --from`
  - `final-image`: depends on both build-step tasks and also references external images
- The final rendered Dockerfile contains all four reference types:
  - `FROM {{ build_step_base }}`
  - `COPY --from={{ build_step_copy_source }} ...`
  - `FROM <local-registry>/<repo>/external-from:tag`
  - `COPY --from=<local-registry>/<repo>/external-copy:tag ...`
- Seed a real local registry using `LocalDockerRegistryContextManager`:
  - build or tag small source images for `external-from` and `external-copy`
  - push them into the local registry under the exact names used by the final Dockerfile
  - remove those external images from the local daemon before the actual Luigi build so the test requires explicit pulls
- Keep build-step images out of the registry entirely so the test proves they are resolved only from earlier Luigi build steps.
- Run the root Luigi build with `workers > 1` so pull tasks are eligible to run in parallel.
- Validate:
  - final image builds successfully
  - final image contains marker artifacts copied from both local build-step and external-copy images
  - final image resolves both `FROM` variants correctly
  - registry contains only seeded external images, not internal build-step images

## Assumptions
- The plan file lives under `doc/plans/`.
- The authoritative signal for internal build-step images is `image_info.depends_on_images`.
- Exact rendered image references are used for local-availability checks, deduplication, and external pull tasks.
- Luigi scheduler parallelism is sufficient; no custom concurrency logic is needed inside pull tasks.
