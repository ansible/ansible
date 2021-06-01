.. _intro_getting_started:

***************
Getting Started
***************

Now that you have read the :ref:`installation guide<installation_guide>` and installed Ansible on a control node, you are ready to learn how Ansible works. A basic Ansible command or playbook:

* selects machines to execute against from inventory
* connects to those machines (or network devices, or other managed nodes), usually over SSH
* copies one or more modules to the remote machines and starts execution there

Ansible can do much more, but you should understand the most common use case before exploring all the powerful configuration, deployment, and orchestration features of Ansible. This page illustrates the basic process with a simple inventory and an ad hoc command. Once you understand how Ansible works, you can read more details about :ref:`ad hoc commands<intro_adhoc>`, organize your infrastructure with :ref:`inventory<intro_inventory>`, and harness the full power of Ansible with :ref:`playbooks<playbooks_intro>`.

.. contents::
   :local:

Selecting machines from inventory
=================================

Ansible reads information about which machines you want to manage from your inventory. Although you can pass an IP address to an ad hoc command, you need inventory to take advantage of the full flexibility and repeatability of Ansible.

Action: create a basic inventory
--------------------------------
For this basic inventory, edit (or create) ``/etc/ansible/hosts`` and add a few remote systems to it. For this example, use either IP addresses or FQDNs:

.. code-block:: text

   192.0.2.50
   aserver.example.org
   bserver.example.org

Beyond the basics
-----------------
Your inventory can store much more than IPs and FQDNs. You can create :ref:`aliases<inventory_aliases>`, set variable values for a single host with :ref:`host vars<host_variables>`, or set variable values for multiple hosts with :ref:`group vars<group_variables>`.

.. _remote_connection_information:

Connecting to remote nodes
==========================

Ansible communicates with remote machines over the `SSH protocol <https://www.ssh.com/ssh/protocol/>`_. By default, Ansible uses native OpenSSH and connects to remote machines using your current user name, just as SSH does.

Action: check your SSH connections
----------------------------------
Confirm that you can connect using SSH to all the nodes in your inventory using the same username. If necessary, add your public SSH key to the ``authorized_keys`` file on those systems.

Beyond the basics
-----------------
You can override the default remote user name in several ways, including:

- passing the ``-u`` parameter at the command line
- setting user information in your inventory file
- setting user information in your configuration file
- setting environment variables

See :ref:`general_precedence_rules` for details on the (sometimes unintuitive) precedence of each method of passing user information. You can read more about connections in :ref:`connections`.

Copying and executing modules
=============================

Once it has connected, Ansible transfers the modules required by your command or playbook to the remote machine(s) for execution.

Action: run your first Ansible commands
---------------------------------------
Use the ping module to ping all the nodes in your inventory:

.. code-block:: bash

   $ ansible all -m ping

You should see output for each host in your inventory, similar to this:

.. code-block:: ansible-output

   aserver.example.org | SUCCESS => {
       "ansible_facts": {
           "discovered_interpreter_python": "/usr/bin/python"
       },
       "changed": false,
       "ping": "pong"
   }

You can use ``-u`` as one way to specify the user to connect as, by default Ansible uses SSH, which defaults to the 'current user'.

Now run a live command on all of your nodes:

.. code-block:: bash

   $ ansible all -a "/bin/echo hello"

You should see output for each host in your inventory, similar to this:

.. code-block:: ansible-output

    aserver.example.org | CHANGED | rc=0 >>
    hello

Action: Run your first playbook
-------------------------------

Playbooks are used to pull together tasks into reusable units.

Ansible does not store playbooks for you; they are simply YAML documents that you store and manage, passing them to Ansible to run as needed.

In a directory of your choice you can create your first playbook in a file called mytask.yml:

.. code-block:: yaml

    ---
    - name: My task
      hosts: all
      tasks:
         - name: Leaving a mark
           command: "touch /tmp/ansible_was_here"

You can run this command as follows:

.. code-block:: bash

    $ ansible-playbook mytask.yaml

and may see output like this:

.. code-block:: ansible-output


   PLAY [My task] **************************************************************************************************************************
   
   TASK [Gathering Facts] ******************************************************************************************************************
   ok: [aserver.example.org]
   ok: [aserver.example.org]
   ok: [192.0.2.50]
   fatal: [192.0.2.50]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh: ssh: connect to host 192.0.2.50 port 22: No route to host", "unreachable": true}
   
   TASK [Leaving a mark] *******************************************************************************************************************
   [WARNING]: Consider using the file module with state=touch rather than running 'touch'.  If you need to use command because file is
   insufficient you can add 'warn: false' to this command task or set 'command_warnings=False' in ansible.cfg to get rid of this message.
   changed: [aserver.example.org]
   changed: [bserver.example.org]
   
   PLAY RECAP ******************************************************************************************************************************
   aserver.example.org        : ok=2    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
   bserver.example.org        : ok=2    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
   192.0.2.50                 : ok=0    changed=0    unreachable=1    failed=0    skipped=0    rescued=0    ignored=0   

Read on to learn more about controlling which nodes your playbooks execute on, more sophisticated tasks, and the meaning of the output.

Beyond the basics
-----------------
By default Ansible uses SFTP to transfer files. If the machine or device you want to manage does not support SFTP, you can switch to SCP mode in :ref:`intro_configuration`. The files are placed in a temporary directory and executed from there.

If you need privilege escalation (sudo and similar) to run a command, pass the ``become`` flags:

.. code-block:: bash

    # as bruce
    $ ansible all -m ping -u bruce
    # as bruce, sudoing to root (sudo is default method)
    $ ansible all -m ping -u bruce --become
    # as bruce, sudoing to batman
    $ ansible all -m ping -u bruce --become --become-user batman

You can read more about privilege escalation in :ref:`become`.

Congratulations! You have contacted your nodes using Ansible. You used a basic inventory file and an ad hoc command to direct Ansible to connect to specific remote nodes, copy a module file there and execute it, and return output. You have a fully working infrastructure.

Resources
=================================
- `Product Demos <https://github.com/ansible/product-demos>`_
- `Katakoda <https://katacoda.com/rhel-labs>`_
- `Workshops <https://github.com/ansible/workshops>`_
- `Ansible Examples <https://github.com/ansible/ansible-examples>`_
- `Ansible Baseline <https://github.com/ansible/ansible-baseline>`_

Next steps
==========
Next you can read about more real-world cases in :ref:`intro_adhoc`,
explore what you can do with different modules, or read about the Ansible
:ref:`working_with_playbooks` language.  Ansible is not just about running commands, it
also has powerful configuration management and deployment features.

.. seealso::

   :ref:`intro_inventory`
       More information about inventory
   :ref:`intro_adhoc`
       Examples of basic commands
   :ref:`working_with_playbooks`
       Learning Ansible's configuration management language
   `Ansible Demos <https://github.com/ansible/product-demos>`_
       Demonstrations of different Ansible usecases
   `RHEL Labs <https://katacoda.com/rhel-labs>`_
       Labs to provide further knowledge on different topics
   `Mailing List <https://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
