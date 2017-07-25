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

Making your own version of ``integration_config.yml`` can allow for setting some
tunable parameters to help run the tests better in your environment.  Some
tests (e.g. cloud) will only run when access credentials are provided.  For
more information about supported credentials, refer to ``credentials.template``.

Prerequisites
=============

The tests will assume things like hg, svn, and git are installed and in path.  Some tests
(such as those for Amazon Web Services) need separate definitions, which will be covered
later in this document.

(Complete list pending)

Non-destructive Tests
=====================

These tests will modify files in subdirectories, but will not do things that install or remove packages or things
outside of those test subdirectories.  They will also not reconfigure or bounce system services.

.. note:: Running integration tests within Docker

   To protect your system from any potential changes caused by integration tests, and to ensure the a sensible set of dependencies are available we recommend that you always run integration tests with the ``--docker`` option. See the `list of supported docker images <https://github.com/ansible/ansible/blob/devel/test/runner/completion/docker.txt>`_ for options.

.. note:: Avoiding pulling new Docker images

   Use the ``--docker-no-pull`` option to avoid pulling the latest container image. This is required when using custom local images that are not available for download.

Run as follows for all POSIX platform tests executed by our CI system::

    test/runner/ansible-test integration --docker fedora25 -v posix/ci/

You can select specific tests as well, such as for individual modules::

    test/runner/ansible-test integration -v ping

By installing ``argcomplete`` you can obtain a full list by doing::

    test/runner/ansible-test integration <tab><tab>

Destructive Tests
=================

These tests are allowed to install and remove some trivial packages.  You will likely want to devote these
to a virtual environment, such as Docker.  They won't reformat your filesystem::

    test/runner/ansible-test integration --docker fedora25 -v destructive/

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

    test/runner/ansible-test windows-integration -v windows/ci/

Tests in Docker containers
==========================

If you have a Linux system with Docker installed, running integration tests using the same Docker containers used by
the Ansible continuous integration (CI) system is recommended.

.. note:: Docker on non-Linux

   Using Docker Engine to run Docker on a non-Linux host (such as macOS) is not recommended.
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

Legacy Cloud Tests
==================

Some of the cloud tests run as normal integration tests, and others run as legacy tests; see the
:doc:`testing_integration_legacy` page for more information.


Other configuration for Cloud Tests
===================================

In order to run some tests, you must provide access credentials in a file named
``cloud-config-aws.yml`` or ``cloud-config-cs.ini`` in the test/integration
directory. Corresponding .template files are available for for syntax help.  The newer AWS
tests now use the file test/integration/cloud-config-aws.yml

IAM policies for AWS
====================

Ansible needs fairly wide ranging powers to run the tests in an AWS account.  This rights can be provided to a dedicated user. These need to be configured before running the test.

testing-iam-policy.json.j2
--------------------------

The testing-iam-policy.json.j2 file contains a policy which can be given to the user
running the tests to minimize the rights of that user.  Please note that while this policy does limit the user to one region, this does not fully restrict the user (primarily due to the limitations of the Amazon ARN notation). The user will still have wide privileges for viewing account definitions, and will also able to manage some resources that are not related to testing (for example, AWS lambdas with different names).  Tests should not be run in a primary production account in any case.

Other Definitions required
--------------------------

Apart from installing the policy and giving it to the user identity running the tests, a
lambda role `ansible_integration_tests` has to be created which has lambda basic execution
privileges.


Network Tests
=============

This page details the specifics around testing Ansible Networking modules.


.. important:: Network testing requirements for Ansible 2.4

   Starting with Ansible 2.4, all network modules MUST include corresponding unit tests to defend functionality.
   The unit tests must be added in the same PR that includes the new network module, or extends functionality.
   Integration tests, although not required, are a welcome addition.
   How to do this is explained in the rest of this document.


Network integration tests can be ran by doing::

    cd test/integration
    ANSIBLE_ROLES_PATH=targets ansible-playbook network-all.yaml


.. note::

  * To run the network tests you will need a number of test machines and suitably configured inventory file. A sample is included in ``test/integration/inventory.network``
  * As with the rest of the integration tests, they can be found grouped by module in ``test/integration/targets/MODULENAME/``

To filter a set of test cases set ``limit_to`` to the name of the group, generally this is the name of the module::

   ANSIBLE_ROLES_PATH=targets ansible-playbook -i inventory.network network-all.yaml -e "limit_to=eos_command"


To filter a singular test case set the tags options to eapi or cli, set limit_to to the test group,
and test_cases to the name of the test::

   ANSIBLE_ROLES_PATH=targets ansible-playbook -i inventory.network network-all.yaml --tags="cli" -e "limit_to=eos_command test_case=notequal"



Writing network integration tests
---------------------------------

Test cases are added to roles based on the module being testing. Test cases
should include both cli and API test cases. Cli test cases should be
added to ``test/integration/targets/modulename/tests/cli`` and API tests should be added to
``test/integration/targets/modulename/tests/eapi``, or ``nxapi``.

In addition to positive testing, negative tests are required to ensure user friendly warnings & errors are generated, rather than backtraces, for example:

.. code-block: yaml

   - name: test invalid subset (foobar)
     eos_facts:
       provider: "{{ cli }}"
       gather_subset:
         - "foobar"
     register: result
     ignore_errors: true

   - assert:
       that:
         # Failures shouldn't return changes
         - "result.changed == false"
         # It's a failure
         - "result.failed == true"
         # Sensible Failure message
         - "'Subset must be one of' in result.msg"


Conventions
```````````

- Each test case should generally follow the pattern:

  setup —> test —> assert —> test again (idempotent) —> assert —> teardown (if needed) -> done

  This keeps test playbooks from becoming monolithic and difficult to
  troubleshoot.

- Include a name for each task that is not an assertion. (It's OK to add names
  to assertions too. But to make it easy to identify the broken task within a failed
  test, at least provide a helpful name for each task.)

- Files containing test cases must end in `.yaml`


Adding a new Network Platform
`````````````````````````````

A top level playbook is required such as ``ansible/test/integration/eos.yaml`` which needs to be references by ``ansible/test/integration/network-all.yaml``

Where to find out more
======================

If you'd like to know more about the plans for improving testing Ansible then why not join the `Testing Working Group <https://github.com/ansible/community/blob/master/meetings/README.md>`_.
