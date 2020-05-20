# cstar

[![CircleCI](https://circleci.com/gh/spotify/cstar/tree/master.svg?style=shield)](https://circleci.com/gh/spotify/cstar)
[![License](https://img.shields.io/github/license/spotify/cstar.svg)](LICENSE)

`cstar` is an Apache Cassandra cluster orchestration tool for the command line.

[![asciicast](https://asciinema.org/a/BJkHpAGCdkSXTAhYf7bPVmerz.png)](https://asciinema.org/a/BJkHpAGCdkSXTAhYf7bPVmerz?autoplay=1)

## Why not simply use Ansible or Fabric?

Ansible does not have the primitives required to run things in a topology aware fashion. One could
split the C* cluster into groups that can be safely executed in parallel and run one group at a time.
But unless the job takes almost exactly the same amount of time to run on every host, such a solution
would run with a significantly lower rate of parallelism, not to mention it would be kludgy enough to
be unpleasant to work with.

Unfortunately, Fabric is not thread safe, so the same type of limitations apply. Fabric allows one to
run a job in parallel on many machines, but with similar restrictions as those of Ansible groups.
It’s possibly to use fabric and celery together to do what is needed, but it’s a very complicated
solution.

## Requirements

All involved machines are assumed to be some sort of UNIX-like system like OS X or Linux. The machine
running cstar must have python3, the Cassandra hosts must have a Bourne style shell.

## Installing

You need to have Python3 and run an updated version of pip (9.0.1).

    # pip3 install cstar

It's also possible to install straight from repo. This installs the latest version that may not be pushed to pypi:

    # pip install git+https://github.com/spotify/cstar.git



## Code of conduct

This project adheres to the
[Open Code of Conduct](https://github.com/spotify/code-of-conduct/blob/master/code-of-conduct.md).
By participating, you are expected to honor this code.

## CLI

CStar is run through the cstar command, like so

    # cstar COMMAND [HOST-SPEC] [PARAMETERS]

The HOST-SPEC specifies what nodes to run the script on. There are three ways to specify a the spec:

1. The `--seed-host` switch tells cstar to connect to a specific host and fetch the full ring topology
   from there, and then run the script on all nodes in the cluster. `--seed-host` can be specified
   multiple times, and multiple hosts can be specified as a comma-separated list in order to run a
   script across multiple clusters.
2. The `--host` switch specifies an exact list of hosts to use. `--host` can be specified multiple
   times, and multiple hosts can be specified as a comma-separated list.
3. The `--host-file` switch points to a file name containing a newline separated list of hosts. This
   can be used together with process substitution, e.g. `--host-file <(dig -t srv ...)`

The command is the name of a script located in either `/usr/lib/cstar/commands` or in
`~/.cstar/commands`. This script will be uploaded to all nodes in the cluster and executed. File suffixes
are stripped. The requirements of the script are described below. Cstar comes pre-packaged with one script file
called ``run`` which takes a single parameter ``--command`` - see examples below.

Some additional switches to control cstar:

* One can override the parallelism specified in a script by setting the switches
  `--cluster-parallel`, `--dc-parallel` and `--strategy`.

There are two special case invocations:

* One can skip the script name and instead use the `continue` command to specify a previously halted job
  to resume.

* One can skip the script name and instead use the `cleanup-jobs`. See [Cleaning up old jobs](#Cleaning-up-old-jobs).

* If you need to access the remote cluster with a specific username, add `--ssh-username=remote_username` to your cstar command line. A private key file can also be specified using `--ssh-identity-file=my_key_file.pem`.

* To use plain text authentication, please add `--ssh-password=my_password` to the command line.

* In order to run the command first on a single node and then stop execution to verify everything worked as expected, add the following flag to your command line : `--stop-after=1`. cstar will stop after the first node executed the command and print out the appropriate resume command to continue the execution when ready : `cstar continue <JOB_ID>`

A script file can specify additional parameters.

## Command syntax

In order to run a command, it is first uploaded to the relevant host, and then executed from there.

Commands can be written in any scripting language in which the hash symbol starts a line comment, e.g.
shell-script, python, perl or ruby.

The first line must be a valid shebang. After that, commented lines containing key value pairs may
be used to override how the script is parallelised as well as providing additional parameters for
the script, e.g. `# C* dc-parallel: true`

The possible keys are:

`cluster-parallel`, can the script be run on multiple clusters in parallel. Default value is `true`.  

`dc-parallel`, can the script be run on multiple data centers in the same cluster in parallel. Default value is `false`.

`strategy`, how many nodes within one data center can the script be run on. Default is `topology`.
Can be one of:

* `one`, only one node per data center
* `topology`, inspect topology and run on as many nodes as the topology allows
* `all`, can be run on all nodes at once

`description`, specifies a description for the script used in the help message.

`argument`, specifies an additional input parameter for the script, as well as a help text and an
optional default value.

## Job output

Cstar automatically saves the job status to file during operation.

Standard output, standard error and exit status of each command run against a Cassandra host is
saved locally on machine where cstar is running. They are available under the users home directory in
`.cstar/jobs/JOB_ID/HOSTNAME`

## How jobs are run

When a new cstar job is created, it is assigned an id. (It's a UUID)

Cstar stores intermediate job output in the directory
`~/.cstar/remote_jobs/<JOB_ID>`. This directory contains files with the stdout, stderr and PID of the
script, and once it finishes, it will also contain a file with the exit status of the script.

Once the job finishes, these files will be moved over to the original host and put in the directory `~/.cstar/jobs/<JOB_ID>/<REMOTE_HOST_NAME>`.

Cstar jobs are run nohuped, this means that even if the ssh connection is severed, the job will proceed.
In order to kill a cstar script invocation on a specific host, you will need ssh to the host and kill
the proccess.

If a job is halted half-way, either by pressing `^C` or by using the `--stop-after` parameter, it can be
restarted using `cstar continue <JOB_ID>`. If the script was finished or already running when cstar
shut down, it will not be rerun.

## Cleaning up old jobs

Even on successful completion, the output of a cstar job is not deleted. This means it's easy to check
what the output of a script was after it completed. The downside of this is that you can get a lot of
data lying around in `~/.cstar/jobs`. In order to clean things up, you can use
`cstar cleanup-jobs`. By default it will remove all jobs older than one week. You can override the
maximum age of a job before it's deleted by using the `--max-job-age` parameter.

## Examples

    # cstar run --command='service cassandra restart' --seed-host some-host

Explanation: Run the local cli command ``service cassandra restart`` on a cluster. If necessary, add ``sudo`` to the
command.

    # cstar puppet-upgrade-cassandra --seed-host some-host --puppet-branch=cass-2.2-upgrade

Explanation: Run the command puppet-upgrade-cassandra on a cluster. The puppet-upgrade-cassandra
command expects a parameter, the puppet branch to run in order to perform the Cassandra upgrade. See the
puppet-upgrade-cassandra example [below](#Example-script-file).

    # cstar puppet-upgrade-cassandra --help

Explanation: Show help for the puppet-upgrade-cassandra command. This includes documentation for any
additional command-specific switches for the puppet-upgrade-cassandra command.

    # cstar continue 90642c11-4714-44c4-a13a-94b86f09e3bb

Explanation: Resume previously created job with job id 90642c11-4714-44c4-a13a-94b86f09e3bb.
The job id is the first line written on any executed job.

## Example script file

This is an example script file that would saved to `~/.cstar/commands/puppet-upgrade-cassandra.sh`. It upgrades a
Cassandra cluster by running puppet on a different branch, then restarting the node, then upgrading the sstables.

    # !/usr/bin/env bash
    # C* cluster-parallel: true                                                                                                                                                                                    
    # C* dc-parallel: true                                                                                                                                                                                         
    # C* strategy: topology                                                                                                                                                                                        
    # C* description: Upgrade one or more clusters by switching to a different puppet branch                                                                                                                       
    # C* argument: {"option":"--snapshot-name", "name":"SNAPSHOT_NAME", "description":"Name of pre-upgrade snapshot", "default":"preupgrade"}                                                                      
    # C* argument: {"option":"--puppet-branch", "name":"PUPPET_BRANCH", "description":"Name of puppet branch to switch to", "required":true}                                                                       

    nodetool snapshot -t $SNAPSHOT_NAME
    sudo puppet --branch $PUPPET_BRANCH
    sudo service cassandra restart
    nodetool upgradesstables
