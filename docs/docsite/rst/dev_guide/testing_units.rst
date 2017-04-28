**********
Unit Tests
**********

Unit tests are small isolated tests that target a specific library or module.

.. contents:: Topics

Available Tests
===============

Unit tests can be found in `test/units <https://github.com/ansible/ansible/tree/devel/test/units>`_, notice that the directory structure matches that of ``lib/ansible/``

Running Tests
=============

Unit tests can be run across the whole code base by doing:

.. code:: shell

    cd /path/to/ansible/source
    source hacking/env-setup
    ansible-test units --tox

Against a single file by doing:

.. code:: shell

   ansible-test units --tox apt

Or against a specific Python version by doing:

.. code:: shell

   ansible-test units --tox --python 2.7 apt



For advanced usage see the online help::

   ansible-test units --help


Installing dependencies
=======================

``ansible-test`` has a number of dependencies , for ``units`` tests we suggest using ``tox``

The dependencies can be installed using the ``--requirements`` argument. For example:

.. code:: shell

   ansible-test units --tox --python 2.7 --requirements apt


.. note:: tox version requirement

   When using ``ansible-test`` with ``--tox`` requires tox >= 2.5.0


The full list of requirements can be found at `test/runner/requirements <https://github.com/ansible/ansible/tree/devel/test/runner/requirements>`_. Requirements files are named after their respective commands. See also the `constraints <https://github.com/ansible/ansible/blob/devel/test/runner/requirements/constraints.txt>`_ applicable to all commands.


Extending unit tests
====================


.. warning:: What a unit test isn't

   If you start writing a test that requires external services then you may be writing an integration test, rather than a unit test.

Fixtures files
``````````````

To mock out fetching results from devices, you can use ``fixtures`` to read in pre-generated data.

Text files live in ``test/units/modules/network/PLATFORM/fixtures/``

Data is loaded using the ``load_fixture`` method

See  `eos_banner test <https://github.com/ansible/ansible/blob/devel/test/units/modules/network/eos/test_eos_banner.py>`_ for a practical example.

Code Coverage
`````````````
Most ``ansible-test`` commands allow you to collect code coverage, this is particularly useful when to indicate where to extend testing.

To collect coverage data add the ``--coverage`` argument to your ``ansible-test`` command line:

.. code:: shell

   ansible-test units --coverage apt
   ansible-test coverage html

Results will be written to ``test/results/reports/coverage/index.html``

Reports can be generated in several different formats:

* ``ansible-test coverage report`` - Console report.
* ``ansible-test coverage html`` - HTML report.
* ``ansible-test coverage xml`` - XML report.

To clear data between test runs, use the ``ansible-test coverage erase`` command. For a full list of features see the online help::

   ansible-test coverage --help

