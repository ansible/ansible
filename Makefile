# WARN: gmake syntax
########################################################
# Makefile for Ansible
#
# useful targets:
#   make sdist ---------------- produce a tarball
#   make srpm ----------------- produce a SRPM
#   make rpm  ----------------- produce RPMs
#   make deb-src -------------- produce a DEB source
#   make deb ------------------ produce a DEB
#   make docs ----------------- rebuild the manpages (results are checked in)
#   make tests ---------------- run the tests (see https://docs.ansible.com/ansible/dev_guide/testing_units.html for requirements)
#   make pyflakes, make pep8 -- source code checks

########################################################
# variable section

NAME = ansible
OS = $(shell uname -s)

# Manpages are currently built with asciidoc -- would like to move to markdown
# This doesn't evaluate until it's called. The -D argument is the
# directory of the target file ($@), kinda like `dirname`.

MANPAGES ?= $(patsubst %.asciidoc.in,%,$(wildcard ./docs/man/man1/ansible*.1.asciidoc.in))
ifneq ($(shell which a2x 2>/dev/null),)
ASCII2MAN = a2x -L -D $(dir $@) -d manpage -f manpage $<
ASCII2HTMLMAN = a2x -L -D docs/html/man/ -d manpage -f xhtml
else
ASCII2MAN = @echo "ERROR: AsciiDoc 'a2x' command is not installed but is required to build $(MANPAGES)" && exit 1
endif

PYTHON=python
SITELIB = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

# VERSION file provides one place to update the software version
VERSION := $(shell cat VERSION | cut -f1 -d' ')
RELEASE := $(shell cat VERSION | cut -f2 -d' ')

# Get the branch information from git
ifneq ($(shell which git),)
GIT_DATE := $(shell git log -n 1 --format="%ai")
GIT_HASH := $(shell git log -n 1 --format="%h")
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD | sed 's/[-_.\/]//g')
GITINFO = .$(GIT_HASH).$(GIT_BRANCH)
else
GITINFO = ""
endif

ifeq ($(shell echo $(OS) | egrep -c 'Darwin|FreeBSD|OpenBSD|DragonFly'),1)
DATE := $(shell date -j -r $(shell git log -n 1 --format="%at") +%Y%m%d%H%M)
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
ifeq ($(OFFICIAL),yes)
    DEB_RELEASE = $(RELEASE)ppa
    # Sign OFFICIAL builds using 'DEBSIGN_KEYID'
    # DEBSIGN_KEYID is required when signing
    ifneq ($(DEBSIGN_KEYID),)
        DEBUILD_OPTS += -k$(DEBSIGN_KEYID)
    endif
else
    DEB_RELEASE = 100.git$(DATE)$(GITINFO)
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

# RPM build parameters
RPMSPECDIR= packaging/rpm
RPMSPEC = $(RPMSPECDIR)/ansible.spec
RPMDIST = $(shell rpm --eval '%{?dist}')
RPMRELEASE = $(RELEASE)
ifneq ($(OFFICIAL),yes)
    RPMRELEASE = 100.git$(DATE)$(GITINFO)
endif
ifeq ($(PUBLISH),nightly)
    # https://fedoraproject.org/wiki/Packaging:Versioning#Snapshots
    RPMRELEASE = $(RELEASE).$(DATE)git.$(GIT_HASH)
endif
RPMNVR = "$(NAME)-$(VERSION)-$(RPMRELEASE)$(RPMDIST)"

# MOCK build parameters
MOCK_BIN ?= mock
MOCK_CFG ?=

# ansible-test parameters
ANSIBLE_TEST ?= test/runner/ansible-test
TEST_FLAGS ?=

# ansible-test units parameters (make test / make test-py3)
PYTHON_VERSION ?= $(shell python2 -c 'import sys; print("%s.%s" % sys.version_info[:2])')
PYTHON3_VERSION ?= $(shell python3 -c 'import sys; print("%s.%s" % sys.version_info[:2])')

# ansible-test integration parameters (make integration)
IMAGE ?= centos7
TARGET ?=

########################################################

all: clean python

tests:
	$(ANSIBLE_TEST) units -v --python $(PYTHON_VERSION) $(TEST_FLAGS)

tests-py3:
	$(ANSIBLE_TEST) units -v --python $(PYTHON3_VERSION) $(TEST_FLAGS)

