#!/usr/bin/make

NAME = "ansible"
ASCII2MAN = a2x -D $(dir $@) -d manpage -f manpage $<
ASCII2HTMLMAN = a2x -D docs/html/man/ -d manpage -f xhtml
MANPAGES := docs/man/man1/ansible.1 docs/man/man1/ansible-playbook.1
SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
RPMVERSION := $(shell awk '/Version/{print $$2; exit}' < ansible.spec | cut -d "%" -f1)
RPMRELEASE := $(shell awk '/Release/{print $$2; exit}' < ansible.spec | cut -d "%" -f1)
RPMNVR = "$(NAME)-$(RPMVERSION)-$(RPMRELEASE)"

all: clean python

tests: 
	PYTHONPATH=./lib nosetests -v

docs: $(MANPAGES)

%.1.asciidoc.gen: %.1.asciidoc ansible.spec
	sed "s/%VERSION%/$(RPMVERSION)/" $< > $@

%.1: %.1.asciidoc.gen
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
	-rm -rf build
	-rm -rf dist
	@echo "Cleaning up byte compiled python stuff"
	find . -regex ".*\.py[co]$$" -delete
	@echo "Cleaning up editor backup files"
	find . -type f \( -name "*~" -or -name "#*" \) -delete
	find . -type f \( -name "*.swp" \) -delete
	@echo "Cleaning up asciidoc to man transformations and results"
	find ./docs/man -type f -name "*.xml" -delete
	find ./docs/man -type f -name "*.gen" -delete
	@echo "Cleaning up output from test runs"
	-rm -rf test/test_data
	@echo "Cleaning up RPM building stuff"
	-rm -rf MANIFEST rpm-build

python:
	python setup.py build

install:
	mkdir -p /usr/share/ansible
	cp ./library/* /usr/share/ansible/
	python setup.py install

sdist: clean
	python ./setup.py sdist

rpmcommon: sdist
	@mkdir -p rpm-build
	@cp dist/*.gz rpm-build/

srpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir %{_topdir}" \
	--define "_sourcedir %{_topdir}" \
	-bs ansible.spec
	@echo "#############################################"
	@echo "Ansible SRPM is built:"
	@echo "    rpm-build/$(RPMNVR).src.rpm"
	@echo "#############################################"

rpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir %{_topdir}" \
	--define "_sourcedir %{_topdir}" \
	-ba ansible.spec
	@echo "#############################################"
	@echo "Ansible RPM is built:"
	@echo "    rpm-build/noarch/$(RPMNVR).noarch.rpm"
	@echo "#############################################"

.PHONEY: docs manual clean pep8
vpath %.asciidoc docs/man/man1
