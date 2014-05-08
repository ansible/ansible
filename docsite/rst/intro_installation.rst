Installation
============

.. contents:: Topics

.. _getting_ansible:

Getting Ansible
```````````````

You may also wish to follow the `Github project <https://github.com/ansible/ansible>`_ if
you have a github account.  This is also where we keep the issue tracker for sharing
bugs and feature ideas.

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

Ansible's release cycles are usually about two months long.  Due to this
short release cycle, minor bugs will generally be fixed in the next release versus maintaining 
backports on the stable branch.  Major bugs will still have maintenance releases when needed, though
these are infrequent.

If you are wishing to run the latest released version of Ansible and you are running Red Hat Enterprise Linux (TM), CentOS, Fedora, Debian, or Ubuntu, we recommend using the OS package manager.

For other installation options, we recommend installing via "pip", which is the Python package manager, though other options are also available.

If you wish to track the development release to use and test the latest features, we will share
information about running from source.  It's not necessary to install the program to run from source.

.. _control_machine_requirements:

Control Machine Requirements
````````````````````````````

Currently Ansible can be run from any machine with Python 2.6 installed (Windows isn't supported for the control machine).

This includes Red Hat, Debian, CentOS, OS X, any of the BSDs, and so on.
  
.. _managed_node_requirements:

Managed Node Requirements
`````````````````````````

On the managed nodes, you only need Python 2.4 or later, but if you are running less than Python 2.5 on the remotes, you will also need:

* ``python-simplejson`` 

.. note::

   Ansible's "raw" module (for executing commands in a quick and dirty
   way) and the script module don't even need that.  So technically, you can use
   Ansible to install python-simplejson using the raw module, which
   then allows you to use everything else.  (That's jumping ahead
   though.)

.. note::

   If you have SELinux enabled on remote nodes, you will also want to install
   libselinux-python on them before using any copy/file/template related functions in
   Ansible. You can of course still use the yum module in Ansible to install this package on
   remote systems that do not have it.

.. note::

   Python 3 is a slightly different language than Python 2 and most Python programs (including
   Ansible) are not switching over yet.  However, some Linux distributions (Gentoo, Arch) may not have a 
   Python 2.X interpreter installed by default.  On those systems, you should install one, and set
   the 'ansible_python_interpreter' variable in inventory (see :doc:`intro_inventory`) to point at your 2.X Python.  Distributions
   like Red Hat Enterprise Linux, CentOS, Fedora, and Ubuntu all have a 2.X interpreter installed
   by default and this does not apply to those distributions.  This is also true of nearly all
   Unix systems.  If you need to bootstrap these remote systems by installing Python 2.X, 
   using the 'raw' module will be able to do it remotely.

.. _installing_the_control_machine:

Installing the Control Machine
``````````````````````````````

.. _from_source:

Running From Source
+++++++++++++++++++

Ansible is trivially easy to run from a checkout, root permissions are not required
to use it and there is no software to actually install for Ansible itself.  No daemons
or database setup are required.  Because of this, many users in our community use the
development version of Ansible all of the time, so they can take advantage of new features
when they are implemented, and also easily contribute to the project. Because there is
nothing to install, following the development version is significantly easier than most
open source projects.

To install from source.

.. code-block:: bash

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible
    $ source ./hacking/env-setup

If you don't have pip installed in your version of Python, install pip::

    $ sudo easy_install pip

Ansible also uses the following Python modules that need to be installed::

    $ sudo pip install paramiko PyYAML jinja2 httplib2

Once running the env-setup script you'll be running from checkout and the default inventory file
will be /etc/ansible/hosts.  You can optionally specify an inventory file (see :doc:`intro_inventory`) 
other than /etc/ansible/hosts:

.. code-block:: bash

    $ echo "127.0.0.1" > ~/ansible_hosts
    $ export ANSIBLE_HOSTS=~/ansible_hosts

You can read more about the inventory file in later parts of the manual.

Now let's test things with a ping command:

.. code-block:: bash

    $ ansible all -m ping --ask-pass

You can also use "sudo make install" if you wish.

.. _from_yum:

Latest Release Via Yum
++++++++++++++++++++++

RPMs are available from yum for `EPEL
<http://fedoraproject.org/wiki/EPEL>`_ 6 and currently supported
Fedora distributions. 

Ansible itself can manage earlier operating
systems that contain Python 2.4 or higher (so also EL5).

Fedora users can install Ansible directly, though if you are using RHEL or CentOS and have not already done so, `configure EPEL <http://fedoraproject.org/wiki/EPEL>`_
   
.. code-block:: bash

    # install the epel-release RPM if needed on CentOS, RHEL, or Scientific Linux
    $ sudo yum install ansible

You can also build an RPM yourself.  From the root of a checkout or tarball, use the ``make rpm`` command to build an RPM you can distribute and install. Make sure you have ``rpm-build``, ``make``, and ``python2-devel`` installed.

.. code-block:: bash

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible
    $ make rpm
    $ sudo rpm -Uvh ~/rpmbuild/ansible-*.noarch.rpm

.. _from_apt:

Latest Releases Via Apt (Ubuntu)
++++++++++++++++++++++++++++++++

Ubuntu builds are available `in a PPA here <https://launchpad.net/~rquillo/+archive/ansible>`_.

Once configured, 

.. code-block:: bash

    $ sudo apt-add-repository ppa:rquillo/ansible
    $ sudo apt-get update
    $ sudo apt-get install ansible

Debian/Ubuntu packages can also be built from the source checkout, run:

.. code-block:: bash

    $ make deb

You may also wish to run from source to get the latest, which is covered above.

.. _from_pkg:

Latest Releases Via pkg (FreeBSD)
+++++++++++++++++++++++++++++++++

.. code-block:: bash

    $ sudo pkg install ansible

You may also wish to install from ports, run:

.. code-block:: bash

    $ sudo make -C /usr/ports/sysutils/ansible install

.. _from_brew:

Latest Releases Via Homebrew (Mac OSX)
++++++++++++++++++++++++++++++++++++++

To install on a Mac, make sure you have Homebrew, then run:

.. code-block:: bash

    $ brew update
    $ brew install ansible

.. _from_pip:

Latest Releases Via Pip
+++++++++++++++++++++++

Ansible can be installed via "pip", the Python package manager.  If 'pip' isn't already available in
your version of Python, you can get pip by::

   $ sudo easy_install pip

Then install Ansible with::

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

