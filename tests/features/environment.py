import os

from behave import use_fixture

def before_scenario(context, scenario):
    context.seed_node = context.config.userdata.get("SEED_HOST")
    context.cstar_job_dir = os.path.join(os.path.expanduser("~"), ".cstar", "jobs")
    if context.seed_node is None:
        raise Exception("Seed host of the test cluster should be provided using: behave -D SEED_HOST=<host_ip>")