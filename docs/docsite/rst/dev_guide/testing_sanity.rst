************
Sanity Tests
************

.. contents:: Topics

Sanity tests are made up of scripts and tools used to perform static code analysis.
The primary purpose of these tests is to enforce Ansible coding standards and requirements.

Tests are run with ``ansible-test sanity``.
All available tests are run unless the ``--test`` option is used.

Available Tests
===============

Tests can be listed with ``ansible-test sanity --list-tests``.

This list is a combination of two different categories of tests, "Code Smell" and "Built-in".

Code Smell Tests
----------------

Miscellaneous `scripts <https://github.com/ansible/ansible/tree/devel/test/sanity/code-smell/>`_ used for enforcing coding standards and requirements, identifying trip hazards, etc.

These tests are listed and accessed by script name. There is no actual test named ``code-smell``.

All executable scripts added to the ``code-smell`` directory are automatically detected and executed by ``ansible-test``.

Scripts in the directory which fail can be skipped by adding them to `skip.txt <https://github.com/ansible/ansible/blob/devel/test/sanity/code-smell/skip.txt>`_.
This is useful for scripts which identify issues that have not yet been resolved in the code base.

Files tested are specific to the individual test scripts and are not affected by command line arguments.

Built-in Tests
--------------

These tests are integrated directly into ``ansible-test``.
All files relevant to each test are tested unless specific files are specified.

A full list of tests can be obtained by doing ``ansible-test sanity --list-tests``.

ansible-doc
~~~~~~~~~~~

Verifies that ``ansible-doc`` can parse module documentation on all supported python versions.

pep8
~~~~

Python static analysis for PEP 8 style guideline compliance. See :doc:`testing_pep8` for more information.

pylint
~~~~~~

Python static analysis for common programming errors.

rstcheck
~~~~~~~~

Check reStructuredText files for syntax and formatting issues.

shellcheck
~~~~~~~~~~

Static code analysis for shell scripts using the excellent `shellcheck <https://www.shellcheck.net/>`_ tool.

validate-modules
~~~~~~~~~~~~~~~~

Analyze modules for common issues in code and documentation. See :doc:`testing_validate-modules` for more information.

yamllint
~~~~~~~~

Check YAML files for syntax and formatting issues.


