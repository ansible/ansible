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

What do we want from testing Ansible:

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
   Different OS + Local runs fit together
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
   * FreeBSD, Windows, Network via AWS
   *  OSX via Parallels
* Network version
* Cloud platforms (AWS, others coming soon)

.. container:: handout

   * Docker images are available for you to use locally ``ansible-test --docker``

Improving Testing
=================

Spot common issues
 * Document how it should be done
 * Improve existing code
 * Enforce higher standard via CI

2.1: added integration testing using docker containers
2.2: switched from Travis to Shippable, added Windows, FreeBSD and OSX testing, added more docker containers
2.3: SINGLE REPO (therefore versioned along side code),  ansible-test, integration testing for network modules

.. container:: handout

   Bulk changes that update all modules are prefered, though speak to us first

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
   * Show the different checks that have failed - Only sanity & compile tests are listed
   * Command that you can run locally
   * Shippable
     * Need to look here if an unit or integration test has failed
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

.. code-block:: bash
   :caption: file/aliases

   posix/ci/group2
   needs/root

.. code-block:: bash
   :caption: file/tasks/main.yml

   # Standard playbook


Integration Tests: Test structure
=================================

* Setup (ensure clean state)
* Set & register
* Check result & changed
* Set again (idempotent)
* Check no change
* Repeat for ``state=absent``
* Teardown

.. container:: handout

  Find an example of this


Integration Tests: Best practices
=================================

* tempdir
* Add tests before refactoring


Code Coverage
=============

* Helps you find gaps
* Now run nightly

Cloud Tests
===========

* Currently undergoing changes
* Aim: all AWS tests will be invoked via ``ansible-test``

Network Tests
=============


Where to find out more
======================

* https://docs.ansible.com/ansible/dev_guide/testing.html
  * Testing working group
* Freenode: ``#ansible-devel``
* Writing tests is easy (install ``argcomplete``)
