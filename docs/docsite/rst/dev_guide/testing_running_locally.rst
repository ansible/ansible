:orphan:

.. _testing_running_locally:

***************
Testing Ansible
***************

This document describes how to run tests locally using ``ansible-test``.

.. contents::
   :local:

Requirements
============

Each ``ansible-test`` subcommand has different requirements, some have none.
You can add the ``--requirements`` option to have ``ansible-test`` install requirements for the current subcommand.
When using a test environment managed by ``ansible-test`` the option is unnecessary.

Test Environments
=================

Most ``ansible-test`` commands support running in one or more isolated test environments to simplify testing.

Containers
----------

Containers are recommended for running sanity, unit and integration tests, since they provide consistent environments.
Additionally, unit tests gain the benefit of network isolation, which avoids unintentional network use in unit tests.

The ``--docker`` option runs tests in a container using either Docker or Podman.

If both Docker and Podman are installed, Docker will be used.
To override this, set the environment variable ``ANSIBLE_TEST_PREFER_PODMAN=1``.

Without an additional argument, the ``--docker`` option uses the ``default`` container.

    Always use the ``default`` container when running sanity tests.

See the `list of supported containers <https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_data/completion/docker.txt>`_ for additional details.

You can also specify your own container. When doing so, you will need to specify the ``--python`` option as well.

Docker and SELinux
******************

Using Docker on a host with SELinux may require setting the system in permissive mode.
Consider using Podman instead.

Docker Desktop with WSL2
************************

These instructions explain how to use ``ansible-test`` with WSL2 and Docker Desktop *without* systemd support.

    If your WSL2 environment includes systemd support, these steps are not required.

Configuration Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^

Open Docker Desktop and go to the Settings screen, then verify these Settings on the General tab:

* Use the WSL 2 based engine - checked
* Start Docker Desktop when you log in - unchecked

Next go to the Resources tab and check the WSL Integration section.

* Under "Enable integration with additional distros" make sure each distro you want to use is enabled.
* Click "Apply and restart" if needed.

Setup Instructions
^^^^^^^^^^^^^^^^^^

    IMPORTANT: If all WSL instances have been stopped, these changes will need to be re-applied.

1. Verify Docker Desktop is properly configured (see Configuration Requirements above)
2. Quit Docker Desktop if it is running (Docker Desktop taskbar icon | Quit Docker Desktop)
3. Stop any running WSL instances with ``wsl --shutdown``
4. Verify all WSL instances have stopped with ``wsl -l -v``
5. Start a WSL instance and perform the following steps as ``root``:

   1. Verify the systemd subsystem is not registered with ``grep systemd /proc/self/cgroup``
   2. Run ``mkdir /sys/fs/cgroup/systemd``
   3. Run ``mount cgroup -t cgroup /sys/fs/cgroup/systemd -o none,name=systemd,xattr``

6. Start Docker Desktop

You should now be able to use ``ansible-test`` with the ``--docker`` option.

Linux cgroup Configuration
**************************

    IMPORTANT: These changes will need to be re-applied each time the container host is booted.

For certain container hosts and container combinations, additional setup on the container host may be required.
In these situations ``ansible-test`` will report an error and provide additional instructions to run as ``root``:

.. code-block:: shell-session

   mkdir /sys/fs/cgroup/systemd
   mount cgroup -t cgroup /sys/fs/cgroup/systemd -o none,name=systemd,xattr

If you are using rootless Podman, an additional command must be run, also as ``root``.
Make sure to substitute your user and group for ``{user}`` and ``{group}`` respectively:

.. code-block:: shell-session

   chown -R {user}:{group} /sys/fs/cgroup/systemd

Podman
^^^^^^

When using Podman, you may need to stop existing Podman processes after following the cgroup instructions above.
Otherwise Podman may be unable to see the new mount point.

You can check to see if Podman is running by looking for ``podman`` and ``catatonit`` processes.

Remote Virtual Machines
-----------------------

Remote virtual machines are recommended for running integration tests not suitable for execution in containers.

The ``--remote`` option runs tests in a cloud hosted ephemeral virtual machine.

    An API key is required to use this feature, unless running under an approved Azure Pipelines organization.

See the `list of supported platforms and versions <https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_data/completion/remote.txt>`_ for additional details.

Python Virtual Environments
---------------------------

Python virtual environments provide a simple way to achieve isolation from the system and user Python environments.
They are recommended for unit and integration tests when the ``--docker`` and ``--remote`` options cannot be used.

The ``--venv`` option runs tests in a virtual environment managed by ``ansible-test``.
Requirements are automatically installed before tests are run.

Environment Variables
=====================

When using environment variables to manipulate tests there some limitations to keep in mind. Environment variables are:

* Not propagated from the host to the test environment when using the ``--docker`` or ``--remote`` options.
* Not exposed to the test environment unless enabled in ``test/lib/ansible_test/_internal/util.py`` in the ``common_environment`` function.

    Example: ``ANSIBLE_KEEP_REMOTE_FILES=1`` can be set when running ``ansible-test integration --venv``. However, using the ``--docker`` option would
    require running ``ansible-test shell`` to gain access to the Docker environment. Once at the shell prompt, the environment variable could be set
    and the tests executed. This is useful for debugging tests inside a container by following the
    :ref:`Debugging AnsibleModule-based modules <debugging_modules>` instructions.

Interactive Shell
=================

Use the ``ansible-test shell`` command to get an interactive shell in the same environment used to run tests. Examples:

* ``ansible-test shell --docker`` - Open a shell in the default docker container.
* ``ansible-test shell --venv --python 3.10`` - Open a shell in a Python 3.10 virtual environment.

Code Coverage
=============

Code coverage reports make it easy to identify untested code for which more tests should
be written.  Online reports are available but only cover the ``devel`` branch (see
:ref:`developing_testing`).  For new code local reports are needed.

Add the ``--coverage`` option to any test command to collect code coverage data.  If you
aren't using the ``--venv`` or ``--docker`` options which create an isolated python
environment then you may have to use the ``--requirements`` option to ensure that the
correct version of the coverage module is installed:

.. code-block:: shell-session

   ansible-test coverage erase
   ansible-test units --coverage apt
   ansible-test integration --coverage aws_lambda
   ansible-test coverage html

Reports can be generated in several different formats:

* ``ansible-test coverage report`` - Console report.
* ``ansible-test coverage html`` - HTML report.
* ``ansible-test coverage xml`` - XML report.

To clear data between test runs, use the ``ansible-test coverage erase`` command. For a full list of features see the online help:

.. code-block:: shell-session

   ansible-test coverage --help
