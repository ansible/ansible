#!/usr/bin/make
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
#   make tests ---------------- run the tests (see test/README.md for requirements)
#   make pyflakes, make pep8 -- source code checks

########################################################
# variable section

NAME = ansible
OS = $(shell uname -s)

# Manpages are currently built with asciidoc -- would like to move to markdown
# This doesn't evaluate until it's called. The -D argument is the
# directory of the target file ($@), kinda like `dirname`.
MANPAGES := docs/man/man1/ansible.1 docs/man/man1/ansible-playbook.1 docs/man/man1/ansible-pull.1 docs/man/man1/ansible-doc.1 docs/man/man1/ansible-galaxy.1 docs/man/man1/ansible-vault.1
ifneq ($(shell which a2x 2>/dev/null),)
ASCII2MAN = a2x -D $(dir $@) -d manpage -f manpage $<
ASCII2HTMLMAN = a2x -D docs/html/man/ -d manpage -f xhtml
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

ifeq ($(shell echo $(OS) | egrep -c 'Darwin|FreeBSD|OpenBSD'),1)
DATE := $(shell date -j -r $(shell git log -n 1 --format="%at") +%Y%m%d%H%M)
else
DATE := $(shell date --utc --date="$(GIT_DATE)" +%Y%m%d%H%M)
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
    DEB_RELEASE = 0.git$(DATE)$(GITINFO)
    # Do not sign unofficial builds
    DEBUILD_OPTS += -uc -us
    DPUT_OPTS += -u
endif
DEBUILD = $(DEBUILD_BIN) $(DEBUILD_OPTS)
DEB_PPA ?= ppa
# Choose the desired Ubuntu release: lucid precise saucy trusty
DEB_DIST ?= unstable

# RPM build parameters
RPMSPECDIR= packaging/rpm
RPMSPEC = $(RPMSPECDIR)/ansible.spec
RPMDIST = $(shell rpm --eval '%{?dist}')
RPMRELEASE = $(RELEASE)
ifneq ($(OFFICIAL),yes)
    RPMRELEASE = 0.git$(DATE)$(GITINFO)
endif
RPMNVR = "$(NAME)-$(VERSION)-$(RPMRELEASE)$(RPMDIST)"

# MOCK build parameters
MOCK_BIN ?= mock
MOCK_CFG ?=

NOSETESTS ?= nosetests

NOSETESTS3 ?= nosetests-3.4

########################################################

all: clean python

tests:
	PYTHONPATH=./lib $(NOSETESTS) -d -w test/units -v --with-coverage --cover-package=ansible --cover-branches

tests-py3:
	PYTHONPATH=./lib $(NOSETESTS3) -d -w test/units -v --with-coverage --cover-package=ansible --cover-branches

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
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests"
	@echo "#############################################"
	-pep8 -r --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225,E261,E241 lib/ bin/
	# -pep8 -r --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225,E261,E241 --filename "*" library/

pyflakes:
	pyflakes lib/ansible/*.py lib/ansible/*/*.py bin/*

clean:
	@echo "Cleaning up distutils stuff"
	rm -rf build
	rm -rf dist
	rm -rf lib/ansible.egg-info/
	@echo "Cleaning up byte compiled python stuff"
	find . -type f -regex ".*\.py[co]$$" -delete
	@echo "Cleaning up editor backup files"
	find . -type f -not -path ./test/units/inventory_test_data/group_vars/noparse/all.yml~ \( -name "*~" -or -name "#*" \) -delete
	find . -type f \( -name "*.swp" \) -delete
	@echo "Cleaning up manpage stuff"
	find ./docs/man -type f -name "*.xml" -delete
	find ./docs/man -type f -name "*.asciidoc" -delete
	find ./docs/man/man3 -type f -name "*.3" -delete
	@echo "Cleaning up output from test runs"
	rm -rf test/test_data
	@echo "Cleaning up RPM building stuff"
	rm -rf MANIFEST rpm-build
	@echo "Cleaning up Debian building stuff"
	rm -rf debian
	rm -rf deb-build
	rm -rf docs/json
	rm -rf docs/js
	@echo "Cleaning up authors file"
	rm -f AUTHORS.TXT
	find . -type f -name '*.pyc' -delete

python:
	$(PYTHON) setup.py build

install:
	$(PYTHON) setup.py install

sdist: clean docs
	$(PYTHON) setup.py sdist

sdist_upload: clean docs
	$(PYTHON) setup.py sdist upload 2>&1 |tee upload.log

rpmcommon: $(MANPAGES) sdist
	@mkdir -p rpm-build
	@cp dist/*.gz rpm-build/
	@sed -e 's#^Version:.*#Version: $(VERSION)#' -e 's#^Release:.*#Release: $(RPMRELEASE)%{?dist}#' $(RPMSPEC) >rpm-build/$(NAME).spec

mock-srpm: /etc/mock/$(MOCK_CFG).cfg rpmcommon
	$(MOCK_BIN) -r $(MOCK_CFG) --resultdir rpm-build/  --buildsrpm --spec rpm-build/$(NAME).spec --sources rpm-build/
	@echo "#############################################"
	@echo "Ansible SRPM is built:"
	@echo rpm-build/*.src.rpm
	@echo "#############################################"

mock-rpm: /etc/mock/$(MOCK_CFG).cfg mock-srpm
	$(MOCK_BIN) -r $(MOCK_CFG) --resultdir rpm-build/ --rebuild rpm-build/$(NAME)-*.src.rpm
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

deb: debian
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

# for arch or gentoo, read instructions in the appropriate 'packaging' subdirectory directory

webdocs: $(MANPAGES)
	(cd docsite/; make docs)

docs: $(MANPAGES)
