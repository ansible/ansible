BSD support
===========

.. contents:: Topics

.. _working_with_bsd:

Working with BSD
````````````````

As you may have already read, Ansible manages Linux/Unix machines using SSH by default. Ansible handles BSD machines in the same manner.

Depending on your control machine, Ansible will try to default to using OpenSSH. This works fine when using SSH keys to authenticate, but when using SSH passwords, Ansible relies on sshpass. Most
versions of sshpass do not deal well with BSD login prompts, so in these cases we recommend changing the transport to paramiko. You can do this in ansible.cfg globaly or set it as
an inventory/group/host variable::

    [freebsd]
    mybsdhost1 ansible_connection=paramiko

Ansible is agentless by default, but it needs some software installed on the target machines, mainly Python 2.4 or higher with an included json library (which is standard in Python 2.5 and above).
Without python you can still use the ``raw`` module to execute commands. This module is very limited, however it can be used to bootstrap Ansible on BSDs.



.. _bootstrap_bsd:

Bootstrapping BSD
`````````````````

For Ansible to effectively manage your machine, we need to install Python along with a json library, in this case we are using Python 2.7 which already has json included.
On your control machine you can simply execute the following for most versions of FreeBSD::

    ansible -m raw -a “pkg_add -r python27” mybsdhost1

Once this is done you can now use other Ansible modules aside from the ``raw`` module.

.. note::
    This example uses pkg_add, you should be able to substitute for the appropriate tool for your BSD,
    also you might need to look up the exact package name you need.


.. _python_location:

Setting python interpreter
``````````````````````````

To support the multitude of Unix/Linux OSs and distributions, Ansible cannot rely on the environment or ``env`` to find the correct Python. By default, modules point at ``/usr/bin/python`` as this is the most common location. On the BSDs you cannot rely on this so you should tell ansible where python is located, through the ``ansible_python_interpreter`` inventory variable::

    [freebsd:vars]
    ansible_python_interpreter=/usr/local/bin/python2.7

If you use plugins other than those included with Ansible you might need to set similar variables for ``bash``, ``perl`` or ``ruby``, depending on how the plugin was written::

    [freebsd:vars]
    ansible_python_interpreter=/usr/local/bin/python
    ansible_perl_interpreter=/usr/bin/perl5


What modules are available
``````````````````````````

Most of the core Ansible modules are written for a combination of Linux/Unix machines and arbitrary web services; most should work fine on the BSDs with the exception of those that are aimed at Linux specific technologies (i.e. lvg).


You can also use a BSD as the control machine
`````````````````````````````````````````````

It should be as simple as installing the Ansible package or follow the ``pip`` or 'from source' instructions.

.. _bsd_facts:

BSD Facts
`````````

Ansible gathers facts from the BSDs as it would from Linux machines, but since the data, names and structures can be different for network, disks and other devices, one should expect the output to be different, but still familiar to a BSD administrator.


.. _bsd_contributions:

BSD Contributions
`````````````````

BSD support is important for Ansible. Even though the majority of our contributors use and target Linux we have an active BSD community and will strive to be as BSD friendly as possible.
Report any issues you see with BSD incompatibilities, even better to submit a pull request with the fix!

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

