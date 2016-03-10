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

all: setup test_test_infra parsing test_var_precedence unicode test_templating_settings environment non_destructive destructive includes blocks pull check_mode test_hash test_handlers test_group_by test_vault test_tags test_lookup_paths no_log test_connection

test_test_infra:
	[ "$$(ansible-playbook -i $(INVENTORY) test_test_infra.yml -e @$(VARS_FILE) $(CREDENTIALS_ARG) $(TEST_FLAGS) | fgrep works | xargs)" = "msg: fail works (True) msg: assert works (True)" ]

setup:
	rm -rf $(TEST_DIR)
	mkdir -p $(TEST_DIR)

parsing: setup
	ansible-playbook bad_parsing.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -vvv $(TEST_FLAGS) --tags prepare,common,scenario5
	ansible-playbook good_parsing.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

includes: setup
	ansible-playbook test_includes.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) $(TEST_FLAGS)

pull:	pull_run pull_no_127 pull_limit_inventory

pull_run:
	ansible-pull -d $(MYTMPDIR) -U https://github.com/ansible-test-robinro/pull-integration-test.git | grep MAGICKEYWORD; \
    RC=$$? ; \
	rm -rf $(MYTMPDIR); \
    exit $$RC

# test for https://github.com/ansible/ansible/issues/13681
pull_no_127:
	ansible-pull -d $(MYTMPDIR) -U https://github.com/ansible-test-robinro/pull-integration-test.git | grep -v 127\.0\.0\.1; \
    RC=$$? ; \
	rm -rf $(MYTMPDIR); \
    exit $$RC

# test for https://github.com/ansible/ansible/issues/13688
pull_limit_inventory:
	ansible-pull -d $(MYTMPDIR) -U https://github.com/ansible-test-robinro/pull-integration-test.git; \
    RC=$$? ; \
	rm -rf $(MYTMPDIR); \
    exit $$RC


unicode: setup
	ansible-playbook unicode.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) -v $(TEST_FLAGS) -e 'extra_var=café'
	# Test the start-at-task flag #9571
	ansible-playbook unicode.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) -v --start-at-task '*¶' -e 'start_at_task=True' $(TEST_FLAGS)

test_templating_settings: setup
	ansible-playbook test_templating_settings.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

environment: setup
	ansible-playbook test_environment.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) $(TEST_FLAGS)

non_destructive: setup
	ansible-playbook non_destructive.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

# Skip connection plugins which require root when not running as root.
ifneq ($(EUID),0)
TEST_CONNECTION_FILTER := !chroot
endif

# Connection plugin test command to repeat with each locale setting.
TEST_CONNECTION_CMD = $(1) ansible-playbook test_connection.yml -i test_connection.inventory -l '!skip-during-build $(TEST_CONNECTION_FILTER)' $(TEST_FLAGS)

test_connection: setup
	$(call TEST_CONNECTION_CMD)
	$(call TEST_CONNECTION_CMD, LC_ALL=C LANG=C)

destructive: setup
	ansible-playbook destructive.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

check_mode: setup
	ansible-playbook check_mode.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v --check $(TEST_FLAGS)

test_group_by: setup
	ansible-playbook test_group_by.yml -i inventory.group_by -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

