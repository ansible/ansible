Collection template
-------------------
-------------------

This readme file should contain a the name and a short description/quick docs of the collection
and an optional link to `docs/` for more complete documentation.

current dir structure:
----------------------

* docs/: local documentation for the collection
* license.txt: optional copy of license(s) for this collection
* galaxy.yml: source data for the MANIFEST.json that will be part of the collection package
* playbooks/: playbooks reside here
	tasks/:	this holds 'task list files' for include_tasks/import_tasks usage
* plugins/: all ansible plugins and modules go here, each in its own subdir
  * modules/: ansible modules
  * lookups/: lookup plugins
  * filters/: Jinja2 filter plugins
  * ... rest of plugins
* README.md or README.rst: this file
* roles/: directory for ansible roles
* tests/: tests for the collection's content
