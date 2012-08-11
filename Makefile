#!/usr/bin/make

########################################################
# Makefile for Ansible
#
# useful targets:
#   make sdist ---------------- produce a tarball
#   make rpm  ----------------- produce RPMs
#   make deb ------------------ produce a DEB
#   make docs ----------------- rebuild the manpages (results are checked in)
#   make tests ---------------- run the tests
#   make pyflakes, make pep8 -- source code checks  

########################################################
# variable section

NAME = "ansible"

# Manpages are currently built with asciidoc -- would like to move to markdown
# This doesn't evaluate until it's called. The -D argument is the
# directory of the target file ($@), kinda like `dirname`.
ASCII2MAN = a2x -D $(dir $@) -d manpage -f manpage $<
ASCII2HTMLMAN = a2x -D docs/html/man/ -d manpage -f xhtml
MANPAGES := docs/man/man1/ansible.1 docs/man/man1/ansible-playbook.1

SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

# VERSION file provides one place to update the software version
VERSION := $(shell cat VERSION)

### Get the branch information from git
ifneq ($(shell which git),)
GIT_DATE := $(shell git log -n 1 --format="%ai")
endif
DATE := $(shell date --date="$(GIT_DATE)" +%Y%m%d%H%M)

# RPM build parameters
RPMSPECDIR= packaging/rpm
RPMSPEC = $(RPMSPECDIR)/ansible.spec
RPMDIST = $(shell rpm --eval '%dist')
RPMRELEASE = 1
ifeq ($(OFFICIAL),)
    RPMRELEASE = 0.git$(DATE)
endif
RPMNVR = "$(NAME)-$(VERSION)-$(RPMRELEASE)$(RPMDIST)"

########################################################

all: clean python

tests: 
	PYTHONPATH=./lib nosetests -v

# To force a rebuild of the docs run 'touch VERSION && make docs'
docs: $(MANPAGES)

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
	-pep8 -r --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225,E261,E241 --filename "*" library/

pyflakes:
	pyflakes lib/ansible/*.py bin/*

clean:
	@echo "Cleaning up distutils stuff"
	rm -rf build
	rm -rf dist
	@echo "Cleaning up byte compiled python stuff"
	find . -type f -regex ".*\.py[co]$$" -delete
	@echo "Cleaning up editor backup files"
	find . -type f \( -name "*~" -or -name "#*" \) -delete
	find . -type f \( -name "*.swp" \) -delete
	@echo "Cleaning up asciidoc to man transformations and results"
	find ./docs/man -type f -name "*.xml" -delete
	find ./docs/man -type f -name "*.asciidoc" -delete
	@echo "Cleaning up output from test runs"
	rm -rf test/test_data
	@echo "Cleaning up RPM building stuff"
	rm -rf MANIFEST rpm-build
	@echo "Cleaning up Debian building stuff"
	rm -rf debian
	rm -rf deb-build

python:
	python setup.py build

install:
	mkdir -p /usr/share/ansible
	cp ./library/* /usr/share/ansible/
	python setup.py install

sdist: clean
	python setup.py sdist -t MANIFEST.in

rpmcommon: sdist
	@mkdir -p rpm-build
	@cp dist/*.gz rpm-build/
	@sed -e 's#^Version:.*#Version: $(VERSION)#' -e 's#^Release:.*#Release: $(RPMRELEASE)%{?dist}#' $(RPMSPEC) >rpm-build/$(NAME).spec

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
	--define "_rpmfilename $(RPMNVR).%%{ARCH}.rpm" \
	-ba rpm-build/$(NAME).spec
	@rm -f rpm-build/$(NAME).spec
	@echo "#############################################"
	@echo "Ansible RPM is built:"
	@echo "    rpm-build/$(RPMNVR).noarch.rpm"
	@echo "#############################################"

debian: sdist
deb: debian
	cp -r packaging/debian ./
	chmod 755 debian/rules
	fakeroot debian/rules clean
	fakeroot dh_install
	fakeroot debian/rules binary

# for arch or gentoo, read instructions in the appropriate 'packaging' subdirectory directory

