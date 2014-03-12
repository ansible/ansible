INVENTORY ?= inventory
VARS_FILE ?= integration_config.yml

all: non_destructive destructive check_mode test_hash

non_destructive:
	ansible-playbook non_destructive.yml -i $(INVENTORY) -e @$(VARS_FILE) -v $(TEST_FLAGS)

destructive:
	ansible-playbook destructive.yml -i $(INVENTORY) -e @$(VARS_FILE) -v $(TEST_FLAGS)

check_mode:
	ansible-playbook check_mode.yml -i $(INVENTORY) -e @$(VARS_FILE) -v --check $(TEST_FLAGS)

test_hash:
	ANSIBLE_HASH_BEHAVIOUR=replace ansible-playbook test_hash.yml -i $(INVENTORY) -v -e '{"test_hash":{"extra_args":"this is an extra arg"}}'
	ANSIBLE_HASH_BEHAVIOUR=merge ansible-playbook test_hash.yml -i $(INVENTORY) -v -e '{"test_hash":{"extra_args":"this is an extra arg"}}'

cloud: amazon rackspace

cloud_cleanup: amazon_cleanup rackspace_cleanup

amazon_cleanup:
	python cleanup_ec2.py -y

rackspace_cleanup:
	@echo "FIXME - cleanup_rax.py not yet implemented"
	@#python cleanup_rax.py -y

credentials.yml:
	@echo "No credentials.yml file found.  A file named 'credentials.yml' is needed to provide credentials needed to run cloud tests.  See sample 'credentials.template' file."
	@exit 1

amazon: credentials.yml
	ansible-playbook amazon.yml -i $(INVENTORY) -e @$(VARS_FILE) -e @credentials.yml -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    make amazon_cleanup ; \
    exit $$RC;

rackspace: credentials.yml
	ansible-playbook rackspace.yml -i $(INVENTORY) -e @$(VARS_FILE) -e @credentials.yml -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    make rackspace_cleanup ; \
    exit $$RC;
