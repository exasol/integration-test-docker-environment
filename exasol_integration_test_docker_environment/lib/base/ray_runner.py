"""
Ray-based replacement for ``luigi.build()``.

Execution model
---------------
* Static deps (``requires()``): scheduled as Ray remote tasks; independent
  branches run in parallel.
* Dynamic deps (``yield`` in ``run_task()``): each yielded task is also
  submitted via the same ``_schedule()`` helper, giving uniform Ray
  parallelism for both static and dynamic sub-trees.
* Deduplication: a ``TaskRegistry`` Ray actor is the single source of truth.
  Because actor methods execute serially the "check + register" operation is
  atomic — two Ray workers that independently try to schedule the same
  ``task_id`` always get back the same ``ObjectRef``.
"""

from __future__ import annotations

import types

import ray

from exasol_integration_test_docker_environment.lib.base.luigi_compat import (
    Task,
    flatten,
)


@ray.remote
class TaskRegistry:
    """Shared atomic registry — ensures each ``task_id`` is submitted at most once."""

    def set_self(self, handle: ray.actor.ActorHandle) -> None:
        self._handle: ray.actor.ActorHandle = handle
        self._refs: dict[str, ray.ObjectRef | None] = {}

    def schedule(
        self,
        task: Task,
        dep_refs: list[ray.ObjectRef],
    ) -> ray.ObjectRef | None:
        """Atomically check + submit *task*.

        *task* is passed directly; Ray serialises it automatically.
        *dep_refs* is a ``list[ObjectRef]``.  Ray does **not** auto-resolve
        elements nested inside a list, so they remain as ``ObjectRef``\\ s and
        are forwarded as-is to ``_run_task.remote()``.

        Returns the task's ``ObjectRef``, or ``None`` if already complete.
        """
        task_id = task.task_id

        if task.complete():
            return None
        if task_id in self._refs:
            return self._refs[task_id]

        ref = _run_task.remote(task, dep_refs, self._handle)
        self._refs[task_id] = ref
        return ref


@ray.remote
def _run_task(
    task: Task,
    dep_refs: list[ray.ObjectRef],
    registry: ray.actor.ActorHandle,
) -> None:
    """Wait for all static deps, then drive the task generator."""
    ray.get(dep_refs)
    if task.complete():
        return
    _drive(task, registry)


def _drive(task: Task, registry: ray.actor.ActorHandle) -> None:
    """Drive ``task.run()`` generator; schedule every dynamic dep via the registry."""
    gen = task.run()
    if not isinstance(gen, types.GeneratorType):
        return
    try:
        yielded = next(gen)
        while True:
            futures: list[ray.ObjectRef] = [
                f for t in flatten(yielded) if (f := _schedule(t, registry)) is not None
            ]
            ray.get(futures)
            gen.send(_map_outputs(yielded))
    except StopIteration:
        pass


def _schedule(task: Task, registry: ray.actor.ActorHandle) -> ray.ObjectRef | None:
    """Schedule *task* and all its static deps; return ``ObjectRef`` or ``None``."""
    if task.complete():
        return None

    dep_refs: list[ray.ObjectRef] = [
        f for d in flatten(task.requires()) if (f := _schedule(d, registry)) is not None
    ]

    # Round-trip to actor (~1 ms); returns the task's ObjectRef without
    # waiting for actual task execution to finish.
    return ray.get(registry.schedule.remote(task, dep_refs))


def _map_outputs(struct: object) -> object:
    """Map a yielded task structure to its ``output()`` equivalents (PickleTargets).

    ``run_dependencies()`` does ``completion_targets = yield tasks``; Luigi
    sends back ``task.output()`` for each yielded task.  This function
    replicates that mapping so the generator resumes with the correct values.
    The mapped value flows through ``yield from`` chains in
    ``DependencyLoggerBaseTask``, ``StoppableBaseTask``, and
    ``TimeableBaseTask`` transparently.
    """
    if isinstance(struct, dict):
        return {k: _map_outputs(v) for k, v in struct.items()}
    if isinstance(struct, list):
        return [_map_outputs(t) for t in struct]
    if hasattr(struct, "output"):
        return struct.output()
    return struct


def build(tasks: list[Task], workers: int = 1, **_ignored: object) -> bool:
    """Ray-based replacement for ``luigi.build()``.

    Parameters
    ----------
    tasks:
        List of root tasks to execute.
    workers:
        Number of Ray CPUs to allocate locally.
    **_ignored:
        All other keyword arguments are accepted but ignored (e.g.
        ``local_scheduler``, ``log_level`` that were passed to
        ``luigi.build()``).
    """
    if not ray.is_initialized():
        ray.init(num_cpus=workers, ignore_reinit_error=True)

    registry: ray.actor.ActorHandle = TaskRegistry.remote()
    ray.get(registry.set_self.remote(registry))

    futures: list[ray.ObjectRef] = [
        f for t in tasks if (f := _schedule(t, registry)) is not None
    ]
    try:
        ray.get(futures)
        return True
    except Exception:
        return False
