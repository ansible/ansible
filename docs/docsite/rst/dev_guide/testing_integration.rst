:orphan:

.. _testing_integration:

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

Configuration
=============

ansible-test command
--------------------

The example below assumes ``bin/`` is in your ``$PATH``. An easy way to achieve that
is to initialize your environment with the ``env-setup`` command::

    source hacking/env-setup
    ansible-test --help

You can also call ``ansible-test`` with the full path::

    bin/ansible-test --help

integration_config.yml
----------------------

Making your own version of ``integration_config.yml`` can allow for setting some
tunable parameters to help run the tests better in your environment.  Some
tests (e.g. cloud) will only run when access credentials are provided.  For more
information about supported credentials, refer to the various ``cloud-config-*.template``
files in the ``test/integration/`` directory.

Prerequisites
=============

Some tests assume things like hg, svn, and git are installed, and in path.  Some tests
(such as those for Amazon Web Services) need separate definitions, which will be covered
later in this document.

(Complete list pending)

Non-destructive Tests
=====================

These tests will modify files in subdirectories, but will not do things that install or remove packages or things
outside of those test subdirectories.  They will also not reconfigure or bounce system services.

.. note:: Running integration tests within Docker

   To protect your system from any potential changes caused by integration tests, and to ensure a sensible set of dependencies are available we recommend that you always run integration tests with the ``--docker`` option. See the `list of supported docker images <https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_data/completion/docker.txt>`_ for options.

.. note:: Avoiding pulling new Docker images

   Use the ``--docker-no-pull`` option to avoid pulling the latest container image. This is required when using custom local images that are not available for download.

Run as follows for all POSIX platform tests executed by our CI system::

    ansible-test integration --docker fedora29 -v shippable/

You can target a specific tests as well, such as for individual modules::

    ansible-test integration -v ping

Use the following command to list all the available targets::

    ansible-test integration --list-targets

.. note:: Bash users

   If you use ``bash`` with ``argcomplete``, obtain a full list by doing: ``ansible-test integration <tab><tab>``

Destructive Tests
=================

These tests are allowed to install and remove some trivial packages.  You will likely want to devote these
to a virtual environment, such as Docker.  They won't reformat your filesystem::

    ansible-test integration --docker fedora29 -v destructive/

Windows Tests
=============

These tests exercise the ``winrm`` connection plugin and Windows modules.  You'll
need to define an inventory with a remote Windows 2008 or 2012 Server to use
for testing, and enable PowerShell Remoting to continue.

Running these tests may result in changes to your Windows host, so don't run
them against a production/critical Windows environment.

Enable PowerShell Remoting (run on the Windows host via Remote Desktop)::

    Enable-PSRemoting -Force

Define Windows inventory::

    cp inventory.winrm.template inventory.winrm
    ${EDITOR:-vi} inventory.winrm

Run the Windows tests executed by our CI system::

    ansible-test windows-integration -v shippable/

Tests in Docker containers
==========================

If you have a Linux system with Docker installed, running integration tests using the same Docker containers used by
the Ansible continuous integration (CI) system is recommended.

.. note:: Docker on non-Linux

   Using Docker Engine to run Docker on a non-Linux host (such as macOS) is not recommended.
   Some tests may fail, depending on the image used for testing.
   Using the ``--docker-privileged`` option when running ``integration`` (not ``network-integration`` or ``windows-integration``) may resolve the issue.

Running Integration Tests
-------------------------

To run all CI integration test targets for POSIX platforms in a Ubuntu 16.04 container::

    ansible-test integration --docker ubuntu1604 -v shippable/

You can also run specific tests or select a different Linux distribution.
For example, to run tests for the ``ping`` module on a Ubuntu 14.04 container::

    ansible-test integration -v ping --docker ubuntu1404

Container Images
----------------

Python 2
````````

Most container images are for testing with Python 2:

  - centos6
  - centos7
  - fedora28
  - opensuse15py2
  - ubuntu1404
  - ubuntu1604

Python 3
````````

To test with Python 3 use the following images:

  - fedora29
  - opensuse15
  - ubuntu1604py3
  - ubuntu1804


