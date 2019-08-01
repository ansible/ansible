.. _installation_guide:
.. _intro_installation_guide:

Installation Guide
==================

.. contents:: Topics

Welcome to the Ansible Installation Guide!

.. _what_will_be_installed:

Basics / What Will Be Installed
```````````````````````````````

Ansible by default manages machines over the SSH protocol.

Once Ansible is installed, it will not add a database, and there will be no daemons to start or keep running.  You only need to install it on one machine (which could easily be a laptop) and it can manage an entire fleet of remote machines from that central point.  When Ansible manages remote machines, it does not leave software installed or running on them, so there's no real question about how to upgrade Ansible when moving to a new version.

.. _what_version:

What Version To Pick?
`````````````````````

Because it runs so easily from source and does not require any installation of software on remote
machines, many users will actually track the development version.

Ansible's release cycles are usually about four months long. Due to this short release cycle,
minor bugs will generally be fixed in the next release versus maintaining backports on the stable branch.
Major bugs will still have maintenance releases when needed, though these are infrequent.

If you are wishing to run the latest released version of Ansible and you are running Red Hat Enterprise Linux (TM), CentOS, Fedora, Debian, or Ubuntu, we recommend using the OS package manager.

For other installation options, we recommend installing via ``pip``, which is the Python package manager.

If you wish to track the development release to use and test the latest features, we will share
information about running from source. It's not necessary to install the program to run from source.

.. _control_node_requirements:

Control Node Requirements
````````````````````````````

Currently Ansible can be run from any machine with Python 2 (version 2.7) or Python 3 (versions 3.5 and higher) installed. Windows isn't supported for the control node.

This includes Red Hat, Debian, CentOS, macOS, any of the BSDs, and so on.

.. note::

    macOS by default is configured for a small number of file handles, so if you want to use 15 or more forks you'll need to raise the ulimit with ``sudo launchctl limit maxfiles unlimited``. This command can also fix any "Too many open files" error.


.. warning::

    Please note that some modules and plugins have additional requirements. For modules these need to be satisfied on the 'target' machine and should be listed in the module specific docs.

.. _managed_node_requirements:

Managed Node Requirements
`````````````````````````

On the managed nodes, you need a way to communicate, which is normally ssh. By
default this uses sftp. If that's not available, you can switch to scp in
:file:`ansible.cfg`.  You also need Python 2 (version 2.6 or later) or Python 3 (version 3.5 or
later).

.. note::

   * If you have SELinux enabled on remote nodes, you will also want to install
     libselinux-python on them before using any copy/file/template related functions in Ansible. You
     can use the :ref:`yum module<yum_module>` or :ref:`dnf module<dnf_module>` in Ansible to install this package on remote systems
     that do not have it.

   * By default, Ansible uses the python interpreter located at :file:`/usr/bin/python` to run its
     modules.  However, some Linux distributions may only have a Python 3 interpreter installed to
     :file:`/usr/bin/python3` by default.  On those systems, you may see an error like::

        "module_stdout": "/bin/sh: /usr/bin/python: No such file or directory\r\n"

     you can either set the :ref:`ansible_python_interpreter<ansible_python_interpreter>` inventory variable (see
     :ref:`inventory`) to point at your interpreter or you can install a Python 2 interpreter for
     modules to use. You will still need to set :ref:`ansible_python_interpreter<ansible_python_interpreter>` if the Python
     2 interpreter is not installed to :command:`/usr/bin/python`.

   * Ansible's "raw" module (for executing commands in a quick and dirty way) and the script module
     don't even need Python installed.  So technically, you can use Ansible to install a compatible
     version of Python using the :ref:`raw module<raw_module>`, which then allows you to use everything else.
     For example, if you need to bootstrap Python 2 onto a RHEL-based system, you can install it
     via

     .. code-block:: shell

        $ ansible myhost --become -m raw -a "yum install -y python2"

.. _installing_the_control_node:

Installing the Control Node
``````````````````````````````
.. _from_yum:

Latest Release via DNF or Yum
+++++++++++++++++++++++++++++

On Fedora:

.. code-block:: bash

    $ sudo dnf install ansible

On RHEL and CentOS:

.. code-block:: bash

    $ sudo yum install ansible

RPMs for RHEL 7  and RHEL 8 are available from the `Ansible Engine repository <https://access.redhat.com/articles/3174981>`_.