test_handlers:
	ansible-playbook test_handlers.yml --tags scenario1 -i inventory.handlers -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)
	[ "$$(ansible-playbook test_handlers.yml --tags scenario2 -l A -i inventory.handlers -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) | grep -Po 'RUNNING HANDLER \[test_handlers : \K[^\]]+')" = "test handler" ]
	# Not forcing, should only run on successful host
	[ "$$(ansible-playbook test_force_handlers.yml --tags normal -i inventory.handlers -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) | egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_B" ]
	# Forcing from command line
	[ "$$(ansible-playbook test_force_handlers.yml --tags normal -i inventory.handlers --force-handlers -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) | egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]
	# Forcing from command line, should only run later tasks on unfailed hosts
	[ "$$(ansible-playbook test_force_handlers.yml --tags normal -i inventory.handlers --force-handlers -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) | egrep -o CALLED_TASK_. | sort | uniq | xargs)" = "CALLED_TASK_B CALLED_TASK_D CALLED_TASK_E" ]
	# Forcing from command line, should call handlers even if all hosts fail
	[ "$$(ansible-playbook test_force_handlers.yml --tags normal -i inventory.handlers --force-handlers -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v -e fail_all=yes $(TEST_FLAGS) | egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]
	# Forcing from ansible.cfg
	[ "$$(ANSIBLE_FORCE_HANDLERS=true ansible-playbook --tags normal test_force_handlers.yml -i inventory.handlers -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) | egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]
	# Forcing true in play
	[ "$$(ansible-playbook test_force_handlers.yml --tags force_true_in_play -i inventory.handlers -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) | egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]
	# Forcing false in play, which overrides command line
	[ "$$(ansible-playbook test_force_handlers.yml --force-handlers --tags force_false_in_play -i inventory.handlers -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) | egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_B" ]

test_hash:
	ANSIBLE_HASH_BEHAVIOUR=replace ansible-playbook test_hash.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v -e '{"test_hash":{"extra_args":"this is an extra arg"}}'
	ANSIBLE_HASH_BEHAVIOUR=merge ansible-playbook test_hash.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v -e '{"test_hash":{"extra_args":"this is an extra arg"}}'

test_var_precedence: setup
	ansible-playbook test_var_precedence.yml -i $(INVENTORY) $(CREDENTIALS_ARG) $(TEST_FLAGS) -v -e outputdir=$(TEST_DIR) -e 'extra_var=extra_var' -e 'extra_var_override=extra_var_override'

test_vault: setup
	ansible-playbook test_vault.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) --vault-password-file $(VAULT_PASSWORD_FILE) --list-tasks -e outputdir=$(TEST_DIR)
	ansible-playbook test_vault.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) --vault-password-file $(VAULT_PASSWORD_FILE) --list-hosts -e outputdir=$(TEST_DIR)
	ansible-playbook test_vault.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) --vault-password-file $(VAULT_PASSWORD_FILE) --syntax-check -e outputdir=$(TEST_DIR)
	ansible-playbook test_vault.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) --vault-password-file $(VAULT_PASSWORD_FILE) -e outputdir=$(TEST_DIR)

# test_delegate_to does not work unless we have permission to ssh to localhost.
# Would take some more effort on our test systems to implement that -- probably
# the test node should create an ssh public-private key pair that allows the
# root user on a node to ssh to itself.  Until then, this is not in make all.
# Have to run it manually.  Ordinary users should be able to run this test as
# long as they have permissions to login to their local machine via ssh.
test_delegate_to: setup
	ansible-playbook test_delegate_to.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

test_winrm: setup
	ansible-playbook test_winrm.yml -i inventory.winrm -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

test_tags: setup
	# Run everything by default
	[ "$$(ansible-playbook --list-tasks test_tags.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) | fgrep Task_with | xargs)" = "Task_with_tag TAGS: [tag] Task_with_always_tag TAGS: [always] Task_without_tag TAGS: []" ]
	# Run the exact tags, and always
	[ "$$(ansible-playbook --list-tasks --tags tag test_tags.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) | fgrep Task_with | xargs)" = "Task_with_tag TAGS: [tag] Task_with_always_tag TAGS: [always]" ]
	# Skip one tag
	[ "$$(ansible-playbook --list-tasks --skip-tags tag test_tags.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) | fgrep Task_with | xargs)" = "Task_with_always_tag TAGS: [always] Task_without_tag TAGS: []" ]

blocks: setup
	# remove old output log
	rm -f block_test.out
	# run the test and check to make sure the right number of completions was logged
	ansible-playbook -vv -e outputdir=$(TEST_DIR) test_blocks/main.yml | tee block_test.out
	[ "$$(grep 'TEST COMPLETE' block_test.out | wc -l)" = "$$(egrep '^[0-9]+ plays in' block_test.out | cut -f1 -d' ')" ]
	# cleanup the output log again, to make sure the test is clean
	rm -f block_test.out
	# run test with free strategy and again count the completions
	ansible-playbook -vv -e outputdir=$(TEST_DIR) test_blocks/main.yml -e test_strategy=free | tee block_test.out
	[ "$$(grep 'TEST COMPLETE' block_test.out | wc -l)" = "$$(egrep '^[0-9]+ plays in' block_test.out | cut -f1 -d' ')" ]

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

test_lookup_paths: setup
	ansible-playbook lookup_paths/play.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -v $(TEST_FLAGS)

no_log: setup
	# This test expects 7 loggable vars and 0 non loggable ones, if either mismatches it fails, run the ansible-playbook command to debug
	[ "$$(ansible-playbook no_log_local.yml -i $(INVENTORY) -e outputdir=$(TEST_DIR) -vvvvv | awk --source 'BEGIN { logme = 0; nolog = 0; } /LOG_ME/ { logme += 1;} /DO_NOT_LOG/ { nolog += 1;} END { printf "%d/%d", logme, nolog; }')" = "6/0" ]
