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

other: ansible test_test_infra parsing test_var_blending test_var_precedence unicode test_templating_settings \
	environment test_as includes blocks pull_run pull_no_127 pull_limit_inventory check_mode test_hash test_handlers \
	test_group_by test_vault test_tags test_lookup_paths no_log test_gathering_facts test_binary_modules_posix \
	test_hosts_field test_lookup_properties args test_jinja2_groupby test_callback_retry_task_name

ansible:
	(cd targets/ansible && ./runme.sh $(TEST_FLAGS))

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

test_jinja2_groupby:
	(cd targets/filters && ./runme.sh $(TEST_FLAGS))

non_destructive: setup
	ANSIBLE_ROLES_PATH=$(shell pwd)/targets ansible-playbook non_destructive.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

# Tests which can be run when running as root and a local SSH daemon is available.
test_root_ssh: test_connection_local test_connection_chroot test_connection_ssh test_connection_paramiko_ssh test_delegate_to

# For tests running in our Docker containers (identified with "ENV container=docker").
# These tests are run as root and have access to a local SSH daemon.
test_as_docker: test_root_ssh test_async_extra_data

# For tests running in our FreeBSD instances on EC2 (identified with "ENV container=freebsd").
# These tests are run as root and have access to a local SSH daemon.
test_as_freebsd: test_root_ssh

# For tests running in our OS X instances at MacStadium (identified with "ENV container=osx").
# These tests are run as root and have access to a local SSH daemon.
test_as_osx: test_root_ssh

# For tests running as root.
# Login to a local SSH daemon assumed to be unavailable.
test_as_root: test_connection_local test_connection_chroot

# For tests not running as root.
# Login to a local SSH daemon assumed to be unavailable.
test_as_non_root: test_connection_local

# Determine which of the above environments we're running in.
ifeq ($(container),docker)
TEST_AS_TARGET := test_as_docker
else ifeq ($(container),freebsd)
TEST_AS_TARGET := test_as_freebsd
else ifeq ($(container),osx)
TEST_AS_TARGET := test_as_osx
else ifeq ($(EUID),0)
TEST_AS_TARGET := test_as_root
else
TEST_AS_TARGET := test_as_non_root
endif

test_as: $(TEST_AS_TARGET)

test_connection_local:
	(cd targets/connection_local && ./runme.sh $(TEST_FLAGS))

test_connection_chroot:
	(cd targets/connection_chroot && ./runme.sh $(TEST_FLAGS))

test_connection_docker:
	(cd targets/connection_docker && ./runme.sh $(TEST_FLAGS))

test_connection_libvirt_lxc:
	(cd targets/connection_libvirt_lxc && ./runme.sh $(TEST_FLAGS))

test_connection_jail:
	(cd targets/connection_jail && ./runme.sh $(TEST_FLAGS))

test_connection_ssh:
	(cd targets/connection_ssh && ./runme.sh $(TEST_FLAGS))

test_connection_paramiko_ssh:
	(cd targets/connection_paramiko_ssh && ./runme.sh $(TEST_FLAGS))

test_connection_lxd:
	(cd targets/connection_lxd && ./runme.sh $(TEST_FLAGS))

test_connection_lxc:
	(cd targets/connection_lxc && ./runme.sh $(TEST_FLAGS))

test_connection_winrm:
	(cd targets/connection_winrm && ./runme.sh $(TEST_FLAGS))

destructive: setup
	ANSIBLE_ROLES_PATH=$(shell pwd)/targets ansible-playbook destructive.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

check_mode:
	(cd targets/check_mode && ./runme.sh $(TEST_FLAGS))

test_group_by:
	(cd targets/group_by && ./runme.sh $(TEST_FLAGS))

test_handlers:
	(cd targets/handlers && ./runme.sh $(TEST_FLAGS))

test_hash:
	(cd targets/hash && ./runme.sh $(TEST_FLAGS))

test_var_blending:
	(cd targets/var_blending && ./runme.sh $(TEST_FLAGS))

test_var_precedence:
	(cd targets/var_precedence && ./runme.sh $(TEST_FLAGS))

test_vault:
	(cd targets/vault && ./runme.sh $(TEST_FLAGS))

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
	ANSIBLE_ROLES_PATH=$(shell pwd)/targets ansible-playbook test_win_group1.yml -i inventory.winrm -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

test_win_group2:
	ANSIBLE_ROLES_PATH=$(shell pwd)/targets ansible-playbook test_win_group2.yml -i inventory.winrm -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

test_win_group3:
	ANSIBLE_ROLES_PATH=$(shell pwd)/targets ansible-playbook test_win_group3.yml -i inventory.winrm -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

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

cloudscale:
	ANSIBLE_ROLES_PATH=$(shell pwd)/targets ansible-playbook cloudscale.yml -i $(INVENTORY) -e @$(VARS_FILE) -e "resource_prefix=$(CLOUD_RESOURCE_PREFIX)" -v $(TEST_FLAGS) ; \
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

test_lookup_paths:
	(cd targets/lookup_paths && ./runme.sh $(TEST_FLAGS))

no_log:
	(cd targets/no_log && ./runme.sh $(TEST_FLAGS))

test_binary_modules_winrm:
	(cd targets/binary_modules_winrm && ./runme.sh $(TEST_FLAGS))

test_binary_modules_posix:
	(cd targets/binary_modules_posix && ./runme.sh $(TEST_FLAGS))

test_async_extra_data:
	(cd targets/async_extra_data && ./runme.sh $(TEST_FLAGS))

test_hosts_field:
	(cd targets/hosts_field && ./runme.sh $(TEST_FLAGS))

test_lookup_properties:
	(cd targets/lookup_properties && ./runme.sh $(TEST_FLAGS))

args:
	(cd targets/args && ./runme.sh $(TEST_FLAGS))

test_callback_retry_task_name:
	(cd targets/callback_retry_task_name && ./runme.sh $(TEST_FLAGS))
