Ansible Testing
===============


Current as of Ansible 2.3 (May 2017)

Who am I?
=========

John Barker

* Principal Engineer, Ansible by Red Hat
* Hats: Ansible Networking, QA and community
* Freenode/GitHub: `gundalow <https://github.com/gundalow>`_

.. container:: handout

    Based in the UK

Ansible Testing
===============

* History of testing Ansible
* How `you` can develop tests
* Where to find out more

.. container:: handout

   Set the scene

     * Quick taster, give you enough to know what's possible and point you in the right direction

   Testing Working Group

     * Setup after AnsibleFest SanFran 2016, ~ year
     * gundalow & Matt Clay, good community

   Tailor content:

     * Q: Show of hands for version, devel, 2.3, -> 1.9? - upgrade!
     * Q: Who's raised a PR?
     * Q: Updated a module (bug fix or functionality)
     * Q: Created a new module - how long ago (should have improved)


This talk is Free Software
==========================

* Written for `presentty` https://pypi.python.org/pypi/presentty
* ``docs/docsite/rst/presentations/ansible-testing.rst`` (once I've committed it)

.. container:: handout

   * Trialing new way of doing presentations
   * Will be on website
   * Aim is that they will evolve over time
   * RST contains speakers notes, which have more detail
   * Add link from the Meetup event
   * Questions welcome at anypoint - Will ask Mark to make a note


Requirements
============

What do we want from testing Ansible:

* Ability to run same tests locally as run by CI (Shippable)
* Different OS, Python versions (2.4+, 3.5+)
* Reasonable run time

.. container:: handout

   * Local run - common request from the community
   * Increasing tha matrix of Python & OS versions vs timely feedback
   * Main aim: Stable product, find issues sooner, speed up PR work flow



Solution: ansible-test
======================

* Shippable
* Different OS & Python: Docker & tox
* Local runs: Shippable is just a wrapper
* Duration: Inspect git diff. File to test mapping.
* Nightly runs with code coverage analysis.


.. container:: handout

   * Into Matt Clay

     * Principal Engineer in USA
     * Full time on Testing, great Python programmer

   * Q: If I said Shippable or Travis who would know what they are:

     * Shippable is a Continuous Integration (CI) tool, like Travis
     * Integrate with GitHub to test (PRs) + merges
     * Originally used Travis, moved as Shippable is cheaper
     * 52 Concurrent jobs as of May 2017

   * tox: Sanity & Unit tests
   * Local Runs

     * Different OS + Local runs fit together
     * Shippable is just a wrapper, all logic in ansible-tets

   * Duration: Tracking of Python imports
   * Code coverage is ~1.5 - 3x as slow (integration - Unit tests)

Types of tests
==============

* **compile**

  * Test python code against a variety of Python versions.

* **sanity**

  * Sanity tests are made up of scripts and tools used to perform static code analysis.
  * The primary purpose of these tests is to enforce Ansible coding standards and requirements.

* **integration**

  * Functional tests of modules and Ansible core functionality.

* **units**

  * Tests directly against individual parts of the code base.

.. container:: handout

   * Explain each type in basic terms

     * What type of issues they identify
     * How long they take to run

  * compile

    * Does NOT ensure code is py2.6+ and py3.5+ compatible

  * Sanity

    * ansible-doc, ansible-var-precedence-check
    * Code: no-iterkeys, pep8, pylint, shellcheck
    * ``ansible-test sanity --list-tests`` for full list

ansible-test platform features
==============================

* Python versions
* OS versions

   * Linux via Docker
   * FreeBSD, Windows, Network via AWS
   * OSX via Parallels

* Network version
* Cloud platforms (AWS, CloudStack, others coming soon)

.. container:: handout

   * OS: CentOS, Fedora, Ubuntu, OpenSUSE, Windows
   * Docker images are available for you to use locally ``ansible-test --docker``
   * Network tests are getting there, vyos, working on others

Improving Testing
=================

Spot common issues
 * Document how it should be done
 * Improve existing code
 * Enforce higher standard via CI

.. container:: handout

   * Bulk changes that update all modules are preferred, though speak to us first
   * Fix a **single** class of issues only, easier to review
   * Recent examples: Modules DOCUMENATION & RETURNS blocks


Improvements since 2.0
======================

* 2.1

   * added integration testing using Docker containers

* 2.2

   * switched from Travis to Shippable
   * added Windows, FreeBSD and OSX testing
   * added more docker containers

* 2.3

   * SINGLE GIT REPO!
   * ansible-test
   * integration testing for Network modules

.. container:: handout

   * Again, lot of this is Matt
   * Single repo; therefore versioned along side code); real pain to write tests before

Improvements in 2.4
===================


* added "cloud" module testing (AWS, CloudStack)
* enhanced code coverage analysis

* unit tests for core modules
* pep8
* pylint
* rstcheck
* module DOCUMENTATION
* module RETURNS

.. container:: handout

   * Unit tests: Networking team adding lots
   * pep8 and pylint continually being updated and spotting more issues
   * pep8 exceptions list dropping at a good rate
   * The last three have

     * dramatically improved our online documentation. Previously some module docs were not being displayed at all
     * Massive reduction human time to review modules




Testing Working Group
=====================

* One of special interest groups, others are Core, Networking and Windows
* Weekly public meeting on ``#ansible-meeting``
* Set direction and combine powers
* Subscribe to the GitHub issue for updates
* Links at the end of the presentation

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

* ``test/units/``

* Unit tests can't use external services
* Ansible modules are mostly about external services
* ``ansible-test units --tox [ --python X.Y ] [ modulename ]``


.. container:: handout

   * That's all I'm going to say on unit tests
   * For more info join ``#ansible-devel``

Integration Tests: Why?
=======================

* If you can write a Playbook you can write a test
* Much easier to write than an unit test
* Testing the interface, can deal with module being rewritten
* Speak with us in TWG or IRC for more info


.. container:: handout

   FIXME: Need to sell/convince people

Integration Tests: File structure
=================================

Directory: ``test/integration/targets/file/``

``file/aliases``

.. code-block:: bash

   posix/ci/group2
   needs/root

``file/tasks/main.yml``

.. code-block:: bash

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

   * Find an example of this


Integration Tests: Best practices
=================================

* output_dir
* Add tests before refactoring

.. container:: handout

   * FIXME Add examples


Integration Tests: Demo
=======================

Demo of running tests with Docker

``source hacking/env setup``

``ansible-test integration --docker centos7 pip``


.. container:: handout

  * FIXME Demo
  * FIXME Add talking points
  * FIXME Document commands here
  * ansible-test uses the tests and ansible from it's source tree

Code Coverage
=============

* Helps you find gaps
* Now run nightly

.. container:: handout

  * FIXME Add URL
  * FIXME Add talking points

Cloud Tests
===========

* Currently undergoing changes
* Aim: all AWS tests will be invoked via ``ansible-test``

.. container:: handout

  * FIXME move API key out the way and run, update docs
  * FIXME Add talking points

Network Tests
=============

* AWS images exist for some platforms
* Previously tests have been ran manually
* Work in progress

Where to find out more
======================

* https://docs.ansible.com/ansible/dev_guide/testing.html
* Testing working group
* Freenode: ``#ansible-devel``
* Writing tests is easy (install ``argcomplete``)
