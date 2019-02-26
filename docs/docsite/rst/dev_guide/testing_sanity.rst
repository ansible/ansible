:orphan:

.. _testing_sanity:

************
Sanity Tests
************

.. contents:: Topics

Sanity tests are made up of scripts and tools used to perform static code analysis.
The primary purpose of these tests is to enforce Ansible coding standards and requirements.

Tests are run with ``ansible-test sanity``.
All available tests are run unless the ``--test`` option is used.


How to run
==========

.. code:: shell

   source hacking/env-setup

   # Run all sanity tests
   ansible-test sanity

   # Run all sanity tests against against certain files
   ansible-test sanity lib/ansible/modules/files/template.py

   # Run all tests
   ansible-test sanity


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

