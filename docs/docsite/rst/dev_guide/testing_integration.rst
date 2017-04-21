*****************
Integration tests
*****************

.. contents:: Topics

The Ansible integration Test system.

Tests for playbooks, by playbooks.

Some tests may require credentials.  Credentials may be specified with `credentials.yml`.

Some tests may require root.

Quick Start
===========

It is highly recommended that you install and activate the ``argcomplete`` python package.
It provides tab completion in ``bash`` for the ``ansible-test`` test runner.

To get started quickly using Docker containers for testing,
see [Tests in Docker containers](#tests-in-docker-containers).

Configuration
=============

Making your own version of ``integration_config.yml`` can allow for setting some
tunable parameters to help run the tests better in your environment.  Some
tests (e.g. cloud) will only run when access credentials are provided.  For
more information about supported credentials, refer to ``credentials.template``.

Prerequisites
=============

The tests will assume things like hg, svn, and git are installed and in path.

(Complete list pending)

Non-destructive Tests
=====================

These tests will modify files in subdirectories, but will not do things that install or remove packages or things
outside of those test subdirectories.  They will also not reconfigure or bounce system services.

Run as follows for all POSIX platform tests executed by our CI system::

    test/runner/ansible-test integration -v posix/ci/

You can select specific tests as well, such as for individual modules::

    test/runner/ansible-test integration -v ping

By installing ``argcomplete`` you can obtain a full list by doing::

    test/runner/ansible-test integration <tab><tab>

Destructive Tests
=================

These tests are allowed to install and remove some trivial packages.  You will likely want to devote these
to a virtual environment, such as docker.  They won't reformat your filesystem::

    test/runner/ansible-test integration --docker=fedora25 -v destructive/

Cloud Tests
===========

Cloud tests exercise capabilities of cloud modules (e.g. ec2_key).  These are
not 'tests run in the cloud' so much as tests that leverage the cloud modules
and are organized by cloud provider.

In order to run cloud tests, you must provide access credentials in a file
named ``credentials.yml``.  A sample credentials file named
``credentials.template`` is available for syntax help.


Provide cloud credentials::

    cp credentials.template credentials.yml
    ${EDITOR:-vi} credentials.yml

Run the tests::

    make cloud

**WARNING** running cloud integration tests will create and destroy cloud
resources.  Running these tests may result in additional fees associated with
your cloud account.  Care is taken to ensure that created resources are
removed.  However, it is advisable to inspect your AWS console to ensure no
unexpected resources are running.

Windows Tests
=============

These tests exercise the winrm connection plugin and Windows modules.  You'll
need to define an inventory with a remote Windows 2008 or 2012 Server to use
for testing, and enable PowerShell Remoting to continue.

Running these tests may result in changes to your Windows host, so don't run
them against a production/critical Windows environment.

Enable PowerShell Remoting (run on the Windows host via Remote Desktop):
    Enable-PSRemoting -Force

Define Windows inventory::

    cp inventory.winrm.template inventory.winrm
    ${EDITOR:-vi} inventory.winrm

Run the Windows tests executed by our CI system::

    test/runner/ansible-test windows-integration -v windows/ci/

Tests in Docker containers
==========================

If you have a Linux system with Docker installed, running integration tests using the same Docker containers used by
the Ansible continuous integration (CI) system is recommended.

.. note: Docker on non-Linux::

   Using Docker Engine to run Docker on a non-Linux host is not recommended.
   Some tests may fail, depending on the image used for testing.
   Using the ``--docker-privileged`` option may resolve the issue.

Running Integration Tests
-------------------------

To run all CI integration test targets for POSIX platforms in a Ubuntu 16.04 container::

    test/runner/ansible-test integration -v posix/ci/ --docker

You can also run specific tests or select a different Linux distribution.
For example, to run tests for the ``ping`` module on a Ubuntu 14.04 container::

    test/runner/ansible-test integration -v ping --docker ubuntu1404

Container Images
----------------

Python 2
````````

Most container images are for testing with Python 2:

  - centos6
  - centos7
  - fedora24
  - fedora25
  - opensuse42.1
  - opensuse42.2
  - ubuntu1204
  - ubuntu1404
  - ubuntu1604

Python 3
````````

To test with Python 3 use the following images:

  - ubuntu1604py3

Network Tests
=============

FIXME Link
