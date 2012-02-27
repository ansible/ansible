#!/usr/bin/make

ASCII2MAN = a2x -D $(dir $@) -d manpage -f manpage $<
ASCII2HTMLMAN = a2x -D docs/html/man/ -d manpage -f xhtml
MANPAGES := docs/man/man1/ansible.1 docs/man/man5/ansible-modules.1 docs/man/man5/ansible-playbook.1
SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

docs: manuals

manuals: $(MANPAGES)

%.1: %.1.asciidoc
	$(ASCII2MAN)

%.5: %.5.asciidoc
	$(ASCII2MAN)

pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests"
	@echo "#############################################"
	pep8 lib/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	find ./docs/ -type f -name "*.xml" -delete
	find . -type f -name "#*" -delete

.PHONEY: docs manual clean pep8
vpath %.asciidoc docs/man/man1
