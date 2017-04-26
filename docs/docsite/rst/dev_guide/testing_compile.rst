*************
Compile Tests
*************

.. contents:: Topics

Overview
========

Compile tests check source files for valid syntax on all supported python versions:

- 2.4 (Ansible 2.3 only)
- 2.6
- 2.7
- 3.5
- 3.6

Running compile tests locally
=============================

Tests are run with ``ansible-test compile``.

All versions are tested unless the ``--python`` option is used.

All ``*.py`` files are tested unless specific files are specified.

For advanced options see ``ansible-test compile --help``

Extending compile tests
=======================

If you believe changes are needed to the Compile tests please add a comment on the `Testing Working Group Agenda <https://github.com/ansible/community/blob/master/MEETINGS.md>`_ so it can be discussed.
