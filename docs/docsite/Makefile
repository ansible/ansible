OS := $(shell uname -s)
SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"):
FORMATTER=../bin/plugin_formatter.py
TESTING_FORMATTER=../bin/testing_formatter.sh
DUMPER=../bin/dump_keywords.py
CONFIG_DUMPER=../bin/dump_config.py
GENERATE_CLI=../bin/generate_man.py
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

DOC_PLUGINS ?= cache callback connection inventory lookup shell strategy vars

assertrst:
ifndef rst
	$(error specify document or pattern with rst=somefile.rst)
endif

all: docs

docs: clean htmldocs

generate_rst: staticmin config cli keywords modules plugins testing

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
	-rm rst/cli/ansible-*.rst
	-rm rst/cli/ansible.rst
	-rm rst/modules/*_by_category.rst
	-rm rst/modules/list_of_*.rst
	-rm rst/modules/*_maintained.rst
	-rm rst/modules/*_module.rst
	-rm rst/modules/*_plugin.rst
	-rm rst/playbooks_directives.rst
	-rm rst/plugins/*/*.rst
	-rm rst/reference_appendices/config.rst
	-rm rst/reference_appendices/playbooks_keywords.rst

.PHONY: docs clean

# TODO: make generate_man output dir cli option
cli: $(GENERATE_CLI)
	mkdir -p rst/cli
	PYTHONPATH=../../lib $(GENERATE_CLI) --template-file=../templates/cli_rst.j2 --output-dir=rst/cli/ --output-format rst ../../lib/ansible/cli/*.py

keywords: $(FORMATTER) ../templates/playbooks_keywords.rst.j2
	PYTHONPATH=../../lib $(DUMPER) --template-dir=../templates --output-dir=rst/reference_appendices/ -d ./keyword_desc.yml

config:
	PYTHONPATH=../../lib $(CONFIG_DUMPER) --template-file=../templates/config.rst.j2 --output-dir=rst/reference_appendices/ -d ../../lib/ansible/config/base.yml

modules: $(FORMATTER) ../templates/plugin.rst.j2
	PYTHONPATH=../../lib $(FORMATTER) -t rst --template-dir=../templates --module-dir=../../lib/ansible/modules -o rst/modules/ $(MODULE_ARGS)

plugins: $(FORMATTER) ../templates/plugin.rst.j2
	@echo "looping over doc plugins"
	for plugin in $(DOC_PLUGINS); \
	do \
		PYTHONPATH=../../lib $(FORMATTER) -t rst --plugin-type $$plugin --template-dir=../templates --module-dir=../../lib/ansible/plugins/$$plugin -o rst $(PLUGIN_ARGS); \
	done

testing:
	$(TESTING_FORMATTER)

staticmin:
	cat _themes/srtd/static/css/theme.css | sed -e 's/^[ 	]*//g; s/[ 	]*$$//g; s/\([:{;,]\) /\1/g; s/ {/{/g; s/\/\*.*\*\///g; /^$$/d' | sed -e :a -e '$$!N; s/\n\(.\)/\1/; ta' > _themes/srtd/static/css/theme.min.css

epub:
	(CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx epub)

htmlsingle: assertrst
	sphinx-build -j $(CPUS) -b html -d $(BUILDDIR)/doctrees ./rst $(BUILDDIR)/html rst/$(rst)
	@echo "Output is in $(BUILDDIR)/html/$(rst:.rst=.html)"
