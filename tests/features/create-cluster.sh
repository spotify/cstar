CASSANDRA_VERSION=$1
mkdir /tmp/cluster-${CASSANDRA_VERSION}
cd /tmp/cluster-${CASSANDRA_VERSION}
tlp-cluster init CSTAR CSTAR-TESTS "cstar integration tests" --instance m5d.large
tlp-cluster up --auto-approve
tlp-cluster build ${CASSANDRA_VERSION} ${CASSANDRA_VERSION}
tlp-cluster use ${CASSANDRA_VERSION}
tlp-cluster install 
tlp-cluster start
