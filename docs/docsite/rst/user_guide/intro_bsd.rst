.. _working_with_bsd:

Ansible and BSD
===============

Managing BSD machines is different from managing other Unix-like machines. If you have managed nodes running BSD, review these topics.

.. contents::
   :local:

Connecting to BSD nodes
-----------------------

Ansible connects to managed nodes using OpenSSH by default. This works on BSD if you use SSH keys for authentication. However, if you use SSH passwords for authentication, Ansible relies on sshpass. Most
versions of sshpass do not deal well with BSD login prompts, so when using SSH passwords against BSD machines, use ``paramiko`` to connect instead of OpenSSH. You can do this in ansible.cfg globally or you can set it as an inventory/group/host variable. For example:

.. code-block:: text

    [freebsd]
    mybsdhost1 ansible_connection=paramiko

.. _bootstrap_bsd:

Bootstrapping BSD
-----------------

Ansible is agentless by default, however, it requires Python on managed nodes. Only the :ref:`raw <raw_module>` module will operate without Python. Although this module can be used to bootstrap Ansible and install Python on BSD variants (see below), it is very limited and the use of Python is required to make full use of Ansible's features.

The following example installs Python 2.7 which includes the json library required for full functionality of Ansible.
On your control machine you can execute the following for most versions of FreeBSD:

.. code-block:: bash

    ansible -m raw -a "pkg install -y python27" mybsdhost1

Or for OpenBSD:

.. code-block:: bash

    ansible -m raw -a "pkg_add python%3.7"

Once this is done you can now use other Ansible modules apart from the ``raw`` module.

.. note::
    This example demonstrated using pkg on FreeBSD and pkg_add on OpenBSD, however you should be able to substitute the appropriate package tool for your BSD; the package name may also differ. Refer to the package list or documentation of the BSD variant you are using for the exact Python package name you intend to install.

.. BSD_python_location:

Setting the Python interpreter
------------------------------

To support a variety of Unix-like operating systems and distributions, Ansible cannot always rely on the existing environment or ``env`` variables to locate the correct Python binary. By default, modules point at ``/usr/bin/python`` as this is the most common location. On BSD variants, this path may differ, so it is advised to inform Ansible of the binary's location, through the ``ansible_python_interpreter`` inventory variable. For example:

.. code-block:: text

    [freebsd:vars]
    ansible_python_interpreter=/usr/local/bin/python2.7
    [openbsd:vars]
    ansible_python_interpreter=/usr/local/bin/python3.7

If you use additional plugins beyond those bundled with Ansible, you can set similar variables for ``bash``, ``perl`` or ``ruby``, depending on how the plugin is written. For example:

.. code-block:: text

    [freebsd:vars]
    ansible_python_interpreter=/usr/local/bin/python
    ansible_perl_interpreter=/usr/bin/perl5


Which modules are available?
----------------------------

The majority of the core Ansible modules are written for a combination of Unix-like machines and other generic services, so most should function well on the BSDs with the obvious exception of those that are aimed at Linux-only technologies (such as LVG).

Using BSD as the control node
-----------------------------

Using BSD as the control machine is as simple as installing the Ansible package for your BSD variant or by following the ``pip`` or 'from source' instructions.

.. _bsd_facts:

BSD facts
---------

Ansible gathers facts from the BSDs in a similar manner to Linux machines, but since the data, names and structures can vary for network, disks and other devices, one should expect the output to be slightly different yet still familiar to a BSD administrator.

.. _bsd_contributions:

BSD efforts and contributions
-----------------------------

BSD support is important to us at Ansible. Even though the majority of our contributors use and target Linux we have an active BSD community and strive to be as BSD-friendly as possible.
Please feel free to report any issues or incompatibilities you discover with BSD; pull requests with an included fix are also welcome!

.. seealso::

   :ref:`intro_adhoc`
       Examples of basic commands
   :ref:`working_with_playbooks`
       Learning ansible's configuration management language
   :ref:`developing_modules`
       How to write modules
   `Mailing List <https://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
