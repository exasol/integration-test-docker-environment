Feature: Dependency Logging (DependencyLoggerBaseTask)

  Scenario: Static dependencies are logged to JSON files after the run phase
    Given a task that extends DependencyLoggerBaseTask with one static child dependency
    When the task completes successfully
    Then a JSON file exists at `{dependencies}/{task_id}/requires`
    And each line is a valid JSON object with fields: source, target, type="requires", index, state

  Scenario: Dynamic dependencies are logged to a separate JSON file
    Given a task that extends DependencyLoggerBaseTask with one dynamic child dependency
    When the task completes successfully
    Then a JSON file exists at `{dependencies}/{task_id}/dynamic`
    And each line is a valid JSON object with fields: source, target, type="dynamic", index, state

  Scenario: Dependency log can be used to render a task graph visualization
    Given a completed task tree with logged dependencies
    When generate_graph_plot is called
    Then a graph image is produced showing the task dependency structure