tests-nonet:
	$(ANSIBLE_TEST) units -v --python $(PYTHON_VERSION) $(TEST_FLAGS)  --exclude test/units/modules/network/

integration:
	$(ANSIBLE_TEST) integration -v --docker $(IMAGE) $(TARGET) $(TEST_FLAGS)

authors:
	sh hacking/authors.sh

# Regenerate %.1.asciidoc if %.1.asciidoc.in has been modified more
# recently than %.1.asciidoc.
%.1.asciidoc: %.1.asciidoc.in
	sed "s/%VERSION%/$(VERSION)/" $< > $@

# Regenerate %.1 if %.1.asciidoc or VERSION has been modified more
# recently than %.1. (Implicitly runs the %.1.asciidoc recipe)
%.1: %.1.asciidoc VERSION
	$(ASCII2MAN)

loc:
	sloccount lib library bin

pep8:
	$(ANSIBLE_TEST) sanity --test pep8 --python $(PYTHON_VERSION) $(TEST_FLAGS)

pyflakes:
	pyflakes lib/ansible/*.py lib/ansible/*/*.py bin/*

clean:
	@echo "Cleaning up distutils stuff"
	rm -rf build
	rm -rf dist
	rm -rf lib/ansible.egg-info/
	@echo "Cleaning up byte compiled python stuff"
	find . -type f -regex ".*\.py[co]$$" -delete
	find . -type d -name "__pycache__" -delete
	@echo "Cleaning up editor backup files"
	find . -type f -not -path ./test/units/inventory_test_data/group_vars/noparse/all.yml~ \( -name "*~" -or -name "#*" \) -delete
	find . -type f \( -name "*.swp" \) -delete
	@echo "Cleaning up manpage stuff"
	find ./docs/man -type f -name "*.xml" -delete
	find ./docs/man -type f -name "*.asciidoc" -delete
	find ./docs/man/man3 -type f -name "*.3" -delete
	rm -f ./docs/man/man1/*
	@echo "Cleaning up output from test runs"
	rm -rf test/test_data
	rm -rf shippable/
	rm -rf logs/
	rm -rf .cache/
	rm -f test/units/.coverage*
	rm -f test/results/*/*
	find test/ -type f -name '*.retry' -delete
	@echo "Cleaning up RPM building stuff"
	rm -rf MANIFEST rpm-build
	@echo "Cleaning up Debian building stuff"
	rm -rf debian
	rm -rf deb-build
	rm -rf docs/json
	rm -rf docs/js
	@echo "Cleaning up authors file"
	rm -f AUTHORS.TXT
	@echo "Cleaning up docsite"
	$(MAKE) -C docs/docsite clean
	$(MAKE) -C docs/api clean

python:
	$(PYTHON) setup.py build

install:
	$(PYTHON) setup.py install

sdist: clean docs
	$(PYTHON) setup.py sdist

sdist_upload: clean docs
	$(PYTHON) setup.py sdist upload 2>&1 |tee upload.log

