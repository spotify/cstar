# Copyright 2017 Spotify AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import queue
import time
import socket
import os
import threading
import functools

import cstar.remote
import cstar.endpoint_mapping
import cstar.topology
import cstar.nodetoolparser
import cstar.state
import cstar.strategy
import cstar.jobrunner
import cstar.jobprinter
import cstar.jobwriter
from cstar.exceptions import BadSSHHost, NoHostsSpecified, HostIsDown, \
    NoDefaultKeyspace, UnknownHost, FailedExecution
from cstar.output import msg, debug, emph, info, error

MAX_ATTEMPTS = 3


@functools.lru_cache(None)
def ip_lookup(name):
    return socket.gethostbyname(name)


class Job(object):
    """The class that wires all the business logic together.

    Currently polluted by some business logic of it's own. The job handling and some small snippets of code
    should be moved out of this class.
    """

    def __init__(self):
        self._connections = {}
        self.results = queue.Queue()
        self.handled_finished_jobs = set()
        self.state = None
        self.command = None
        self.job_id = None
        self.timeout = None
        self.env = None
        self.errors = []
        self.do_loop = False
        self.job_runner = None
        self.key_space = None
        self.output_directory = None
        self.is_preheated = False
        self.sleep_on_new_runner = None
        self.sleep_after_done = None
        self.ssh_username = None
        self.ssh_password = None
        self.ssh_identity_file = None
        self.jmx_username = None
        self.jmx_password = None
        self.hosts_variables = dict()
        self.returned_jobs = list()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

        if exc_type:
            if exc_type == NoHostsSpecified:
                error("No hosts specified")
            elif exc_type in [BadSSHHost, NoDefaultKeyspace, HostIsDown, UnknownHost]:
                error(exc_value)


    def get_cluster_topology(self, seed_nodes):
        count = 0
        tried_hosts = []
        for host in seed_nodes:
            tried_hosts.append(host)
            conn = self._connection(host)

            describe_res = self.run_nodetool(conn, "describecluster")
            topology_res = self.run_nodetool(conn, "ring")

            if (describe_res.status == 0) and (topology_res.status == 0):
                cluster_name = cstar.nodetoolparser.parse_describe_cluster(describe_res.out)
                topology = cstar.nodetoolparser.parse_nodetool_ring(topology_res.out, cluster_name, self.reverse_dns_preheat)
                return topology

            count += 1
            if count >= MAX_ATTEMPTS:
                break
        raise HostIsDown("Could not find any working host while fetching topology. Is Cassandra actually running? Tried the following hosts:",
                         ", ".join(tried_hosts))

    def reverse_dns_preheat(self, ips):
        if self.is_preheated:
            return
        self.is_preheated = True

        def get_host_by_addr(ip):
            try:
                socket.gethostbyaddr(ip)
            except socket.herror:
                pass

        def create_lookup_thread(ip):
            return threading.Thread(target=lambda: get_host_by_addr(ip))

        print("Preheating DNS cache")
        threads = [create_lookup_thread(ip) for ip in ips]

        for thread in threads:
            thread.start()

        for thread in threads:
            # Don't wait around forever for slow DNS
            thread.join(1.0)
        print("Preheating done")

    def get_keyspaces(self, conn):
        cfstats_output = self.run_nodetool(conn, *("cfstats", "|", "grep", "Keyspace"))
        return cstar.nodetoolparser.extract_keyspaces_from_cfstats(cfstats_output.out)

    def get_endpoint_mapping(self, topology):
        count = 0
        tried_hosts = []
        for host in topology.get_up():
            tried_hosts.append(host)
            conn = self._connection(host)

            mappings = []

            if self.key_space:
                keyspaces = [self.key_space]
            else:
                keyspaces = self.get_keyspaces(conn)
            has_error = True
            for keyspace in keyspaces:
                if not keyspace in ['system', 'system_schema']:
                    debug("Fetching endpoint mapping for keyspace", keyspace)
                    res = self.run_nodetool(conn, *("describering", keyspace))
                    has_error = False

                    if res.status != 0 and not keyspace.startswith("system"):
                        has_error = True
                        break
                    describering = cstar.nodetoolparser.parse_nodetool_describering(res.out)
                    range_mapping = cstar.nodetoolparser.convert_describering_to_range_mapping(describering)
                    mappings.append(cstar.endpoint_mapping.parse(range_mapping, topology, lookup=ip_lookup))
                    
            if not has_error:
                return cstar.endpoint_mapping.merge(mappings)

            count += 1
            if count >= MAX_ATTEMPTS:
                break
        raise HostIsDown("Could not find any working host while fetching endpoint mapping. Tried the following hosts:",
                         ", ".join(host.fqdn for host in tried_hosts))

    def run_nodetool(self, conn, *cmds):
        if self.jmx_username and self.jmx_password:
            return conn.run(("nodetool", "-u", self.jmx_username, "-pw", self.jmx_password, *cmds))
        else:
            return conn.run(("nodetool", *cmds))

    def setup(self, hosts, seeds, command, job_id, strategy, cluster_parallel, dc_parallel, job_runner,
              max_concurrency, timeout, env, stop_after, key_space, output_directory,
              ignore_down_nodes, dc_filter,
              sleep_on_new_runner, sleep_after_done,
              ssh_username, ssh_password, ssh_identity_file, ssh_lib,
              jmx_username, jmx_password, hosts_variables):

        msg("Starting setup")

        msg("Strategy:", cstar.strategy.serialize(strategy))
        msg("DC parallel:", dc_parallel)
        msg("Cluster parallel:", cluster_parallel)

        self.command = command
        self.job_id = job_id
        self.timeout = timeout
        self.env = env
        self.job_runner = job_runner
        self.key_space = key_space
        self.output_directory = output_directory or os.path.expanduser("~/.cstar/jobs/" + job_id)
        self.sleep_on_new_runner = sleep_on_new_runner
        self.sleep_after_done = sleep_after_done
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.ssh_identity_file = ssh_identity_file
        self.ssh_lib = ssh_lib
        self.jmx_username = jmx_username
        self.jmx_password = jmx_password
        self.hosts_variables = hosts_variables
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

        msg("Loading cluster topology")
        if seeds:
            current_topology = cstar.topology.Topology([])
            for seed in seeds:
                current_topology = current_topology | self.get_cluster_topology((seed,))
            original_topology = current_topology
            if dc_filter:
                original_topology = original_topology.with_dc(dc_filter)
        else:
            current_topology = cstar.topology.Topology()
            hosts_ip_set = set(socket.gethostbyname(host) for host in hosts)
            for raw_host in hosts:
                host = socket.gethostbyname(raw_host)
                if host in current_topology:
                    continue
                current_topology = current_topology | self.get_cluster_topology((host,))
            original_topology = cstar.topology.Topology(host for host in current_topology if host.ip in hosts_ip_set)
        msg("Done loading cluster topology")

        debug("Run on hosts", original_topology)
        debug("in topology", current_topology)

        msg("Generating endpoint mapping")
        if strategy is cstar.strategy.Strategy.TOPOLOGY:
            endpoint_mapping = self.get_endpoint_mapping(current_topology)
            msg("Done generating endpoint mapping")
        else:
            endpoint_mapping = None
            msg("Skipping endpoint mapping because of selected strategy")

        self.state = cstar.state.State(original_topology, strategy, endpoint_mapping, cluster_parallel, dc_parallel,
                                       max_concurrency, current_topology=current_topology, stop_after=stop_after,
                                       ignore_down_nodes=ignore_down_nodes)
        msg("Setup done")

    def update_current_topology(self, skip_nodes=()):
        new_topology = cstar.topology.Topology()
        for cluster in self.state.original_topology.get_clusters():
            seeds = self.state.get_idle().with_cluster(cluster).without_hosts(skip_nodes).get_up()
            # When using the all strategy, all nodes go to running, so we need to pick some node
            seeds = seeds or self.state.current_topology.with_cluster(cluster).get_up()
            new_topology = new_topology | self.get_cluster_topology(seeds)
        self.state = self.state.with_topology(new_topology)

    def wait_for_node_to_return(self, nodes=()):
        """Wait until node returns"""
        while True:
            try:
                self.update_current_topology(nodes)

                if self.state.is_healthy():
                    break
            except BadSSHHost as e:
                # If the instance used to poll cluster health is down it probably means that machine is rebooting
                # State is then NOT healthy, so continue waiting...
                debug("SSH to %s failed, instance down?" % (node, ), e)
            cstar.jobprinter.print_progress(self.state.original_topology,
                                            self.state.progress,
                                            self.state.current_topology.get_down())
            time.sleep(5)

    def resume(self):
        self.update_current_topology()
        self.resume_on_running_hosts()
        self.run()

    def run(self):
        self.do_loop = True

        cstar.jobwriter.write(self)
        if not self.state.is_healthy():
            raise HostIsDown(
                "Can't run job because hosts are down: " + ", ".join(
                    host.fqdn for host in self.state.current_topology.get_down()))

        while self.do_loop:
            self.schedule_all_runnable_jobs()

            if self.state.is_done():
                self.do_loop = False

            self.wait_for_any_job()

        self.wait_for_all_jobs()
        cstar.jobprinter.print_progress(self.state.original_topology,
                                        self.state.progress,
                                        self.state.current_topology.get_down())
        self.print_outcome()

    def resume_on_running_hosts(self):
        for host in self.state.progress.running:
            debug("Resume on host", host.fqdn)
            threading.Thread(target=self.job_runner(self, host, self.ssh_username, self.ssh_password, self.ssh_identity_file, self.ssh_lib),
                             name="cstar %s" % host.fqdn).start()
            time.sleep(self.sleep_on_new_runner)

    def print_outcome(self):
        if self.state.is_done() and not self.errors:
            if len(self.state.progress.done) == self.state.stop_after:
                cstar.jobwriter.write(self)
                msg("Job", self.job_id, "successfully ran on", self.state.stop_after, "hosts.\nTo finish the job, run",
                    emph("cstar continue %s" % (self.job_id,)))

            msg("Job", self.job_id, "finished successfully")
        else:
            msg("Job", self.job_id, "finished with errors.\n"
                                    "%s nodes finished successfully\n"
                                    "%s nodes had errors\n"
                                    "%s nodes didn't start executing"
                                    % (len(self.state.progress.done),
                                       len(self.state.progress.failed),
                                       len(self.state.original_topology) - len(self.state.progress.done) - len(self.state.progress.failed)))

    def wait_for_all_jobs(self):
        while self.state.progress.running:
            host, result = self.results.get()
            self.returned_jobs.append((host, result))
            if self.results.empty():
                self.handle_finished_jobs(self.returned_jobs)
                self.returned_jobs = list()

    def wait_for_any_job(self):
        if self.do_loop:
            host, result = self.results.get(timeout=self.timeout)
            self.returned_jobs.append((host, result))
            while not self.results.empty():
                host, result = self.results.get(timeout=self.timeout)
                self.returned_jobs.append((host, result))
            self.handle_finished_jobs(self.returned_jobs)
            
            self.wait_for_node_to_return(returned_job[0] for returned_job in self.returned_jobs)
            self.returned_jobs = list()

    def handle_finished_jobs(self, finished_jobs):
        debug("Processing ", len(finished_jobs), " finished jobs")
        for finished_job in finished_jobs:
            host = finished_job[0]
            result = finished_job[1]
            if result.status != 0:
                self.errors.append((host, result))
                self.state = self.state.with_failed(host)
                msg("Failure on host", host.fqdn)
                if result.out:
                    msg("stdout:", result.out)
                if result.err:
                    msg("stderr:", result.err)
                self.do_loop = False
            else:
                self.state = self.state.with_done(host)
                info("Host %s finished successfully" % (host.fqdn,))
                if result.out:
                    info("stdout:", result.out, sep="\n")
                if result.err:
                    info("stderr:", result.err)
                if self.sleep_after_done:
                    debug("Sleeping %d seconds..." % self.sleep_after_done)
                    time.sleep(self.sleep_after_done)
        cstar.jobwriter.write(self)
        # Signal the jobrunner that it can delete the remote job files and terminate.
        for finished_job in finished_jobs:
            host, result = finished_job
            self.handled_finished_jobs.add(host)

    def schedule_all_runnable_jobs(self):
        while True:
            next_host = self.state.find_next_host()
            if not next_host:
                if not self.state.progress.running:
                    self.do_loop = False
                break
            if (not next_host.is_up) and self.state.ignore_down_nodes:
                self.state = self.state.with_done(next_host)
            else:
                self.state = self.state.with_running(next_host)
                self.schedule_job(next_host)
            cstar.jobwriter.write(self)
            cstar.jobprinter.print_progress(self.state.original_topology,
                                            self.state.progress,
                                            self.state.current_topology.get_down())

    def schedule_job(self, host):
        debug("Running on host", host.fqdn)
        threading.Thread(target=self.job_runner(self, host, self.ssh_username, self.ssh_password, self.ssh_identity_file, self.ssh_lib, self.get_host_variables(host)),
                         name="cstar %s" % host.fqdn).start()
        time.sleep(self.sleep_on_new_runner)

    def _connection(self, host):
        if host not in self._connections:
            self._connections[host] = cstar.remote.Remote(host, self.ssh_username, self.ssh_password, self.ssh_identity_file, self.ssh_lib, self.get_host_variables(host))
        return self._connections[host]

    def close(self):
        for name, conn in self._connections.items():
            if conn:
                conn.close()
        self._connections = {}

    def get_host_variables(self, host):
        hostname = host
        if type(host).__name__ == "Host":
            hostname = host.fqdn

        host_variables = dict()
        if hostname in self.hosts_variables.keys():
            host_variables = self.hosts_variables[hostname]
        debug("Variables for host {} = {}".format(hostname, host_variables))
        return host_variables
