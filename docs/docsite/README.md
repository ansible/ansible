Homepage and documentation source for Ansible
=============================================

This project hosts the source behind [docs.ansible.com](https://docs.ansible.com/)

Contributions to the documentation are welcome. To make changes, submit a pull request that changes the reStructuredText files in the `rst/` directory only, and the core team can do a docs build and push the static files.

If you wish to verify output from the markup such as link references, you may install sphinx and build the documentation by running `make viewdocs` from the `ansible/docsite` directory.

To include module documentation you'll need to run `make webdocs` at the top level of the repository. The generated html files are in `docsite/htmlout/`.

To limit module documentation building to a specific module, run `MODULES=NAME make webdocs` instead. This should make testing module documentation syntax much faster. Instead of a single module, you can also specify a comma-separated list of modules. In order to skip building documentation for all modules, specify non-existing module name, for example `MODULES=none make webdocs`.

If you do not want to learn the reStructuredText format, you can also [file issues] about documentation problems on the Ansible GitHub project.

Note that module documentation can actually be [generated from a DOCUMENTATION docstring][module-docs] in the modules directory, so corrections to modules written as such need to be made in the module source, rather than in docsite source.

To install sphinx and the required theme, install pip and then "pip install sphinx sphinx_rtd_theme"

[file issues]: https://github.com/ansible/ansible/issues
[module-docs]: https://docs.ansible.com/developing_modules.html#documenting-your-module

HEADERS
=======

RST allows for arbitrary hierchy for the headers, it will 'learn on the fly' but we want a standard so all our documents can follow:

```
##########################
# with overline, for parts
##########################

*****************************
* with overline, for chapters
*****************************

=, for sections
===============

-, for subsections
------------------

^, for sub-subsections
^^^^^^^^^^^^^^^^^^^^^

", for paragraphs
"""""""""""""""""

```

We do have pages littered with ```````` headers, but those should be removed for one of the above.
