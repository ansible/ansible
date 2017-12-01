.. network-getting-started-example:

***************************************
Getting Started with Ansible Networking
***************************************

.. contents:: Topics


Overview
========

This example shows how Ansible can be used to connect to and manage multiple network devices.

.. FIXME FUTURE Gundalow - Link to examples index once created

.. note:: This example is for educational purposes only and is not intended for production use. Example code may sometimes eliminate safe coding practices in the interest of making concepts easier to understand (for example, passwords should NEVER be stored in cleartext).

Audience
--------

* This example is intended for network or system administrators who want to understand how to use Ansible to manage network devices.


Prerequisites
-------------

This example requires the following:

* **Ansible 2.5** (or higher) installed. See :doc:`intro_installation` for more information.
* One or more network devices that are compatible with Ansible.
* Basic understanding of YAML :doc:`YAMLSyntax`.
* Basic understanding of Jinja2 Templates. See :doc:`playbooks_templating` for more information.
* Basic Linux command line use.
* Basic knowledge of network switch & router configurations.


.. FIXME FUTURE Gundalow - Once created we will link to the connection table here (which platforms support network_cli & credentials through inventory)
.. FIXME FUTURE Gundalow - Using ``ansible_ssh_pass`` will not work for REST transports such as ``eapi``, ``nxapi`` - Once documented in above FIXME add details here

Concepts
========

This section explains some fundamental concepts that you should understand when working with Ansible Networking.

Inventory
---------

An ``inventory`` file is an INI-like configuration file that defines the mapping of hosts into groups.

In our example, the inventory file defines the groups ``eos``, ``vyos`` and a "group of groups" called ``switches``. Further details about subgroups and inventory files can be found in the :ref:`Ansible inventory Group documentation <subgroups>`.


Credentials
^^^^^^^^^^^

Although there are many ways to supply credentials in Ansible, in this example we are using ``ansible_user`` and ``ansible_ssh_pass`` for simplicity.

.. FIXME FUTURE Gundalow - Link to network auth & proxy page (to be written)

.. warning:: Never store passwords in plain text

   Passwords should never be stored in plain text. The "Vault" feature of Ansible allows keeping sensitive data such as passwords or keys in encrypted files, rather than as plaintext in your playbooks or roles. These vault files can then be distributed or placed in source control. See :doc:`playbooks_vault` for more information.

ansible_connection
^^^^^^^^^^^^^^^^^^

The ansible-connection setting tells Ansible how it should connect to a remote device. When working with Ansible Networking, setting this to ``ansible_connection=network_cli`` informs Ansible that the remote node is a network device with a limited execution environment. Without this setting, Ansible would attempt to use ssh to connect to the remote and execute the Python script on the network device, which would fail because Python generally isn't available on network devices.

.. FIXME FUTURE Gundalow - Link to network auth & proxy page (to be written) - in particular eapi/nxapi

Playbook
--------

Collect data
^^^^^^^^^^^^

Ansible facts modules gather system information 'facts' that are available to the rest of your playbook.

Ansible Networking ships with a number of network-specific facts modules. In this example, we use the ``_facts`` modules :ref:`eos_facts <eos_facts>` and :ref:`vyos_facts <vyos_facts>` to connect to the remote networking device. As the credentials are not explicitly passed via module arguments, Ansible uses the username and password from the inventory file.

Ansible's "Network Fact modules" gather information from the system and store the results in facts prefixed with ``ansible_net_``. The data collected by these modules is documented in the `Return Values` section of the module docs, in this case :ref:`eos_facts <eos_facts>` and :ref:`vyos_facts <vyos_facts>`. We can use the facts, such as ``ansible_net_version`` late on in the "Display some facts" task.

To ensure we call the correct mode (eos_facts or vyos_facts) the task is conditionally run based on the group defined in the inventory file, for more information on the use of conditionals in Ansible Playbooks see :ref:`the_when_statement`.

Privilege escalation
^^^^^^^^^^^^^^^^^^^^

Certain network platforms, such as eos and ios, have the concept of different privilege modes. Certain network modules, such as those that modify system state including users, will only work in high privilege states. Ansible version 2.5 added support for ``become`` when using ``connection=network_cli``. This allows privileges to be raised for the specific tasks that need them. Adding ``become: true`` and ``become_method: enable`` informs Ansible to go into privilege mode before executing the task, as shown here:

.. code-block:: yaml

   - name: Gather facts (eos)
     eos_facts:
     become: true
     become_method: enable
     when: "'eos' in group_names"


For more information, see the :doc:`Ansible Privilege Escalation<become>` guide.

Example
=======

In this example, we will create an inventory file containing some network switches, then run a playbook to connect to the network devices and return some information about them.

**Create an inventory file**

First, create a file called ``inventory``, containing:

