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

all: other non_destructive destructive

other: test_test_infra parsing test_var_precedence unicode test_templating_settings environment test_connection test_async_conditional includes blocks pull_run pull_no_127 pull_limit_inventory check_mode test_hash test_handlers test_group_by test_vault test_tags test_lookup_paths no_log test_gathering_facts test_binary_modules_posix test_hosts_field args

test_test_infra:
	(cd targets/test_infra && ./runme.sh $(TEST_FLAGS))

setup:
	rm -rf $(TEST_DIR)
	mkdir -p $(TEST_DIR)

parsing:
	(cd targets/parsing && ./runme.sh $(TEST_FLAGS))

includes:
	(cd targets/includes && ./runme.sh $(TEST_FLAGS))

pull_run:
	(cd targets/pull_run && ./runme.sh $(TEST_FLAGS))

pull_no_127:
	(cd targets/pull_no_127 && ./runme.sh $(TEST_FLAGS))

pull_limit_inventory:
	(cd targets/pull_limit_inventory && ./runme.sh $(TEST_FLAGS))

unicode:
	(cd targets/unicode && ./runme.sh $(TEST_FLAGS))

test_templating_settings:
	(cd targets/templating_settings && ./runme.sh $(TEST_FLAGS))

test_gathering_facts:
	(cd targets/gathering_facts && ./runme.sh $(TEST_FLAGS))

environment:
	(cd targets/environment && ./runme.sh $(TEST_FLAGS))

non_destructive: setup
	ansible-playbook non_destructive.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

# For our Docker images, which identify themselves with "ENV container=docker", automatically run the test_async target.
# Otherwise, skip it, since we don't know if local ssh is available. You can always run the test_async target manually.
ifeq ($(container),docker)
test_async_conditional: test_async
else
test_async_conditional:
endif

# For our Docker images, which identify themselves with "ENV container=docker", use the test_docker inventory group.
# Otherwise use the test_default inventory group, which runs fewer tests, but should work on any system.
ifeq ($(container),docker)
TEST_CONNECTION_FILTER := 'test_docker'
else ifeq ($(container),freebsd)
TEST_CONNECTION_FILTER := 'test_freebsd'
else
TEST_CONNECTION_FILTER := 'test_default'
endif

# Skip connection plugins which require root when not running as root.
ifneq ($(EUID),0)
TEST_CONNECTION_FILTER += !chroot
endif

test_connection:
	(cd targets/connection_posix && ./runme.sh -l '$(TEST_CONNECTION_FILTER)' $(TEST_FLAGS))

test_connection_winrm:
	(cd targets/connection_winrm && ./runme.sh $(TEST_FLAGS))

destructive: setup
	ansible-playbook destructive.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

check_mode:
	(cd targets/check_mode && ./runme.sh $(TEST_FLAGS))

test_group_by:
	(cd targets/group_by && ./runme.sh $(TEST_FLAGS))

test_handlers:
	(cd targets/handlers && ./runme.sh $(TEST_FLAGS))

test_hash:
	(cd targets/hash && ./runme.sh $(TEST_FLAGS))

test_var_precedence:
	(cd targets/var_precedence && ./runme.sh $(TEST_FLAGS))

test_vault:
	(cd targets/vault && ./runme.sh $(TEST_FLAGS))

# test_delegate_to does not work unless we have permission to ssh to localhost.
# Would take some more effort on our test systems to implement that -- probably
# the test node should create an ssh public-private key pair that allows the
# root user on a node to ssh to itself.  Until then, this is not in make all.
# Have to run it manually.  Ordinary users should be able to run this test as
# long as they have permissions to login to their local machine via ssh.
test_delegate_to:
	(cd targets/delegate_to && ./runme.sh $(TEST_FLAGS))

# Split Windows CI targets to support parallel execution.
# Targets should be balanced to have similar run times.
ci_win: ci_win1 ci_win2 ci_win3
ci_win1: test_win_group1
ci_win2: test_win_group2 test_binary_modules_winrm
ci_win3: test_win_group3 test_connection_winrm

test_winrm: test_win_group1 test_win_group2 test_win_group3

test_win_group1:
	ansible-playbook test_win_group1.yml -i inventory.winrm -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

test_win_group2:
	ansible-playbook test_win_group2.yml -i inventory.winrm -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

test_win_group3:
	ansible-playbook test_win_group3.yml -i inventory.winrm -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

test_tags:
	(cd targets/tags && ./runme.sh $(TEST_FLAGS))

blocks:
	(cd targets/blocks && ./runme.sh $(TEST_FLAGS))

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

cloudstack:
	ansible-playbook cloudstack.yml -i $(INVENTORY) -e @$(VARS_FILE) -e "resource_prefix=$(CLOUD_RESOURCE_PREFIX)" -v $(TEST_FLAGS) ; \
	RC=$$? ; \
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
    ansible-playbook -i $(INVENTORY) $$mytmpdir/galaxy_playbook.yml -e outputdir=$(TEST_DIR) -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    rm -rf $$mytmpdir ; \
    exit $$RC

test_galaxy_yaml: setup
	mytmpdir=$(MYTMPDIR) ; \
	ansible-galaxy install -r galaxy_roles.yml -p $$mytmpdir/roles -vvvv; \
    cp galaxy_playbook.yml $$mytmpdir ; \
    ansible-playbook -i $(INVENTORY) $$mytmpdir/galaxy_playbook.yml -e outputdir=$(TEST_DIR) -v $(TEST_FLAGS) ; \
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

test_lookup_paths:
	(cd targets/lookup_paths && ./runme.sh $(TEST_FLAGS))

no_log:
	(cd targets/no_log && ./runme.sh $(TEST_FLAGS))

test_binary_modules_winrm:
	(cd targets/binary_modules_winrm && ./runme.sh $(TEST_FLAGS))

test_binary_modules_posix:
	(cd targets/binary_modules_posix && ./runme.sh $(TEST_FLAGS))

test_async:
	(cd targets/async_extra_data && ./runme.sh $(TEST_FLAGS))

test_hosts_field:
	(cd targets/hosts_field && ./runme.sh $(TEST_FLAGS))

args:
	(cd targets/args && ./runme.sh $(TEST_FLAGS))
