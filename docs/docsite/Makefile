OS := $(shell uname -s)
SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"):
PLUGIN_FORMATTER=../../hacking/build-ansible.py docs-build
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

# Intenationalisation and Localisation
LANGUAGES ?=

# Sets the build output directory for the main docsite if it's not already specified
ifndef BUILDDIR
	BUILDDIR = _build
endif

ifndef POTDIR
	POTDIR = $(BUILDDIR)/gettext
endif

# Backwards compat for separate VARS
PLUGIN_ARGS=
ifdef MODULES
ifndef PLUGINS
	PLUGIN_ARGS = -l $(MODULES)
else
	PLUGIN_ARGS = -l $(MODULES),$(PLUGINS)
endif
else
ifdef PLUGINS
	PLUGIN_ARGS = -l $(PLUGINS)
endif
endif

ANSIBLE_VERSION_ARGS=
ifdef ANSIBLE_VERSION
	ANSIBLE_VERSION_ARGS=--ansible-version=$(ANSIBLE_VERSION)
endif

DOC_PLUGINS ?= become cache callback cliconf connection httpapi inventory lookup netconf shell strategy vars

PYTHON=python
# fetch version from project release.py as single source-of-truth
VERSION := $(shell $(PYTHON) ../../packaging/release/versionhelper/version_helper.py --raw || echo error)
ifeq ($(findstring error,$(VERSION)), error)
$(error "version_helper failed")
endif

MAJOR_VERSION := $(shell $(PYTHON) ../../packaging/release/versionhelper/version_helper.py --majorversion || echo error)
ifeq ($(findstring error,$(MAJOR_VERSION)), error)
$(error "version_helper failed to determine major version")
endif

assertrst:
ifndef rst
	$(error specify document or pattern with rst=somefile.rst)
endif

all: docs

docs: htmldocs

coredocs: core_htmldocs

generate_rst: collections_meta config cli keywords plugins testing
core_generate_rst: collections_meta config cli keywords base_plugins testing

# At the moment localizing the plugins and collections is not required for the ongoing
# localisation effort. It will come at a later time.
gettext_generate_rst: collections_meta config cli keywords testing

# The following two symlinks are necessary to produce two different docsets
# from the same set of rst files (Ansible the package docs, and core docs).
# Symlink the relevant index into place for building Ansible docs
ansible_structure:
	# We must have python and python-packaging for the version_helper
	# script so use it for version comparison
	if python -c "import sys, packaging.version as p; sys.exit(not p.Version('$(MAJOR_VERSION)') >  p.Version('2.10'))" ; then \
		echo "Creating symlinks in ansible_structure"; \
		ln -sf ../rst/ansible_index.rst rst/index.rst; \
		ln -sf ../sphinx_conf/ansible_conf.py rst/conf.py; \
	else \
		echo 'Creating symlinks for older ansible in ansible_structure'; \
		ln -sf ../rst/2.10_index.rst rst/index.rst; \
		ln -sf ../sphinx_conf/2.10_conf.py rst/conf.py; \
	fi

# Symlink the relevant index into place for building core docs
core_structure:
	@echo "Creating symlinks in core_structure"
	-ln -sf ../rst/core_index.rst rst/index.rst
	-ln -sf ../sphinx_conf/core_conf.py rst/conf.py

# Symlink the relevant index into place for building core docs
gettext_structure:
	@echo "Creating symlinks in gettext_structure"
	-ln -sf ../rst/core_index.rst rst/index.rst
	-ln -sf ../sphinx_conf/all_conf.py rst/conf.py

gettext: gettext_structure gettext_generate_rst
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx gettext
	# if msgcat is installed handle all indexes, otherwise use the index from gettext_structure.
	-msgcat "$(POTDIR)/core_index.pot" "$(POTDIR)/ansible_index.pot" "$(POTDIR)/2.10_index.pot" > "$(POTDIR)/tmp_index.pot" && mv "$(POTDIR)/tmp_index.pot" "$(POTDIR)/index.pot"
	rm "$(POTDIR)/core_index.pot" "$(POTDIR)/ansible_index.pot" "$(POTDIR)/2.10_index.pot"

generate-po:
ifeq ($(LANGUAGES),)
	@echo 'LANGUAGES is not defined. It is mandatory. LANGUAGES should be a comma separated list of languages to support. (Exampe: fr,es)'
