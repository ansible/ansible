.. _network-best-practices:

**************************************
Network Best Practices for Ansible 2.5
**************************************


Overview
========

This document explains the best practices for using Ansible 2.5 to manage your network infrastructure.


Audience
--------

* This example is intended for network or system administrators who want to understand how to use Ansible to manage network devices.


Prerequisites
-------------

This example requires the following:

* **Ansible 2.5** (or higher) installed. See :doc:`../../installation_guide/intro_installation` for more information.
* One or more network devices that are compatible with Ansible.
* Basic understanding of YAML :doc:`../../reference_appendices/YAMLSyntax`.
* Basic understanding of Jinja2 Templates. See :doc:`../../user_guide/playbooks_templating` for more information.
* Basic Linux command line use.
* Basic knowledge of network switch & router configurations.



Concepts
========

This section explains some fundamental concepts that you should understand when working with Ansible Networking.

Structure
----------

The examples on this page use the following structure:

.. code-block:: console

   .
   ├── facts-demo.yml
   └── inventory


Inventory, Connections, Credentials: Grouping Devices and Variables
-------------------------------------------------------------------

An ``inventory`` file is an INI-like configuration file that defines the mapping of hosts into groups.

In our example, the inventory file defines the groups ``eos``, ``ios``, ``vyos`` and a "group of groups" called ``switches``. Further details about subgroups and inventory files can be found in the :ref:`Ansible inventory Group documentation <subgroups>`.

Because Ansible is a flexible tool, there are a number of ways to specify connection information and credentials. We recommend using the ``[my_group:vars]`` capability in your inventory file. Here's what it would look like if you specified your ssh passwords (encrypted with Ansible Vault) among your variables:

.. code-block:: ini

   [all:vars]
   # these defaults can be overridden for any group in the [group:vars] section
   ansible_connection=network_cli
   ansible_user=ansible

   [switches:children]
   eos
   ios
   vyos

   [eos]
   veos01 ansible_host=veos-01.example.net
   veos02 ansible_host=veos-02.example.net
   veos03 ansible_host=veos-03.example.net
   veos04 ansible_host=veos-04.example.net

   [eos:vars]
   ansible_become=yes
   ansible_become_method=enable
   ansible_network_os=eos
   ansible_user=my_eos_user
   ansible_ssh_pass= !vault |
                     $ANSIBLE_VAULT;1.1;AES256
                     37373735393636643261383066383235363664386633386432343236663533343730353361653735
                     6131363539383931353931653533356337353539373165320a316465383138636532343463633236
                     37623064393838353962386262643230303438323065356133373930646331623731656163623333
                     3431353332343530650a373038366364316135383063356531633066343434623631303166626532
                     9562

   [ios]
   ios01 ansible_host=ios-01.example.net
   ios02 ansible_host=ios-02.example.net
   ios03 ansible_host=ios-03.example.net

   [ios:vars]
   ansible_become=yes
   ansible_become_method=enable
   ansible_network_os=ios
   ansible_user=my_ios_user
   ansible_ssh_pass= !vault |
                     $ANSIBLE_VAULT;1.1;AES256
                     34623431313336343132373235313066376238386138316466636437653938623965383732373130
                     3466363834613161386538393463663861636437653866620a373136356366623765373530633735
                     34323262363835346637346261653137626539343534643962376139366330626135393365353739
                     3431373064656165320a333834613461613338626161633733343566666630366133623265303563
                     8472

   [vyos]
   vyos01 ansible_host=vyos-01.example.net
   vyos02 ansible_host=vyos-02.example.net
   vyos03 ansible_host=vyos-03.example.net

   [vyos:vars]
   ansible_network_os=vyos
   ansible_user=my_vyos_user
   ansible_ssh_pass= !vault |
                     $ANSIBLE_VAULT;1.1;AES256
                     39336231636137663964343966653162353431333566633762393034646462353062633264303765
                     6331643066663534383564343537343334633031656538370a333737656236393835383863306466
                     62633364653238323333633337313163616566383836643030336631333431623631396364663533
                     3665626431626532630a353564323566316162613432373738333064366130303637616239396438
                     9853

