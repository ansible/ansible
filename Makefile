# WARN: gmake syntax
########################################################
# Makefile for Ansible
#
# useful targets:
#   make clean ---------------- clean up
#   make webdocs -------------- produce ansible doc at docs/docsite/_build/html
#   make coredocs ------------- produce core doc at docs/docsite/_build/html
#   make sdist ---------------- produce a tarball
#   make deb-src -------------- produce a DEB source
#   make deb ------------------ produce a DEB
#   make docs ----------------- rebuild the manpages (results are checked in)
#   make tests ---------------- run the tests (see https://docs.ansible.com/ansible/devel/dev_guide/testing_units.html for requirements)

########################################################
# variable section

NAME = ansible-base
OS = $(shell uname -s)
PREFIX ?= '/usr/local'
SDIST_DIR ?= 'dist'

# This doesn't evaluate until it's called. The -D argument is the
# directory of the target file ($@), kinda like `dirname`.
MANPAGES ?= $(patsubst %.rst.in,%,$(wildcard ./docs/man/man1/ansible*.1.rst.in))
ifneq ($(shell which rst2man 2>/dev/null),)
ASCII2MAN = rst2man $< $@
else ifneq ($(shell which rst2man.py 2>/dev/null),)
ASCII2MAN = rst2man.py $< $@
else
ASCII2MAN = @echo "ERROR: rst2man from docutils command is not installed but is required to build $(MANPAGES)" && exit 1
endif

PYTHON=python
GENERATE_CLI = hacking/build-ansible.py generate-man

# fetch version from project release.py as single source-of-truth
VERSION := $(shell $(PYTHON) packaging/release/versionhelper/version_helper.py --raw || echo error)
ifeq ($(findstring error,$(VERSION)), error)
$(error "version_helper failed")
endif

# Get the branch information from git
ifneq ($(shell which git),)
GIT_DATE := $(shell git log -n 1 --format="%ci")
GIT_HASH := $(shell git log -n 1 --format="%h")
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD | sed 's/[-_.\/]//g')
GITINFO = .$(GIT_HASH).$(GIT_BRANCH)
else
GITINFO = ""
endif

ifeq ($(shell echo $(OS) | egrep -c 'Darwin|FreeBSD|OpenBSD|DragonFly'),1)
DATE := $(shell date -j -r $(shell git log -n 1 --format="%ct") +%Y%m%d%H%M)
CPUS ?= $(shell sysctl hw.ncpu|awk '{print $$2}')
else
DATE := $(shell date --utc --date="$(GIT_DATE)" +%Y%m%d%H%M)
CPUS ?= $(shell nproc)
endif

# DEB build parameters
DEBUILD_BIN ?= debuild
DEBUILD_OPTS = --source-option="-I"
DPUT_BIN ?= dput
DPUT_OPTS ?=
DEB_DATE := $(shell LC_TIME=C date +"%a, %d %b %Y %T %z")
DEB_VERSION ?= $(shell $(PYTHON) packaging/release/versionhelper/version_helper.py --debversion)
ifeq ($(OFFICIAL),yes)
    DEB_RELEASE ?= $(shell $(PYTHON) packaging/release/versionhelper/version_helper.py --debrelease)ppa
    # Sign OFFICIAL builds using 'DEBSIGN_KEYID'
    # DEBSIGN_KEYID is required when signing
    ifneq ($(DEBSIGN_KEYID),)
        DEBUILD_OPTS += -k$(DEBSIGN_KEYID)
    endif
else
    DEB_RELEASE ?= 100.git$(DATE)$(GITINFO)
    # Do not sign unofficial builds
    DEBUILD_OPTS += -uc -us
    DPUT_OPTS += -u
endif
DEBUILD = $(DEBUILD_BIN) $(DEBUILD_OPTS)
DEB_PPA ?= ppa
# Choose the desired Ubuntu release: lucid precise saucy trusty
DEB_DIST ?= unstable

