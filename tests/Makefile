
all: setup test teardown
	

test:
	docker exec -t tests_cstar_1 cstar run --command='nodetool status' --seed-host cassandra-0 --ssh-password=root
# todo: add some verification steps

setup:
	docker-compose up --build -d
	docker-compose ps
	sleep 20

# todo: replace with volume to local git clone
	docker exec tests_cstar_1 /usr/bin/pip3 install git+https://github.com/spotify/cstar.git

# verify sshd and open CQL ports
	docker exec -t tests_cassandra-0_1 pgrep sshd
	docker exec -t tests_cassandra-1_1 pgrep sshd
#	docker exec -t tests_cassandra-2_1 pgrep sshd
#	docker exec -t tests_cassandra-3_1 pgrep sshd

teardown:
	docker-compose down
