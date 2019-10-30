Feature: Integration tests
    In order to run integration tests
    We'll spin up a Cassandra cluster

    Scenario: Run a nodetool status command
        When I run "nodetool status" on the cluster with strategy all
        Then there are as many nodes reported by nodetool as cstar detected
        And there are no errors in the job

    Scenario: Run a nodetool command that doesnt exist
        When I run "nodetool statussss" on the cluster with strategy all
        Then the job fails
    
    Scenario: Run a sudo command
        When I run "sudo blockdev --report" on the cluster with strategy all
        Then there are no errors in the job
        And the output for the first node contains "RO    RA   SSZ   BSZ"

    Scenario: Stop execution after one node
        When I run "nodetool status" and stop it after 1 node on the cluster with strategy one
        Then 1 node completed the execution
        And there are no errors in the job
        When I resume the job
        Then all nodes complete the execution successfully