# pbuilder parameters
PBUILDER_ARCH ?= amd64
PBUILDER_CACHE_DIR = /var/cache/pbuilder
PBUILDER_BIN ?= pbuilder
PBUILDER_OPTS ?= --debootstrapopts --variant=buildd --architecture $(PBUILDER_ARCH) --debbuildopts -b

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
	rm -rf shippable/
	rm -rf logs/
	rm -rf .cache/
	rm -f test/units/.coverage*
	rm -rf test/results/*/*
	find test/ -type f -name '*.retry' -delete
	@echo "Cleaning up Debian building stuff"
	rm -rf debian
	rm -rf deb-build
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

.PHONY: debian
debian: sdist
	@for DIST in $(DEB_DIST) ; do \
	    mkdir -p deb-build/$${DIST} ; \
	    tar -C deb-build/$${DIST} -xvf dist/$(NAME)-$(VERSION).tar.gz ; \
	    cp -a packaging/debian deb-build/$${DIST}/$(NAME)-$(VERSION)/ ; \
        sed -ie "s|%VERSION%|$(DEB_VERSION)|g;s|%RELEASE%|$(DEB_RELEASE)|;s|%DIST%|$${DIST}|g;s|%DATE%|$(DEB_DATE)|g" deb-build/$${DIST}/$(NAME)-$(VERSION)/debian/changelog ; \
	done

.PHONY: deb
deb: deb-src
	@for DIST in $(DEB_DIST) ; do \
	    PBUILDER_OPTS="$(PBUILDER_OPTS) --distribution $${DIST} --basetgz $(PBUILDER_CACHE_DIR)/$${DIST}-$(PBUILDER_ARCH)-base.tgz --buildresult $(CURDIR)/deb-build/$${DIST}" ; \
	    $(PBUILDER_BIN) create $${PBUILDER_OPTS} --othermirror "deb http://archive.ubuntu.com/ubuntu $${DIST} universe" ; \
	    $(PBUILDER_BIN) update $${PBUILDER_OPTS} ; \
	    $(PBUILDER_BIN) build $${PBUILDER_OPTS} deb-build/$${DIST}/$(NAME)_$(DEB_VERSION)-$(DEB_RELEASE)~$${DIST}.dsc ; \
	done
	@echo "#############################################"
	@echo "Ansible DEB artifacts:"
	@for DIST in $(DEB_DIST) ; do \
	    echo deb-build/$${DIST}/$(NAME)_$(DEB_VERSION)-$(DEB_RELEASE)~$${DIST}_amd64.changes ; \
	done
	@echo "#############################################"

# Build package outside of pbuilder, with locally installed dependencies.
# Install BuildRequires as noted in packaging/debian/control.
.PHONY: local_deb
local_deb: debian
	@for DIST in $(DEB_DIST) ; do \
	    (cd deb-build/$${DIST}/$(NAME)-$(VERSION)/ && $(DEBUILD) -b) ; \
	done
	@echo "#############################################"
	@echo "Ansible DEB artifacts:"
	@for DIST in $(DEB_DIST) ; do \
	    echo deb-build/$${DIST}/$(NAME)_$(DEB_VERSION)-$(DEB_RELEASE)~$${DIST}_amd64.changes ; \
	done
	@echo "#############################################"

.PHONY: deb-src
deb-src: debian
	@for DIST in $(DEB_DIST) ; do \
	    (cd deb-build/$${DIST}/$(NAME)-$(VERSION)/ && $(DEBUILD) -S) ; \
	done
	@echo "#############################################"
	@echo "Ansible DEB artifacts:"
	@for DIST in $(DEB_DIST) ; do \
	    echo deb-build/$${DIST}/$(NAME)_$(DEB_VERSION)-$(DEB_RELEASE)~$${DIST}_source.changes ; \
	done
	@echo "#############################################"

.PHONY: deb-upload
deb-upload: deb
	@for DIST in $(DEB_DIST) ; do \
	    $(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$${DIST}/$(NAME)_$(DEB_VERSION)-$(DEB_RELEASE)~$${DIST}_amd64.changes ; \
	done

.PHONY: deb-src-upload
deb-src-upload: deb-src
	@for DIST in $(DEB_DIST) ; do \
	    $(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$${DIST}/$(NAME)_$(DEB_VERSION)-$(DEB_RELEASE)~$${DIST}_source.changes ; \
	done

.PHONY: epub
epub:
	(cd docs/docsite/; CPUS=$(CPUS) $(MAKE) epub)

# for arch or gentoo, read instructions in the appropriate 'packaging' subdirectory directory
.PHONY: webdocs
webdocs:
	(cd docs/docsite/; CPUS=$(CPUS) $(MAKE) docs)

.PHONY: coredocs
coredocs:
	(cd docs/docsite/; CPUS=$(CPUS) $(MAKE) coredocs)

.PHONY: linkcheckdocs
linkcheckdocs:
	(cd docs/docsite/; CPUS=$(CPUS) $(MAKE) linkcheckdocs)

.PHONY: generate_rst
generate_rst: lib/ansible/cli/*.py
	mkdir -p ./docs/man/man1/ ; \
	$(GENERATE_CLI) --template-file=docs/templates/man.j2 --output-dir=docs/man/man1/ --output-format man lib/ansible/cli/*.py


docs: generate_rst
	$(MAKE) $(MANPAGES)

.PHONY: alldocs
alldocs: docs webdocs

version:
	@echo $(VERSION)
