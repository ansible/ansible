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

   * Based in the UK
   * ~ 1 year

Ansible Testing
===============

* History of testing Ansible
* How `you` can develop tests
* Where to find out more

.. container:: handout

   * Set the scene

     * Quick taster, give you enough to know what's possible and point you in the right direction
     * Important: Reduce regression, help support Python 3

   * Tailor content:

     * Q: Show of hands for version, devel, 2.3, -> 1.9? - upgrade!
     * Q: Who's raised a PR, should be getting easier on each release, especially modules

   * ReStructured Text: Slides will be made available online, which include speakers notes
   * All docs & module docs can be edited in GitHub UI, no knowledge of Git needed!
   * Questions welcome at any point - Will ask Mark to make a note


Requirements
============

What do we want from testing Ansible:

* Prevent regressions & speed up development
* Increase code quality
* Better readable code, improve collaboration

* Ability to run same tests locally as run by CI (Shippable)
* Different OS, Python versions (2.4+, 3.5+)
* Reasonable run time

.. container:: handout

   * Local run - common request from the community
   * Increasing the matrix of Python & OS versions vs timely feedback
   * Main aim: Stable product, find issues sooner, speed up PR work flow

Solution: ansible-test
======================

* Shippable
* Different OS & Python: Docker & tox
* Local runs: Shippable is just a wrapper
* Duration: Inspect git diff. File to test mapping.
* Nightly runs with code coverage analysis.


.. container:: handout

   * Intro Matt Clay

     * Principal Engineer in USA
     * Full time on Testing, great Python programmer

   * Q: If I said Shippable or Travis, who would know what they are:

     * Shippable is a Continuous Integration (CI) tool, like Travis
     * Integrate with GitHub to test (PRs) + merges
     * Originally used Travis, moved as Shippable is cheaper
     * 52 Concurrent jobs as of May 2017

   * Local Runs

     * Different OS + Local runs fit together
     * Shippable is just a wrapper, all logic in ansible-test
     * tox: Sanity & Unit tests

   * Duration

     * Tracking of Python imports
     * No need to run integration tests on RST changes

   * Code coverage is ~1.5 - 3x as slow (integration - Unit tests)

   * Cost vs benefits

     * Interrupts the workflow (wait until CI is finished, change, amend, push)
     * Not everything can be tested locally
     * Cosmetic failures can be frustrating
     * Do the benefits outweigh the costs ? We sure hope so :-)


Types of tests
==============

* **compile**

  * Test python code against a variety of Python versions.

* **sanity**

  * Sanity tests are made up of scripts and tools used to perform static code analysis.
  * The primary purpose of these tests is to enforce Ansible coding standards and requirements.

* **integration**

  * Functional tests of modules and Ansible core functionality.
  * Best for testing modules and core features (become, ``with_*``, add_host)

* **units**

  * Tests directly against individual parts of the code base.
  * Best for testing libraries (``module_utils``)

.. container:: handout

   * compile

     * Does NOT ensure code is py2.6+ and py3.5+ compatible
     * PY3: Not a porting job, need to support py2.6 + py3.5+

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
  * macOS via Parallels

* Network version
* Cloud platforms (AWS, CloudStack, others coming soon)

.. container:: handout

   * Linux: CentOS, Fedora, Ubuntu, OpenSUSE
   * Docker images are available for you to use locally ``ansible-test --docker``
   * Network tests are getting there, vyos, working on others

Improving Testing
=================

Spot common issues
 * Document how it should be done
 * Improve existing code
 * Enforce higher standard via CI

.. container:: handout

   * Fix a **single** class of issues only, easier to review
   * e.g Look at lots if new module PRs. Also about improving documentation
   * Bulk changes that update all modules are preferred, though speak to us first
   * Fixes to existing modules, people often copy them
   * Recent examples: Modules DOCUMENATION & RETURNS blocks


Improvements since 2.1
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
   * Single repo

     * therefore versioned along side code
     * real pain to write tests before
     * NOW: Single PR with module & tests

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
   * The last three have:

     * Dramatically improved our online documentation. Previously some module docs were not being displayed at all
     * Massive reduction of human time to review modules


Demo
====

Lets look at a PR to see how this all fits together...


