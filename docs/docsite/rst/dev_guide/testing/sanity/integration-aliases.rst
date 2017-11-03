Sanity Tests » integration-aliases
==================================

Each integration test must have an ``aliases`` file to control test execution.

If the tests cannot be run as part of CI (requires external services, unsupported dependencies, etc.),
then they most likely belong in ``test/integration/roles/`` instead of ``test/integration/targets/``.
In that case, do not add an ``aliases`` file. Instead, just relocate the tests.

In some cases tests requiring external resources can be run as a part of CI.
This is often true when those resources can be provided by a docker container.

However, if you think that the tests should be able to be supported by CI, please discuss test
organization with @mattclay or @gundalow on GitHub or #ansible-devel on IRC.

If the tests can be run as part of CI, you'll need to add an appropriate CI alias, such as:

- ``posix/ci/group1``
- ``windows/ci/group2``

The CI groups are used to balance tests across multiple jobs to minimize test run time.
Using the relevant ``group1`` entry is fine in most cases. Groups can be changed later to redistribute tests.

Aliases can also be used to express test requirements:

- ``needs/privileged``
- ``needs/root``
- ``needs/ssh``

Other aliases are used to skip tests under certain conditions:

- ``skip/freebsd``
- ``skip/osx``
- ``skip/python3``

Take a look at existing ``aliases`` files to see what aliases are available and how they're used.
