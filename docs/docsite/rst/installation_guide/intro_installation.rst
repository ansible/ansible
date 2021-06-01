.. _installation_guide:
.. _intro_installation_guide:

******************
Installing Ansible
******************

Ansible is an agentless automation tool that you install on a control node. From the control node, Ansible manages machines and other devices remotely (by default, over the SSH protocol).

To install Ansible for use at the command line, simply install the Ansible package on one machine (which could easily be a laptop). You do not need to install a database or run any daemons. Ansible can manage an entire fleet of remote machines from that one control node.

.. contents::
  :local:

Prerequisites
=============

Before you install Ansible, review the requirements for a control node. Before you use Ansible, review the requirements for managed nodes (those end devices you want to automate). Control nodes and managed nodes have different minimum requirements.

.. _control_node_requirements:

Control node requirements
-------------------------

For your control node (the machine that runs Ansible), you can use any machine with Python 2 (version 2.7) or Python 3 (versions 3.5 and higher) installed. ansible-core 2.11 and Ansible 4.0.0 will make Python 3.8 a soft dependency for the control node, but will function with the aforementioned requirements. ansible-core 2.12 and Ansible 5.0.0 will require Python 3.8 or newer to function on the control node. Starting with ansible-core 2.11, the project will only be packaged for Python 3.8 and newer.
This includes Red Hat, Debian, CentOS, macOS, any of the BSDs, and so on.
Windows is not supported for the control node, read more about this in `Matt Davis's blog post <http://blog.rolpdog.com/2020/03/why-no-ansible-controller-for-windows.html>`_.

.. warning::

    Please note that some plugins that run on the control node have additional requirements. These requirements should be listed in the plugin documentation.

When choosing a control node, remember that any management system benefits from being run near the machines being managed. If you are using Ansible to manage machines in a cloud, consider using a machine inside that cloud as your control node. In most cases Ansible will perform better from a machine on the cloud than from a machine on the open Internet.

.. warning::

    Ansible 2.11 will make Python 3.8 a soft dependency for the control node, but will function with the aforementioned requirements. Ansible 2.12 will require Python 3.8 or newer to function on the control node. Starting with Ansible 2.11, the project will only be packaged for Python 3.8 and newer.


.. _managed_node_requirements:

Managed node requirements
-------------------------

Although you do not need a daemon on your managed nodes, you do need a way for Ansible to communicate with them. For most managed nodes, Ansible makes a connection over SSH and transfers modules using SFTP. If SSH works but SFTP is not available on some of your managed nodes, you can switch to SCP in :ref:`ansible.cfg <ansible_configuration_settings>`. For any machine or device that can run Python, you also need Python 2 (version 2.6 or later) or Python 3 (version 3.5 or later).

.. warning::

    Please note that some modules have additional requirements that need to be satisfied on the 'target' machine (the managed node). These requirements should be listed in the module documentation.

.. note::

   * If you have SELinux enabled on remote nodes, you will also want to install libselinux-python on them before using any copy/file/template related functions in Ansible. You can use the :ref:`yum module<yum_module>` or :ref:`dnf module<dnf_module>` in Ansible to install this package on remote systems that do not have it.

   * By default, before the first Python module in a playbook runs on a host, Ansible attempts to discover a suitable Python interpreter on that host. You can override the discovery behavior by setting the :ref:`ansible_python_interpreter<ansible_python_interpreter>` inventory variable to a specific interpreter, and in other ways. See :ref:`interpreter_discovery` for details.

   * Ansible's :ref:`raw module<raw_module>`, and the :ref:`script module<script_module>`, do not depend on a client side install of Python to run.  Technically, you can use Ansible to install a compatible version of Python using the :ref:`raw module<raw_module>`, which then allows you to use everything else. For example, if you need to bootstrap Python 2 onto a RHEL-based system, you can install it as follows:

     .. code-block:: shell

        $ ansible myhost --become -m raw -a "yum install -y python2"

.. _what_version:

Selecting an Ansible artifact and version to install
====================================================

Starting with version 2.10, Ansible distributes two artifacts: a community package called ``ansible`` and a minimalist language and runtime called ``ansible-core`` (called `ansible-base` in version 2.10). Choose the Ansible artifact and version that matches your particular needs.

Installing the Ansible community package
----------------------------------------

The ``ansible`` package includes the Ansible language and runtime plus a range of community curated Collections. It recreates and expands on the functionality that was included in Ansible 2.9.

You can choose any of the following ways to install the Ansible community package:

