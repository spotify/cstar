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

from collections import namedtuple
import hashlib

from cstar.exceptions import UnknownHost

Host = namedtuple("Host", "fqdn ip dc cluster rack is_up host_id")
Host.__hash__ = lambda self: self.ip.__hash__()

Datacenter = namedtuple("Datacenter", "cluster dc")

def _host_eq(self, other):
    if hasattr(other, 'ip'):
        return self.ip == other.ip
    return self.ip == other


Host.__eq__ = _host_eq


class Topology(object):
    """An immutable type describing a topology of C* clusters. Contains utility methods for creating filtered
    subtopologies.

    This type is meant to be used without mutating it."""

    def __init__(self, hosts=[]):
        self.hosts = set(hosts)
        self.hosts_by_ip = {host.ip:host for host in self.hosts}

    def first(self):
        """Return first host in topology (by cluster position)"""
        if not self:
            return None
        return sorted(self.hosts, key=lambda x: x.rack)[0]

    def get_host(self, ip):
        for h in self:
            if h.ip == ip:
                return h
        raise UnknownHost(ip)

    def with_cluster(self, cluster):
        """Return subtopology filtered on cluster"""
        return Topology(filter(lambda host: cluster == host.cluster, self.hosts))

    def with_dc(self, cluster, dc):
        """Return subtopology filtered on pair cluster/dc for uniqness concerns"""
        return Topology(filter(lambda host: dc == host.dc and cluster == host.cluster, self.hosts))

    def with_dc_or_distinct_cluster(self, hosts=None):
        """Return subtopology with DCs of passed hosts or DCs in a distinct cluster"""
        all_dcs = self.get_dcs()
        running_dcs = self.get_dcs(hosts)
        clusters = set(cluster_dc.cluster for cluster_dc in running_dcs)
        return Topology(filter(lambda host: Datacenter(host.cluster, host.dc) in running_dcs
                                      or host.cluster not in clusters, self.hosts))

    def with_dc_filter(self, dc):
        """Retrun subtopology filtered on dc only dc is used,
           if clusters share a DC name, all clusters will be considered
           Prefer 'with_dc()' function"""
        return Topology(filter(lambda host: dc == host.dc, self.hosts))

    def without_dcs(self, dcs):
        """Return subtopology with specific DCs filtered out"""
        return Topology(filter(lambda host: Datacenter(host.cluster, host.dc) not in dcs, self.hosts))

    def without_host(self, host):
        """Return subtopology without specified host"""
        return Topology(self.hosts - set((host,)))

    def without_hosts(self, hosts):
        """Return subtopology without specified hosts"""
        return Topology(self.hosts - set(hosts))

    def get_clusters(self):
        """Returns a set containing all the individual clusters in this topology"""
        return set(host.cluster for host in self.hosts)

    def get_dcs(self, hosts=None):
        """Returns a set containing all the individual data centers for given hosts"""
        subtopology = self if hosts is None else Topology(hosts)
        return set(Datacenter(host.cluster,host.dc) for host in subtopology.hosts)

    def get_down(self):
        """Returns a set of all nodes that are down in this topology"""
        return Topology(node for node in self if not node.is_up)

    def get_up(self):
        """Returns a set of all nodes that are up in this topology"""
        return Topology(node for node in self if node.is_up)
    
    def get_hash(self):
        """Computes a hash for the current topology of the cluster"""
        return hashlib.md5(next(iter(self.get_clusters())).encode('utf-8') + '-'.join(sorted(host.host_id for host in set(self.hosts))).encode('utf-8')).hexdigest()

    def __contains__(self, o):
        return self.hosts.__contains__(o)

    def __str__(self):
        return " ".join(host.fqdn for host in self.hosts)

    def __or__(self, other):
        return Topology(self.hosts | other.hosts)

    def __len__(self):
        return len(self.hosts)

    def __iter__(self):
        return iter(self.hosts)

    def __repr__(self):
        return "Topology(%s)" % (self.hosts,)

    def __eq__(self, other):
        return self.hosts.__eq__(other.hosts)
