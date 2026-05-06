Feature: Port Allocation

  Scenario: Automatically allocated ports are all positive and unique
    When `find_free_ports(N)` is called for N in [1, 2, 100, 1000]
    Then the returned list contains exactly N port numbers
    And none of the port numbers is 0
    And all port numbers in the list are distinct

  Scenario: SSH port forward defaults to a randomly selected free port
    Given an environment spawned without an explicit ssh_port_forward
    Then the environment info reports an SSH forwarded port that is greater than 0

  Scenario: Default internal ports match the documented values
    Then the database internal port is 8563
    And the BucketFS HTTP internal port is 2580
    And the BucketFS HTTPS internal port is 2581
    And the SSH internal port is 22
