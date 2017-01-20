OS := $(shell uname -s)
SITELIB = $(shell python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"):
FORMATTER=../../hacking/module_formatter.py
DUMPER=../../hacking/dump_playbook_attributes.py
ifeq ($(shell echo $(OS) | egrep -ic 'Darwin|FreeBSD|OpenBSD|DragonFly'),1)
CPUS ?= $(shell sysctl hw.ncpu|awk '{print $$2}')
else
CPUS ?= $(shell nproc)
endif

all: docs

docs: clean htmldocs

htmldocs: directives modules staticmin
	CPUS=$(CPUS) $(MAKE) -f Makefile.sphinx html

webdocs: docs

#TODO: leaving htmlout removal for those having older versions, should eventually be removed also
clean:
	-rm -rf htmlout
	-rm -rf _build
	-rm -f .buildinfo
	-rm -f *.inv
	-rm -rf *.doctrees
	@echo "Cleaning up minified css files"
	find . -type f -name "*.min.css" -delete
	@echo "Cleaning up byte compiled python stuff"
	find . -regex ".*\.py[co]$$" -delete
	@echo "Cleaning up editor backup files"
	find . -type f \( -name "*~" -or -name "#*" \) -delete
	find . -type f \( -name "*.swp" \) -delete
	@echo "Cleaning up generated rst"
	-rm rst/list_of_*.rst
	-rm rst/*_by_category.rst
	-rm rst/*_module.rst
	-rm rst/playbooks_directives.rst

.PHONEY: docs clean

directives: $(FORMATTER) ../../hacking/templates/rst.j2
	PYTHONPATH=../../lib $(DUMPER) --template-dir=../../hacking/templates --output-dir=rst/

modules: $(FORMATTER) ../../hacking/templates/rst.j2
	PYTHONPATH=../../lib $(FORMATTER) -t rst --template-dir=../../hacking/templates --module-dir=../../lib/ansible/modules -o rst/

staticmin:
	cat _themes/srtd/static/css/theme.css | sed -e 's/^[ 	]*//g; s/[ 	]*$$//g; s/\([:{;,]\) /\1/g; s/ {/{/g; s/\/\*.*\*\///g; /^$$/d' | sed -e :a -e '$$!N; s/\n\(.\)/\1/; ta' > _themes/srtd/static/css/theme.min.css
