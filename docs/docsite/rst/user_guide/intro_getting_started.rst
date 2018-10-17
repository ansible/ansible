.. _intro_getting_started:

Getting Started
===============

.. contents:: Topics

.. _gs_about:

Foreword
````````

Now that you've read the :ref:`installation guide<installation_guide>` and installed Ansible, it's time to get
started with some ad-hoc commands.

What we are showing first are not the powerful configuration/deployment/orchestration features of Ansible.
These features are handled by playbooks which are covered in a separate section.

This section is about how to initially get Ansible running.  Once you understand these concepts, read :doc:`intro_adhoc` for some more detail, and then you'll be ready to begin learning about playbooks and explore the most interesting parts!

.. _remote_connection_information:

Remote Connection Information
`````````````````````````````

Before we get started, it's important to understand how Ansible communicates with remote
machines over SSH.

By default, Ansible will try to use native
OpenSSH for remote communication when possible.  This enables ControlPersist (a performance feature), Kerberos, and options in ``~/.ssh/config`` such as Jump Host setup.  However, when using Enterprise Linux 6 operating systems as the control machine (Red Hat Enterprise Linux and derivatives such as CentOS), the version of OpenSSH may be too old to support ControlPersist. On these operating systems, Ansible will fallback into using a high-quality Python implementation of
OpenSSH called 'paramiko'.  If you wish to use features like Kerberized SSH and more, consider using Fedora, macOS, or Ubuntu as your control machine until a newer version of OpenSSH is available for your platform.

Occasionally you'll encounter a device that doesn't support SFTP. This is rare, but should it occur, you can switch to SCP mode in :ref:`intro_configuration`.

When speaking with remote machines, Ansible by default assumes you are using SSH keys.  SSH keys are encouraged but password authentication can also be used where needed by supplying the option ``--ask-pass``.  If using sudo features and when sudo requires a password, also supply ``--ask-become-pass`` (previously ``--ask-sudo-pass`` which has been deprecated).

.. include:: shared_snippets/SSH_password_prompt.txt

While it may be common sense, it is worth sharing: Any management system benefits from being run near the machines being managed. If you are running Ansible in a cloud, consider running it from a machine inside that cloud.  In most cases this will work better than on the open Internet.

As an advanced topic, Ansible doesn't just have to connect remotely over SSH.  The transports are pluggable, and there are options for managing things locally, as well as managing chroot, lxc, and jail containers.  A mode called 'ansible-pull' can also invert the system and have systems 'phone home' via scheduled git checkouts to pull configuration directives from a central repository.

.. _your_first_commands:

Your first commands
```````````````````

Now that you've installed Ansible, it's time to get started with some basics.

Edit (or create) ``/etc/ansible/hosts`` and put one or more remote systems in it. Your
public SSH key should be located in ``authorized_keys`` on those systems::

    192.0.2.50
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

    # With latest version of ansible `sudo` is deprecated so use become
    # as bruce, sudoing to root
    $ ansible all -m ping -u bruce -b
    # as bruce, sudoing to batman
    $ ansible all -m ping -u bruce -b --become-user batman

(The sudo implementation is changeable in Ansible's configuration file if you happen to want to use a sudo
replacement.  Flags passed to sudo (like -H) can also be set there.)

Now run a live command on all of your nodes:

.. code-block:: bash

   $ ansible all -a "/bin/echo hello"

Congratulations!  You've just contacted your nodes with Ansible.  It's
soon going to be time to: read about some more real-world cases in :doc:`intro_adhoc`,
explore what you can do with different modules, and to learn about the Ansible
:doc:`playbooks` language.  Ansible is not just about running commands, it
also has powerful configuration management and deployment features.  There's more to
explore, but you already have a fully working infrastructure!

Tips

When running commands, you can specify the local server by using "localhost" or "127.0.0.1" for the server name.

Example:

.. code-block:: bash

    $ ansible localhost -m ping -e 'ansible_python_interpreter="/usr/bin/env python"'

You can specify localhost explicitly by adding this to your inventory file::

    localhost ansible_connection=local ansible_python_interpreter="/usr/bin/env python"

.. _a_note_about_host_key_checking:

Host Key Checking
`````````````````

Ansible has host key checking enabled by default.

If a host is reinstalled and has a different key in 'known_hosts', this will result in an error message until corrected.  If a host is not initially in 'known_hosts' this will result in prompting for confirmation of the key, which results in an interactive experience if using Ansible, from say, cron.  You might not want this.

If you understand the implications and wish to disable this behavior, you can do so by editing ``/etc/ansible/ansible.cfg`` or ``~/.ansible.cfg``::

    [defaults]
    host_key_checking = False

Alternatively this can be set by the :envvar:`ANSIBLE_HOST_KEY_CHECKING` environment variable:

.. code-block:: bash

    $ export ANSIBLE_HOST_KEY_CHECKING=False

Also note that host key checking in paramiko mode is reasonably slow, therefore switching to 'ssh' is also recommended when using this feature.

.. _a_note_about_logging:

Ansible will log some information about module arguments on the remote system in the remote syslog, unless a task or play is marked with a "no_log: True" attribute. This is explained later.

To enable basic logging on the control machine see :ref:`intro_configuration` document and set the 'log_path' configuration file setting.  Enterprise users may also be interested in :ref:`ansible_tower`.  Tower provides a very robust database logging feature where it is possible to drill down and see history based on hosts, projects, and particular inventories over time -- explorable both graphically and through a REST API.

.. seealso::

   :ref:`intro_inventory`
       More information about inventory
   :ref:`intro_adhoc`
       Examples of basic commands
   :ref:`working_with_playbooks`
       Learning Ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
