Testing Ansible
===============

How to run and create tests for the Ansible core engine and modules with ``ansible-test``.

Requirements
============

There are no special requirements for running ``ansible-test`` on Python 2.7 or later.
The ``argparse`` package is required for Python 2.6.
The requirements for each ``ansible-test`` command are covered later.

Setup
=====

#. Fork the `ansible/ansible <https://github.com/ansible/ansible/>`_ repository on Git Hub.
#. Clone your fork: ``git clone git@github.com:USERNAME/ansible.git``
#. Install the optional ``argcomplete`` package for tab completion (highly recommended):

   #. ``pip install argcomplete``
   #. ``activate-global-python-argcomplete``
   #. Restart your shell to complete global activation.

#. Configure your environment to run from your clone (once per shell): ``. hacking/env-setup``

Test Environments
=================

Most ``ansible-test`` commands support running in one or more isolated test environments to simplify testing.

Local
-----

The ``--local`` option runs tests locally without the use of an isolated test environment.
This is the default behavior.

    Recommended for ``compile`` tests.

See the `command requirements directory <runner/requirements/>`_ for the requirements for each ``ansible-test`` command.
Requirements files are named after their respective commands.
See also the `constraints <runner/requirements/constraints.txt>`_ applicable to all commands.

    Use the ``--requirements`` option to automatically install ``pip`` requirements relevant to the command being used.

Docker
------

The ``--docker`` option runs tests in a docker container.

    Recommended for ``integration`` tests.

This option accepts an optional docker container image.
See the `list of supported docker images <runner/completion/docker.txt>`_ for options.

    Use the ``--docker-no-pull`` option to avoid pulling the latest container image.
    This is required when using custom local images that are not available for download.

Tox
---

The ``--tox`` option run tests in a ``tox`` managed Python virtual environment.

    Recommended for ``windows-integration`` and ``units`` tests.

The following Python versions are supported:

* 2.6
* 2.7
* 3.5
* 3.6

By default, test commands will run against all supported Python versions when using ``tox``.

    Use the ``--python`` option to specify a single Python version to use for test commands.

Remote
------

The ``--remote`` option runs tests in a cloud hosted environment.
An API key is required to use this feature.

    Recommended for integration tests.

See the `list of supported platforms and versions <runner/completion/remote.txt>`_ for additional details.

General Usage
=============

Tests are run with the ``ansible-test`` command.
Consult ``ansible-test --help`` for usage information not covered here.

    Use the ``--explain`` option to see what commands will be executed without actually running them.

Running Tests
=============

There are four main categories of tests, each in their own directory.

* `compile <compile/>`_ - Python syntax checking for supported versions. Examples:

  * ``ansible-test compile`` - Check syntax for all supported versions.
  * ``ansible-test compile --python 3.5`` - Check only Python 3.5 syntax.

* `sanity <sanity/>`_ - Static code analysis and general purpose script-based tests. Examples:

  * ``ansible-test sanity --tox --python 2.7`` - Run all sanity tests on Python 2.7 using ``tox``.
  * ``ansible-test sanity --test pep8`` - Run the ``pep8`` test without ``tox``.

* `integration <integration/>`_ - Playbook based tests for modules and core engine functionality. Examples:

  * ``ansible-test integration ping --docker`` - Run the ``ping`` module test using ``docker``.
  * ``ansible-test windows-integration windows/ci/`` - Run all Windows tests covered by CI.

* `units <units/>`_ - API oriented tests using mock interfaces for modules and core engine functionality. Examples:

  * ``ansible-test units --tox`` - Run all unit tests on all supported Python versions using ``tox``.
  * ``ansible-test units --tox --python 2.7 test/units/vars/`` - Run specific tests on Python 2.7 using ``tox``.

Consult each of the test directories for additional details on usage and requirements.

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
