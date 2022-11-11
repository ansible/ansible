:orphan:

.. _testing_running_locally:

*******************************
Testing Ansible and Collections
*******************************

This document describes how to run tests using ``ansible-test``.

.. contents::
   :local:

Setup
=====

To run ``ansible-test``, you need to make sure your environment is properly setup.

.. warning::

   If you use ``git`` for version control, make sure the files you are working with are not ignored by ``git``.
   If they are, ``ansible-test`` will ignore them as well.

Testing an Ansible Collection
-----------------------------

If you're testing an Ansible Collection, you'll need a copy of the collection, preferably a git clone.
As with Ansible itself, ``ansible-test`` requires collections to be within a valid collection root.

For example, if you want to work with the ``community.windows`` collection, you could clone it from GitHub:

.. code-block:: shell-session

   git clone https://github.com/ansible-collections/community.windows ~/dev/ansible_collections/community/windows

Since it depends on the ``ansible.windows`` collection you need to clone that as well:

.. code-block:: shell-session

   git clone https://github.com/ansible-collections/ansible.windows ~/dev/ansible_collections/ansible/windows

Finally, you can switch to the directory where the ``community.windows`` collection resides:

.. code-block:: shell-session

   cd ~/dev/ansible_collections/community/windows

Now you're ready to start testing the collection with ``ansible-test`` commands.

.. note::

   If your collection has any dependencies on other collections, they must be in the same collection root.
   Unlike Ansible, ``ansible-test`` will not use your configured collection roots (or other Ansible configuration).

Testing Ansible
---------------

If you're testing Ansible itself, you'll need a copy of the Ansible source code, preferably a git clone.
Having an installed copy of Ansible is not sufficient, or required.

.. note::

   If you do have an installed version of Ansible,
   make sure you are not using that copy of ``ansible-test`` to test Ansible itself.

Commands
========

The most commonly used test commands are:

* ``ansible-test sanity`` - Run sanity tests (mostly linters and static analysis).
* ``ansible-test integration`` - Run integration tests.
* ``ansible-test units`` - Run unit tests.

Run ``ansible-test --help`` to see a complete list of available commands.

.. note::

   For detailed help on a specific command, add the ``--help`` option after the command.

Environments
============

Most ``ansible-test`` commands support running in one or more isolated test environments to simplify testing.

Containers
----------

Containers are recommended for running sanity, unit and integration tests, since they provide consistent environments.
Unit tests will be run with network isolation, which avoids unintentional dependencies on network resources.

The ``--docker`` option runs tests in a container using either Docker or Podman.

.. note::

   If both Docker and Podman are installed, Docker will be used.
   To override this, set the environment variable ``ANSIBLE_TEST_PREFER_PODMAN=1``.

Choosing a container
^^^^^^^^^^^^^^^^^^^^

Without an additional argument, the ``--docker`` option uses the ``default`` container.
To use another container, specify it immediately after the ``--docker`` option.

.. note::

   The ``default`` container is recommended for all sanity and unit tests.

To see the list of supported containers, use the ``--help`` option with the ``ansible-test`` command you want to use.

.. note::

   The list of available containers is dependent on the ``ansible-test`` command you are using.

You can also specify your own container.
When doing so, you will need to indicate the Python version in the container with the ``--python`` option.

Docker and SELinux
^^^^^^^^^^^^^^^^^^

Using Docker on a host with SELinux may require setting the system in permissive mode.
Consider using Podman instead.

Docker Desktop with WSL2
^^^^^^^^^^^^^^^^^^^^^^^^

These instructions explain how to use ``ansible-test`` with WSL2 and Docker Desktop *without* systemd support.

.. note::

   If your WSL2 environment includes systemd support, these steps are not required.

Configuration requirements
""""""""""""""""""""""""""

Open Docker Desktop and go to the Settings screen, then verify these Settings on the General tab:

* Use the WSL 2 based engine - checked
* Start Docker Desktop when you log in - unchecked

Next go to the Resources tab and check the WSL Integration section.

* Under "Enable integration with additional distros" make sure each distro you want to use is enabled.
* Click "Apply and restart" if needed.

Setup instructions
""""""""""""""""""

.. note::

   If all WSL instances have been stopped, these changes will need to be re-applied.

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

Linux cgroup configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

   These changes will need to be re-applied each time the container host is booted.

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
""""""

When using Podman, you may need to stop existing Podman processes after following the cgroup instructions above.
Otherwise Podman may be unable to see the new mount point.

You can check to see if Podman is running by looking for ``podman`` and ``catatonit`` processes.

Remote virtual machines
-----------------------

Remote virtual machines are recommended for running integration tests not suitable for execution in containers.

The ``--remote`` option runs tests in a cloud hosted ephemeral virtual machine.

.. note::

   An API key is required to use this feature, unless running under an approved Azure Pipelines organization.

To see the list of supported systems, use the ``--help`` option with the ``ansible-test`` command you want to use.

.. note::

   The list of available systems is dependent on the ``ansible-test`` command you are using.

Python virtual environments
---------------------------

Python virtual environments provide a simple way to achieve isolation from the system and user Python environments.
They are recommended for unit and integration tests when the ``--docker`` and ``--remote`` options cannot be used.

The ``--venv`` option runs tests in a virtual environment managed by ``ansible-test``.
Requirements are automatically installed before tests are run.

Composite environment arguments
-------------------------------

The environment arguments covered in this document are sufficient for most use cases.
However, some scenarios may require the additional flexibility offered by composite environment arguments.

The ``--controller`` and ``--target`` options are alternatives to the ``--docker``, ``--remote`` and ``--venv`` options.

.. note::

   When using the ``shell`` command, the ``--target`` option is replaced by three platform specific options.

Add the ``--help`` option to your ``ansible-test`` command to learn more about the composite environment arguments.

Requirements
============

Some ``ansible-test`` commands have additional requirements.
You can use the ``--requirements`` option to automatically install them.

.. note::

   When using a test environment managed by ``ansible-test`` the ``--requirements`` option is usually unnecessary.

Environment variables
=====================

When using environment variables to manipulate tests there some limitations to keep in mind. Environment variables are:

* Not propagated from the host to the test environment when using the ``--docker`` or ``--remote`` options.
* Not exposed to the test environment unless enabled in ``test/lib/ansible_test/_internal/util.py`` in the ``common_environment`` function.

    Example: ``ANSIBLE_KEEP_REMOTE_FILES=1`` can be set when running ``ansible-test integration --venv``. However, using the ``--docker`` option would
    require running ``ansible-test shell`` to gain access to the Docker environment. Once at the shell prompt, the environment variable could be set
    and the tests executed. This is useful for debugging tests inside a container by following the
    :ref:`Debugging AnsibleModule-based modules <debugging_modules>` instructions.

Interactive shell
=================

Use the ``ansible-test shell`` command to get an interactive shell in the same environment used to run tests. Examples:

* ``ansible-test shell --docker`` - Open a shell in the default docker container.
* ``ansible-test shell --venv --python 3.10`` - Open a shell in a Python 3.10 virtual environment.

Code coverage
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

To clear data between test runs, use the ``ansible-test coverage erase`` command.