* Install the latest release with your OS package manager (for Red Hat Enterprise Linux (TM), CentOS, Fedora, Debian, or Ubuntu).
* Install with ``pip`` (the Python package manager).

Installing `ansible-core`
-------------------------

Ansible also distributes a minimalist object called ``ansible-core`` (or ``ansible-base`` in version 2.10). It contains the Ansible language, runtime, and a short list of core modules and other plugins. You can build functionality on top of ``ansible-core`` by installing collections from Galaxy, Automation Hub, or any other source.

You can choose any of the following ways to install ``ansible-core``:

* Install ``ansible-core`` (version 2.11 and greater) or ``ansible-base`` (version 2.10) with ``pip``.
* Install ``ansible-core`` from source from the ansible/ansible GitHub repository to access the development (``devel``) version to develop or test the latest features.

.. note::

	You should only run ``ansible-core`` from ``devel`` if you are modifying ``ansible-core``, or trying out features under development. This is a rapidly changing source of code and can become unstable at any point.

Ansible generally creates new releases twice a year. See :ref:`release_and_maintenance` for information on release timing and maintenance of older releases.

.. _from_pip:

Installing and upgrading Ansible with ``pip``
=============================================

Ansible can be installed on many systems with ``pip``, the Python package manager.

Prerequisites: Installing ``pip``
----------------------------------

If ``pip`` is not already available on your system, run the following commands to install it::

    $ curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $ python get-pip.py --user

You may need to perform some additional configuration before you are able to run Ansible. See the Python documentation on `installing to the user site`_ for more information.

.. _installing to the user site: https://packaging.python.org/tutorials/installing-packages/#installing-to-the-user-site

Installing Ansible with ``pip``
-------------------------------

Once ``pip`` is installed, you can install Ansible [1]_::

    $ python -m pip install --user ansible

In order to use the ``paramiko`` connection plugin or modules that require ``paramiko``, install the required module [2]_::

    $ python -m pip install --user paramiko

If you wish to install Ansible globally, run the following commands::

    $ sudo python get-pip.py
    $ sudo python -m pip install ansible

.. note::

    Running ``pip`` with ``sudo`` will make global changes to the system. Since ``pip`` does not coordinate with system package managers, it could make changes to your system that leaves it in an inconsistent or non-functioning state. This is particularly true for macOS. Installing with ``--user`` is recommended unless you understand fully the implications of modifying global files on the system.

.. note::

    Older versions of ``pip`` default to http://pypi.python.org/simple, which no longer works.
    Please make sure you have the latest version of ``pip`` before installing Ansible.
    If you have an older version of ``pip`` installed, you can upgrade by following `pip's upgrade instructions <https://pip.pypa.io/en/stable/installing/#upgrading-pip>`_ .

.. _from_pip_venv:

Installing Ansible in a virtual environment with ``pip``
--------------------------------------------------------

.. note::

	If you have Ansible 2.9 or older installed, you need to use ``pip uninstall ansible`` first to remove older versions of Ansible before re-installing it.

Ansible can also be installed inside a new or existing ``virtualenv``::

    $ python -m virtualenv ansible  # Create a virtualenv if one does not already exist
    $ source ansible/bin/activate   # Activate the virtual environment
    $ python -m pip install ansible

.. _pip_upgrade:

Upgrading Ansible with ``pip``
------------------------------

Upgrading from 2.9 or earlier to 2.10
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Starting in version 2.10, Ansible is made of two packages. When you upgrade from version 2.9 and older to version 2.10 or later, you need to uninstall the old Ansible version (2.9 or earlier) before upgrading. If you do not uninstall the older version of Ansible, you will see the following message, and no change will be performed:

.. code-block:: console

    Cannot install ansible-base with a pre-existing ansible==2.x installation.

    Installing ansible-base with ansible-2.9 or older currently installed with
    pip is known to cause problems. Please uninstall ansible and install the new
    version:

    pip uninstall ansible
    pip install ansible-base

    ...

As explained by the message, to upgrade you must first remove the version of Ansible installed and then install it to the latest version.

.. code-block:: console

    $ pip uninstall ansible
    $ pip install ansible

.. _installing_the_control_node:
.. _from_yum:

Installing Ansible on specific operating systems
================================================

Follow these instructions to install the Ansible community package on a variety of operating systems.

Installing Ansible on RHEL, CentOS, or Fedora
----------------------------------------------

On Fedora:

.. code-block:: bash

    $ sudo dnf install ansible

On RHEL and CentOS:

.. code-block:: bash

    $ sudo yum install ansible