To enable the Ansible Engine repository for RHEL 8, run the following command:

.. code-block:: bash

    $ sudo subscription-manager repos --enable ansible-2.8-for-rhel-8-x86_64-rpms

To enable the Ansible Engine repository for RHEL 7, run the following command:

.. code-block:: bash

    $ sudo subscription-manager repos --enable rhel-7-server-ansible-2.8-rpms

RPMs for currently supported versions of RHEL, CentOS, and Fedora are available from `EPEL <https://fedoraproject.org/wiki/EPEL>`_ as well as `releases.ansible.com <https://releases.ansible.com/ansible/rpm>`_.

Ansible version 2.4 and later can manage earlier operating systems that contain Python 2.6 or higher.

You can also build an RPM yourself. From the root of a checkout or tarball, use the ``make rpm`` command to build an RPM you can distribute and install.

.. code-block:: bash

    $ git clone https://github.com/ansible/ansible.git
    $ cd ./ansible
    $ make rpm
    $ sudo rpm -Uvh ./rpm-build/ansible-*.noarch.rpm

.. _from_apt:

Latest Releases via Apt (Ubuntu)
++++++++++++++++++++++++++++++++

Ubuntu builds are available `in a PPA here <https://launchpad.net/~ansible/+archive/ubuntu/ansible>`_.

To configure the PPA on your machine and install ansible run these commands:

.. code-block:: bash

    $ sudo apt update
    $ sudo apt install software-properties-common
    $ sudo apt-add-repository --yes --update ppa:ansible/ansible
    $ sudo apt install ansible

.. note:: On older Ubuntu distributions, "software-properties-common" is called "python-software-properties". You may want to use ``apt-get`` instead of ``apt`` in older versions. Also, be aware that only newer distributions (i.e. 18.04, 18.10, etc.) have a ``-u`` or ``--update`` flag, so adjust your script accordingly.

Debian/Ubuntu packages can also be built from the source checkout, run:

.. code-block:: bash

    $ make deb

You may also wish to run from source to get the latest, which is covered below.

Latest Releases via Apt (Debian)
++++++++++++++++++++++++++++++++

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

Latest Releases via Portage (Gentoo)
++++++++++++++++++++++++++++++++++++

.. code-block:: bash

    $ emerge -av app-admin/ansible

To install the newest version, you may need to unmask the ansible package prior to emerging:

.. code-block:: bash

    $ echo 'app-admin/ansible' >> /etc/portage/package.accept_keywords

Latest Releases via pkg (FreeBSD)
+++++++++++++++++++++++++++++++++

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

You can also choose a specific version, i.e  ``ansible25``.

Older versions of FreeBSD worked with something like this (substitute for your choice of package manager):

.. code-block:: bash

    $ sudo pkg install ansible

.. _on_macos:

Latest Releases on macOS
++++++++++++++++++++++++++

The preferred way to install Ansible on a Mac is via ``pip``.

The instructions can be found in `Latest Releases via Pip`_ section. If you are running macOS version 10.12 or older, then you should upgrade to the latest ``pip`` to connect to the Python Package Index securely.

.. _from_pkgutil:

Latest Releases via OpenCSW (Solaris)
+++++++++++++++++++++++++++++++++++++

Ansible is available for Solaris as `SysV package from OpenCSW <https://www.opencsw.org/packages/ansible/>`_.

.. code-block:: bash

    # pkgadd -d http://get.opencsw.org/now
    # /opt/csw/bin/pkgutil -i ansible

.. _from_pacman:

