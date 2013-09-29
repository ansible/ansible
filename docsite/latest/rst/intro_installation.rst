Installation
============

.. contents::
   :depth: 2

What Will Be Installed
``````````````````````

Ansible by default manages machines over the SSH protocol.

Once ansible is installed, it will not add a database, and there will be no daemons to start or keep running.  You only need to install it on one machine (which could easily be a laptop) and it can manage an entire fleet of remote machines from that central point.  When Ansible manages remote machines, it does not leave software installed or running on them, so there's no real question about how to upgrade Ansible when moving to a new version.

What Version To Pick?
`````````````````````

Because it runs so easily from source and does not require any installation of software on remote
machines, many users will actually track the development version.  

If you are wishing to run the latest released version of Ansible and you are running Red Hat Enterprise Linux (TM), CentOS, Fedora, Debian, or Ubuntu, we recommend using our OS package manager.

For other installation options, we recommend installing via "pip", which is the Python package manager, though other options are also available.

If you wish to track the development release to use and test the latest features, we will share
information about running from source.  It's not neccessary to install the program to run from source.

Control Machine Requirements
````````````````````````````

Currently Ansible can be from any machine with Python 2.6 installed (Windows isn't supported for the control machine).

This includes Red Hat, Debian, CentOS, OS X, any of the BSDs, and so on.
  

Remote Node Requirements
````````````````````````

On the managed nodes, you only need Python 2.4 or later, but if you are are running less than Python 2.6 on them, you will also need:

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

   Python 3 is a slightly different language than Python 2 and most python programs (including
   Ansible) are not switching over yet.  However, some Linux distributions (Gentoo, Arch) may not have a 
   Python 2.X interpreter installed by default.  On those systems, you should install one, and set
   the 'ansible_python_interpreter' variable in inventory (see :doc:`patterns`) to point at your 2.X python.  Distributions
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

Ansible's release cycles are usually about two months long.  Due to this
short release cycle, minor bugs will generally be fixed in the next release versus maintaining 
backports on the stable branch.

You may also wish to follow the `Github project <https://github.com/ansible/ansible>`_ if
you have a github account.  This is also where we keep the issue tracker for sharing
bugs and feature ideas.

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

Ansible also uses the the following Python modules that need to be installed::

    $ sudo pip install paramiko PyYAML jinja2

Once running the env-setup script you'll be running from checkout and the default inventory file
will be /etc/ansible/hosts.  You can optionally specify an inventory file (see :doc:`patterns`) 
other than /etc/ansible/hosts:

.. code-block:: bash

    $ echo "127.0.0.1" > ~/ansible_hosts
    $ export ANSIBLE_HOSTS=~/ansible_hosts

You can read more about the inventory file in later parts of the manual.

Now let's test things with a ping command:

.. code-block:: bash

    $ ansible all -m ping --ask-pass

You can also use "sudo make install" if you wish.

Latest Release Via Yum
++++++++++++++++++++++

RPMs are available from yum for `EPEL
<http://fedoraproject.org/wiki/EPEL>`_ 6 and currently supported
Fedora distributions. 

Ansible itself can manage earlier operating
systems that contain python 2.4 or higher (so also EL5).

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

Latest Releases Via Apt (Ubuntu)
++++++++++++++++++++++++++++++++

Ubuntu builds are available `in a PPA here <https://launchpad.net/~rquillo/+archive/ansible>`_.

Once configured, 

.. code-block:: bash

    $ sudo add-apt-repository ppa:rquillo/ansible
    $ sudo apt-get update
    $ sudo apt-get install ansible

Debian/Ubuntu packages can also be built from the source checkout, run:

.. code-block:: bash

    $ make debian

You may also wish to run from source to get the latest, which is covered above.

Latest Releases Via Pip
+++++++++++++++++++++++

Ansible can be installed via "pip", the Python package manager.  If 'pip' isn't already available in
your version of Python, you can get pip by::

   $ sudo easy_install pip

