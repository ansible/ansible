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
    ansible-test units 


For advanced usage see the online help::

   ansible-test units --help

Extending unit tests
====================


.. warning:: What a unit test isn't

   If you start writing a test that starts requiring external services then you may be writing an integration test, rather than a unit tests.

Fixtures files
``````````````

To mock out fetching results from devices you can use ``fixtures`` to read in pre-generated data.

Text files live in ``test/units/modules/network/PLATFORM/fixtures/``

Data is loaded using the ``load_fixture`` method

See  `eos_banner test <https://github.com/ansible/ansible/blob/devel/test/units/modules/network/eos/test_eos_banner.py>`_ for a practical example.

Code Coverage
`````````````

When writing unit tests it can be usefull to generate code coverage data and use this to guide you in where to add extra tests.


.. code:: shell

    ansible-test units --coverage
    ansible-test coverage html