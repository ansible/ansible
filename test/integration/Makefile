INVENTORY ?= inventory
VARS_FILE ?= integration_config.yml

# Create a semi-random string for use when testing cloud-based resources
ifndef CLOUD_RESOURCE_PREFIX
CLOUD_RESOURCE_PREFIX := $(shell python -c "import string,random; print 'ansible-testing-' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in xrange(8));")
endif

CREDENTIALS_FILE = credentials.yml
# If credentials.yml exists, use it
ifneq ("$(wildcard $(CREDENTIALS_FILE))","")
CREDENTIALS_ARG = -e @$(CREDENTIALS_FILE)
else
CREDENTIALS_ARG =
endif

# http://unix.stackexchange.com/questions/30091/fix-or-alternative-for-mktemp-in-os-x
TMPDIR = $(shell mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')

VAULT_PASSWORD_FILE = vault-password

all: non_destructive destructive includes unicode test_var_precedence check_mode test_hash test_handlers test_group_by test_vault parsing

parsing:
	ansible-playbook bad_parsing.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -vvv $(TEST_FLAGS) --tags common,scenario1; [ $$? -eq 3 ]
	ansible-playbook bad_parsing.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -vvv $(TEST_FLAGS) --tags common,scenario2; [ $$? -eq 3 ]
	ansible-playbook bad_parsing.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -vvv $(TEST_FLAGS) --tags common,scenario3; [ $$? -eq 3 ]
	ansible-playbook bad_parsing.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -vvv $(TEST_FLAGS) --tags common,scenario4; [ $$? -eq 3 ]
	ansible-playbook bad_parsing.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -vvv $(TEST_FLAGS) --tags common,scenario5; [ $$? -eq 3 ]
	ansible-playbook good_parsing.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

includes:
	ansible-playbook test_includes.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) $(TEST_FLAGS) 

unicode:
	ansible-playbook unicode.yml -i $(INVENTORY) -e @$(VARS_FILE) -v $(TEST_FLAGS)

non_destructive:
	ansible-playbook non_destructive.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

mine:
	ansible-playbook mine.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

destructive:
	ansible-playbook destructive.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

check_mode:
	ansible-playbook check_mode.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v --check $(TEST_FLAGS)

test_group_by:
	ansible-playbook test_group_by.yml -i inventory.group_by -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

test_handlers:
	ansible-playbook test_handlers.yml -i inventory.handlers -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

test_hash:
	ANSIBLE_HASH_BEHAVIOUR=replace ansible-playbook test_hash.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v -e '{"test_hash":{"extra_args":"this is an extra arg"}}'
	ANSIBLE_HASH_BEHAVIOUR=merge ansible-playbook test_hash.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v -e '{"test_hash":{"extra_args":"this is an extra arg"}}'

test_var_precedence:
	ansible-playbook test_var_precedence.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v -e 'extra_var=extra_var'

test_vault:
	ansible-playbook test_vault.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) --vault-password-file $(VAULT_PASSWORD_FILE) --list-tasks
	ansible-playbook test_vault.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) --vault-password-file $(VAULT_PASSWORD_FILE) --list-hosts
	ansible-playbook test_vault.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) --vault-password-file $(VAULT_PASSWORD_FILE) --syntax-check
	ansible-playbook test_vault.yml -i $(INVENTORY) $(CREDENTIALS_ARG) -v $(TEST_FLAGS) --vault-password-file $(VAULT_PASSWORD_FILE)

test_winrm:
	ansible-playbook test_winrm.yml -i inventory.winrm -e @$(VARS_FILE) $(CREDENTIALS_ARG) -v $(TEST_FLAGS)

cloud: amazon rackspace

cloud_cleanup: amazon_cleanup rackspace_cleanup

amazon_cleanup:
	python cleanup_ec2.py -y --match="^$(CLOUD_RESOURCE_PREFIX)"

gce_setup:
	python setup_gce.py "$(CLOUD_RESOURCE_PREFIX)"

gce_cleanup:
	python cleanup_gce.py -y --match="^$(CLOUD_RESOURCE_PREFIX)"

rackspace_cleanup:
	@echo "FIXME - cleanup_rax.py not yet implemented"
	@# python cleanup_rax.py -y --match="^$(CLOUD_RESOURCE_PREFIX)"

$(CREDENTIALS_FILE):
	@echo "No credentials file found.  A file named '$(CREDENTIALS_FILE)' is needed to provide credentials needed to run cloud tests.  See sample 'credentials.template' file."
	@exit 1

amazon: $(CREDENTIALS_FILE)
	ANSIBLE_HOST_KEY_CHECKING=False ANSIBLE_SSH_PIPELINING=no BOTO_CONFIG=/dev/null ansible-playbook amazon.yml -i $(INVENTORY) -e @$(VARS_FILE) $(CREDENTIALS_ARG) -e "resource_prefix=$(CLOUD_RESOURCE_PREFIX)" -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    CLOUD_RESOURCE_PREFIX="$(CLOUD_RESOURCE_PREFIX)" make amazon_cleanup ; \
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

test_galaxy: test_galaxy_spec test_galaxy_yaml

test_galaxy_spec:
	mytmpdir=$(TMPDIR) ; \
	ansible-galaxy install -r galaxy_rolesfile -p $$mytmpdir/roles ; \
    cp galaxy_playbook.yml $$mytmpdir ; \
    ansible-playbook -i $(INVENTORY) $$mytmpdir/galaxy_playbook.yml -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    rm -rf $$mytmpdir ; \
    exit $$RC

test_galaxy_yaml:
	mytmpdir=$(TMPDIR) ; \
	ansible-galaxy install -r galaxy_roles.yml -p $$mytmpdir/roles ; \
    cp galaxy_playbook.yml $$mytmpdir ; \
    ansible-playbook -i $(INVENTORY) $$mytmpdir/galaxy_playbook.yml -v $(TEST_FLAGS) ; \
    RC=$$? ; \
    rm -rf $$mytmpdir ; \
    exit $$RC