Latest Releases via Pacman (Arch Linux)
+++++++++++++++++++++++++++++++++++++++

Ansible is available in the Community repository::

    $ pacman -S ansible

The AUR has a PKGBUILD for pulling directly from GitHub called `ansible-git <https://aur.archlinux.org/packages/ansible-git>`_.

Also see the `Ansible <https://wiki.archlinux.org/index.php/Ansible>`_ page on the ArchWiki.

.. _from_sbopkg:

Latest Releases via sbopkg (Slackware Linux)
++++++++++++++++++++++++++++++++++++++++++++

Ansible build script is available in the `SlackBuilds.org <https://slackbuilds.org/apps/ansible/>`_ repository.
Can be built and installed using `sbopkg <https://sbopkg.org/>`_.

Create queue with Ansible and all dependencies::

    # sqg -p ansible

Build and install packages from created queuefile (answer Q for question if sbopkg should use queue or package)::

    # sbopkg -k -i ansible

.. _from swupd:

Latest Release via swupd (Clear Linux)
+++++++++++++++++++++++++++++++++++++++

Ansible and its dependencies are available as part of the sysadmin host management bundle::

    $ sudo swupd bundle-add sysadmin-hostmgmt

Update of the software will be managed by the swupd tool::

   $ sudo swupd update

.. _from_pip:

Latest Releases via Pip
+++++++++++++++++++++++

Ansible can be installed via ``pip``, the Python package manager.  If ``pip`` isn't already available on your system of Python, run the following commands to install it::

    $ curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $ python get-pip.py --user

Then install Ansible [1]_::

    $ pip install --user ansible

Or if you are looking for the latest development version::

    $ pip install --user git+https://github.com/ansible/ansible.git@devel

If you are installing on macOS Mavericks (10.9), you may encounter some noise from your compiler. A workaround is to do the following::

    $ CFLAGS=-Qunused-arguments CPPFLAGS=-Qunused-arguments pip install --user ansible

In order to use the ``paramiko`` connection plugin or modules that require ``paramiko``, install the required module [2]_::

    $ pip install --user paramiko

Ansble can also be installed inside a new or existing ``virtualenv``::

    $ python -m virtualenv ansible  # Create a virtualenv if one does not already exist
    $ source ansible/bin/activate   # Activate the virtual environment
    $ pip install ansible

If you wish to install Ansible globally, run the following commands::

    $ sudo python get-pip.py
    $ sudo pip install ansible

.. note::

    Running ``pip`` with ``sudo`` will make global changes to the system. Since ``pip`` does not coordinate with system package managers, it could make changes to your system that leaves it in an inconsistent or non-functioning state. This is particularly true for macOS. Installing with ``--user`` is recommended unless you understand fully the implications of modifying global files on the system.

.. note::

    Older versions of ``pip`` default to http://pypi.python.org/simple, which no longer works.
    Please make sure you have the latest version of ``pip`` before installing Ansible.
    If you have an older version of ``pip`` installed, you can upgrade by following `pip's upgrade instructions <https://pip.pypa.io/en/stable/installing/#upgrading-pip>`_ .

.. _tagged_releases:

Tarballs of Tagged Releases
+++++++++++++++++++++++++++

Packaging Ansible or wanting to build a local package yourself, but don't want to do a git checkout?  Tarballs of releases are available on the `Ansible downloads <https://releases.ansible.com/ansible>`_ page.

These releases are also tagged in the `git repository <https://github.com/ansible/ansible/releases>`_ with the release version.




.. _from_source:

Running From Source
+++++++++++++++++++

Ansible is easy to run from source. You do not need ``root`` permissions
to use it and there is no software to actually install. No daemons
or database setup are required. Because of this, many users in our community use the
development version of Ansible all of the time so they can take advantage of new features
when they are implemented and easily contribute to the project. Because there is
nothing to install, following the development version is significantly easier than most
open source projects.

