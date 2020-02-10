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

import cstar.output

"""Pretty-print the progress of a cstar job"""


def print_progress(original_topology, progress, down, printer=cstar.output.print_topology):
    def get_status(host):
        if host in progress.done:
            if host in down:
                return "-"
            return '+'
        if host in progress.running:
            if host in down:
                return "/"
            return '*'
        if host in progress.failed:
            if host in down:
                return "X"
            return '!'
        if host in down:
            return ":"
        return '.'
    
    def get_ordered_status(host):
        if host in progress.done:
            return 10
        if host in progress.running:
            return 100
        if host in progress.failed:
            return 50
        return 1000

    lines = [" +  Done, up      * Executing, up      !  Failed, up      . Waiting, up",
             " -  Done, down    / Executing, down    X  Failed, down    : Waiting, down"]

    clusters = sorted(original_topology.get_clusters())
    for cluster in clusters:
        if len(clusters):
            lines.append("Cluster: " + cluster)
        cluster_topology = original_topology.with_cluster(cluster)
        dcs = sorted(cluster_topology.get_dcs())
        for cluster, dc in dcs:
            if len(dcs):
                lines.append("DC: " + dc)
            dc_topology = cluster_topology.with_dc(cluster, dc)
            hosts = sorted(dc_topology, key=lambda x: (get_ordered_status(x), x.rack, x.ip))
            status = "".join([get_status(host) for host in hosts])
            if len(status) >= 6:
                splitStatus = list(chunks(status, 3))
                status = splitStatus[0] + "\n" + splitStatus[1] + "\n" + splitStatus[2]
            lines.append(status)
    lines.append("%d done, %d failed, %d executing" % (len(progress.done), len(progress.failed), len(progress.running)))
    printer("\n".join(lines))

def chunks(l, n):
    """Yield n number of sequential chunks from l."""
    d, r = divmod(len(l), n)
    for i in range(n):
        si = (d+1)*(i if i < r else r) + d*(0 if i < r else i - r)
        yield l[si:si+(d+1 if i < r else d)]
