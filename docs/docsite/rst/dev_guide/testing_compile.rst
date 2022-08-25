:orphan:

.. _testing_compile:

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
- 3.7
- 3.8
- 3.9

NOTE: In Ansible 2.4 and earlier the compile test was provided by a dedicated sub-command ``ansible-test compile`` instead of a sanity test using ``ansible-test sanity --test compile``.

Running compile tests locally
=============================

Compile tests can be run across the whole code base by doing:

.. code:: shell

    cd /path/to/ansible/source
    source hacking/env-setup
    ansible-test sanity --test compile

Against a single file by doing:

.. code:: shell

   ansible-test sanity --test compile lineinfile

Or against a specific Python version by doing:

.. code:: shell

   ansible-test sanity --test compile --python 2.7 lineinfile

For advanced usage see the help:

.. code:: shell

   ansible-test sanity --help


Installing dependencies
=======================

``ansible-test`` has a number of dependencies , for ``compile`` tests we suggest running the tests with ``--local``, which is the default

The dependencies can be installed using the ``--requirements`` argument. For example:

.. code:: shell

   ansible-test sanity --test compile --requirements lineinfile



The full list of requirements can be found at `test/lib/ansible_test/_data/requirements <https://github.com/ansible/ansible/tree/devel/test/lib/ansible_test/_data/requirements>`_. Requirements files are named after their respective commands. See also the `constraints <https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_data/requirements/constraints.txt>`_ applicable to all commands.


Extending compile tests
=======================

If you believe changes are needed to the compile tests please add a comment on the `Testing Working Group Agenda <https://github.com/ansible/community/blob/main/meetings/README.md>`_ so it can be discussed.
