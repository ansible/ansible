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

Unit tests can be run across the whole code base by doing:

.. code:: shell

    cd /path/to/ansible/source
    source hacking/env-setup
    ansible-test compile

Against a single file by doing:

.. code:: shell

   ansible-test compile lineinfile

Or against a specific Python version by doing:

.. code:: shell

   ansible-test compile --python 2.7 lineinfile

For advanced usage see the help:

.. code:: shell

   ansible-test units --help


Installing dependencies
=======================

``ansible-test`` has a number of dependencies , for ``compile`` tests we suggest running the tests with ``--local``, which is the default

The dependencies can be installed using the ``--requirements`` argument. For example:

.. code:: shell

   ansible-test units --requirements lineinfile



The full list of requirements can be found at `test/runner/requirements <https://github.com/ansible/ansible/tree/devel/test/runner/requirements>`_. Requirements files are named after their respective commands. See also the `constraints <https://github.com/ansible/ansible/blob/devel/test/runner/requirements/constraints.txt>`_ applicable to all commands.


Extending compile tests
=======================

If you believe changes are needed to the Compile tests please add a comment on the `Testing Working Group Agenda <https://github.com/ansible/community/blob/master/meetings/README.md>`_ so it can be discussed.
