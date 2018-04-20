Sanity Tests » integration-aliases
==================================

Integration tests are executed by ``ansible-test`` and reside in directories under ``test/integration/targets/``.
Each test must have an ``aliases`` file to control test execution.

Aliases are explained in the following sections. Each alias must be on a separate line in an ``aliases`` file.

Groups
------

Tests must be configured to run in a specific group. This is done by adding the appropriate group to the ``aliases`` file.

The following are examples of some of the available groups:

- ``posix/ci/group1``
- ``windows/ci/group2``
- ``posix/ci/cloud/group3/azure``
- ``posix/ci/cloud/group4/aws``

Groups are used to balance tests across multiple CI jobs to minimize test run time.
They also improve efficiency by keeping tests with similar requirements running together.

When selecting a group for a new test, use the same group as existing tests similar to the one being added.

Requirements
------------

Aliases can be used to express some test requirements:

- ``needs/privileged`` - Requires ``--docker-privileged`` when running tests with ``--docker``.
- ``needs/root`` - Requires running tests as ``root`` or with ``--docker``.
- ``needs/ssh`` - Requires SSH connections to localhost (or the test container with ``--docker``) without a password.

Skipping
--------

Aliases can be used to skip platforms:

- ``skip/freebsd`` - Skip tests on FreeBSD.
- ``skip/osx`` - Skip tests on macOS / OS X.
- ``skip/rhel`` - Skip tests on RHEL.

Aliases can be used to skip Python major versions:

- ``skip/python2`` - Skip tests on Python 2.x.
- ``skip/python3`` - Skip tests on Python 3.x.

Unstable
--------

Tests which fail sometimes should be marked with the ``unstable`` alias until the instability has been fixed.
These tests will continue to run for pull requests which modify the test or the module under test.

This avoids unnecessary test failures for other pull requests, as well as tests on merge runs and nightly CI jobs.

There are two ways to run unstable tests manually:

- Use the ``--allow-unstable`` option for ``ansible-test``
- Prefix the test name with ``unstable/`` when passing it to ``ansible-test``.

Disabled
--------

Tests which always fail should be marked with the ``disabled`` alias until they can be fixed.

Disabled tests are automatically skipped.

There are two ways to run disabled tests manually:

- Use the ``--allow-disabled`` option for ``ansible-test``
- Prefix the test name with ``disabled/`` when passing it to ``ansible-test``.

Unsupported
-----------

Tests which cannot be run in CI should be marked with the ``unsupported`` alias.
Most tests can be supported through the use of simulators and/or cloud plugins.

However, if that is not possible then marking a test as unsupported will prevent it from running in CI.

There are two ways to run unsupported tests manually:

* Use the ``--allow-unsupported`` option for ``ansible-test``
* Prefix the test name with ``unsupported/`` when passing it to ``ansible-test``.

Cloud
-----

Tests for cloud services and other modules that require access to external APIs usually require special support for testing in CI.

These require an additional alias to indicate the required test plugin.

Some of the available aliases are:

- ``cloud/aws``
- ``cloud/azure``
- ``cloud/cs``
- ``cloud/foreman``
- ``cloud/openshift``
- ``cloud/tower``
- ``cloud/vcenter``

Untested
--------

Every module and plugin should have integration tests, even if the tests cannot be run in CI.

Questions
---------

For questions about integration tests reach out to @mattclay or @gundalow on GitHub or #ansible-devel on IRC.