RPMs for RHEL 7 and RHEL 8 are available from the `Ansible Engine repository <https://access.redhat.com/articles/3174981>`_.

To enable the Ansible Engine repository for RHEL 8, run the following command:

.. code-block:: bash

    $ sudo subscription-manager repos --enable ansible-2.9-for-rhel-8-x86_64-rpms

To enable the Ansible Engine repository for RHEL 7, run the following command:

.. code-block:: bash

    $ sudo subscription-manager repos --enable rhel-7-server-ansible-2.9-rpms

RPMs for currently supported versions of RHEL and CentOS are also available from `EPEL <https://fedoraproject.org/wiki/EPEL>`_.

.. note::

	Since Ansible 2.10 for RHEL is not available at this time,  continue to use Ansible 2.9.

Ansible can manage older operating systems that contain Python 2.6 or higher.

.. _from_apt:

Installing Ansible on Ubuntu
----------------------------

Ubuntu builds are available `in a PPA here <https://launchpad.net/~ansible/+archive/ubuntu/ansible>`_.

To configure the PPA on your machine and install Ansible run these commands:

.. code-block:: bash

    $ sudo apt update
    $ sudo apt install software-properties-common
    $ sudo apt-add-repository --yes --update ppa:ansible/ansible
    $ sudo apt install ansible

.. note:: On older Ubuntu distributions, "software-properties-common" is called "python-software-properties". You may want to use ``apt-get`` instead of ``apt`` in older versions. Also, be aware that only newer distributions (in other words, 18.04, 18.10, and so on) have a ``-u`` or ``--update`` flag, so adjust your script accordingly.

Debian/Ubuntu packages can also be built from the source checkout, run:

.. code-block:: bash

    $ make deb

Installing Ansible on Debian
----------------------------

Debian users may leverage the same source as the Ubuntu PPA.

Add the following line to /etc/apt/sources.list:

.. code-block:: bash

    deb http://ppa.launchpad.net/ansible/ansible/ubuntu trusty main

Then run these commands:

.. code-block:: bash

    $ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 93C4A3FD7BB9C367
    $ sudo apt update
    $ sudo apt install ansible

.. note:: This method has been verified with the Trusty sources in Debian Jessie and Stretch but may not be supported in earlier versions. You may want to use ``apt-get`` instead of ``apt`` in older versions.

Installing Ansible on Gentoo with portage
-----------------------------------------

.. code-block:: bash

    $ emerge -av app-admin/ansible

To install the newest version, you may need to unmask the Ansible package prior to emerging:

.. code-block:: bash

    $ echo 'app-admin/ansible' >> /etc/portage/package.accept_keywords

Installing Ansible on FreeBSD
-----------------------------

Though Ansible works with both Python 2 and 3 versions, FreeBSD has different packages for each Python version.
So to install you can use:

.. code-block:: bash

    $ sudo pkg install py27-ansible

or:

.. code-block:: bash

    $ sudo pkg install py36-ansible


You may also wish to install from ports, run:

.. code-block:: bash

    $ sudo make -C /usr/ports/sysutils/ansible install

You can also choose a specific version, for example ``ansible25``.

Older versions of FreeBSD worked with something like this (substitute for your choice of package manager):

.. code-block:: bash

    $ sudo pkg install ansible

.. _on_macos:

Installing Ansible on macOS
---------------------------

The preferred way to install Ansible on a Mac is with ``pip``.

The instructions can be found in :ref:`from_pip`. If you are running macOS version 10.12 or older, then you should upgrade to the latest ``pip`` to connect to the Python Package Index securely. It should be noted that pip must be run as a module on macOS, and the linked ``pip`` instructions will show you how to do that.

.. note::

	To upgrade from Ansible 2.9 or older to Ansible 3 or later, you must ``pip uninstall ansible`` first to remove older versions of Ansible before re-installing it.

.. note::

   macOS by default is configured for a small number of file handles, so if you want to use 15 or more forks you'll need to raise the ulimit with ``sudo launchctl limit maxfiles unlimited``. This command can also fix any "Too many open files" errors.

If you are installing on macOS Mavericks (10.9), you may encounter some noise from your compiler. A workaround is to do the following::

    $ CFLAGS=-Qunused-arguments CPPFLAGS=-Qunused-arguments pip install --user ansible


.. _from_pkgutil:

Installing Ansible on Solaris
-----------------------------

Ansible is available for Solaris as `SysV package from OpenCSW <https://www.opencsw.org/packages/ansible/>`_.

.. code-block:: bash

    # pkgadd -d http://get.opencsw.org/now
    # /opt/csw/bin/pkgutil -i ansible

