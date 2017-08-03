# This Makefile is for legacy integration tests.
# Most new tests should be implemented using ansible-test.
# Existing tests are slowly being migrated to ansible-test.
# See: http://docs.ansible.com/ansible/dev_guide/testing_integration.html

TEST_DIR ?= ~/ansible_testing
INVENTORY ?= inventory
VARS_FILE ?= integration_config.yml

# Create a semi-random string for use when testing cloud-based resources
ifndef CLOUD_RESOURCE_PREFIX
CLOUD_RESOURCE_PREFIX := $(shell python -c "import string,random; print('ansible-testing-' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8)));")
endif

CREDENTIALS_FILE ?= credentials.yml
# If credentials.yml exists, use it
ifneq ("$(wildcard $(CREDENTIALS_FILE))","")
CREDENTIALS_ARG = -e @$(CREDENTIALS_FILE)
else
CREDENTIALS_ARG =
endif

# http://unix.stackexchange.com/questions/30091/fix-or-alternative-for-mktemp-in-os-x
MYTMPDIR = $(shell mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')

VAULT_PASSWORD_FILE = vault-password

CONSUL_RUNNING := $(shell python consul_running.py)
EUID := $(shell id -u -r)

UNAME := $(shell uname | tr '[:upper:]' '[:lower:]')

setup:
	rm -rf $(TEST_DIR)
	mkdir -p $(TEST_DIR)

cloud: amazon rackspace azure

cloud_cleanup: amazon_cleanup rackspace_cleanup

amazon_cleanup:
	python cleanup_ec2.py -y --match="^$(CLOUD_RESOURCE_PREFIX)"

azure_cleanup:
	python cleanup_azure.py -y --match="^$(CLOUD_RESOURCE_PREFIX)"

gce_setup:
	python setup_gce.py "$(CLOUD_RESOURCE_PREFIX)"

gce_cleanup:
	python cleanup_gce.py -y --match="^$(CLOUD_RESOURCE_PREFIX)"

rackspace_cleanup:
	python cleanup_rax.py -y --match="^$(CLOUD_RESOURCE_PREFIX)"

$(CREDENTIALS_FILE):
	@echo "No credentials file found.  A file named '$(CREDENTIALS_FILE)' is needed to provide credentials needed to run cloud tests.  See sample 'credentials.template' file."
	@exit 1

amazon: $(CREDENTIALS_FILE)
	ANSIBLE_HOST_KEY_CHECKING=False ANSIBLE_SSH_PIPELINING=no BOTO_CONFIG=/dev/null ansible-playbook amazon.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -e "resource_prefix=$(CLOUD_RESOURCE_PREFIX)" -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    CLOUD_RESOURCE_PREFIX="$(CLOUD_RESOURCE_PREFIX)" make amazon_cleanup ; \
    exit $$RC;

azure: $(CREDENTIALS_FILE)
	ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook azure.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -e "resource_prefix=$(CLOUD_RESOURCE_PREFIX)" -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    CLOUD_RESOURCE_PREFIX="$(CLOUD_RESOURCE_PREFIX)" make azure_cleanup ; \
    exit $$RC;

gce: $(CREDENTIALS_FILE)
	CLOUD_RESOURCE_PREFIX="$(CLOUD_RESOURCE_PREFIX)" make gce_setup ; \
    ansible-playbook gce.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -e "resource_prefix=$(CLOUD_RESOURCE_PREFIX)" -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    CLOUD_RESOURCE_PREFIX="$(CLOUD_RESOURCE_PREFIX)" make gce_cleanup ; \
    exit $$RC;

rackspace: $(CREDENTIALS_FILE)
	ansible-playbook rackspace.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -e "resource_prefix=$(CLOUD_RESOURCE_PREFIX)" -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    CLOUD_RESOURCE_PREFIX="$(CLOUD_RESOURCE_PREFIX)" make rackspace_cleanup ; \
    exit $$RC;

exoscale:
	ansible-playbook exoscale.yml -i $(INVENTORY) -e @$(VARS_FILE) -v $(TEST_FLAGS) ; \
	RC=$$? ; \
	exit $$RC;

jenkins:
	ansible-playbook jenkins.yml -i $(INVENTORY) -e @$(VARS_FILE) -v $(TEST_FLAGS) ; \
	RC=$$? ; \
	exit $$RC;

cloudflare: $(CREDENTIALS_FILE)
	ansible-playbook cloudflare.yml -i $(INVENTORY) -e @$(VARS_FILE) -e @$(CREDENTIALS_FILE) -e "resource_prefix=$(CLOUD_RESOURCE_PREFIX)" -v $(TEST_FLAGS) ; \
	RC=$$? ; \
	exit $$RC;

cloudscale:
	ansible-playbook cloudscale.yml -i $(INVENTORY) -e @$(VARS_FILE) -e "resource_prefix=$(CLOUD_RESOURCE_PREFIX)" -v $(TEST_FLAGS) ; \
	RC=$$? ; \
	exit $$RC;

$(CONSUL_RUNNING):

consul:
ifeq ($(CONSUL_RUNNING), True)
	ansible-playbook -i $(INVENTORY) consul.yml ; \
	ansible-playbook -i ../../contrib/inventory/consul_io.py consul_inventory.yml
else
	@echo "Consul agent is not running locally. To run a cluster locally see http://github.com/sgargan/consul-vagrant"
endif

test_galaxy: test_galaxy_spec test_galaxy_yaml test_galaxy_git

test_galaxy_spec: setup
	mytmpdir=$(MYTMPDIR) ; \
	ansible-galaxy install -r galaxy_rolesfile -p $$mytmpdir/roles -vvvv ; \
    cp galaxy_playbook.yml $$mytmpdir ; \
    ansible-playbook -i $(INVENTORY) $$mytmpdir/galaxy_playbook.yml -e @$(VARS_FILE) -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    rm -rf $$mytmpdir ; \
    exit $$RC

test_galaxy_yaml: setup
	mytmpdir=$(MYTMPDIR) ; \
	ansible-galaxy install -r galaxy_roles.yml -p $$mytmpdir/roles -vvvv; \
    cp galaxy_playbook.yml $$mytmpdir ; \
    ansible-playbook -i $(INVENTORY) $$mytmpdir/galaxy_playbook.yml -e @$(VARS_FILE) -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    rm -rf $$mytmpdir ; \
    exit $$RC

test_galaxy_git: setup
	mytmpdir=$(MYTMPDIR) ; \
	ansible-galaxy install git+https://bitbucket.org/willthames/git-ansible-galaxy,v1.6 -p $$mytmpdir/roles -vvvv; \
    cp galaxy_playbook_git.yml $$mytmpdir ; \
    ansible-playbook -i $(INVENTORY) $$mytmpdir/galaxy_playbook_git.yml -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    rm -rf $$mytmpdir ; \
    exit $$RC
