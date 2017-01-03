Integration tests
=================

The ansible integration system.

Tests for playbooks, by playbooks.

Some tests may require credentials.  Credentials may be specified with `credentials.yml`.

Tests should be run as root.

Quick Start
===========

To get started quickly using Docker containers for testing,
see [Tests in Docker containers](#tests-in-docker-containers).

Configuration
=============

Making your own version of `integration_config.yml` can allow for setting some
tunable parameters to help run the tests better in your environment.  Some
tests (e.g. cloud) will only run when access credentials are provided.  For
more information about supported credentials, refer to `credentials.template`.

Prerequisites
=============

The tests will assume things like hg, svn, and git are installed and in path.

(Complete list pending)

Non-destructive Tests
=====================

These tests will modify files in subdirectories, but will not do things that install or remove packages or things
outside of those test subdirectories.  They will also not reconfigure or bounce system services.

Run as follows:

    make non_destructive

You can select specific tests with the --tags parameter.

    TEST_FLAGS="--tags test_vars_blending" make

Destructive Tests
=================

These tests are allowed to install and remove some trivial packages.  You will likely want to devote these
to a virtual environment.  They won't reformat your filesystem, however :)

    make destructive

Cloud Tests
===========

Cloud tests exercise capabilities of cloud modules (e.g. ec2_key).  These are
not 'tests run in the cloud' so much as tests that leverage the cloud modules
and are organized by cloud provider.

In order to run cloud tests, you must provide access credentials in a file
named `credentials.yml`.  A sample credentials file named
`credentials.template` is available for syntax help.


Provide cloud credentials:
    cp credentials.template credentials.yml
    ${EDITOR:-vi} credentials.yml

Run the tests:
    make cloud

*WARNING* running cloud integration tests will create and destroy cloud
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

Define Windows inventory:
    cp inventory.winrm.template inventory.winrm
    ${EDITOR:-vi} inventory.winrm

Run the tests:
    make test_winrm

Tests in Docker containers
==========================

If you have a Linux system with Docker installed, running integration tests using the same Docker containers used by
the Ansible continuous integration (CI) system is recommended.

> Using Docker Engine to run Docker on a non-Linux host is not recommended. Some tests, such as those that manage
> services or use local SSH connections are known to fail in such an environment. For best results, install Docker on a
> full Linux distribution such as Ubuntu, running on real hardware or in a virtual machine.

## Running Integration Tests

To run all integration test targets with the default settings in a Centos 7 container, run `make integration` from the repository root.

You can also run specific tests or select a different Linux distribution.
For example, to run the test `test_ping` from the non_destructive target on a Ubuntu 14.04 container:

- go to the repository root
- and execute `make integration IMAGE=ansible/ansible:ubuntu1404 TARGET=non_destructive TEST_FLAGS='--tags test_ping'`

## Container Images

Use the prefix `ansible/ansible:` with the image names below.

> Running `make integration` will automatically download the container image you have specified, if it is not already 
> available. However, you will be responsible for keeping the container images up-to-date using `docker pull`.

### Python 2

Most container images are for testing with Python 2:

  - centos6
  - centos7
  - fedora24
  - fedora25
  - opensuse42.1
  - opensuse42.2
  - ubuntu1204 (requires `PRIVILEGED=true`)
  - ubuntu1404 (requires `PRIVILEGED=true`)
  - ubuntu1604

### Python 3

To test with Python 3 you must set `PYTHON3=1` and use the following images:

  - ubuntu1604py3

## Additional Options

There are additional environment variables that can be used. A few of the more useful ones:

  - `KEEP_CONTAINERS=onfailure` - Containers will be preserved if tests fail.
  - `KEEP_CONTAINERS=1` - Containers will always be preserved.
  - `SHARE_SOURCE=1` - Changes to source from the host or container will be shared between host and container.
                       _**CAUTION:** Files created by the container will be owned by root on the host._