Legacy Cloud Tests
==================

Some of the cloud tests run as normal integration tests, and others run as legacy tests; see the
:ref:`testing_integration_legacy` page for more information.


Other configuration for Cloud Tests
===================================

In order to run some tests, you must provide access credentials in a file named
``cloud-config-aws.yml`` or ``cloud-config-cs.ini`` in the test/integration
directory. Corresponding .template files are available for for syntax help.  The newer AWS
tests now use the file test/integration/cloud-config-aws.yml

IAM policies for AWS
====================

Ansible needs fairly wide ranging powers to run the tests in an AWS account.  This rights can be provided to a dedicated user. These need to be configured before running the test.

testing-policies
----------------

``hacking/aws_config/testing_policies`` contains a set of policies that are required for all existing AWS module tests.
The ``hacking/aws_config/setup_iam.yml`` playbook can be used to add all of those policies to an IAM group (using
``-e iam_group=GROUP_NAME``. Once the group is created, you'll need to create a user and make the user a member of the
group. The policies are designed to minimize the rights of that user.  Please note that while this policy does limit
the user to one region, this does not fully restrict the user (primarily due to the limitations of the Amazon ARN
notation). The user will still have wide privileges for viewing account definitions, and will also able to manage
some resources that are not related to testing (for example, AWS lambdas with different names).  Tests should not
be run in a primary production account in any case.

Other Definitions required
--------------------------

Apart from installing the policy and giving it to the user identity running the tests, a
lambda role `ansible_integration_tests` has to be created which has lambda basic execution
privileges.


Network Tests
=============

Starting with Ansible 2.4, all network modules MUST include unit tests that cover all functionality. You must add unit tests for each new network module and for each added feature. Please submit the unit tests and the code in a single PR. Integration tests are also strongly encouraged.

Writing network integration tests
---------------------------------

For guidance on writing network test see the `adding tests for Network modules guide <https://github.com/ansible/community/blob/master/group-network/network_test.rst>`_.


Running network integration tests locally
-----------------------------------------

Ansible uses Shippable to run an integration test suite on every PR, including new tests introduced by that PR. To find and fix problems in network modules, run the network integration test locally before you submit a PR.

To run the network integration tests, use a command in the form::

    ansible-test network-integration --inventory /path/to/inventory tests_to_run

First, define a network inventory file::

    cd test/integration
    cp inventory.network.template inventory.networking
    ${EDITOR:-vi} inventory.networking
    # Add in machines for the platform(s) you wish to test

To run all Network tests for a particular platform::

    ansible-test network-integration --inventory  /path/to/ansible/test/integration/inventory.networking vyos_.*

This example will run against all vyos modules. Note that ``vyos_.*`` is a regex match, not a bash wildcard - include the `.` if you modify this example.


To run integration tests for a specific module::

    ansible-test network-integration --inventory  /path/to/ansible/test/integration/inventory.networking vyos_vlan

To run a single test case on a specific module::

    # Only run vyos_vlan/tests/cli/basic.yaml
    ansible-test network-integration --inventory  /path/to/ansible/test/integration/inventory.networking vyos_vlan --testcase basic

To run integration tests for a specific transport::

    # Only run nxapi test
    ansible-test network-integration --inventory  /path/to/ansible/test/integration/inventory.networking  --tags="nxapi" nxos_.*

    # Skip any cli tests
    ansible-test network-integration --inventory  /path/to/ansible/test/integration/inventory.networking  --skip-tags="cli" nxos_.*

See `test/integration/targets/nxos_bgp/tasks/main.yaml <https://github.com/ansible/ansible/blob/devel/test/integration/targets/nxos_bgp/tasks/main.yaml>`_ for how this is implemented in the tests.

For more options::

    ansible-test network-integration --help

If you need additional help or feedback, reach out in ``#ansible-network`` on Freenode.


Where to find out more
======================

If you'd like to know more about the plans for improving testing Ansible, join the `Testing Working Group <https://github.com/ansible/community/blob/master/meetings/README.md>`_.
