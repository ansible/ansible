#!/usr/bin/make
ASCII2HTMLMAN = a2x -D man/ -d manpage -f xhtml
SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

all: clean docs

docs: clean
	./build-site.py

viewdocs: clean
	./build-site.py view

htmlman:
	mkdir -p man
	$(ASCII2HTMLMAN) ansible/docs/man/man1/ansible.1.asciidoc
	$(ASCII2HTMLMAN) ansible/docs/man/man1/ansible-playbook.1.asciidoc

htmldocs:
	 ./build-site.py rst

clean:
	@echo "Cleaning up byte compiled python stuff"
	find . -regex ".*\.py[co]$$" -delete
	@echo "Cleaning up editor backup files"
	find . -type f \( -name "*~" -or -name "#*" \) -delete
	find . -type f \( -name "*.swp" \) -delete

.PHONEY: docs manual clean
vpath %.asciidoc docs/man/man1