.. note::

   If you are want to use Ansible Tower as the Control Node, do not use a source installation of Ansible. Please use an OS package manager (like ``apt`` or ``yum``) or ``pip`` to install a stable version.


To install from source, clone the Ansible git repository:

.. code-block:: bash

    $ git clone https://github.com/ansible/ansible.git
    $ cd ./ansible

Once ``git`` has cloned the Ansible repository, setup the Ansible environment:

Using Bash:

.. code-block:: bash

    $ source ./hacking/env-setup

Using Fish::

    $ source ./hacking/env-setup.fish

If you want to suppress spurious warnings/errors, use::

    $ source ./hacking/env-setup -q

If you don't have ``pip`` installed in your version of Python, install it::

    $ curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $ python get-pip.py --user

Ansible also uses the following Python modules that need to be installed [1]_:

.. code-block:: bash

    $ pip install --user -r ./requirements.txt

To update ansible checkouts, use pull-with-rebase so any local changes are replayed.

.. code-block:: bash

    $ git pull --rebase

.. code-block:: bash

    $ git pull --rebase #same as above
    $ git submodule update --init --recursive

Once running the env-setup script you'll be running from checkout and the default inventory file
will be ``/etc/ansible/hosts``. You can optionally specify an inventory file (see :ref:`inventory`)
other than ``/etc/ansible/hosts``:

.. code-block:: bash

    $ echo "127.0.0.1" > ~/ansible_hosts
    $ export ANSIBLE_INVENTORY=~/ansible_hosts

You can read more about the inventory file in later parts of the manual.

Now let's test things with a ping command:

.. code-block:: bash

    $ ansible all -m ping --ask-pass

You can also use "sudo make install".

.. _shell_completion:

Shell Completion
````````````````

As of Ansible 2.9 shell completion of the ansible command line utilities is available and provided through an optional dependency
called ``argcomplete``. ``argcomplete`` supports bash, and limited support for zsh and tcsh

``python-argcomplete`` can be installed from EPEL on Red Hat Enterprise based distributions, and is available in the standard OS repositories for many other distributions.

For more information about installing and configuration see the `argcomplete documentation <https://argcomplete.readthedocs.io/en/latest/>_`.

Installing
++++++++++

via yum/dnf
-----------

On Fedora:

.. code-block:: bash

    $ sudo dnf install python-argcomplete

On RHEL and CentOS:

.. code-block:: bash

    $ sudo yum install epel-release
    $ sudo yum install python-argcomplete

via apt
-------

.. code-block:: bash

    $ sudo apt install python-argcomplete

via pip
-------

.. code-block:: bash

    $ pip install argcomplete

Configuring
+++++++++++

There are 2 ways to configure argcomplete to allow shell completion of the Ansible command line utilities. Per command, or globally.

Globally
--------

Global completion requires bash 4.2

.. code-block:: bash

    $ sudo activate-global-python-argcomplete

This will write a bash completion file to a global location, use ``--dest`` to change the location

Per Command
-----------

If you do not have bash 4.2, you must register each script independently

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

It would be advisable to place the above commands, into your shells profile file such as ``~/.profile`` or ``~/.bash_profile``.

Zsh or tcsh
-----------

See the `argcomplete documentation <https://argcomplete.readthedocs.io/en/latest/>_`.

.. _getting_ansible:

Ansible on GitHub
`````````````````

You may also wish to follow the `GitHub project <https://github.com/ansible/ansible>`_ if
you have a GitHub account. This is also where we keep the issue tracker for sharing
bugs and feature ideas.


.. seealso::

   :ref:`intro_adhoc`
       Examples of basic commands
   :ref:`working_with_playbooks`
       Learning ansible's configuration management language
   :ref:`installation_faqs`
       Ansible Installation related to FAQs
   `Mailing List <https://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

.. [1] If you have issues with the "pycrypto" package install on macOS, then you may need to try ``CC=clang sudo -E pip install pycrypto``.
.. [2] ``paramiko`` was included in Ansible's ``requirements.txt`` prior to 2.8.
