Installation
============

.. index::
   pair: installation; introduction

.. contents:: Topics

.. _getting_ansible:

Ansible GitHub Project
````````````````````````

.. index::
   single: GitHub
   single: issue tracker
   single: bug reporting
   single: feature ideas

If you have a GitHub account, it may interest you to follow the `Ansible GitHub project <https://github.com/ansible/ansible>`_. This is also where the issue tracker for sharing bugs and feature ideas is kept.

.. _what_will_be_installed:

Basics / What Will Be Installed
`````````````````````````````````

.. index::
   pair: installation; what is installed

Ansible by default manages machines over the SSH protocol.

Once Ansible is installed, it will not add a database, and there will be no daemons to start or keep running.  You only need to install Ansible on one machine (which could easily be a laptop) and it can manage an entire fleet of remote machines from that central point.  When Ansible manages remote machines, it does not leave software installed or running on them, so there is no question about how to upgrade Ansible when moving to a new version.

.. _what_version:

.. index::
  single: versioning
  pair: Ansible; selecting a version
  pair: Ansible; release cycles

What Version To Pick?
`````````````````````

Because Ansible runs so easily from source and does not require any installation of software on remote machines, many users choose to track the development version.  

Ansible's release cycles are usually about two months long.  Due to this short release cycle, minor bugs are generally fixed in the next release versus maintaining backports on the stable branch.  Major bugs will still have maintenance releases when needed, although these are infrequent.

If you want to run the latest released version of Ansible, and you are running |rhel| (TM), CentOS, Fedora, Debian, or Ubuntu, it is recommended that you use the OS package manager.

For other installation options, it is recommended that you install via the ``pip`` command, which is the Python package manager, though other options are also available.

To track the development release to use and test the latest features, we will share information about running from source.  Note, however, that it is not necessary to install Ansible to run from source.
.. FIXME  we will share *what info, where?* about running from source..? 

.. _control_machine_requirements:

Control Machine Requirements
````````````````````````````

.. index:: 
  single: control machine requirements
  single: too many open files
  single: ulimit, raising
  single: fork management

