Feature: Luigi BaseTask — Lifecycle and State Transitions

  Background:
    Given a task class that extends BaseTask

  Scenario: Task transitions through states in normal execution
    Given a task with no dependencies and a simple run_task implementation
    When the task is executed by the Luigi runner
    Then the task state transitions in order: INIT → AFTER_INIT → RUN → FINISHED → CLEANUP → CLEANED

  Scenario: Task state is set to ERROR when run_task raises an exception
    Given a task whose run_task raises a RuntimeError
    When the task is executed
    Then the task state is set to ERROR before the exception propagates
    And the exception is re-raised to the Luigi scheduler

  Scenario: Completion target is written after successful run
    Given a task that calls `self.return_object(value)` in run_task
    When the task finishes successfully
    Then a PickleTarget file exists at the task's output path
    And reading that file returns the value passed to return_object

  Scenario: return_object may only be called once per task run
    Given a task that calls `self.return_object(value)` twice in run_task
    When the task is executed
    Then an exception is raised on the second call


Feature: Luigi BaseTask — Static Dependencies

  Scenario: Static dependencies are registered during initialization
    Given a task that overrides register_required to create one child task
    When the task object is constructed
    Then the child task appears in requires() before run_task is called

  Scenario: Parent reads child return value via RequiresTaskFuture
    Given a parent task with a static child dependency
    And the child task calls return_object("child-result")
    When the parent's run_task calls get_values_from_future(self.child_future)
    Then the parent receives "child-result"

  Scenario: Multiple static dependencies return values in declaration order
    Given a parent task that registers [child_a, child_b] as static dependencies
    When both children complete and the parent calls get_values_from_futures([future_a, future_b])
    Then the returned list is [value_a, value_b] in the same order


Feature: Luigi BaseTask — Dynamic Dependencies

  Scenario: Dynamic dependencies can be created based on runtime state
    Given a task whose run_task yields a child task conditionally
    When the condition is true at runtime
    Then the child task is executed before run_task resumes
    And the parent can read the child's return value via the RunTaskFuture

  Scenario: Dynamic dependencies support lists of tasks
    Given a task whose run_task yields a list [child_a, child_b]
    When both children complete
    Then get_values_from_future returns a list [value_a, value_b]

  Scenario: Dynamic dependencies support dicts of tasks
    Given a task whose run_task yields {"key1": child_a, "key2": child_b}
    When both children complete
    Then get_values_from_future returns {"key1": value_a, "key2": value_b}

  Scenario: Dynamic dependencies are persisted for cleanup
    Given a task that registers dynamic dependencies during run_task
    When the task finishes
    Then the dynamic dependency list is written to the run_dependencies_target pickle file
    And those tasks are cleaned up during the cleanup phase


Feature: Luigi BaseTask — Cleanup Ordering and Deduplication

  Scenario: Cleanup is called on child tasks before parent tasks
    Given a parent task with one child static dependency
    When the parent's cleanup is invoked
    Then the child's cleanup_task is called before the parent's cleanup_task

  Scenario: Dynamic run dependencies are cleaned before static dependencies
    Given a task with both a static child and a dynamic child
    When cleanup is invoked on the parent
    Then the dynamic child is cleaned before the static child

  Scenario: A task shared by multiple parents is only cleaned once
    Given two parent tasks that both declare the same child task as a static dependency
    When both parents complete and cleanup is invoked on the root task
    Then the shared child task's cleanup_task is called exactly once
    And the cleanup_checklist contains the child's string representation

  Scenario: Tasks with different parameters are cleaned independently
    Given two parent tasks that each require a child with a different parameter value
    When cleanup is invoked
    Then each child's cleanup_task is called exactly once (two separate cleanups total)

  Scenario: Cleanup receives success=True after a successful run
    Given a task that records the value of the success argument in cleanup_task
    When the task completes without error
    Then cleanup_task is called with success=True

  Scenario: Cleanup receives success=False after a failed run
    Given a task that records the value of the success argument in cleanup_task
    When the task raises an exception during run_task
    Then cleanup_task is called with success=False


Feature: Luigi BaseTask — Failure Handling (StoppableBaseTask)

  Background:
    Given a task hierarchy where tasks extend StoppableBaseTask

  Scenario: A failing task writes its traceback to the failure directory
    Given a task whose run_task raises an exception
    When the task is executed
    Then a file exists at `{output}/failure/{task_id}` containing the exception traceback

  Scenario: A TASK_FAILED marker is created on the first failure
    Given a task that fails during run_task
    When the exception occurs
    Then a TASK_FAILED marker file is created in the job output directory

  Scenario: Subsequent tasks check the TASK_FAILED marker and stop early
    Given a task hierarchy where one task has already failed and created the TASK_FAILED marker
    When a sibling task begins execution
    Then it raises StoppingFurtherExecution without running its own logic

  Scenario: collect_failures returns all failures from the task tree
    Given a task tree where two leaf tasks failed
    When collect_failures is called on the root task
    Then the returned dict contains entries for both failed tasks
    And each entry includes the task identity and formatted traceback
    And the failures are deduplicated by task_id