else
	(cd docs/docsite/; sphinx-intl update -w 0 -d rst/locales -p "$(POTDIR)" -l $(LANGUAGES))
endif

needs-translation:
ifeq ($(LANGUAGES),)
	@echo 'LANGUAGES is not defined. It is mandatory. LANGUAGES should be a comma separated list of languages to support. (Exampe: fr,es)'
else
	(cd docs/docsite/; sphinx-intl stat -d rst/locales -l $(LANGUAGES) | grep -E ' [1-9][0-9]* (fuzzy|untranslated)' | sort)
endif

htmldocs: ansible_structure generate_rst
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx html

core_htmldocs: core_structure core_generate_rst
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx html

singlehtmldocs: ansible_structure generate_rst
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx singlehtml

core_singlehtmldocs: core_structure core_generate_rst
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx singlehtml

# Note: The linkcheckdocs and htmlsingle targets depend on gettext_structure
# because that one does not exclude any rst files in its conf.py.
linkcheckdocs: gettext_structure generate_rst
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx linkcheck

htmlsingle: assertrst gettext_structure
	sphinx-build -j $(CPUS) -b html -d $(BUILDDIR)/doctrees ./rst $(BUILDDIR)/html rst/$(rst)
	@echo "Output is in $(BUILDDIR)/html/$(rst:.rst=.html)"

webdocs: docs

#TODO: leaving htmlout removal for those having older versions, should eventually be removed also
clean:
	@echo "Cleaning $(BUILDDIR)"
	-rm -rf $(BUILDDIR)/doctrees
	-rm -rf $(BUILDDIR)/html
	-rm -rf htmlout
	-rm -rf module_docs
	-rm -rf $(BUILDDIR)
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
	rm -f rst/playbooks_directives.rst
	rm -f rst/reference_appendices/config.rst
	rm -f rst/reference_appendices/playbooks_keywords.rst
	rm -f rst/dev_guide/collections_galaxy_meta.rst
	rm -f rst/cli/*.rst
	for filename in `ls rst/collections/` ; do \
		if test x"$$filename" != x'all_plugins.rst' ; then \
			rm -rf "rst/collections/$$filename"; \
		fi \
	done
	@echo "Cleanning up generated ansible_structure"
	find . -type l -delete
	@echo "Cleaning up legacy generated rst locations"
	rm -rf rst/modules
	rm -f rst/plugins/*/*.rst

.PHONY: docs clean

collections_meta: ../templates/collections_galaxy_meta.rst.j2
	$(COLLECTION_DUMPER) --template-file=../templates/collections_galaxy_meta.rst.j2 --output-dir=rst/dev_guide/ $(EXTRA_COLLECTION_META_ARGS) ../../lib/ansible/galaxy/data/collections_galaxy_meta.yml

# TODO: make generate_man output dir cli option
cli:
	mkdir -p rst/cli
	$(GENERATE_CLI) --template-file=../templates/cli_rst.j2 --output-dir=rst/cli/ --output-format rst $(EXTRA_CLI_DUMPER_ARGS) ../../lib/ansible/cli/*.py

keywords: ../templates/playbooks_keywords.rst.j2
	$(KEYWORD_DUMPER) --template-dir=../templates --output-dir=rst/reference_appendices/ ../../lib/ansible/keyword_desc.yml $(EXTRA_KEYWORD_DUMPER_ARGS)

config: ../templates/config.rst.j2
	$(CONFIG_DUMPER) --template-file=../templates/config.rst.j2 --output-dir=rst/reference_appendices/ $(EXTRA_CONFIG_DUMPER_ARGS) ../../lib/ansible/config/base.yml

plugins:
	$(PLUGIN_FORMATTER) full -o rst $(ANSIBLE_VERSION_ARGS) $(EXTRA_PLUGIN_FORMATTER_ARGS) $(PLUGIN_ARGS)

# This only builds the plugin docs included with ansible-core
base_plugins:
	$(PLUGIN_FORMATTER) base -o rst $(EXTRA_PLUGIN_FORMATTER_ARGS) $(PLUGIN_ARGS)

testing:
	$(TESTING_FORMATTER)

epub:
	(CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx epub)
