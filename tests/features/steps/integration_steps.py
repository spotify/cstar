import json
import logging
import os
import re
import uuid
import subprocess
import sys
from contextlib import contextmanager

from behave import given, when, then
import cstar.signalhandler
import cstar.job
import cstar.jobreader
import cstar.command

@when(u'I run "{command}" on the cluster with strategy {strategy}')
def _i_run_nodetool_status_on_the_cluster(context, command, strategy):
    logging.info("Running {} command with strategy {}...".format(command, strategy))
    context.last_job_id = str(uuid.uuid4())
    run_job(context, command, strategy, context.last_job_id)
    assert os.path.isdir(os.path.join(context.cstar_job_dir, context.last_job_id))

@when(u'I run "{command}" and stop it after {stop_after:d} node on the cluster with strategy {strategy}')
def _i_run_nodetool_status_on_the_cluster(context, command, stop_after, strategy):
    logging.info("Running {} command with strategy {}...".format(command, strategy))
    context.last_job_id = str(uuid.uuid4())
    run_job(context, command, strategy, context.last_job_id, stop_after=stop_after)
    assert os.path.isdir(os.path.join(context.cstar_job_dir, context.last_job_id))

@then(u'there are as many nodes reported by nodetool as cstar detected')
def _there_are_x_nodes_reported_by_nodetool(context):
    logging.info("Checking nodetool status reported nodes...")
    _ip_re = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", re.MULTILINE)
    first_node = next(os.walk(os.path.join(context.cstar_job_dir, context.last_job_id)))[1][0]
    nodetool_status_output = ''
    with open(os.path.join(context.cstar_job_dir, context.last_job_id, first_node, "out"), 'r') as f:
        nodetool_status_output = f.read()
    logging.info(nodetool_status_output)
    nodes = re.findall(_ip_re, nodetool_status_output)
    assert len(nodes) == len(context.job.state.current_topology)

@then(u'{nb_nodes:d} node completed the execution')
def _node_completed_the_execution(context, nb_nodes):
    assert len(context.job.state.progress.done) == nb_nodes

@then(u'there are no errors in the job')
def _there_are_no_errors_in_the_job(context):
    assert len(context.job.errors) == 0

@then(u'the job fails')
def _the_job_fails(context):
    assert len(context.job.errors) > 0

@then(u'the output for the first node contains "{expected_output}"')
def _the_output_for_the_first_node_contains(context, expected_output):
    first_node = list(context.job.state.progress.done)[0].fqdn
    with open(os.path.join(os.path.expanduser("~"), ".cstar", "jobs", context.last_job_id, first_node, "out"), "r") as f:
        assert expected_output in f.read()

@when(u'I resume the job')
def _i_resume_the_job(context):
    with cstar.job.Job() as job:
        cstar.jobreader.read(job, context.last_job_id, 0, max_days=30)
        cstar.signalhandler.print_message_and_save_on_sigint(job, job.job_id)
        job.resume()
        context.job = job

@then(u'all nodes complete the execution successfully')
def _all_nodes_complete_the_execution_successfully(context):
    assert len(context.job.state.current_topology) == len(context.job.state.progress.done)

@contextmanager
def stdout_redirected(new_stdout):
    save_stdout = sys.stdout
    sys.stdout = new_stdout
    try:
        yield None
    finally:
        sys.stdout = save_stdout

def run_job(context, command, strategy, job_id, stop_after=None):
    run_command = cstar.command.load("run")
    env = dict()
    env["COMMAND"] = command
    with open("/tmp/cstar_output.out", "w") as f:
        with stdout_redirected(f):
            with cstar.job.Job() as job:
                cstar.signalhandler.print_message_and_save_on_sigint(job, job_id)
                job.setup(
                    seeds=[context.seed_node],
                    command=run_command.file,
                    job_id=job_id,
                    strategy=cstar.strategy.parse(strategy),
                    cluster_parallel=False,
                    dc_parallel=False,
                    max_concurrency=None,
                    timeout=None,
                    env=env,
                    stop_after=stop_after,
                    job_runner=cstar.jobrunner.RemoteJobRunner,
                    key_space=None,
                    output_directory=None,
                    ignore_down_nodes=False,
                    dc_filter=None,
                    sleep_on_new_runner=0,
                    sleep_after_done=0,
                    ssh_username=None,
                    ssh_password=None,
                    ssh_identity_file=None,
                    ssh_lib="paramiko",
                    jmx_username=None,
                    jmx_password=None,
                    hosts=None,
                    hosts_variables=dict())
                job.run()
                context.job = job