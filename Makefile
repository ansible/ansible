#!/usr/bin/make

ASCII2MAN = a2x -D $(dir $@) -d manpage -f manpage $<
ASCII2HTMLMAN = a2x -D docs/html/man/ -d manpage -f xhtml
MANPAGES := docs/man/man1/ansible.1 docs/man/man5/ansible-modules.5 docs/man/man5/ansible-playbook.5
SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

all: clean python

docs: manuals

manuals: $(MANPAGES)

%.1: %.1.asciidoc
	$(ASCII2MAN)

%.5: %.5.asciidoc
	$(ASCII2MAN)

loc:
	sloccount lib library bin

pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests"
	@echo "#############################################"
	pep8 -r --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225 lib/ bin/

clean:
	rm -rf build
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	find ./docs/ -type f -name "*.xml" -delete
	find . -type f -name "#*" -delete

python: docs
	python setup.py build

install: docs
	python setup.py install

.PHONEY: docs manual clean pep8
vpath %.asciidoc docs/man/man1