Then install Ansible with::

   $ sudo pip install ansible

Readers that use virtualenv can also install Ansible under virtualenv, though we'd recommend to not worry about it and just install Ansible globally.  Do not use easy_install to install ansible directly.

Tarballs of Tagged Releases
+++++++++++++++++++++++++++

Packaging Ansible or wanting to build a local package yourself, but don't want to do a git checkout?  Tarballs of releases are available on the ansibleworks.com page.

* `Ansible/downloads <http://ansibleworks.com/releases>`_

These releases are also tagged in the git repository with the release version.

Choosing Between Paramiko and Native SSH
````````````````````````````````````````

By default, ansible 1.3 and later will try to use native SSH for remote communication when possible.
This is done when ControlPersist support is available.  Paramiko is however reasonably fast and makes
a good default on versions of Enterprise Linux where ControlPersist is not available.  However, Paramiko 
does not support some advanced SSH features that folks will want to use.  In Ansible 1.2 and before,
the default was strictly paramiko and native SSH had to be explicitly selected with -c ssh or set in the
configuration file.

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

(The sudo implementation is changeable in ansible's configuration file if you happen to want to use a sudo
replacement.  Flags passed dot sudo can also be set.)

Now run a live command on all of your nodes:
  
.. code-block:: bash

   $ ansible all -a "/bin/echo hello"

Congratulations.  You've just contacted your nodes with Ansible.  It's
soon going to be time to read some of the more real-world :doc:`examples`, and explore
what you can do with different modules, as well as the Ansible
:doc:`playbooks` language.  Ansible is not just about running commands, it
also has powerful configuration management and deployment features.  There's more to
explore, but you already have a fully working infrastructure!

A note about Connection (Transport) Modes
`````````````````````````````````````````

Ansible has two major forms of SSH transport implemented, 'ssh' (OpenSSH) and 'paramiko'.  Paramiko is a python
SSH implementation and 'ssh' simply calls OpenSSH behind the scenes.  There are additionally 'fireball' (an accelerated
remote transport), 'local', and 'chroot' connection modes in Ansible that don't use SSH, but connecting by one of the two 
SSH transports is the most common way to manage systems.  It is useful to understand the difference between the 'ssh' 
and 'paramiko' modes.

Paramiko is provided because older Enterprise Linux operating systems do not have an efficient OpenSSH that support
ControlPersist technology, and in those cases, 'paramiko' is faster than 'ssh'.  Thus, until EL6 backports a newer
SSH, 'paramiko' is the faster option on that platform. 

However, if you have a newer 'ssh' that supports ControlPersist, usage of the 'ssh' transport unlocks additional
configurability, including the option to use Kerberos.  For instance, the latest Fedora and Ubuntu releases
all offer a sufficiently new OpenSSH.  With ControlPersist available, 'ssh' is usually about as fast as paramiko.
If you'd like even more speed, read about 'fireball' in the Advanced Playbooks section.

Starting with Ansible 1.2.1, the default transport mode for Ansible is 'smart', which means it will detect
if OpenSSH supports ControlPersist, and will select 'ssh' if available, and otherwise pick 'paramiko'.
Previous versions of Ansible defaulted to 'paramiko'.

A note about Host Key Checking
``````````````````````````````

Ansible 1.2.1 and later have host key checking enabled by default.  

If a host is reinstalled and has a different key in 'known_hosts', this will result in a error message until
corrected.  If a host is not initially in 'known_hosts' this will result in prompting for confirmation of the key,
which results in a interactive experience if using Ansible, from say, cron.

If you wish to disable this behavior and understand the implications, you can do so by editing /etc/ansible/ansible.cfg or ~/.ansible.cfg::

    [defaults]
    host_key_checking = False

Alternatively this can be set by an environment variable:

    $ export ANSIBLE_HOST_KEY_CHECKING=False

Also note that host key checking in paramiko mode is reasonably slow, therefore switching to 'ssh' is also recommended when using this
feature.

.. seealso::

   :doc:`examples`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

