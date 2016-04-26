BSD Support
===========

.. contents:: Topics

.. _working_with_bsd:

Working with BSD
````````````````

Ansible manages Linux/Unix machines using SSH by default. BSD machines are no exception, however this document covers some of the differences you may encounter with Ansible when working with BSD variants.

Typically, Ansible will try to default to using OpenSSH as a connection method. This is suitable when when using SSH keys to authenticate, but when using SSH passwords, Ansible relies on sshpass. Most
versions of sshpass do not deal particularly well with BSD login prompts, so when using SSH passwords against BSD machines, it is recommended to change the transport method to paramiko. You can do this in ansible.cfg globally or you can set it as an inventory/group/host variable. For example::

    [freebsd]
    mybsdhost1 ansible_connection=paramiko

Ansible is agentless by default, however certain software is required on the target machines. Using Python 2.4 on the agents requires an additional py-simplejson package/library to be installed, however this library is already included in Python 2.5 and above.
Operating without Python is possible with the ``raw`` module. Although this module can be used to bootstrap Ansible and install Python on BSD variants (see below), it is very limited and the use of Python is required to make full use of Ansible's features.

.. _bootstrap_bsd:

Bootstrapping BSD
`````````````````

As mentioned above, you can bootstrap Ansible with the ``raw`` module and remotely install Python on targets. The following example installs Python 2.7 which includes the json library required for full functionality of Ansible.
On your control machine you can simply execute the following for most versions of FreeBSD::

    ansible -m raw -a “pkg install -y python27” mybsdhost1

Once this is done you can now use other Ansible modules apart from the ``raw`` module.

.. note::
    This example used pkg_add as used on FreeBSD, however you should be able to substitute the appropriate package tool for your BSD; the package name may also differ. Refer to the package list or documentation of the BSD variant you are using for the exact Python package name you intend to install.

.. _python_location:

Setting the Python interpreter
``````````````````````````````

To support a variety of Unix/Linux operating systems and distributions, Ansible cannot always rely on the existing environment or ``env`` variables to locate the correct Python binary. By default, modules point at ``/usr/bin/python`` as this is the most common location. On BSD variants, this path may differ, so it is advised to inform Ansible of the binary's location, through the ``ansible_python_interpreter`` inventory variable. For example::

    [freebsd:vars]
    ansible_python_interpreter=/usr/local/bin/python2.7

If you use additional plugins beyond those bundled with Ansible, you can set similar variables for ``bash``, ``perl`` or ``ruby``, depending on how the plugin is written. For example::

    [freebsd:vars]
    ansible_python_interpreter=/usr/local/bin/python
    ansible_perl_interpreter=/usr/bin/perl5


Which modules are available?
````````````````````````````

The majority of the core Ansible modules are written for a combination of Linux/Unix machines and other generic services, so most should function well on the BSDs with the obvious exception of those that are aimed at Linux-only technologies (such as LVG).

Using BSD as the control machine
````````````````````````````````

Using BSD as the control machine is as simple as installing the Ansible package for your BSD variant or by following the ``pip`` or 'from source' instructions.

.. _bsd_facts:

BSD Facts
`````````

Ansible gathers facts from the BSDs in a similar manner to Linux machines, but since the data, names and structures can vary for network, disks and other devices, one should expect the output to be slightly different yet still familiar to a BSD administrator.

.. _bsd_contributions:

BSD Efforts and Contributions
`````````````````````````````

BSD support is important to us at Ansible. Even though the majority of our contributors use and target Linux we have an active BSD community and strive to be as BSD friendly as possible.
Please feel free to report any issues or incompatibilities you discover with BSD; pull requests with an included fix are also welcome!

.. seealso::

   :doc:`intro_adhoc`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   :doc:`developing_modules`
       How to write modules
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

