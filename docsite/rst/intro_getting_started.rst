Getting Started
===============

.. contents:: Topics

.. _gs_about:

Foreword
````````

Now that you've read :doc:`intro_installation` and installed Ansible, it's time to dig in and get
started with some commands.  

What we are showing first are not the powerful configuration/deployment/orchestration of Ansible, called playbooks.
Playbooks are covered in a separate section.

This section is about how to get going initially.  Once you have these concepts down, read :doc:`intro_adhoc` for some more
detail, and then you'll be ready to dive into playbooks and explore the most interesting parts!

.. _remote_connection_information:

Remote Connection Information
`````````````````````````````

Before we get started, it's important to understand how Ansible is communicating with remote
machines over SSH. 

By default, Ansible 1.3 and later will try to use native 
OpenSSH for remote communication  when possible.  This enables both ControlPersist (a performance feature), Kerberos, and options in ~/.ssh/config such as Jump Host setup.  When using Enterprise Linux 6 operating systems as the control machine (Red Hat Enterprise Linux and derivatives such as CentOS), however, the version of OpenSSH may be too old to support ControlPersist. On these operating systems, Ansible will fallback into using a high-quality Python implementation of
OpenSSH called 'paramiko'.  If you wish to use features like Kerberized SSH and more, consider using Fedora, OS X, or Ubuntu as your control machine until a newer version of OpenSSH is available for your platform -- or engage 'accelerated mode' in Ansible.  See :doc:`playbooks_acceleration`.

In Ansible 1.2 and before, the default was strictly paramiko and native SSH had to be explicitly selected with -c ssh or set in the configuration file.

Occasionally you'll encounter a device that doesn't do SFTP. This is rare, but if talking with some remote devices that don't support SFTP, you can switch to SCP mode in :doc:`intro_configuration`.

When speaking with remote machines, Ansible will by default assume you are using SSH keys -- which we encourage -- but passwords are fine too.  To enable password auth, supply the option ``--ask-pass`` where needed.  If using sudo features and when sudo requires a password, also supply ``--ask-sudo-pass`` as appropriate.

While it may be common sense, it is worth sharing: Any management system benefits from being run near the machines being managed. If running in a cloud, consider running Ansible from a machine inside that cloud.  It will work better than on the open
internet in most cases.

As an advanced topic, Ansible doesn't just have to connect remotely over SSH.  The transports are pluggable, and there are options for managing things locally, as well as managing chroot, lxc, and jail containers.  A mode called 'ansible-pull' can also invert the system and have systems 'phone home' via scheduled git checkouts to pull configuration directives from a central repository.

.. _your_first_commands:

Your first commands
```````````````````

Now that you've installed Ansible, it's time to get started with some basics.

Edit (or create) /etc/ansible/hosts and put one or more remote systems in it, for
which you have your SSH key in ``authorized_keys``::

    192.168.1.50
    aserver.example.org
    bserver.example.org

This is an inventory file, which is also explained in greater depth here:  :doc:`intro_inventory`.

We'll assume you are using SSH keys for authentication.  To set up SSH agent to avoid retyping passwords, you can
do:

.. code-block:: bash

    $ ssh-agent bash
    $ ssh-add ~/.ssh/id_rsa

(Depending on your setup, you may wish to use Ansible's ``--private-key`` option to specify a pem file instead)

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

(The sudo implementation is changeable in Ansible's configuration file if you happen to want to use a sudo
replacement.  Flags passed to sudo (like -H) can also be set there.)

Now run a live command on all of your nodes:
  
.. code-block:: bash

   $ ansible all -a "/bin/echo hello"

Congratulations.  You've just contacted your nodes with Ansible.  It's
soon going to be time to read some of the more real-world :doc:`intro_adhoc`, and explore
what you can do with different modules, as well as the Ansible
:doc:`playbooks` language.  Ansible is not just about running commands, it
also has powerful configuration management and deployment features.  There's more to
explore, but you already have a fully working infrastructure!

.. _a_note_about_host_key_checking:

Host Key Checking
`````````````````

Ansible 1.2.1 and later have host key checking enabled by default.  

If a host is reinstalled and has a different key in 'known_hosts', this will result in an error message until corrected.  If a host is not initially in 'known_hosts' this will result in prompting for confirmation of the key, which results in an interactive experience if using Ansible, from say, cron.  You might not want this.

If you wish to disable this behavior and understand the implications, you can do so by editing /etc/ansible/ansible.cfg or ~/.ansible.cfg::

    [defaults]
    host_key_checking = False

Alternatively this can be set by an environment variable:

.. code-block:: bash

    $ export ANSIBLE_HOST_KEY_CHECKING=False

Also note that host key checking in paramiko mode is reasonably slow, therefore switching to 'ssh' is also recommended when using this feature.

.. _a_note_about_logging:

Ansible will log some information about module arguments on the remote system in the remote syslog.  To enable basic
logging on the control machine see :doc:`intro_configuration` document and set the 'log_path' configuration file setting.  Enterprise users may also be interested in :doc:`tower`.  Tower provides a very robust database logging feature where it is possible to drill down and see history based on hosts, projects, and particular inventories over time -- explorable both graphically and through a REST API.

.. seealso::

   :doc:`intro_inventory`
       More information about inventory
   :doc:`intro_adhoc`
       Examples of basic commands
   :doc:`playbooks`
       Learning Ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

