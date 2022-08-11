# WARN: gmake syntax
########################################################
# Makefile for Ansible
#
# useful targets:
#   make clean ---------------- clean up
#   make sdist ---------------- produce a tarball
#   make tests ---------------- run the tests (see https://docs.ansible.com/ansible/devel/dev_guide/testing_units.html for requirements)

########################################################
# variable section

NAME = ansible-core
OS = $(shell uname -s)
PREFIX ?= '/usr/local'
SDIST_DIR ?= 'dist'

# This doesn't evaluate until it's called. The -D argument is the
# directory of the target file ($@), kinda like `dirname`.
MANPAGES ?= $(patsubst %.rst.in,%,$(wildcard ./docs/man/man1/ansible*.1.rst.in))
ifneq ($(shell command -v rst2man 2>/dev/null),)
ASCII2MAN = rst2man $< $@
else ifneq ($(shell command -v rst2man.py 2>/dev/null),)
ASCII2MAN = rst2man.py $< $@
else
ASCII2MAN = @echo "ERROR: rst2man from docutils command is not installed but is required to build $(MANPAGES)" && exit 1
endif

PYTHON ?= python
GENERATE_CLI = hacking/build-ansible.py generate-man

# fetch version from project release.py as single source-of-truth
VERSION := $(shell $(PYTHON) packaging/release/versionhelper/version_helper.py --raw || echo error)
ifeq ($(findstring error,$(VERSION)), error)
$(error "version_helper failed")
endif

# ansible-test parameters
ANSIBLE_TEST ?= bin/ansible-test
TEST_FLAGS ?=

# ansible-test units parameters (make test / make test-py3)
PYTHON_VERSION ?= $(shell python2 -c 'import sys; print("%s.%s" % sys.version_info[:2])')
PYTHON3_VERSION ?= $(shell python3 -c 'import sys; print("%s.%s" % sys.version_info[:2])')

# ansible-test integration parameters (make integration)
IMAGE ?= centos7
TARGET ?=

########################################################

.PHONY: all
all: clean python

.PHONY: tests
tests:
	$(ANSIBLE_TEST) units -v --python $(PYTHON_VERSION) $(TEST_FLAGS)

.PHONY: tests-py3
tests-py3:
	$(ANSIBLE_TEST) units -v --python $(PYTHON3_VERSION) $(TEST_FLAGS)

.PHONY: integration
integration:
	$(ANSIBLE_TEST) integration -v --docker $(IMAGE) $(TARGET) $(TEST_FLAGS)

# Regenerate %.1.rst if %.1.rst.in has been modified more
# recently than %.1.rst.
%.1.rst: %.1.rst.in
	sed "s/%VERSION%/$(VERSION)/" $< > $@
	rm $<

# Regenerate %.1 if %.1.rst or release.py has been modified more
# recently than %.1. (Implicitly runs the %.1.rst recipe)
%.1: %.1.rst lib/ansible/release.py
	$(ASCII2MAN)

.PHONY: clean
clean:
	@echo "Cleaning up distutils stuff"
	rm -rf build
	rm -rf dist
	rm -rf lib/ansible*.egg-info/
	@echo "Cleaning up byte compiled python stuff"
	find . -type f -regex ".*\.py[co]$$" -delete
	find . -type d -name "__pycache__" -delete
	@echo "Cleaning up editor backup files"
	find . -type f -not -path ./test/units/inventory_test_data/group_vars/noparse/all.yml~ \( -name "*~" -or -name "#*" \) -delete
	find . -type f \( -name "*.swp" \) -delete
	@echo "Cleaning up manpage stuff"
	find ./docs/man -type f -name "*.xml" -delete
	find ./docs/man -type f -name "*.rst" -delete
	find ./docs/man/man3 -type f -name "*.3" -delete
	rm -f ./docs/man/man1/*
	@echo "Cleaning up output from test runs"
	rm -rf test/test_data
	rm -rf logs/
	rm -rf .cache/
	rm -f test/units/.coverage*
	rm -rf test/results/*/*
	find test/ -type f -name '*.retry' -delete
	@echo "Cleaning up symlink cache"
	rm -f SYMLINK_CACHE.json
	rm -rf docs/json
	rm -rf docs/js
	@echo "Cleaning up docsite"
	$(MAKE) -C docs/docsite clean

.PHONY: python
python:
	$(PYTHON) setup.py build

.PHONY: install
install:
	$(PYTHON) setup.py install

.PHONY: install_manpages
install_manpages:
	gzip -9 $(wildcard ./docs/man/man1/ansible*.1)
	cp $(wildcard ./docs/man/man1/ansible*.1.gz) $(PREFIX)/man/man1/

.PHONY: sdist_check
sdist_check:
	$(PYTHON) -c 'import setuptools, sys; sys.exit(int(not (tuple(map(int, setuptools.__version__.split("."))) > (39, 2, 0))))'
	$(PYTHON) packaging/sdist/check-link-behavior.py

.PHONY: sdist
sdist: sdist_check clean docs
	_ANSIBLE_SDIST_FROM_MAKEFILE=1 $(PYTHON) setup.py sdist --dist-dir=$(SDIST_DIR)

# Official releases generate the changelog as the last commit before the release.
# Snapshots shouldn't result in new checkins so the changelog is generated as
# part of creating the tarball.
.PHONY: snapshot
snapshot: sdist_check clean docs changelog
	_ANSIBLE_SDIST_FROM_MAKEFILE=1 $(PYTHON) setup.py sdist --dist-dir=$(SDIST_DIR)

.PHONY: sdist_upload
sdist_upload: clean docs
	$(PYTHON) setup.py sdist upload 2>&1 |tee upload.log

.PHONY: changelog
changelog:
	PYTHONPATH=./lib antsibull-changelog release -vv --use-ansible-doc && PYTHONPATH=./lib antsibull-changelog generate -vv --use-ansible-doc

.PHONY: generate_rst
generate_rst: lib/ansible/cli/*.py
	mkdir -p ./docs/man/man1/ ; \
	$(PYTHON) $(GENERATE_CLI) --template-file=docs/templates/man.j2 --output-dir=docs/man/man1/ --output-format man lib/ansible/cli/*.py

.PHONY: docs
docs: generate_rst
	$(MAKE) $(MANPAGES)

.PHONY: version
version:
	@echo $(VERSION)
