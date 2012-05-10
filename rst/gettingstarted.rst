Downloads & Getting Started
===========================

Requirements
````````````

Requirements for Ansible are extremely minimal.

Ansible is written for Python 2.6.  If you are running Python 2.5 on an "Enterprise Linux" variant,
your distribution can easily install 2.6 (see instructions in the next section).  Newer versions
of Linux and OS X should already have 2.6.

In additon to Python 2.6, you will want the following packages:

* ``paramiko``
* ``PyYAML``
* ``python-jinja2``

On the managed nodes, you only need Python 2.4 or later, but if you are are running less than Python 2.6 on them, you will
also need:

* ``python-simplejson`` 

NOTE: Ansible 0.4 will have ways to remote bootstrap this, using Ansible itself.  Stay tuned.

Python 2.6 EPEL instructions for RHEL and CentOS 5
``````````````````````````````````````````````````

These distributions don't have Python 2.6 by default, but it is easily installable.

* If you have not already done so, `configure EPEL <http://fedoraproject.org/wiki/EPEL>`_
* yum install python26 python26-PyYAML python26-paramiko python26-jinja2

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
to use it::

    $ git clone git://github.com/ansible/ansible.git
    $ git checkout -t origin/devel
    $ cd ./ansible
    $ source ./hacking/env-setup

You can optionally specify an inventory file (see doc:`patterns`) other than /etc/ansible/hosts::

    $ echo "127.0.0.1" > ~/ansible_hosts
    $ export ANSIBLE_HOSTS=~/ansible_hosts

Now let's test things::

    $ ansible all -m ping --ask-pass


Make Install
++++++++++++

If you are not working from a distribution where Ansible is packaged yet, you can install Ansible 
using "make install".  This is done through `python-distutils`::

    $ git clone git://github.com/ansible/ansible.git
    $ git checkout -t origin/devel
    $ cd ./ansible
    $ sudo make install


Via RPM
+++++++

RPMs for the last Ansible release are available for `EPEL <http://fedoraproject.org/wiki/EPEL>`_ 6 and currently supported
Fedora distributions.

    # install the epel-release RPM if needed on CentOS, RHEL, or Scientific Linux
    $ sudo yum install ansible

You can also use the ``make rpm`` command to
build an RPM you can distribute and install::

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible
    $ make rpm
    $ sudo rpm -Uvh ~/rpmbuild/RPMS/noarch/ansible-*.noarch.rpm

Note that if you are tracking the upstream source (i.e. git), the RPM revision will not be 
bumped with every source code change.  To get around this, you can use
``rpm -Uvh`` with ``--force`` when RPM tells you the package is still at the
same version.  This is perfectly safe to do.

Debian, Gentoo, Arch, Others
++++++++++++++++++++++++++++

Gentoo eBuilds are available `here <https://github.com/uu/ubuilds>`_

Debian package recipes can be built from the source checkout, run::

    make debian

An Arch PKGBUILD is available on `AUR <https://aur.archlinux.org/packages.php?ID=58621>`_
If you have python3 installed on Arch, you probably want to symlink python to python2.::

    sudo ln -sf /usr/bin/python2 /usr/bin/python

If you would like to package Ansible for Homebrew, BSD, or others,
please stop by the mailing list and say hi!


Tagged Releases
+++++++++++++++

Tagged releases are available as tar.gz files from the Ansible github
project page:

* `Ansible/downloads <https://github.com/ansible/ansible/downloads>`_


Your first commands
```````````````````

Now that you've installed Ansible, it's time to test it.

Edit (or create) /etc/ansible/hosts and put one or more remote systems in it, for
which you have your SSH key in ``authorized_keys``::

    192.168.1.50
    aserver.example.org
    bserver.example.org

Set up SSH agent to avoid retyping passwords::

    ssh-agent bash
    ssh-add ~/.ssh/id_rsa

Now ping all your nodes::

    ansible all -m ping

Now run a live command on all of your nodes::
  
    ansible all -a "/bin/echo hello"

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