.. _from_pacman:

Installing Ansible on Arch Linux
---------------------------------

Ansible is available in the Community repository::

    $ pacman -S ansible

The AUR has a PKGBUILD for pulling directly from GitHub called `ansible-git <https://aur.archlinux.org/packages/ansible-git>`_.

Also see the `Ansible <https://wiki.archlinux.org/index.php/Ansible>`_ page on the ArchWiki.

.. _from_sbopkg:

Installing Ansible on Slackware Linux
-------------------------------------

Ansible build script is available in the `SlackBuilds.org <https://slackbuilds.org/apps/ansible/>`_ repository.
Can be built and installed using `sbopkg <https://sbopkg.org/>`_.

Create queue with Ansible and all dependencies::

    # sqg -p ansible

Build and install packages from a created queuefile (answer Q for question if sbopkg should use queue or package)::

    # sbopkg -k -i ansible

.. _from swupd:

Installing Ansible on Clear Linux
---------------------------------

Ansible and its dependencies are available as part of the sysadmin host management bundle::

    $ sudo swupd bundle-add sysadmin-hostmgmt

Update of the software will be managed by the swupd tool::

   $ sudo swupd update

.. _from_pip_devel:
.. _getting_ansible:

Installing and running the ``devel`` branch from source
=======================================================

In Ansible 2.10 and later, the `ansible/ansible repository <https://github.com/ansible/ansible>`_ contains the code for basic features and functions, such as copying module code to managed nodes. This code is also known as ``ansible-core``.

New features are added to ``ansible-core`` on a branch called ``devel``. If you are testing new features, fixing bugs, or otherwise working with the development team on changes to the core code, you can install and run ``devel``.

.. note::

    You should only install and run the ``devel`` branch if you are modifying ``ansible-core`` or trying out features under development. This is a rapidly changing source of code and can become unstable at any point.

.. note::

   If you want to use Ansible Tower as the control node, do not install or run the ``devel`` branch of Ansible. Use an OS package manager (like ``apt`` or ``yum``) or ``pip`` to install a stable version.

If you are running Ansible from source, you may also wish to follow the `Ansible GitHub project <https://github.com/ansible/ansible>`_. We track issues, document bugs, and share feature ideas in this and other related repositories.

For more information on getting involved in the Ansible project, see the :ref:`ansible_community_guide`. For more information on creating Ansible modules and Collections, see the :ref:`developer_guide`.

Installing ``devel`` from GitHub with ``pip``
---------------------------------------------

You can install the ``devel`` branch of ``ansible-core`` directly from GitHub with ``pip``:

.. code-block:: bash

    $ python -m pip install --user https://github.com/ansible/ansible/archive/devel.tar.gz

.. note::

    If you have Ansible 2.9 or older installed, you need to use ``pip uninstall ansible`` first to remove older versions of Ansible before re-installing it. See :ref:`pip_upgrade` for more details.

You can replace ``devel`` in the URL mentioned above, with any other branch or tag on GitHub to install older versions of Ansible (prior to ``ansible-base`` 2.10.), tagged alpha or beta versions, and release candidates. This installs all of Ansible.

.. code-block:: bash

    $ python -m pip install --user https://github.com/ansible/ansible/archive/stable-2.9.tar.gz

See :ref:`from_source` for instructions on how to run ``ansible-core`` directly from source.


Installing ``devel`` from GitHub by cloning
-------------------------------------------

You can install the ``devel`` branch of ``ansible-core`` by cloning the GitHub repository:

.. code-block:: bash

    $ git clone https://github.com/ansible/ansible.git
    $ cd ./ansible

The default branch is ``devel``.

.. _from_source:

Running the ``devel`` branch from a clone
-----------------------------------------

``ansible-core`` is easy to run from source. You do not need ``root`` permissions to use it and there is no software to actually install. No daemons or database setup are required.

Once you have installed the ``ansible-core`` repository by cloning, setup the Ansible environment:

Using Bash:

.. code-block:: bash

    $ source ./hacking/env-setup

Using Fish::

    $ source ./hacking/env-setup.fish

If you want to suppress spurious warnings/errors, use::

    $ source ./hacking/env-setup -q

If you do not have ``pip`` installed in your version of Python, install it::

    $ curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $ python get-pip.py --user

Ansible also uses the following Python modules that need to be installed [1]_:

.. code-block:: bash

    $ python -m pip install --user -r ./requirements.txt

To update the ``devel`` branch of ``ansible-core`` on your local machine, use pull-with-rebase so any local changes are replayed.

