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

Before running ``ansible-test``, set up your environment for :ref:`testing_an_ansible_collection` or
:ref:`testing_ansible_core`, depending on which scenario applies to you.

.. warning::

   If you use ``git`` for version control, make sure the files you are working with are not ignored by ``git``.
   If they are, ``ansible-test`` will ignore them as well.

.. _testing_an_ansible_collection:

Testing an Ansible Collection
-----------------------------

If you are testing an Ansible Collection, you need a copy of the collection, preferably a git clone.
For example, to work with the ``community.windows`` collection, follow these steps:

1. Clone the collection you want to test into a valid collection root:

   .. code-block:: shell

      git clone https://github.com/ansible-collections/community.windows ~/dev/ansible_collections/community/windows

   .. important::

      The path must end with ``/ansible_collections/{collection_namespace}/{collection_name}`` where
      ``{collection_namespace}`` is the namespace of the collection and ``{collection_name}`` is the collection name.

2. Clone any collections on which the collection depends:

   .. code-block:: shell

      git clone https://github.com/ansible-collections/ansible.windows ~/dev/ansible_collections/ansible/windows

   .. important::

      If your collection has any dependencies on other collections, they must be in the same collection root, since
      ``ansible-test`` will not use your configured collection roots (or other Ansible configuration).

   .. note::

      See the collection's ``galaxy.yml`` for a list of possible dependencies.

3. Switch to the directory where the collection to test resides:

   .. code-block:: shell

      cd ~/dev/ansible_collections/community/windows

.. _testing_ansible_core:

Testing ``ansible-core``
------------------------

If you are testing ``ansible-core`` itself, you need a copy of the ``ansible-core`` source code, preferably a git clone.
Having an installed copy of ``ansible-core`` is not sufficient or required.
For example, to work with the ``ansible-core`` source cloned from GitHub, follow these steps:

1. Clone the ``ansible-core`` repository:

   .. code-block:: shell

      git clone https://github.com/ansible/ansible ~/dev/ansible

2. Switch to the directory where the ``ansible-core`` source resides:

   .. code-block:: shell

      cd ~/dev/ansible

3. Add ``ansible-core`` programs to your ``PATH``:

   .. code-block:: shell

      source hacking/env-setup

   .. note::

      You can skip this step if you only need to run ``ansible-test``, and not other ``ansible-core`` programs.
      In that case, simply run ``bin/ansible-test`` from the root of the ``ansible-core`` source.

   .. caution::

      If you have an installed version of ``ansible-core`` and are trying to run ``ansible-test`` from your ``PATH``,
      make sure the program found by your shell is the one from the ``ansible-core`` source:

      .. code-block:: shell

         which ansible-test

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
   To override this, set the environment variable ``ANSIBLE_TEST_PREFER_PODMAN`` to any non-empty value.

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

Custom containers
"""""""""""""""""

When building custom containers, keep in mind the following requirements:

* The ``USER`` should be ``root``.
* Use an ``init`` process, such as ``systemd``.
* Include ``sshd`` and accept connections on the default port of ``22``.
* Include a POSIX compatible ``sh`` shell which can be found on ``PATH``.
* Include a ``sleep`` utility which runs as a subprocess.
* Include a supported version of Python.
* Avoid using the ``VOLUME`` statement.

Docker and SELinux
^^^^^^^^^^^^^^^^^^

Using Docker on a host with SELinux may require setting the system in permissive mode.
Consider using Podman instead.

Docker Desktop with WSL2
^^^^^^^^^^^^^^^^^^^^^^^^

These instructions explain how to use ``ansible-test`` with WSL2 and Docker Desktop *without* ``systemd`` support.

.. note::

   If your WSL2 environment includes ``systemd`` support, these steps are not required.

.. _configuration_requirements:

Configuration requirements
""""""""""""""""""""""""""

1. Open Docker Desktop and go to the **Settings** screen.
2. On the the **General** tab:

   a. Uncheck the **Start Docker Desktop when you log in** checkbox.
   b. Check the **Use the WSL 2 based engine** checkbox.

3. On the **Resources** tab under the **WSL Integration** section:

   a. Enable distros you want to use under the **Enable integration with additional distros** section.

4. Click **Apply and restart** if changes were made.

.. _setup_instructions:

Setup instructions
""""""""""""""""""

.. note::

   If all WSL instances have been stopped, these changes will need to be re-applied.

1. Verify Docker Desktop is properly configured (see :ref:`configuration_requirements`).
2. Quit Docker Desktop if it is running:

   a. Right click the **Docker Desktop** taskbar icon.
   b. Click the **Quit Docker Desktop** option.

3. Stop any running WSL instances with the command:

   .. code-block:: shell

      wsl --shutdown

4. Verify all WSL instances have stopped with the command:

   .. code-block:: shell

      wsl -l -v

5. Start a WSL instance and perform the following steps as ``root``:

   a. Verify the ``systemd`` subsystem is not registered:

      a.  Check for the ``systemd`` cgroup hierarchy with the following command:

          .. code-block:: shell

             grep systemd /proc/self/cgroup

      b. If any matches are found, re-check the :ref:`configuration_requirements` and follow the
         :ref:`setup_instructions` again.

   b. Mount the ``systemd`` cgroup hierarchy with the following commands:

   .. code-block:: shell

      mkdir /sys/fs/cgroup/systemd
      mount cgroup -t cgroup /sys/fs/cgroup/systemd -o none,name=systemd,xattr

6. Start Docker Desktop.

You should now be able to use ``ansible-test`` with the ``--docker`` option.

.. _linux_cgroup_configuration:

Linux cgroup configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

   These changes will need to be re-applied each time the container host is booted.

For certain container hosts and container combinations, additional setup on the container host may be required.
In these situations ``ansible-test`` will report an error and provide additional instructions to run as ``root``:

.. code-block:: shell

   mkdir /sys/fs/cgroup/systemd
   mount cgroup -t cgroup /sys/fs/cgroup/systemd -o none,name=systemd,xattr

If you are using rootless Podman, an additional command must be run, also as ``root``.
Make sure to substitute your user and group for ``{user}`` and ``{group}`` respectively:

.. code-block:: shell

   chown -R {user}:{group} /sys/fs/cgroup/systemd

Podman
""""""

When using Podman, you may need to stop existing Podman processes after following the :ref:`linux_cgroup_configuration`
instructions. Otherwise Podman may be unable to see the new mount point.

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

Additional Requirements
=======================

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
    :ref:`debugging_modules` instructions.

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

.. code-block:: shell

   ansible-test coverage erase
   ansible-test units --coverage apt
   ansible-test integration --coverage aws_lambda
   ansible-test coverage html

Reports can be generated in several different formats:

* ``ansible-test coverage report`` - Console report.
* ``ansible-test coverage html`` - HTML report.
* ``ansible-test coverage xml`` - XML report.

To clear data between test runs, use the ``ansible-test coverage erase`` command.
