Integration tests
=================

The ansible integration system.

Tests for playbooks, by playbooks.

Some tests may require credentials.  Credentials may be specified with `credentials.yml`.

Tests should be run as root.

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
