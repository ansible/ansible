Ansible Testing
===============


Who am I?
=========

John Barker

* Principal Engineer, Ansible by Red Hat
* Hats: Ansible Networking, QA and community
* Freenode/GitHub: gundalow

Ansible Testing
===============

* History of testing Ansible
* How `you` can develop tests
* Where to find out more

.. container:: handout

   Set the scene
     Quick taster, give you enought to know what's possible and where to find out more

   Testing Working Group

     gundalow & Matt Clay

   Tailor content:

     * Q: Show of hands for version, devel -> 1.9? - upgrade!
     * Q: Who's raised a PR?
     * Q: Module PR?


This talk is Free Software
==========================

* Written for `presentty` https://pypi.python.org/pypi/presentty
* ``docs/docsite/rst/presentations/ansible-testing.rst`` (once I've committed it)

.. container:: handout

   Will update with feedback
   Add link from the Meetup event
   Questions welcome at anypoint


Requirements
============

What do we want from testing Ansible

* Different OS, python versions
* Ability to run same tests locally
* Reasonable run time

.. container:: handout

   Increasing tha matrix of Python & OS versions vs timely feedback

Solution: ansible-test
======================

* Different OS/Py: Docker & tox
* Local runs: Shippable is just a wrapper
* Duration: Inspect git diff. File to test mapping. Nightly runs

``test/runner/ansible-test``

.. container:: handout

   Into Matt Clay
   Duration: Tracking of Python imports

Types of tests
==============

:compile:
  * Test python code against a variety of Python versions.
:sanity:
  * Sanity tests are made up of scripts and tools used to perform static code analysis.
  * The primary purpose of these tests is to enforce Ansible coding standards and requirements.
:integration:
  * Functional tests of modules and Ansible core functionality.
:units:
  * Tests directly against individual parts of the code base.

Ansible-test Platform Features
==============================

* Python versions
* OS versions
   * Linux via Docker
   *  AWS, or macstadium)
* Network version
* Cloud platforms (AWS, others coming soon)

.. container:: handout

   * DEMO: show shippable

     * Show list of platforms


Improving Testing
=================

Spot common issues
 * Document how it should be done
 * Improve existing code
 * Enforce higher standard via CI

2.1: added integration testing using docker containers
2.2: switched from Travis to Shippable, added Windows, FreeBSD and OSX testing, added more docker containers
2.3: SINGLE REPO (therefore versioned along side code),  ansible-test, integration testing for network modules

Improvements in 2.4
===================


* added “cloud” module testing (AWD, CloudStack, VMware [in progress])
* enhanced code coverage analysis [in progress]

* Unit tests for core modules
* pep8
* pylint
* rstcheck
* Module DOCUMENTATION
* Module RETURNS

.. container:: handout

   The last three have dramaticly improved our online documentation. Previously some module docs were not being displayed at all


Testing Working Group
=====================

Subscribe to the GitHub issue for updates

Demo
====

Lets look at a PR...



.. container:: handout

   * FIXME link to PR
   * Start with a PR
   * Show the different checks that have failed
   * Command that you can run locally
   * Shippable
     * Generaly you wouldn't need to look here
     * List of platforms
     * Tests tab on left hand side
     * Show console
     * Describe "unstable tests"


Unit Tests: Creating
====================

``test/units/``

If you start writing a test that requires external services then you may be writing an integration test, rather than a unit test.

.. container:: handout

   That's all I'm going to say on unit tests
   For more info join ``#ansible-devel``

Integration Tests: Why?
=======================

If you can write a Playbook you can write a test
Much easier to write than an unit test
Testing the interface, can deal with module being rewritten


.. container:: handout

   FIXME: Need to sell/convince people

Integration Tests: File structure
=================================

Directory: ``test/integration/targets/file/``

.. code::
   :caption: file/aliases

   posix/ci/group2
   needs/root

.. code::
   :caption: file/tasks/main.yml

   # Standard playbook
   
