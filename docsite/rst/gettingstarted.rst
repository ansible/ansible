Getting Started
===============

.. image:: http://ansible.cc/docs/_static/ansible_fest_2013.png
   :alt: ansiblefest 2013
   :target: http://ansibleworks.com/fest


.. contents::
   :depth: 2
   :backlinks: top

Requirements
````````````

Requirements for Ansible are extremely minimal.

Ansible is written for Python 2.6+.  If you are running Python 2.5 on an "Enterprise Linux" variant, we'll show you how to add
2.6.  Newer versions of Linux and OS X should already have 2.6 or higher.

In additon to Python 2.6+, you will want the following Python modules (installed via pip or perhaps via your OS package manager via slightly different names):

* ``paramiko``
* ``PyYAML``
* ``jinja2``

If you are using RHEL or CentOS 5 , python is version 2.4 by default, but you can get python 2.6 installed easily. `Use EPEL <http://fedoraproject.org/wiki/EPEL>`_ and install these dependencies as follows:

.. code-block:: bash

   $ yum install python26 python26-PyYAML python26-paramiko python26-jinja2


On the managed nodes, you only need Python 2.4 or later, but if you are are running less than Python 2.6 on them, you will
also need:

* ``python-simplejson`` 

.. note::

   Ansible's "raw" module (for executing commands in a quick and dirty
   way) and the script module don't even need that.  So technically, you can use
   Ansible to install python-simplejson using the raw module, which
   then allows you to use everything else.  (That's jumping ahead
   though.)

.. note::

   Python 3 is a slightly different language than Python 2 and most python programs (including
   Ansible) are not
   switching over yet.  However, some Linux distributions (Gentoo, Arch) may not have a 
   Python 2.X interpreter installed by default.  On those systems, you should install one, and set
   the 'ansible_python_interpreter' variable in inventory to point at your 2.X python.  Distributions
   like Red Hat Enterprise Linux, CentOS, Fedora, and Ubuntu all have a 2.X interpreter installed
   by default and this does not apply to those distributions.  This is also true of nearly all
   Unix systems.  If you need to bootstrap these remote systems by installing Python 2.X, 
   using the 'raw' module will be able to do it remotely.

Getting Ansible
```````````````

If you are interested in using all the latest features, you may wish to keep up to date
with the development branch of the git checkout.  This also makes it easiest to contribute
back to the project.  

Instructions for installing from source are below.

Ansible's release cycles are about one month long.  Due to this
short release cycle, any bugs will generally be fixed in the next release versus maintaining 
backports on the stable branch.

You may also wish to follow the `Github project <https://github.com/ansible/ansible>`_ if
you have a github account.  This is also where we keep the issue tracker for sharing
bugs and feature ideas.


Running From Checkout
+++++++++++++++++++++

Ansible is trivially easy to run from a checkout, root permissions are not required
to use it:

.. code-block:: bash

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible
    $ source ./hacking/env-setup

You can optionally specify an inventory file (see :doc:`patterns`) other than /etc/ansible/hosts:

.. code-block:: bash

    $ echo "127.0.0.1" > ~/ansible_hosts
    $ export ANSIBLE_HOSTS=~/ansible_hosts

You can read more about the inventory file in later parts of the manual.

Now let's test things:

.. code-block:: bash

    $ ansible all -m ping --ask-pass


Make Install
++++++++++++

If you are not working from a distribution where Ansible is packaged yet, you can install Ansible 
using "make install".  This is done through `python-distutils`:

.. code-block:: bash

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible
    $ sudo make install

Via Pip
+++++++

Are you a python developer?

Ansible can be installed via Pip, but when you do so, it will ask to install other dependencies used for
optional modes::

   $ sudo easy_install pip
   $ sudo pip install ansible

Readers that use virtualenv can also install Ansible under virtualenv.  Do not use easy_install to install
ansible directly.

Via RPM
+++++++

RPMs for the last Ansible release are available for `EPEL
<http://fedoraproject.org/wiki/EPEL>`_ 6 and currently supported
Fedora distributions.  Ansible itself can manage earlier operating
systems that contain python 2.4 or higher.

If you are using RHEL or CentOS and have not already done so, `configure EPEL <http://fedoraproject.org/wiki/EPEL>`_
   
.. code-block:: bash

    # install the epel-release RPM if needed on CentOS, RHEL, or Scientific Linux
    $ sudo yum install ansible

You can also use the ``make rpm`` command to build an RPM you can distribute and install. 
Make sure you have ``rpm-build``, ``make``, and ``python2-devel`` installed.

