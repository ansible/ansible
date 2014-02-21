Integration tests
=================

The ansible integration system.

Tests for playbooks, by playbooks.

Some tests may require cloud credentials.

Tests should be run as root.

Configuration
=============

Making your own version of integration_config.yml can allow for setting some tunable parameters to help run
the tests better in your environment.

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

Details pending, but these require cloud credentials.  These are not 'tests run in the cloud' so much as tests
that leverage the cloud modules and are organized by cloud provider.

