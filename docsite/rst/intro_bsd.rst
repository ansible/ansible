BSD support
===========

.. contents:: Topics

.. _working_with_bsd:

Working with BSD
````````````````

As you may have already read, Ansible manages Linux/Unix machines using SSH by default. You access BSD machines the same way.

Depending on your control machine ansible will try to default to using OpenSSH, this works fine in the case of ssh keys but when using ssh passwords it relies on sshpass, most
versions of sshpass do not deal well with BSD login prompts, in these cases we recommend changing the transport to paramiko. You can do this in ansible.cfg globaly or set it as
an inventory/group/host var::

    [freebsd]
    mybsdhost1 ansible_connection=paramiko

Ansible is agentless by default, but it needs some software installed on the target machines, mainly python 2.4 or higher with an included json library (standard in 2.5 and above).
Without python you can still use the ``raw`` module to execute commands but this is very limited, still it can be used to bootstrap ansible on BSDs.



.. _bootstrap_bsd:

Bootstrapping BSD
`````````````````

For ansible to effectively manage your machine, we need to install python + a json library, in this case we are using python 2.7 which already has json included.
From your control machine you can just execute the following on most versions of FreeBSD::

    ansible -m raw -a “pkg_add -r python27” mybsdhost1

Once this is done you can now use other ansible modules aside from ``raw``.

.. note::
    This example uses pkg_add, you should be able to subsitute for the appropriate tool for your BSD,
    also you might need to lookup the exact package name you need.


.. _python_location:

Setting python interpreter
``````````````````````````

To support the multitude of Unix/Linux OSs and distributions ansible cannot rely on the environment or ``env`` to find the correct python, by default modules point at ``/usr/bin/python`` as this is the most common location. On the BSDs you cannot rely on this so you should tell ansible where python is located, through the ``ansible_python_interpreter`` invenotry variable::

    [freebsd:vars]
    ansible_python_interpreter=/usr/local/bin/python2.7

If you use plugins other than those included with ansible you might need to set the same for ``bash``, ``perl`` or ``ruby``, depending on how the plugin was written::

    [freebsd:vars]
    ansible_python_interpreter=/usr/local/bin/python
    ansible_perl_interpreter=/usr/bin/perl5


What modules are available
``````````````````````````

Most of the Ansible modules in core Ansible are written for a combination of Linux/Unix machines and arbitrary web services, most should work fine on the BSDs with the exception of those that are for linux specific technologies (i.e. lvg).


You can also use a BSD as the control machine
`````````````````````````````````````````````

It should be as simple as installing the Ansible package or follow the ``pip`` or 'from source' instructions.

.. _bsd_facts:

BSD Facts
`````````

Ansible gathers facts from the BSDs as it would from Linux machines, but since the data, names and structures can be different for network, disks and other devices expect the output to be different, but familiar to a BSD admin.


.. _bsd_contributions:

BSD Contributions
`````````````````

BSD support is important for Ansible, though the majority of our contributors use and target Linux we have a active BSD community and will strive to be as BSD friendly as possible.
Report any issues you see with BSD incompatibilities, even better if you can submit a pull request with the fix!

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

