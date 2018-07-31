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

from cstar.exceptions import UnknownHost

Host = namedtuple("Host", "fqdn ip dc cluster token is_up")
Host.__hash__ = lambda self: self.ip.__hash__()


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

    def first(self):
        """Return first host in topology (by cluster position)"""
        if not self:
            return None
        return sorted(self.hosts, key=lambda x: x.token)[0]

    def get_host(self, ip):
        for h in self:
            if h.ip == ip:
                return h
        raise UnknownHost(ip)

    def with_cluster(self, cluster):
        """Return subtopology filtered on cluster"""
        return Topology(filter(lambda host: cluster == host.cluster, self.hosts))

    def with_dc(self, dc):
        """Return subtopology filtered on dc"""
        return Topology(filter(lambda host: dc == host.dc, self.hosts))

    def without_host(self, host):
        """Return subtopology without specified host"""
        return Topology(self.hosts - set((host,)))

    def without_hosts(self, hosts):
        """Return subtopology without specified hosts"""
        return Topology(self.hosts - set(hosts))

    def get_clusters(self):
        """Returns a set containing all the individual clusters in this topology"""
        return set(host.cluster for host in self.hosts)

    def get_dcs(self):
        """Returns a set containing all the individual data centers in this topology"""
        return set(host.dc for host in self.hosts)

    def get_down(self):
        """Returns a set of all nodes that are down in this topology"""
        return Topology(node for node in self if not node.is_up)

    def get_up(self):
        """Returns a set of all nodes that are up in this topology"""
        return Topology(node for node in self if node.is_up)

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
