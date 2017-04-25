**********
Unit Tests
**********

Unit tests are small isolated tests

.. contents:: Topics

Available Tests
===============


Running Tests
=============

Extending unit tests
====================

FIXME Details here ``test/units`` ``test/units/modules``

FIXME Link back to :doc:`testing_networking`

.. warning:: What a unit test isn't

   If you start writing a test that starts requiring external services then you may be writing an integration test, rather than a unit tests.

Fixtures files
``````````````

To mock out fetching results from devices you can use ``fixtures`` to read in pre-generated data.

Text files live in ``test/units/modules/network/PLATFORM/fixtures/``

Data is loaded using the ``load_fixture`` method

See  `eos_banner test <https://github.com/ansible/ansible/blob/devel/test/units/modules/network/eos/test_eos_banner.py>`_ for a practical example.