If you use ssh-agent, you do not need the ``ansible_ssh_pass`` lines. If you use ssh keys, but not ssh-agent, and you have multiple keys, specify the key to use for each connection in the ``[group:vars]`` section with ``ansible_ssh_private_key_file=/path/to/correct/key``. For more information on ``ansible_ssh_`` options see the :ref:`behavioral_parameters`.

.. FIXME FUTURE Gundalow - Link to network auth & proxy page (to be written)

.. warning:: Never store passwords in plain text.

The "Vault" feature of Ansible allows you to keep sensitive data such as passwords or keys in encrypted files, rather than as plain text in your playbooks or roles. These vault files can then be distributed or placed in source control. See :doc:`../../user_guide/playbooks_vault` for more information.

:ansible_connection:

  Ansible uses the ansible-connection setting to determine how to connect to a remote device. When working with Ansible Networking, set this to ``network_cli`` so Ansible treats the remote node as a network device with a limited execution environment. Without this setting, Ansible would attempt to use ssh to connect to the remote and execute the Python script on the network device, which would fail because Python generally isn't available on network devices.
:ansible_network_os:
  Informs Ansible which Network platform this hosts corresponds to. This is required when using ``network_cli`` or ``netconf``.
:ansible_user: The user to connect to the remote device (switch) as. Without this the user that is running ``ansible-playbook`` would be used.
  Specifies which user on the network device the connection
:ansible_ssh_pass:
  The corresponding password for ``ansible_user`` to log in as. If not specified SSH key will be used.
:ansible_become:
  If enable mode (privilege mode) should be used, see the next section.
:ansible_become_method:
  Which type of `become` should be used, for ``network_cli`` the only valid choice is ``enable``.

Privilege escalation
^^^^^^^^^^^^^^^^^^^^

Certain network platforms, such as eos and ios, have the concept of different privilege modes. Certain network modules, such as those that modify system state including users, will only work in high privilege states. Ansible version 2.5 added support for ``become`` when using ``connection: network_cli``. This allows privileges to be raised for the specific tasks that need them. Adding ``become: yes`` and ``become_method: enable`` informs Ansible to go into privilege mode before executing the task, as shown here:

.. code-block:: ini

   [eos:vars]
   ansible_connection=network_cli
   ansible_network_os=eos
   ansible_become=yes
   ansible_become_method=enable

For more information, see the :ref:`using become with network modules<become-network>` guide.


Jump hosts
^^^^^^^^^^

If the Ansible Controller doesn't have a direct route to the remote device and you need to use a Jump Host, please see the :ref:`Ansible Network Proxy Command <network_delegate_to_vs_ProxyCommand>` guide for details on how to achieve this.

Playbook
--------

Collect data
^^^^^^^^^^^^

Ansible facts modules gather system information 'facts' that are available to the rest of your playbook.

Ansible Networking ships with a number of network-specific facts modules. In this example, we use the ``_facts`` modules :ref:`eos_facts <eos_facts_module>`, :ref:`ios_facts <ios_facts_module>` and :ref:`vyos_facts <vyos_facts_module>` to connect to the remote networking device. As the credentials are not explicitly passed via module arguments, Ansible uses the username and password from the inventory file.

Ansible's "Network Fact modules" gather information from the system and store the results in facts prefixed with ``ansible_net_``. The data collected by these modules is documented in the `Return Values` section of the module docs, in this case :ref:`eos_facts <eos_facts_module>` and :ref:`vyos_facts <vyos_facts_module>`. We can use the facts, such as ``ansible_net_version`` late on in the "Display some facts" task.

