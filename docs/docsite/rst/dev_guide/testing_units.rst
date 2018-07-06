**********
Unit Tests
**********

Unit tests are small isolated tests that target a specific library or module.  Unit tests
in Ansible are currently the only way of driving tests from python within Ansible's
continuous integration process. This means that in some circumstances the tests may be a
bit wider than just units.

.. contents:: Topics

Available Tests
===============

Unit tests can be found in `test/units
<https://github.com/ansible/ansible/tree/devel/test/units>`_. Notice that the directory
structure of the tests matches that of ``lib/ansible/``.

Running Tests
=============

The Ansible unit tests can be run across the whole code base by doing:

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

You can also run tests in Ansible's continuous integration system by opening a pull
request.  This will automatically determine which tests to run based on the changes made
in your pull request.


Installing dependencies
=======================

``ansible-test`` has a number of dependencies. For ``units`` tests we suggest using ``tox``.

The dependencies can be installed using the ``--requirements`` argument, which will
install all the required dependencies needed for unit tests. For example:

.. code:: shell

   ansible-test units --tox --python 2.7 --requirements apache2_module


.. note:: tox version requirement

   When using ``ansible-test`` with ``--tox`` requires tox >= 2.5.0


The full list of requirements can be found at `test/runner/requirements
<https://github.com/ansible/ansible/tree/devel/test/runner/requirements>`_. Requirements
files are named after their respective commands. See also the `constraints
<https://github.com/ansible/ansible/blob/devel/test/runner/requirements/constraints.txt>`_
applicable to all commands.


Extending unit tests
====================


.. warning:: What a unit test isn't

   If you start writing a test that requires external services then
   you may be writing an integration test, rather than a unit test.


Structuring Unit Tests
``````````````````````

Ansible drives unit tests through `pytest <https://docs.pytest.org/en/latest/>`_. This
means that tests can either be written a simple functions which are included in any file
name like ``test_<something>.py`` or as classes. 

Here is an example of a function::

  #this function will be called simply because it is called test_*()

  def test_add()
      a = 10
      b = 23
      c = 33
      assert a + b = c
    
Here is an example of a class::

  import unittest
      
  class AddTester(unittest.TestCase)
      
      def SetUp()
          self.a = 10
          self.b = 23
 
      # this function will 
      def test_add()
        c = 33
        assert self.a + self.b = c

     # this function will 
      def test_subtract()
        c = -13
        assert self.a - self.b = c

Both methods work fine in most circumstances; the function-based interface is simpler and
quicker and so that's probably where you should start when you are just trying to add a
few basic tests for a module.  The class-based test allows more tidy set up and tear down
of pre-requisites, so if you have many test cases for your module you may want to refactor
to use that.  

Assertions using the simple ``assert`` function inside the tests will give full
information on the cause of the failure with a trace-back of functions called during the
assertion.  This means that plain asserts are recommended over other external assertion
libraries.

A number of the unit test suites include functions that are shared between several
modules, especially in the networking arena.  In these cases a file is created in the same
directory, which is then included directly.


Module test case common code
````````````````````````````

Keep common code as specific as possible within the `test/units/` directory structure. For
example, if it's specific to testing Amazon modules, it should be in
`test/units/modules/cloud/amazon/`. Don't import common unit test code from directories
outside the current or parent directories.

Don't import other unit tests from a unit test. Any common code should be in dedicated
files that aren't themselves tests.


Fixtures files
``````````````

To mock out fetching results from devices, or provide other complex datastructures that
come from external libraries, you can use ``fixtures`` to read in pre-generated data.

Text files live in ``test/units/modules/network/PLATFORM/fixtures/``

Data is loaded using the ``load_fixture`` method

See `eos_banner test
<https://github.com/ansible/ansible/blob/devel/test/units/modules/network/eos/test_eos_banner.py>`_
for a practical example.

If you are simulating APIs you may find that python placebo is useful.  See
:ref:`testing_units_modules` for more information.


Code Coverage For New or Updated Unit Tests
```````````````````````````````````````````
New code will be missing from the codecov.io coverage reports (see :doc:`testing`), so
local reporting is needed.  Most ``ansible-test`` commands allow you to collect code
coverage; this is particularly useful when to indicate where to extend testing.

To collect coverage data add the ``--coverage`` argument to your ``ansible-test`` command line:

.. code:: shell

   ansible-test units --coverage apt
   ansible-test coverage html

Results will be written to ``test/results/reports/coverage/index.html``

Reports can be generated in several different formats:

* ``ansible-test coverage report`` - Console report.
* ``ansible-test coverage html`` - HTML report.
* ``ansible-test coverage xml`` - XML report.

To clear data between test runs, use the ``ansible-test coverage erase`` command.  See
:ref:`testing_running_locally` for more information about generating coverage
reports.


.. seealso::

   :ref:`testing_units_modules`
       Special considerations for unit testing modules
   :doc:`testing_running_locally`
       Running tests locally including gathering and reporting coverage data
   `Python 3 documentation - 26.4. unittest — Unit testing framework <https://docs.python.org/3/library/unittest.html>`_
       The documentation of the unittest framework in python 3 
   `Python 2 documentation - 25.3. unittest — Unit testing framework <https://docs.python.org/3/library/unittest.html>`_
       The documentation of the earliest supported unittest framework - from Python 2.6
   `pytest: helps you write better programs <https://docs.pytest.org/en/latest/>`_
       The documentation of pytest - the framework actually used to run Ansible unit tests

