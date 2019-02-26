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

   # Run all tests inside docker (good if you don't have dependencies installed)
   ansible-test sanity --docker default

   # Run validate-modules against a specific file
   ansible-test sanity --test validate-modules lib/ansible/modules/files/template.py

Available Tests
===============

Tests can be listed with ``ansible-test sanity --list-tests``.

See the full list of :ref:`sanity tests <all_sanity_tests>`, which details the various tests and details how to fix identified issues.
