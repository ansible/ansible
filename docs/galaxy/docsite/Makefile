OS := $(shell uname -s)
#--SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"):
#--PLUGIN_FORMATTER=../../hacking/build-ansible.py document-plugins
#--TESTING_FORMATTER=../bin/testing_formatter.sh
#--KEYWORD_DUMPER=../../hacking/build-ansible.py document-keywords
#--CONFIG_DUMPER=../../hacking/build-ansible.py document-config
#--GENERATE_CLI=../../hacking/build-ansible.py generate-man
#--COLLECTION_DUMPER=../../hacking/build-ansible.py collection-meta
ifeq ($(shell echo $(OS) | egrep -ic 'Darwin|FreeBSD|OpenBSD|DragonFly'),1)
CPUS ?= $(shell sysctl hw.ncpu|awk '{print $$2}')
else
CPUS ?= $(shell nproc)
endif

# Sets the build output directory if it's not already specified
ifndef BUILDDIR
	BUILDDIR = _build
endif

assertrst:
ifndef rst
	$(error specify document or pattern with rst=somefile.rst)
endif

all: docs

docs: htmldocs


htmldocs:
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx html

singlehtmldocs: generate_rst
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx singlehtml

webdocs: docs

#TODO: leaving htmlout removal for those having older versions, should eventually be removed also
clean:
	@echo "Cleaning $(BUILDDIR)"
	-rm -rf $(BUILDDIR)/doctrees
	-rm -rf $(BUILDDIR)/html
	-rm -rf htmlout
	-rm -rf _build
	-rm -f .buildinfo
	-rm -f objects.inv
	-rm -rf *.doctrees
	@echo "Cleaning up minified css files"
	find . -type f -name "*.min.css" -delete
	@echo "Cleaning up byte compiled python stuff"
	find . -regex ".*\.py[co]$$" -delete
	@echo "Cleaning up editor backup files"
	find . -type f \( -name "*~" -or -name "#*" \) -delete
	find . -type f \( -name "*.swp" \) -delete


.PHONY: docs clean

epub:
	(CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx epub)

htmlsingle: assertrst
	sphinx-build -j $(CPUS) -b html -d $(BUILDDIR)/doctrees ./rst $(BUILDDIR)/html rst/$(rst)
	@echo "Output is in $(BUILDDIR)/html/$(rst:.rst=.html)"
