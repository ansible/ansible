***************
Testing Ansible
***************

.. contents:: Topics

This document describes how to:

* Run tests locally using ``ansible-test``
* Extend

Requirements
============

There are no special requirements for running ``ansible-test`` on Python 2.7 or later.
The ``argparse`` package is required for Python 2.6.
The requirements for each ``ansible-test`` command are covered later.


Test Environments
=================

Most ``ansible-test`` commands support running in one or more isolated test environments to simplify testing.


Remote
------

The ``--remote`` option runs tests in a cloud hosted environment.
An API key is required to use this feature.

    Recommended for integration tests.

See the `list of supported platforms and versions <https://github.com/ansible/ansible/blob/devel/test/runner/completion/remote.txt>`_ for additional details.


Interactive Shell
=================

Use the ``ansible-test shell`` command to get an interactive shell in the same environment used to run tests. Examples:

* ``ansible-test shell --docker`` - Open a shell in the default docker container.
* ``ansible-test shell --tox --python 3.6`` - Open a shell in the Python 3.6 ``tox`` environment.

Code Coverage
=============

Add the ``--coverage`` option to any test command to collect code coverage data.

Reports can be generated in several different formats:

* ``ansible-test coverage report`` - Console report.
* ``ansible-test coverage html`` - HTML report.
* ``ansible-test coverage xml`` - XML report.

To clear data between test runs, use the ``ansible-test coverage erase`` command.