.. code-block:: bash

    $ git pull --rebase

.. code-block:: bash

    $ git pull --rebase #same as above
    $ git submodule update --init --recursive

After you run the the env-setup script, you will be running from the source code. The default inventory file will be ``/etc/ansible/hosts``. You can optionally specify an inventory file (see :ref:`inventory`) other than ``/etc/ansible/hosts``:

.. code-block:: bash

    $ echo "127.0.0.1" > ~/ansible_hosts
    $ export ANSIBLE_INVENTORY=~/ansible_hosts

You can read more about the inventory file at :ref:`inventory`.

Confirming your installation
============================

Whatever method of installing Ansible you chose, you can test that it is installed correctly with a ping command:

.. code-block:: bash

    $ ansible all -m ping --ask-pass

You can also use "sudo make install".

.. _tagged_releases:

Finding tarballs of tagged releases
===================================

Packaging Ansible or wanting to build a local package yourself, but don't want to do a git checkout?  Tarballs of releases are available from ``pypi`` as https://pypi.python.org/packages/source/a/ansible/ansible-{{VERSION}}.tar.gz. You can make VERSION a variable in your package managing system that you update in one place whenever you package a new version. Alternately, you can download https://pypi.python.org/project/ansible  to get the latest stable release.

.. note::

	If you are creating your own Ansible package, you must also download or package ``ansible-base`` as part of your Ansible package. You can download it as https://pypi.python.org/packages/source/a/ansible-base/ansible-base-{{VERSION}}.tar.gz.

These releases are also tagged in the `git repository <https://github.com/ansible/ansible/releases>`_ with the release version.


.. _shell_completion:

Adding Ansible command shell completion
=======================================

As of Ansible 2.9, you can add shell completion of the Ansible command line utilities by installing an optional dependency called ``argcomplete``. ``argcomplete`` supports bash, and has limited support for zsh and tcsh.

You can install ``python-argcomplete`` from EPEL on Red Hat Enterprise based distributions, and or from the standard OS repositories for many other distributions.

For more information about installation and configuration, see the `argcomplete documentation <https://argcomplete.readthedocs.io/en/latest/>`_.

Installing ``argcomplete`` on RHEL, CentOS, or Fedora
-----------------------------------------------------

On Fedora:

.. code-block:: bash

    $ sudo dnf install python-argcomplete

On RHEL and CentOS:

.. code-block:: bash

    $ sudo yum install epel-release
    $ sudo yum install python-argcomplete


Installing ``argcomplete`` with ``apt``
---------------------------------------

.. code-block:: bash

    $ sudo apt install python-argcomplete


Installing ``argcomplete`` with ``pip``
---------------------------------------

.. code-block:: bash

    $ python -m pip install argcomplete

Configuring ``argcomplete``
---------------------------

There are 2 ways to configure ``argcomplete`` to allow shell completion of the Ansible command line utilities: globally or per command.

Global configuration
^^^^^^^^^^^^^^^^^^^^

Global completion requires bash 4.2.

.. code-block:: bash

    $ sudo activate-global-python-argcomplete

This will write a bash completion file to a global location. Use ``--dest`` to change the location.

Per command configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

If you do not have bash 4.2, you must register each script independently.

.. code-block:: bash

    $ eval $(register-python-argcomplete ansible)
    $ eval $(register-python-argcomplete ansible-config)
    $ eval $(register-python-argcomplete ansible-console)
    $ eval $(register-python-argcomplete ansible-doc)
    $ eval $(register-python-argcomplete ansible-galaxy)
    $ eval $(register-python-argcomplete ansible-inventory)
    $ eval $(register-python-argcomplete ansible-playbook)
    $ eval $(register-python-argcomplete ansible-pull)
    $ eval $(register-python-argcomplete ansible-vault)

You should place the above commands into your shells profile file such as ``~/.profile`` or ``~/.bash_profile``.

Using ``argcomplete`` with zsh or tcsh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See the `argcomplete documentation <https://argcomplete.readthedocs.io/en/latest/>`_.


.. seealso::

   :ref:`intro_adhoc`
       Examples of basic commands
   :ref:`working_with_playbooks`
       Learning ansible's configuration management language
   :ref:`installation_faqs`
       Ansible Installation related to FAQs
   `Mailing List <https://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel

.. [1] If you have issues with the "pycrypto" package install on macOS, then you may need to try ``CC=clang sudo -E pip install pycrypto``.
.. [2] ``paramiko`` was included in Ansible's ``requirements.txt`` prior to 2.8.
