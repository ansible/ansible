***************
Testing Ansible
***************

.. contents:: Topics

Introduction
============

This page, and it's subpages, describes:

* how ansible is tested
* how to test Ansible locally
* how to extend the testing capabilities

Types of tests
==============

At a high level we have the following classifications of tests

:compile:
  * :doc:`testing_compile`
  * Test python code against a variety of Python versions.
:sanity:
  * :doc:`testing_sanity`
  * Sanity tests are made up of scripts and tools used to perform static code analysis.
  * The primary purpose of these tests is to enforce Ansible coding standards and requirements.
:integration:
  * :doc:`testing_integration`
  * Functional tests of modules and Ansible language and core functionality.
:network-integration:
  * :doc:`testing_network`
  * Tests for Ansible Networking
:windows-integration:
  * :doc:`testing_windows`
  * Tests for Windows.
:units:
  * :doc:`testing_units`
  * Tests directly directly against individual parts of the code base.


.. note:: Ansible Networking
   Network testing is a large topic that has it's that :doc:`testing_network` has a dedicated page regarding testing.



Link to Manual testing of PRs (testing_pullrequests.rst)
If you're a developer, one of the most valuable things you can do is look at the github issues list and help fix bugs.  We almost always prioritize bug fixing over
feature development, so clearing bugs out of the way is one of the best things you can do.

Even if you're not a developer, helping test pull requests for bug fixes and features is still immensely valuable.

This goes for testing new features as well as testing bugfixes.


Testing withing GitHub & Shippable
==================================

Organization
------------

FIXME Details of different jobs, overlap wi

Understanding the results
-------------------------

FIXME Example of Ansibullbot with two failures

.. code:: none

   The test `ansible-test sanity --test pep8` failed with the following errors:

   lib/ansible/modules/network/foo/bar.py:509:17: E265 block comment should start with '# '

   The test `ansible-test sanity --test validate-modules` failed with the following errors:
   lib/ansible/modules/network/foo/bar.py:0:0: E307 version_added should be 2.4. Currently 2.3
   lib/ansible/modules/network/foo/bar.py:0:0: E316 ANSIBLE_METADATA.metadata_version: required key not provided @ data['metadata_version']. Got None


FIXME How to look at Shippable

Rerunning a failing CI job
--------------------------

FIXME close/reopen or push another commit


Running the same tests locally
------------------------------

FIXME Include example

Want to know more
=================

FIXME Testing Working Group





FIXME Stuff to review and add
=============================


FIXME Look at TWG Etherpad
FIXME Look at Etherpad that contributor started
https://public.etherpad-mozilla.org/p/ansible-testing-notes


1) What type of testing we have

1.1) Where the files live in gitcheckout

2) How they get run in shippable

3) How to read and understand what Shippable/Ansibullbot is telling you

4) How to run locally

5) How to develop unit tests

6) How to develop integration tests

7) How to generate code coverage


FIXME See also links (to all test* pages)