Currently Ansible can be run from any machine with Python 2.6 or 2.7 installed (Windows isn't supported for the control machine).

This includes Red Hat, Debian, CentOS, OS X, any of the BSDs, and so on.

.. note::

    As of version 2.0, Ansible uses a few more file handles to manage its forks. OS X has a very low fork setting--to use 15 or more forks
    you must raise the *ulimit*, such as ``sudo launchctl limit maxfiles 1024 2048``. This is good troubleshooting advice to try any time you see a "Too many open files" type of error message.


.. _managed_node_requirements:

Managed Node Requirements
`````````````````````````

.. index::
  single: managed node requirements
  single: SFTP
  single: SCP
  single: python requirements
  single: bootstrapping 

On the managed nodes, you need a way to communicate, which is normally ``ssh``. By default this uses ``sftp``,  but you can switch to ``scp`` in the ``ansible.cfg`` file if it is needed. Also, you must have Python 2.4 or later installed. Please note that if you are running a version earlier than Python 2.5 on the remotes, you must also install ``python-simplejson``.

.. tip::

   Ansible's ``raw`` module (for executing commands in a quick and dirty
   way) and the script module don't have these requirements.  Technically, you can use
   Ansible to install python-simplejson using the ``raw`` module, which
   then allows you to use everything else.  (That's jumping ahead,
   though, and may be best left to more experienced users.)

.. note::

   If you have SELinux enabled on remote nodes, you should also install
   ``libselinux-python`` on them before using any copy/file/template related functions in
   Ansible. Use the ``yum`` module in Ansible to install this package on
   remote systems that do not have it.

.. note::

   Python 3 is a slightly different language than Python 2 and most Python programs (including
   Ansible) are not switching over yet.  However, some Linux distributions (Gentoo, Arch) may not have a 
   Python 2.X interpreter installed by default.  On those systems, you should install one, and set
   the ``ansible_python_interpreter`` variable in the inventory (see :doc:`intro_inventory`) to point at your 2.X Python.  Distributions
   like |rhel|, CentOS, Fedora, and Ubuntu all have a 2.X interpreter installed
   by default and this does not apply to those distributions.  This is also true of nearly all
   Unix systems.  If you need to bootstrap these remote systems by installing Python 2.X, 
   you can use the ``raw`` module to do this remotely.

.. _installing_the_control_machine:

Installing the Control Machine
````````````````````````````````

.. index:: 
  pair: installation; control machine
  pair: installation; source 
  pair: installation; Tower as the control machine
  pair: installation; python modules
  pair: installation; pip

.. _from_source:

Running From Source
+++++++++++++++++++

Ansible is trivially easy to run from a checkout--root permissions are not required to use it and there is no software to actually install for Ansible itself.  No daemons or database setups are required.  Many users in our community use the development version of Ansible all of the time, so they can take advantage of new features when they are implemented, as well as easily contribute to the project. Because there is
nothing to install, following the development version is significantly easier with Ansible than it is with most other open source projects.

.. note::
  
   If you are intending to use Tower as the Control Machine, do not use a source install. Please use an OS package manager (eg. apt/yum) or the ``pip`` command to install a stable version.


To install from source.

.. code-block:: bash

    $ git clone git://github.com/ansible/ansible.git --recursive
    $ cd ./ansible

Using Bash:

.. code-block:: bash

    $ source ./hacking/env-setup

Using Fish::

    $ . ./hacking/env-setup.fish

If you want to suppress spurious warnings/errors, use::

    $ source ./hacking/env-setup -q

If you don't have pip installed in your version of Python, install pip::

    $ sudo easy_install pip

Ansible also uses the following Python modules that need to be installed [1]_::

    $ sudo pip install paramiko PyYAML Jinja2 httplib2 six

Note when updating ansible, be sure to not only update the source tree, but also the "submodules" in git
which point at Ansible's own modules (not the same kind of modules, alas).

.. code-block:: bash

    $ git pull --rebase
    $ git submodule update --init --recursive

Once running the env-setup script you'll be running from checkout and the default inventory file
will be /etc/ansible/hosts.  You can optionally specify an inventory file (see :doc:`intro_inventory`)
other than /etc/ansible/hosts:

.. code-block:: bash

    $ echo "127.0.0.1" > ~/ansible_hosts
    $ export ANSIBLE_INVENTORY=~/ansible_hosts

.. note::

    ANSIBLE_INVENTORY is available starting at 1.9 and substitutes the deprecated ANSIBLE_HOSTS

You can read more about the inventory file in later parts of the manual.

Now let's test things with a ping command:

.. code-block:: bash

    $ ansible all -m ping --ask-pass

You can also use "sudo make install" if you wish.

.. _from_yum:

Latest Release Via Yum
++++++++++++++++++++++

RPMs are available from yum for `EPEL
<http://fedoraproject.org/wiki/EPEL>`_ 6, 7, and currently supported
Fedora distributions. 

Ansible itself can manage earlier operating
systems that contain Python 2.4 or higher (so also EL5).

Fedora users can install Ansible directly, though if you are using RHEL or CentOS and have not already done so, `configure EPEL <http://fedoraproject.org/wiki/EPEL>`_
   
.. code-block:: bash

    # install the epel-release RPM if needed on CentOS, RHEL, or Scientific Linux
    $ sudo yum install ansible

You can also build an RPM yourself.  From the root of a checkout or tarball, use the ``make rpm`` command to build an RPM you can distribute and install. Make sure you have ``rpm-build``, ``make``, and ``python2-devel`` installed.

.. code-block:: bash

    $ git clone git://github.com/ansible/ansible.git --recursive
    $ cd ./ansible
    $ make rpm
    $ sudo rpm -Uvh ./rpm-build/ansible-*.noarch.rpm

.. _from_apt:

Latest Releases Via Apt (Ubuntu)
++++++++++++++++++++++++++++++++

.. index::
  pair: installation; Ubuntu/Debian
  pair: installation; PPA

Ubuntu builds are available `in a PPA here <https://launchpad.net/~ansible/+archive/ansible>`_.

To configure the PPA on your machine and install Ansible, run the following commands:

.. code-block:: bash

    $ sudo apt-get install software-properties-common
    $ sudo apt-add-repository ppa:ansible/ansible
    $ sudo apt-get update
    $ sudo apt-get install ansible

.. note:: On older Ubuntu distributions, "software-properties-common" is called "python-software-properties".

Debian/Ubuntu packages can also be built from the source checkout, run:

.. code-block:: bash

    $ make deb

You may also wish to run from source to get the latest, which is covered in :ref:`from_source`.

.. _from_pkg:

Latest Releases Via Portage (Gentoo)
++++++++++++++++++++++++++++++++++++

.. index::
  pair: installation; latest releases
  pair: installation; Portage (Gentoo)
  single: Portage (Gentoo)

.. code-block:: bash

    $ emerge -av app-admin/ansible

To install the newest version, you may need to unmask the Ansible package prior to emerging:

.. code-block:: bash

    $ echo 'app-admin/ansible' >> /etc/portage/package.accept_keywords

.. note::

   If you have Python 3 as a default Python slot on your Gentoo nodes (default setting), then you
   must set ``ansible_python_interpreter = /usr/bin/python2`` in your group or inventory variables.


Latest Releases Via pkg (FreeBSD)
+++++++++++++++++++++++++++++++++

.. index::
  pair: installation; latest releases
  pair: installation; pkg (FreeBSD)
  pair: releases; pkg (FreeBSD)

.. code-block:: bash

    $ sudo pkg install ansible

To install from ports, run:

.. code-block:: bash

    $ sudo make -C /usr/ports/sysutils/ansible install

.. _on_macos:

Latest Releases on Mac OS X
++++++++++++++++++++++++++++++++++++++

.. index::
  pair: installation; latest releases
  pair: installation; Mac OS X
  pair: releases; Mac OS X

The preferred way to install Ansible on a Mac is via ``pip``.

The instructions can be found in the `Latest Releases Via Pip`_ section.

.. _from_pkgutil:

Latest Releases Via OpenCSW (Solaris)
+++++++++++++++++++++++++++++++++++++

.. index::
  pair: installation; latest releases
  pair: installation; OpenCSW (Solaris)
  pair: releases; OpenCSW (Solaris)

Ansible is available for Solaris as an SysV package from OpenCSW. Refer to the `OpenCSW documention <https://www.opencsw.org/packages/ansible/>`_ for more information.

.. code-block:: bash

    # pkgadd -d http://get.opencsw.org/now
    # /opt/csw/bin/pkgutil -i ansible

.. _from_pacman:

Latest Releases Via Pacman (Arch Linux)
+++++++++++++++++++++++++++++++++++++++

.. index::
   pair: installation; latest releases
   pair: installation; Pacman (Arch Linux)
   pair: releases; Pacman (Arch Linux)

Ansible is available in the Community repository:

::

    $ pacman -S ansible

The AUR has a PKGBUILD for pulling directly from Github called `ansible-git <https://aur.archlinux.org/packages/ansible-git>`_.

You should also review the `Ansible <https://wiki.archlinux.org/index.php/Ansible>`_ page on the ArchWiki.

.. note::

   If you have Python 3 as a default Python slot on your Arch nodes (default setting), then you
   must set ``ansible_python_interpreter = /usr/bin/python2`` in your group or inventory variables.

.. _from_pip:

Latest Releases Via Pip
+++++++++++++++++++++++

Ansible can be installed via "pip", the Python package manager.  If 'pip' isn't already available in
your version of Python, you can get pip by::

   $ sudo easy_install pip

Then install Ansible with [1]_::

   $ sudo pip install ansible

If you are installing on OS X Mavericks, you may encounter some noise from your compiler.  A workaround is to do the following::

   $ sudo CFLAGS=-Qunused-arguments CPPFLAGS=-Qunused-arguments pip install ansible

Readers that use virtualenv can also install Ansible under virtualenv, though we'd recommend to not worry about it and just install Ansible globally.  Do not use easy_install to install ansible directly.

.. _tagged_releases:

Tarballs of Tagged Releases
+++++++++++++++++++++++++++

Packaging Ansible or wanting to build a local package yourself, but don't want to do a git checkout?  Tarballs of releases are available on the `Ansible downloads <http://releases.ansible.com/ansible>`_ page.

These releases are also tagged in the `git repository <https://github.com/ansible/ansible/releases>`_ with the release version.

.. seealso::

   :doc:`intro_adhoc`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

.. [1] If you have issues with the "pycrypto" package install on Mac OSX, which is included as a dependency for paramiko, then you may need to try "CC=clang sudo -E pip install pycrypto".
