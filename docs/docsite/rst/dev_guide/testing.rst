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

* compile
* sanity
* integration
* network-integration
* windows-integration
* units




FIXME High level detail, with links to subpages for: Unit (compile, sanity, etc), integration,

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

Running the same tests locally
------------------------------



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

1.2) Where different tests should be extended

2) How they get run in shippable

3) How to read and understand what Shippable/Ansibullbot is telling you

4) How to run locally

5) How to develop unit tests

6) How to develop integration tests

7) How to generate code coverage


FIXME See also links (to all test* pages)
