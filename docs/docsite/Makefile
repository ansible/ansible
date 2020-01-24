OS := $(shell uname -s)
SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"):
PLUGIN_FORMATTER=../../hacking/build-ansible.py document-plugins
TESTING_FORMATTER=../bin/testing_formatter.sh
KEYWORD_DUMPER=../../hacking/build-ansible.py document-keywords
CONFIG_DUMPER=../../hacking/build-ansible.py document-config
GENERATE_CLI=../../hacking/build-ansible.py generate-man
COLLECTION_DUMPER=../../hacking/build-ansible.py collection-meta
ifeq ($(shell echo $(OS) | egrep -ic 'Darwin|FreeBSD|OpenBSD|DragonFly'),1)
CPUS ?= $(shell sysctl hw.ncpu|awk '{print $$2}')
else
CPUS ?= $(shell nproc)
endif

# Sets the build output directory if it's not already specified
ifndef BUILDDIR
	BUILDDIR = _build
endif

MODULE_ARGS=
ifdef MODULES
	MODULE_ARGS = -l $(MODULES)
endif

PLUGIN_ARGS=
ifdef PLUGINS
	PLUGIN_ARGS = -l $(PLUGINS)
endif

DOC_PLUGINS ?= become cache callback cliconf connection httpapi inventory lookup netconf shell strategy vars

assertrst:
ifndef rst
	$(error specify document or pattern with rst=somefile.rst)
endif

all: docs

docs: htmldocs

generate_rst: collections_meta config cli keywords modules plugins testing

htmldocs: generate_rst
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
	-rm -rf module_docs
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
	@echo "Cleaning up generated rst"
	rm -f rst/modules/*_by_category.rst
	rm -f rst/modules/list_of_*.rst
	rm -f rst/modules/*_maintained.rst
	rm -f rst/modules/*_module.rst
	rm -f rst/modules/*_plugin.rst
	rm -f rst/playbooks_directives.rst
	rm -f rst/plugins/*/*.rst
	rm -f rst/reference_appendices/config.rst
	rm -f rst/reference_appendices/playbooks_keywords.rst
	rm -f rst/dev_guide/collections_galaxy_meta.rst
	rm -f rst/cli/*.rst

.PHONY: docs clean

collections_meta: ../templates/collections_galaxy_meta.rst.j2
	PYTHONPATH=../../lib $(COLLECTION_DUMPER) --template-file=../templates/collections_galaxy_meta.rst.j2 --output-dir=rst/dev_guide/ ../../lib/ansible/galaxy/data/collections_galaxy_meta.yml

# TODO: make generate_man output dir cli option
cli:
	mkdir -p rst/cli
	PYTHONPATH=../../lib $(GENERATE_CLI) --template-file=../templates/cli_rst.j2 --output-dir=rst/cli/ --output-format rst ../../lib/ansible/cli/*.py

keywords: ../templates/playbooks_keywords.rst.j2
	PYTHONPATH=../../lib $(KEYWORD_DUMPER) --template-dir=../templates --output-dir=rst/reference_appendices/ ./keyword_desc.yml

config: ../templates/config.rst.j2
	PYTHONPATH=../../lib $(CONFIG_DUMPER) --template-file=../templates/config.rst.j2 --output-dir=rst/reference_appendices/ ../../lib/ansible/config/base.yml

modules: ../templates/plugin.rst.j2
	PYTHONPATH=../../lib $(PLUGIN_FORMATTER) -t rst --template-dir=../templates --module-dir=../../lib/ansible/modules -o rst/modules/ $(MODULE_ARGS)

plugins: ../templates/plugin.rst.j2
	@echo "looping over doc plugins"
	for plugin in $(DOC_PLUGINS); \
	do \
		PYTHONPATH=../../lib $(PLUGIN_FORMATTER) -t rst --plugin-type $$plugin --template-dir=../templates --module-dir=../../lib/ansible/plugins/$$plugin -o rst $(PLUGIN_ARGS); \
	done

testing:
	$(TESTING_FORMATTER)

epub:
	(CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx epub)

htmlsingle: assertrst
	sphinx-build -j $(CPUS) -b html -d $(BUILDDIR)/doctrees ./rst $(BUILDDIR)/html rst/$(rst)
	@echo "Output is in $(BUILDDIR)/html/$(rst:.rst=.html)"