.. container:: handout

   * https://github.com/ansible/ansible/pull/24748#issuecomment-302212014

     * Start with a PR
     * Show the different checks that have failed - Only sanity & compile tests are listed
     * Command that you can run locally
     * Lots of issues spotted that previously humans may or may not have seen

   * Shippable

     * https://app.shippable.com/github/ansible/ansible/runs/22111/summary
     * Need to look here if an unit or integration test has failed
     * List of platforms

       * Go to Tests tab first
       * File name of test
       * Failure reason
       * Go to console tab, and click through till you find the message
       * Failure will be rerun with higher verbosity
       * Describe "unstable tests"

         * Work around transitent issues, such as network issue pulling packages

Testing Working Group
=====================

* One of the special interest groups, others are: Core, Networking and Windows
* Weekly public meeting on ``#ansible-meeting``
* Set direction and combine powers
* Subscribe to the GitHub issue for updates
* Links at the end of the presentation

.. container:: handout

  * Q: Who knows ``#ansible-devel``
  * Q: Who knows about IRC Meetings?
  * Testing Working Group

    * Setup after AnsibleFest SanFran 2016, ~ year
    * gundalow & Matt Clay + a good community

  * Join ``#ansible-meeting`` on Freenode, see topic for link


Unit Tests: Creating
====================

* ``test/units/``

* Unit tests can't use external services
* Ansible modules are mostly about external services
* Good for ``lib/{module_utils,playbook,plugins,utils}``
* Bad fit for Modules
* ``ansible-test units --tox [ --python X.Y ] [ modulename ]``


.. container:: handout

   * That's all I'm going to say on unit tests
   * For more info join ``#ansible-devel``

Integration Tests: Why?
=======================

* If you can write a Playbook you can write a test
* Much easier to write than an unit test
* Testing the interface (Options such as ``state``, ``name``), can deal with module being rewritten
* More info: Testing Working Group, or ``#ansible-devel``


.. container:: handout

   * Q: Who has found a regression when upgrading
   * Q: Would you like to help reduce the chance of future regressions?
   * Q: Who has written more than a handful of Playbooks?

     * You have already have the skills to write integration tests :)
     * Just add ``assert``

   * Need to sell/convince people

Integration Tests: Test structure
=================================

Example package test

1 Setup - remove Apache

2 Install Apache

3 Check result & changed

4 Install Apache again

5 Check no change

6 Repeat for ``state=absent``

7 Teardown (if needed)

.. container:: handout

   * Idempotent is a key feature, test it



Integration Tests: Demo
=======================

Demo of running tests with Docker

``source hacking/env setup``

``ansible-test integration --docker ubuntu1604 apt``

``find test/integration/targets/apt/``


.. container:: handout

  * DEMO
  * I don't have ansible installed as a I swap branches a lot
  * source ``hacking/env-setup``
  * ``which ansible-playbook``
  * Show you ``ansible-test``, inc tab completion
  * ``ansible-test <tab><tab>``
  * ``ansible-test integration --docker ubuntu1604 <tab>tab>``

  * Run ``ansible-test`` apt

    * Show the docker instane being span up
    * Reminder: Exactly the same as in Shippable
    * ansible-test uses the tests and ansible from it's source tree

  * How did that work

    * Last argument = name of test
    * ``test/integration/target/NAME``
    * dir = module names
    * cat aliases
    * ``cat test/integration/targets/*/aliases  | sort -u1``
    * main.yml

      * Use of output_dir
      * Conditional include selinux

Integration Tests: Best practices
=================================

* ``set_fact: output_file={{output_dir}}/foo.txt``
* Add tests before refactoring
* Negative Testing - backtraces are bugs
* Test multiple options
* Check RETURNed data with ``register`` and ``assert``

.. container:: handout

   * FIXME Add examples

Code Coverage
=============

* Helps you find gaps
* Now run nightly
* https://codecov.io/gh/ansible/ansible/


.. container:: handout

  * https://codecov.io/gh/ansible/ansible/
  * FIXME Add talking points

Cloud Tests
===========

* Currently undergoing changes
* Aim: all AWS tests will be invoked via ``ansible-test``

.. container:: handout

  * See online docs
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
