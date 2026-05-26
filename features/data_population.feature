Feature: Data Population

  Scenario: Populate test data into a running database
    Given a running test environment with a test container
    When `PopulateTestDataToDatabase` is executed for the first time
    Then the SQL import script is executed successfully
    And the table TEST.ENGINETABLE contains 100 rows

  Scenario: Duplicate data population raises an error
    Given a running test environment where test data has already been populated
    When `PopulateTestDataToDatabase` is executed a second time without prior cleanup
    Then a RuntimeError is raised
    And the database state remains consistent