.. code-block:: ini

   [switches:children]
   eos
   vyos

   [eos]
   eos01.example.net ansible_connection=network_cli ansible_network_os=eos ansible_user=myuser ansible_ssh_pass=mypassword

   [vyos]
   vyos01.example.net ansible_connection=network_cli ansible_network_os=vyos ansible_user=admin ansible_ssh_pass=mypassword


**Create a playbook**

Next, create a playbook file called ``fetch-facts.yml`` containing the following:

.. code-block:: yaml

   - name: "Demonstrate connecting to switches"
     hosts: switches
     gather_facts: no

     tasks:
       ###
       # Collect data
       #
       - name: Gather facts (eos)
         eos_facts:
         become: true
         become_method: enable
         when: "'eos' in group_names"

       - name: Gather facts (vyos)
         vyos_facts:
         when: "'vyos' in group_names"

       ###
       # Demonstrate variables
       #
       - name: Display some facts
         debug:
           msg: "The hostname is {{ ansible_net_hostname }} and the OS is {{ ansible_net_version }}"

       - name: Facts from a specific host
         debug:
           var: hostvars['vyos01.example.net']

       - name: Write facts to disk using a template
         copy:
           content: |
             #jinja2: lstrip_blocks: True
             EOS device info:
               {% for host in groups['eos'] %}
               Hostname: {{ hostvars[host].ansible_net_version }}
               Version: {{ hostvars[host].ansible_net_version }}
               Model: {{ hostvars[host].ansible_net_model }}
               Serial: {{ hostvars[host].ansible_net_serialnum }}
               {% endfor %}

             VyOS device info:
               {% for host in groups['vyos'] %}
               Hostname: {{ hostvars[host].ansible_net_version }}
               Version: {{ hostvars[host].ansible_net_version }}
               Model: {{ hostvars[host].ansible_net_model }}
               Serial: {{ hostvars[host].ansible_net_serialnum }}
               {% endfor %}
           dest: /tmp/switch-facts
         run_once: yes

       ###
       # Get running configuration
       #

       - name: Backup switch (eos)
         eos_config:
           backup: yes
         become: true
         become_method: enable
         register: backup_eos
         when: "'eos' in group_names"

       - name: backup switch (vyos)
         vyos_config:
           backup: yes
         register: backup_vyos
         when: "'vyos' in group_names"

       - name: Create backup dir
         file:
           path: "/tmp/backups/{{ inventory_hostname }}"
           state: directory
           recurse: yes

       - name: Copy backup files into /tmp/backups/ (eos)
         copy:
           src: "{{ backup_eos.backup_path }}"
           dest: "/tmp/backups/{{ inventory_hostname }}/{{ inventory_hostname }}.bck"
         when: "'eos' in group_names"

       - name: Copy backup files into /tmp/backups/ (vyos)
         copy:
           src: "{{ backup_vyos.backup_path }}"
           dest: "/tmp/backups/{{ inventory_hostname }}/{{ inventory_hostname }}.bck"
         when: "'vyos' in group_names"

Running the playbook
--------------------

To run the playbook, run the following from a console prompt:

.. code-block:: console

   ansible-playbook -i inventory fetch-facts.yml

This should return output similar to the following:

.. code-block:: console

   PLAY RECAP
   eos01.example.net          : ok=7    changed=2    unreachable=0    failed=0
   vyos01.example.net         : ok=6    changed=2    unreachable=0    failed=0

Next, look at the contents of the file we created containing the switch facts:

.. code-block:: console

   cat /tmp/switch-facts

You can also look at the backup files:

.. code-block:: console

   find /tmp/backups


If `ansible-playbook` fails, please follow the debug steps in :doc:`network_debug_troubleshooting`.


Implementation Notes
====================


Demo variables
--------------

Although these tasks are not needed to write data to disk, they are used in this example to demonstrate some methods of accessing facts about the given devices or a named host.

Ansible ``hostvars`` allows you to access variables from a named host. Without this we would return the details for the current host, rather than the named host.

For more information, see :ref:`magic_variables_and_hostvars`.

Get running configuration
-------------------------

The :ref:`eos_config <eos_config>` and :ref:`vyos_config <vyos_config>` modules have a ``backup:`` option that when set will cause the module to create a full backup of the current ``running-config`` from the remote device before any changes are made. The backup file is written to the ``backup`` folder in the playbook root directory. If the directory does not exist, it is created.

To demonstrate how we can move the backup file to a different location we ``register`` the result and use the ``backup_path`` return value as source location to move the file into ``/tmp/backups/`` directory which we have created.

Note that when using variables from tasks in this way we use double quotes (``"``) and double curly-brackets (``{{...}}`` to tell Ansible that this is a variable.

Troubleshooting
===============

If you receive an connection error please double check the inventory and Playbook for typos or missing lines, if the issue still occurs follow the debug steps in :doc:`network_debug_troubleshooting`.


.. seealso::

  * Network landing page
  * intro_inventory
  * playbooks_best_practices.html#best-practices-for-variables-and-vaults

