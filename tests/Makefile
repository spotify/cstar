
all: setup test teardown


test:
	docker exec -t tests_cstar_1 bash -c "cd /usr/src/app/cstar/ && behave tests/features -D SEED_HOST=cassandra-10 --no-capture --no-capture-stderr --format=plain --junit --junit-directory=/usr/src/app/cstar/tests/results"
# todo: add some verification steps

setup:
	docker-compose up --build -d
	docker-compose ps
	sleep 60
	docker-compose ps

# todo: replace with volume to local git clone
	#docker exec tests_cstar_1 /usr/bin/pip3 install git+https://github.com/spotify/cstar.git
	docker exec tests_cstar_1 /usr/bin/pip3 install behave
	docker exec tests_cstar_1 bash -c "cd /usr/src/app/cstar/ && pwd && ls -lrt && /usr/bin/python3 setup.py install"

# verify sshd and open CQL ports
	docker exec -t tests_cassandra-00_1 bash -c 'pgrep sshd 2>&1 > /dev/null && echo "SSHd is running" || echo "SSHd is not running"'
	docker exec -t tests_cassandra-00_1 bash -c 'ps aux | grep cassandra | grep -v grep 2>&1 > /dev/null && echo "Cassandra is running" || echo "Cassandra is not running"'

	docker exec -t tests_cassandra-01_1 bash -c 'pgrep sshd 2>&1 > /dev/null && echo "SSHd is running" || echo "SSHd is not running"'
	docker exec -t tests_cassandra-01_1 bash -c 'ps aux | grep cassandra | grep -v grep 2>&1 > /dev/null && echo "Cassandra is running" || echo "Cassandra is not running"'

	docker exec -t tests_cassandra-02_1 bash -c 'pgrep sshd 2>&1 > /dev/null && echo "SSHd is running" || echo "SSHd is not running"'
	docker exec -t tests_cassandra-02_1 bash -c 'ps aux | grep cassandra | grep -v grep 2>&1 > /dev/null && echo "Cassandra is running" || echo "Cassandra is not running"'

	docker exec -t tests_cassandra-03_1 bash -c 'pgrep sshd 2>&1 > /dev/null && echo "SSHd is running" || echo "SSHd is not running"'
	docker exec -t tests_cassandra-03_1 bash -c 'ps aux | grep cassandra | grep -v grep 2>&1 > /dev/null && echo "Cassandra is running" || echo "Cassandra is not running"'

	docker exec -t tests_cassandra-10_1 bash -c 'pgrep sshd 2>&1 > /dev/null && echo "SSHd is running" || echo "SSHd is not running"'
	docker exec -t tests_cassandra-10_1 bash -c 'ps aux | grep cassandra | grep -v grep 2>&1 > /dev/null && echo "Cassandra is running" || echo "Cassandra is not running"'

	docker exec -t tests_cassandra-11_1 bash -c 'pgrep sshd 2>&1 > /dev/null && echo "SSHd is running" || echo "SSHd is not running"'
	docker exec -t tests_cassandra-11_1 bash -c 'ps aux | grep cassandra | grep -v grep 2>&1 > /dev/null && echo "Cassandra is running" || echo "Cassandra is not running"'

teardown:
	docker-compose down
