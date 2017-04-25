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

FIXME Details of different jobs, overlap with types of tests

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


How to test a PR
================

If you're a developer, one of the most valuable things you can do is look at the github issues list and help fix bugs.  We almost always prioritize bug fixing over
feature development, so clearing bugs out of the way is one of the best things you can do.

Even if you're not a developer, helping test pull requests for bug fixes and features is still immensely valuable.

This goes for testing new features as well as testing bugfixes.

In many cases, code should add tests that prove it works but that's not ALWAYS possible and tests are not always comprehensive, especially when a user doesn't have access
to a wide variety of platforms, or that is using an API or web service.

In these cases, live testing against real equipment can be more valuable than automation that runs against simulated interfaces.
In any case, things should always be tested manually the first time too.

Thankfully helping test ansible is pretty straightforward, assuming you are already used to how ansible works.

Setup: Checking out a Pull Request
----------------------------------

You can do this by checking out ansible, making a test branch off the main one, merging a GitHub issue, testing,
and then commenting on that particular issue on GitHub. Here's how:

.. warning::
   Testing source code from GitHub pull requests sent to us does have some inherent risk, as the source code
   sent may have mistakes or malicious code that could have a negative impact on your system. We recommend
   doing all testing on a virtual machine, whether a cloud instance, or locally.  Some users like Vagrant
   or Docker for this, but they are optional.  It is also useful to have virtual machines of different Linux or
   other flavors, since some features (apt vs. yum, for example) are specific to those OS versions.


Create a fresh area to work::


   git clone https://github.com/ansible/ansible.git ansible-pr-testing
   cd ansible-pr-testing

Next, find the pull request you'd like to test and make note of the line at the top which describes the source
and destination repositories. It will look something like this::

   Someuser wants to merge 1 commit into ansible:devel from someuser:feature_branch_name

.. note:: Only test ``ansible:devel``
   It is important that the PR request target be ansible:devel, as we do not accept pull requests into any other branch.  Dot releases are cherry-picked manually by Ansible staff.

The username and branch at the end are the important parts, which will be turned into git commands as follows::

   git checkout -b testing_PRXXXX devel
   git pull https://github.com/someuser/ansible.git feature_branch_name

The first command creates and switches to a new branch named testing_PRXXXX, where the XXXX is the actual issue number associated with the pull request (for example, 1234). This branch is based on the devel branch. The second command pulls the new code from the users feature branch into the newly created branch.

.. note::
   If the GitHub user interface shows that the pull request will not merge cleanly, we do not recommend proceeding if you are not somewhat familiar with git and coding, as you will have to resolve a merge conflict.  This is the responsibility of the original pull request contributor.

.. note::
   Some users do not create feature branches, which can cause problems when they have multiple, un-related commits in their version of `devel`. If the source looks like `someuser:devel`, make sure there is only one commit listed on the pull request.

The Ansible source includes a script that allows you to use Ansible directly from source without requiring a
full installation, that is frequently used by developers on Ansible.

Simply source it (to use the Linux/Unix terminology) to begin using it immediately::

   source ./hacking/env-setup

This script modifies the PYTHONPATH enviromnent variables (along with a few other things), which will be temporarily
set as long as your shell session is open.

Testing the Pull Request
------------------------

At this point, you should be ready to begin testing!

Some idea of what to test are:

* Create a test Playbook with the examples in, do they function correctly
* Are any Python backtraces returned, if so that's a bug
* Testing on different Operating Systems, or against different library version.


Any potential issues should be added as comments on the Pull Request, likewise if it works say so, remembering to include the output of ``ansible --version``

Example!

   | Works for me!  Tested on `Ansible 2.3.0`.  I verified this on CentOS 6.5 and also Ubuntu 14.04.

If the PR does not resolve the issue, or if you see any failures from the unit/integration tests, just include that output instead:

   | This doesn't work for me.
   |
   | When I ran this Ubuntu 16.04 it failed with the following:
   |
   |   \```
   |   BLARG
   |   StrackTrace
   |   RRRARRGGG
   |   \```

Want to know more about testing?
================================

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
