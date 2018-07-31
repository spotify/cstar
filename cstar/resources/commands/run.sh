#! /bin/bash
# C* cluster-parallel: true
# C* dc-parallel: true
# C* strategy: topology
# C* description: Run an arbitrary shell command
# C* argument: {"option":"--command", "name":"COMMAND", "description":"Command to run", "required":true}

eval "$COMMAND"
