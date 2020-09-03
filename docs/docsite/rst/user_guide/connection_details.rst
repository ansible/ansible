.. _connections:

******************************
Connection methods and details
******************************

This section shows you how to expand and refine the connection methods Ansible uses for your inventory.

ControlPersist and paramiko
---------------------------

By default, Ansible uses native OpenSSH, because it supports ControlPersist (a performance feature), Kerberos, and options in ``~/.ssh/config`` such as Jump Host setup. If your control machine uses an older version of OpenSSH that does not support ControlPersist, Ansible will fallback to a Python implementation of OpenSSH called 'paramiko'.

.. _connection_set_user:

Setting a remote user
---------------------

By default, Ansible connects to all remote devices with the user name you are using on the control node. If that user name does not exist on a remote device, you can set a different user name for the connection. If you just need to do some tasks as a different user, look at :ref:`become`. You can set the connection user in a playbook:

.. code-block:: yaml

   ---
   - name: update webservers
     hosts: webservers
     remote_user: admin

     tasks:
     - name: thing to do first in this playbook
     . . .

as a host variable in inventory:

.. code-block:: text

   other1.example.com     ansible_connection=ssh        ansible_user=myuser
   other2.example.com     ansible_connection=ssh        ansible_user=myotheruser

or as a group variable in inventory:

.. code-block:: yaml

    cloud:
      hosts:
        cloud1: my_backup.cloud.com
        cloud2: my_backup2.cloud.com
      vars:
        ansible_user: admin

Setting up SSH keys
-------------------

By default, Ansible assumes you are using SSH keys to connect to remote machines.  SSH keys are encouraged, but you can use password authentication if needed with the ``--ask-pass`` option. If you need to provide a password for :ref:`privilege escalation <become>` (sudo, pbrun, and so on), use ``--ask-become-pass``.

.. include:: shared_snippets/SSH_password_prompt.txt

To set up SSH agent to avoid retyping passwords, you can do:

.. code-block:: bash

   $ ssh-agent bash
   $ ssh-add ~/.ssh/id_rsa

Depending on your setup, you may wish to use Ansible's ``--private-key`` command line option to specify a pem file instead.  You can also add the private key file:

.. code-block:: bash

   $ ssh-agent bash
   $ ssh-add ~/.ssh/keypair.pem

Another way to add private key files without using ssh-agent is using ``ansible_ssh_private_key_file`` in an inventory file as explained here:  :ref:`intro_inventory`.

Running against localhost
-------------------------

You can run commands against the control node by using "localhost" or "127.0.0.1" for the server name:

.. code-block:: bash

    $ ansible localhost -m ping -e 'ansible_python_interpreter="/usr/bin/env python"'

You can specify localhost explicitly by adding this to your inventory file:

.. code-block:: bash

    localhost ansible_connection=local ansible_python_interpreter="/usr/bin/env python"

.. _host_key_checking_on:

Managing host key checking
--------------------------

Ansible enables host key checking by default. Checking host keys guards against server spoofing and man-in-the-middle attacks, but it does require some maintenance.

If a host is reinstalled and has a different key in 'known_hosts', this will result in an error message until corrected.  If a new host is not in 'known_hosts' your control node may prompt for confirmation of the key, which results in an interactive experience if using Ansible, from say, cron. You might not want this.

If you understand the implications and wish to disable this behavior, you can do so by editing ``/etc/ansible/ansible.cfg`` or ``~/.ansible.cfg``:

.. code-block:: text

    [defaults]
    host_key_checking = False

Alternatively this can be set by the :envvar:`ANSIBLE_HOST_KEY_CHECKING` environment variable:

.. code-block:: bash

    $ export ANSIBLE_HOST_KEY_CHECKING=False

Also note that host key checking in paramiko mode is reasonably slow, therefore switching to 'ssh' is also recommended when using this feature.

Other connection methods
------------------------

Ansible can use a variety of connection methods beyond SSH. You can select any connection plugin, including managing things locally and managing chroot, lxc, and jail containers.
A mode called 'ansible-pull' can also invert the system and have systems 'phone home' via scheduled git checkouts to pull configuration directives from a central repository.