To ensure we call the correct mode (``*_facts``) the task is conditionally run based on the group defined in the inventory file, for more information on the use of conditionals in Ansible Playbooks see :ref:`the_when_statement`.


Example
=======

In this example, we will create an inventory file containing some network switches, then run a playbook to connect to the network devices and return some information about them.

**Create an inventory file**

First, create a file called ``inventory``, containing:

.. code-block:: ini

   [switches:children]
   eos
   ios
   vyos

   [eos]
   eos01.example.net

   [ios]
   ios01.example.net

   [vyos]
   vyos01.example.net


**Create a playbook**

Next, create a playbook file called ``facts-demo.yml`` containing the following:

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
         when: ansible_network_os == 'eos'

       - name: Gather facts (ops)
         ios_facts:
         when: ansible_network_os == 'ios'

       - name: Gather facts (vyos)
         vyos_facts:
         when: ansible_network_os == 'vyos'

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
               Hostname: {{ hostvars[host].ansible_net_hostname }}
               Version: {{ hostvars[host].ansible_net_version }}
               Model: {{ hostvars[host].ansible_net_model }}
               Serial: {{ hostvars[host].ansible_net_serialnum }}
               {% endfor %}

             IOS device info:
               {% for host in groups['ios'] %}
               Hostname: {{ hostvars[host].ansible_net_hostname }}
               Version: {{ hostvars[host].ansible_net_version }}
               Model: {{ hostvars[host].ansible_net_model }}
               Serial: {{ hostvars[host].ansible_net_serialnum }}
               {% endfor %}

             VyOS device info:
               {% for host in groups['vyos'] %}
               Hostname: {{ hostvars[host].ansible_net_hostname }}
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
         register: backup_eos_location
         when: ansible_network_os == 'eos'

       - name: backup switch (vyos)
         vyos_config:
           backup: yes
         register: backup_vyos_location
         when: ansible_network_os == 'vyos'

       - name: Create backup dir
         file:
           path: "/tmp/backups/{{ inventory_hostname }}"
           state: directory
           recurse: yes

       - name: Copy backup files into /tmp/backups/ (eos)
         copy:
           src: "{{ backup_eos_location.backup_path }}"
           dest: "/tmp/backups/{{ inventory_hostname }}/{{ inventory_hostname }}.bck"
         when: ansible_network_os == 'eos'

       - name: Copy backup files into /tmp/backups/ (vyos)
         copy:
           src: "{{ backup_vyos_location.backup_path }}"
           dest: "/tmp/backups/{{ inventory_hostname }}/{{ inventory_hostname }}.bck"
         when: ansible_network_os == 'vyos'

Running the playbook
--------------------

To run the playbook, run the following from a console prompt:

.. code-block:: console

   ansible-playbook -i inventory facts-demo.yml

This should return output similar to the following:

.. code-block:: console

   PLAY RECAP
   eos01.example.net          : ok=7    changed=2    unreachable=0    failed=0
   ios01.example.net          : ok=7    changed=2    unreachable=0    failed=0
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

The :ref:`eos_config <eos_config_module>` and :ref:`vyos_config <vyos_config_module>` modules have a ``backup:`` option that when set will cause the module to create a full backup of the current ``running-config`` from the remote device before any changes are made. The backup file is written to the ``backup`` folder in the playbook root directory. If the directory does not exist, it is created.

To demonstrate how we can move the backup file to a different location, we register the result and move the file to the path stored in ``backup_path``.

Note that when using variables from tasks in this way we use double quotes (``"``) and double curly-brackets (``{{...}}`` to tell Ansible that this is a variable.

Troubleshooting
===============

If you receive an connection error please double check the inventory and Playbook for typos or missing lines. If the issue still occurs follow the debug steps in :doc:`network_debug_troubleshooting`.

.. seealso::

  * :ref:`network_guide`
  * :doc:`../../user_guide/intro_inventory`
  * :ref:`Vault best practices <best_practices_for_variables_and_vaults>`




