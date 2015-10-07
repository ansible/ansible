Getting Started
===============

.. index::
  single: getting started

.. contents:: Topics

.. _gs_about:

Foreword
````````

Now that you have read the :doc:`intro_installation` section and installed Ansible, it is time to dig in and get started with some commands.  

This section does not discuss the powerful configuration, deployment, and orchestration features of Ansible.
These features are handled by playbooks which are covered in a separate section (refer to :ref:`playbooks` for more information).

This section is about how to initially get going.  Once you have these basic concepts down, read :doc:`intro_adhoc` for some more
detail, and then you should be ready to dive into playbooks and explore the most interesting parts of Ansible.

.. _remote_connection_information:

Remote Connection Information
`````````````````````````````

.. index::
  single: remote connections
  single: OpenSSH
  single: ControlPersist
  single: paramiko 
  single: SFTP
  single: SCP

Before we get started, it's important to understand how Ansible communicates with remote
machines over SSH. 

By default, Ansible 1.3 and later will try to use native OpenSSH for remote communication when possible.  This enables ControlPersist (a performance feature), Kerberos, and options in ``~/.ssh/config`` such as "Jump Host" setup.  However, when using Enterprise Linux 6 operating systems as the control machine (Red Hat Enterprise Linux and derivatives such as CentOS), the version of OpenSSH may be too old to support ControlPersist. On these operating systems, Ansible fallbacks into using a high-quality Python implementation of OpenSSH called "paramiko".  If you wish to use a feature like Kerberized SSH, consider using Fedora, OS X, or Ubuntu as your control machine until a newer version of OpenSSH is available for your platform.  Another alternative is engaging "accelerated mode" in Ansible.  Refer to :doc:`playbooks_acceleration` for more information.

In releases up to and including Ansible 1.2, the default was strictly paramiko.  Native SSH had to be explicitly selected with the ``-c ssh`` option or set in the configuration file.

Occasionally you may encounter a device that doesn't support SFTP. This is rare, but should it occur, you can switch to SCP mode as outlined in the:doc:`intro_configuration` section.

When speaking with remote machines, Ansible by default assumes you are using SSH keys.  SSH keys are encouraged but password authentication can also be used where needed by supplying the option ``--ask-pass``.  If using sudo features and when sudo requires a password, also supply ``--ask-sudo-pass``.

While it may be common sense, the following advice is worth sharing: Any management system benefits from being run near the machines being managed. If you are running Ansible in a cloud, consider running it from a machine inside that cloud.  In most cases, this works better than running it on the open Internet.

As an advanced topic, Ansible is not limited to connecting remotely over SSH.  The transports are pluggable, and there are options for managing things locally, as well as managing chroot, lxc, and jail containers.  A mode called 'ansible-pull' can also invert the system and have systems "phone home" via scheduled git checkouts to pull configuration directives from a central repository.

.. _your_first_commands:

Your First Commands
````````````````````

.. index::
  pair: commands; basic
  single: /etc/ansible/hosts
  pair: commands; sudo
  pair: commands; ssh-agent
  pair: commands; ping
  pair: commands; hello

Now that you have installed Ansible, it is time to get started with some basics.

Edit (or create) the ``/etc/ansible/hosts`` file and put one or more remote systems in it. Your
public SSH key should be located in ``authorized_keys`` on those systems:

::

    192.168.1.50
    aserver.example.org
    bserver.example.org

This is an inventory file, which is also explained in greater depth in the :doc:`intro_inventory` section.

It is assumed that you are using SSH keys for authentication.  To set up an SSH agent to avoid retyping passwords, you can
do:

.. code-block:: bash

    $ ssh-agent bash
    $ ssh-add ~/.ssh/id_rsa

(Depending on your setup, you may wish to use Ansible's ``--private-key`` option to specify a pem file instead.)

Now ping all your nodes:

.. code-block:: bash

   $ ansible all -m ping

Ansible attempts to establish remote connections to the machines using your current
user name, just like SSH would.  To override the remote user name, just use the ``-u`` parameter.

To access ``sudo`` mode, use flags:

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

.. note::

    The ``sudo`` implementation is changeable in Ansible's configuration file if you happen to want to use a ``sudo`` replacement.  Flags passed to ``sudo`` (like ``-H``) can also be set there.

Now run a live command on all of your nodes:
  
.. code-block:: bash

   $ ansible all -a "/bin/echo hello"

Congratulations!  You have contacted your nodes with Ansible.  It is soon going to be time to read about some more real-world cases in :doc:`intro_adhoc`, explore what you can do with different modules, and to learn about the Ansible :doc:`playbooks` language.  Ansible is not just about running commands, it also has powerful configuration management and deployment features.  

.. _a_note_about_host_key_checking:

Host Key Checking
`````````````````

.. index::
  single: host key checking
  single: known_hosts

Ansible 1.2.1 and later have host key checking enabled by default.  

If a host is reinstalled and has a different key in ``known_hosts``, an error message appears until this is corrected.  If a host is not initially in ``known_hosts``, you will be prompted for confirmation of the key, which results in an interactive experience if using Ansible from, say, cron.  You might not want this.

If you fully understand the implications and want to disable this behavior, you can do so by editing ``/etc/ansible/ansible.cfg`` or ``~/.ansible.cfg``:

::

    [defaults]
    host_key_checking = False

Alternatively this can be set by an environment variable:

.. code-block:: bash

    $ export ANSIBLE_HOST_KEY_CHECKING=False

Also note that host key checking in paramiko mode is reasonably slow, therefore switching to ``ssh`` is also recommended when using this feature.

.. _a_note_about_logging:

.. index::
  pair: Ansible; logging

Ansible logs some information about module arguments on the remote system in the remote ``syslog``, unless a task or play is marked with a ``no_log: True`` attribute. This is explained later.

To enable basic logging on the control machine, review the :doc:`intro_configuration` section and set the ``log_path`` configuration file setting.  Enterprise users may also be interested in reading about :doc:`tower`.  |at| provides a very robust database logging feature, allowing users to drill down and see system history based on hosts, projects, and particular inventories over time--explorable both graphically and through a REST API.

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