.. code-block:: bash

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible
    $ make rpm
    $ sudo rpm -Uvh ~/rpmbuild/ansible-*.noarch.rpm

Python 2.6 EPEL instructions for RHEL and CentOS 5
``````````````````````````````````````````````````

These distributions don't have Python 2.6 by default, but it is easily
installable. 


.. code-block:: bash



Via MacPorts
++++++++++++

An OSX port is available via MacPorts, to install the stable version of
Ansible from MacPorts (this is the recommended way), run:

.. code-block:: bash

    $ sudo port install ansible

If you wish to install the latest build via the MacPorts system from a
git checkout, run:

.. code-block:: bash

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible/packaging/macports
    $ sudo port install

Please refer to the documentation at <http://www.macports.org> for
further information on using Portfiles with MacPorts.


Ubuntu and Debian
+++++++++++++++++

Ubuntu builds are available `in a PPA here <https://launchpad.net/~rquillo/+archive/ansible>`_

Debian/Ubuntu package recipes can also be built from the source checkout, run:

.. code-block:: bash

    $ make debian

Gentoo, Arch, Others
++++++++++++++++++++

Gentoo eBuilds are in portage, version 1.0 `coming soon <https://bugs.gentoo.org/show_bug.cgi?id=461830>`_.

.. code-block:: bash

    $ emerge ansible


An Arch PKGBUILD is available on `AUR <https://aur.archlinux.org/packages.php?ID=58621>`_
If you have python3 installed on Arch, you probably want to symlink python to python2:

.. code-block:: bash

    $ sudo ln -sf /usr/bin/python2 /usr/bin/python

You should also set a 'ansible_python_interpreter' inventory variable for hosts that have python 
pointing to python3, so the right python can be found on the managed nodes.

Tagged Releases
+++++++++++++++

Tarballs of releases are available on the ansible.cc page.

* `Ansible/downloads <https://ansible.cc/releases>`_

These releases are also tagged in the git repository with the release version.

Choosing Between Paramiko and Native SSH
````````````````````````````````````````

By default, ansible uses paramiko to talk to managed nodes over SSH.  Paramiko is fast, works
very transparently, requires no configuration, and is a good choice for most users.
However, it does not support some advanced SSH features that folks will want to use.

.. versionadded:: 0.5

If you want to leverage more advanced SSH features (such as Kerberized
SSH or jump hosts), pass the flag "--connection=ssh" to any ansible
command, or set the ANSIBLE_TRANSPORT environment variable to
'ssh'. This will cause Ansible to use openssh tools instead.

If ANSIBLE_SSH_ARGS are not set, ansible will try to use some sensible ControlMaster options
by default.  You are free to override this environment variable, but should still pass ControlMaster
options to ensure performance of this transport.  With ControlMaster in use, both transports
are roughly the same speed.  Without CM, the binary ssh transport is signficantly slower.

If none of this makes sense to you, the default paramiko option is probably fine.


Your first commands
```````````````````

Now that you've installed Ansible, it's time to test it.

Edit (or create) /etc/ansible/hosts and put one or more remote systems in it, for
which you have your SSH key in ``authorized_keys``::

    192.168.1.50
    aserver.example.org
    bserver.example.org

Set up SSH agent to avoid retyping passwords:

.. code-block:: bash

    $ ssh-agent bash
    $ ssh-add ~/.ssh/id_rsa

(Depending on your setup, you may wish to ansible's --private-key option to specify a pem file instead)

Now ping all your nodes:

.. code-block:: bash

   $ ansible all -m ping

Ansible will attempt to remote connect to the machines using your current
user name, just like SSH would.  To override the remote user name, just use the '-u' parameter.

If you would like to access sudo mode, there are also flags to do that:

.. code-block:: bash

    # as bruce
    $ ansible all -m ping -u bruce
    # as bruce, sudoing to root
    $ ansible all -m ping -u bruce --sudo 
    # as bruce, sudoing to batman
    $ ansible all -m ping -u bruce --sudo --sudo-user batman

(The sudo implementation is changeable in ansbile's configuration file if you happen to want to use a sudo
replacement.  Flags passed dot sudo can also be set.)

Now run a live command on all of your nodes:
  
.. code-block:: bash

   $ ansible all -a "/bin/echo hello"

Congratulations.  You've just contacted your nodes with Ansible.  It's
now time to read some of the more real-world :doc:`examples`, and explore
what you can do with different modules, as well as the Ansible
:doc:`playbooks` language.  Ansible is not just about running commands, it
also has powerful configuration management and deployment features.  There's more to
explore, but you already have a fully working infrastructure!


.. seealso::

   :doc:`examples`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

