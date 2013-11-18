Homepage and documentation source for Ansible
=============================================

This project hosts the source behind [ansibleworks.com/docs](http://www.ansibleworks.com/docs/)

Contributions to the documentation are welcome.  To make changes, submit a pull request
that changes the reStructuredText files in the "rst/" directory only, and Michael can
do a docs build and push the static files. If you wish to verify output from the markup
such as link references, you may [install Sphinx] and build the documentation by running
`make viewdocs` from the `ansible/docsite` directory.

If you do not want to learn the reStructuredText format, you can also [file issues] about
documentation problems on the Ansible GitHub project.

Note that module documentation can actually be [generated from a DOCUMENTATION docstring][module-docs]
in the modules directory, so corrections to modules written as such need to be made
in the module source, rather than in docsite source.

Author
======

Michael DeHaan -- michael.dehaan@gmail.com

[http://michaeldehaan.net](http://michaeldehaan.net/)

[install Sphinx]: http://sphinx-doc.org/install.html
[file issues]: https://github.com/ansible/ansible/issues
[module-docs]: http://www.ansibleworks.com/docs/developing_modules.html#documenting-your-module