rpmcommon: sdist
	@mkdir -p rpm-build
	@cp dist/*.gz rpm-build/
	@sed -e 's#^Version:.*#Version: $(VERSION)#' -e 's#^Release:.*#Release: $(RPMRELEASE)%{?dist}$(REPOTAG)#' $(RPMSPEC) >rpm-build/$(NAME).spec

mock-srpm: /etc/mock/$(MOCK_CFG).cfg rpmcommon
	$(MOCK_BIN) -r $(MOCK_CFG) $(MOCK_ARGS) --resultdir rpm-build/  --buildsrpm --spec rpm-build/$(NAME).spec --sources rpm-build/
	@echo "#############################################"
	@echo "Ansible SRPM is built:"
	@echo rpm-build/*.src.rpm
	@echo "#############################################"

mock-rpm: /etc/mock/$(MOCK_CFG).cfg mock-srpm
	$(MOCK_BIN) -r $(MOCK_CFG) $(MOCK_ARGS) --resultdir rpm-build/ --rebuild rpm-build/$(NAME)-*.src.rpm
	@echo "#############################################"
	@echo "Ansible RPM is built:"
	@echo rpm-build/*.noarch.rpm
	@echo "#############################################"

srpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-bs rpm-build/$(NAME).spec
	@rm -f rpm-build/$(NAME).spec
	@echo "#############################################"
	@echo "Ansible SRPM is built:"
	@echo "    rpm-build/$(RPMNVR).src.rpm"
	@echo "#############################################"

rpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	--define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm" \
	--define "__python `which $(PYTHON)`" \
	-ba rpm-build/$(NAME).spec
	@rm -f rpm-build/$(NAME).spec
	@echo "#############################################"
	@echo "Ansible RPM is built:"
	@echo "    rpm-build/$(RPMNVR).noarch.rpm"
	@echo "#############################################"

debian: sdist
	@for DIST in $(DEB_DIST) ; do \
	    mkdir -p deb-build/$${DIST} ; \
	    tar -C deb-build/$${DIST} -xvf dist/$(NAME)-$(VERSION).tar.gz ; \
	    cp -a packaging/debian deb-build/$${DIST}/$(NAME)-$(VERSION)/ ; \
        sed -ie "s|%VERSION%|$(VERSION)|g;s|%RELEASE%|$(DEB_RELEASE)|;s|%DIST%|$${DIST}|g;s|%DATE%|$(DEB_DATE)|g" deb-build/$${DIST}/$(NAME)-$(VERSION)/debian/changelog ; \
	done

deb: deb-src
	@for DIST in $(DEB_DIST) ; do \
	    PBUILDER_OPTS="$(PBUILDER_OPTS) --distribution $${DIST} --basetgz $(PBUILDER_CACHE_DIR)/$${DIST}-$(PBUILDER_ARCH)-base.tgz --buildresult $(CURDIR)/deb-build/$${DIST}" ; \
	    $(PBUILDER_BIN) create $${PBUILDER_OPTS} --othermirror "deb http://archive.ubuntu.com/ubuntu $${DIST} universe" ; \
	    $(PBUILDER_BIN) update $${PBUILDER_OPTS} ; \
	    $(PBUILDER_BIN) build $${PBUILDER_OPTS} deb-build/$${DIST}/$(NAME)_$(VERSION)-$(DEB_RELEASE)~$${DIST}.dsc ; \
	done
	@echo "#############################################"
	@echo "Ansible DEB artifacts:"
	@for DIST in $(DEB_DIST) ; do \
	    echo deb-build/$${DIST}/$(NAME)_$(VERSION)-$(DEB_RELEASE)~$${DIST}_amd64.changes ; \
	done
	@echo "#############################################"

# Build package outside of pbuilder, with locally installed dependencies.
# Install BuildRequires as noted in packaging/debian/control.
local_deb: debian
	@for DIST in $(DEB_DIST) ; do \
	    (cd deb-build/$${DIST}/$(NAME)-$(VERSION)/ && $(DEBUILD) -b) ; \
	done
	@echo "#############################################"
	@echo "Ansible DEB artifacts:"
	@for DIST in $(DEB_DIST) ; do \
	    echo deb-build/$${DIST}/$(NAME)_$(VERSION)-$(DEB_RELEASE)~$${DIST}_amd64.changes ; \
	done
	@echo "#############################################"

deb-src: debian
	@for DIST in $(DEB_DIST) ; do \
	    (cd deb-build/$${DIST}/$(NAME)-$(VERSION)/ && $(DEBUILD) -S) ; \
	done
	@echo "#############################################"
	@echo "Ansible DEB artifacts:"
	@for DIST in $(DEB_DIST) ; do \
	    echo deb-build/$${DIST}/$(NAME)_$(VERSION)-$(DEB_RELEASE)~$${DIST}_source.changes ; \
	done
	@echo "#############################################"

deb-upload: deb
	@for DIST in $(DEB_DIST) ; do \
	    $(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$${DIST}/$(NAME)_$(VERSION)-$(DEB_RELEASE)~$${DIST}_amd64.changes ; \
	done

deb-src-upload: deb-src
	@for DIST in $(DEB_DIST) ; do \
	    $(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$${DIST}/$(NAME)_$(VERSION)-$(DEB_RELEASE)~$${DIST}_source.changes ; \
	done

epub:
	(cd docs/docsite/; CPUS=$(CPUS) make epub)

# for arch or gentoo, read instructions in the appropriate 'packaging' subdirectory directory
webdocs:
	(cd docs/docsite/; CPUS=$(CPUS) make docs)

generate_asciidoc: lib/ansible/cli/*.py
	mkdir -p ./docs/man/man1/
	PYTHONPATH=./lib ./docs/bin/generate_man.py

docs: generate_asciidoc
	make $(MANPAGES)

alldocs: docs webdocs

version:
	@echo $(VERSION)

