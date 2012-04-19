#!/usr/bin/make

NAME = "ansible"
# This doesn't evaluate until it's called. The -D argument is the
# directory of the target file ($@), kinda like `dirname`.
ASCII2MAN = a2x -D $(dir $@) -d manpage -f manpage $<
ASCII2HTMLMAN = a2x -D docs/html/man/ -d manpage -f xhtml
# Space separated list of all the manpages we want to end up with.
MANPAGES := docs/man/man1/ansible.1 docs/man/man1/ansible-playbook.1
SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
VERSION := $(shell cat VERSION)
# These are for building the RPM.
RPMSPECDIR= packaging/rpm
RPMSPEC = $(RPMSPECDIR)/ansible.spec
RPMVERSION := $(shell awk '/Version/{print $$2; exit}' < $(RPMSPEC) | cut -d "%" -f1)
RPMRELEASE := $(shell awk '/Release/{print $$2; exit}' < $(RPMSPEC) | cut -d "%" -f1)
RPMDIST = $(shell rpm --eval '%dist')
RPMNVR = "$(NAME)-$(RPMVERSION)-$(RPMRELEASE)$(RPMDIST)"
# Python distutils options
DUDIR = packaging/distutils
DUSETUP = $(DUDIR)/setup.py
DUMANIFEST = $(DUDIR)/MANIFEST.in


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
	pep8 -r --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225 lib/ bin/

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

python:
	python $(DUSETUP) build

install:
	mkdir -p /usr/share/ansible
	cp ./library/* /usr/share/ansible/
	python $(DUSETUP) install

sdist: clean
	python ./$(DUSETUP) sdist -t $(DUMANIFEST)

rpmcommon: sdist
	@mkdir -p rpm-build
	@cp dist/*.gz rpm-build/

srpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-bs $(RPMSPEC)
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
	-ba $(RPMSPEC)
	@echo "#############################################"
	@echo "Ansible RPM is built:"
	@echo "    rpm-build/noarch/$(RPMNVR).noarch.rpm"
	@echo "#############################################"
