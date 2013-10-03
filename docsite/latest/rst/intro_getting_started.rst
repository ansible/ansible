Getting Started
===============

.. contents::
   :depth: 2

About
`````

Now that you've read :doc:`intro_installation` and installed Ansible, it's time to dig in and get
started with some commands.  

What we are showing first are not the powerful configuration/deployment/orchestration of Ansible, called playbooks.
Playbooks are covered in a seperate section.

This is basically about how to get going initially.  Once you have this down, read :doc:`intro_adhoc` for some more
detail, and then you'll be ready to dive into playbooks.

Remote Connection Information
`````````````````````````````

Before we get started, it's important to understand how Ansible is communicating with remote
machines over SSH. 

By default, ansible 1.3 and later will try to use native 
OpenSSH for remote communication  when possible.  This enables both ControlPersist (a performance feature), Kerbos, and options in ~/.ssh/config such as Jump Host setup.  When using Enterprise Linux 6 operating systems as the control machine (Red Hat Enterprise Linux and derivatives such as CentOS), however, the version of OpenSSH may be too old to support Control Persist. On these operating systems, Ansible will fallback into using a high-quality python implementation of
OpenSSH called 'paramiko'.  If you wish to use features like Kerberized SSH and more, consider using Fedora, OS X, or Ubuntu as your control machine until a newer version of OpenSSH is available for your platform.

In Ansible 1.2 and before, the default was strictly paramiko and native SSH had to be explicitly selected with -c ssh or set in the configuration file.

If talking with some remote devices that don't support SFTP, you can switch to SCP mode in :doc:`intro_configuration`.

When speaking with remote machines, Ansible will by default assume you are using SSH keys.  To enable password auth, supply the option --ask-pass where needed.  If using sudo features and when sudo requires a password, also supply --ask-sudo-pass as appropriate.

Ansible also contains a feature called :doc:`playbooks_acceleration` which uses SSH for initial key exchange
and then communicates over a high speed encrypted connection.  

While it may be common sense, it is worth sharing: Any management system benefits from being run near your machines you are being managed. If running in a cloud, onsider running Ansible from a machine inside that cloud.

As an advanced topic, ansible doesn't just have to connect remotely over SSH.  The transports are pluggable, and there are options for managing things locally, as well as managing chroot, lxc, and jail containers.  A mode called 'ansible-pull' can also invert the system and have systems 'phone home' via scheduled git checkouts to pull configuration directives from a central repository.

Your first commands
```````````````````

Now that you've installed Ansible, it's time to get started with some basic tests.

Edit (or create) /etc/ansible/hosts and put one or more remote systems in it, for
which you have your SSH key in ``authorized_keys``::

    192.168.1.50
    aserver.example.org
    bserver.example.org

This is an inventory file, which is also explained in greater depth here:  :doc:`intro_inventory`.

We'll assume you are using SSH keys for authentication.  Set up SSH agent to avoid retyping passwords:

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
soon going to be time to read some of the more real-world :doc:`intro_adhoc`, and explore
what you can do with different modules, as well as the Ansible
:doc:`playbooks` language.  Ansible is not just about running commands, it
also has powerful configuration management and deployment features.  There's more to
explore, but you already have a fully working infrastructure!

A note about Host Key Checking
``````````````````````````````

Ansible 1.2.1 and later have host key checking enabled by default.  

If a host is reinstalled and has a different key in 'known_hosts', this will result in a error message until corrected.  If a host is not initially in 'known_hosts' this will result in prompting for confirmation of the key, which results in a interactive experience if using Ansible, from say, cron.

If you wish to disable this behavior and understand the implications, you can do so by editing /etc/ansible/ansible.cfg or ~/.ansible.cfg::

    [defaults]
    host_key_checking = False

Alternatively this can be set by an environment variable:

    $ export ANSIBLE_HOST_KEY_CHECKING=False

Also note that host key checking in paramiko mode is reasonably slow, therefore switching to 'ssh' is also recommended when using this feature.

.. seealso::

   :doc:`intro_inventory`
       More information about inventory
   :doc:`intro_adhoc`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

