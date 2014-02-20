all: non_destructive destructive # amazon rackspace

non_destructive:
	ansible-playbook non_destructive.yml -i inventory -e @integration_config.yml -v $(TEST_FLAGS)

destructive:
	ansible-playbook destructive.yml -i inventory -e @integration_config.yml -v $(TEST_FLAGS)

