************************************************************
How Network Automation is Different
************************************************************

Network automation leverages the basic Ansible concepts, but there are important differences in how the network modules work. This introduction prepares you to understand the exercises in this guide.

.. contents:: Topics

Execution on the Control Node
================================================================================

Unlike most Ansible modules, network modules do not run on the managed nodes. From a user's point of view, network modules work like any other modules. They work with ad-hoc commands, playbooks, and roles. Behind the scenes, however, network modules use a different methodology than the other (Linux/Unix and Windows) modules use. Ansible is written and executed in Python. Because the majority of network devices can not run Python, the Ansible network modules are executed on the Ansible control node, where ``ansible`` or ``ansible-playbook`` runs. 

Network modules also use the control node as a destination for backup files, for those modules that offer a ``backup`` option. With Linux/Unix modules, where a configuration file already exists on the managed node(s), the backup file gets written by default in the same directory as the new, changed file. Network modules do not update configuration files on the managed nodes, because network configuration is not written in files. Network modules write backup files on the control node, usually in the `backup` directory under the playbook root directory.

Multiple Communication Protocols
================================================================================

Because network modules execute on the control node instead of on the managed nodes, they can support multiple communication protocols. The communication protocol (XML over SSH, CLI over SSH, API over HTTPS) selected for each network module depends on the platform and the purpose of the module. Some network modules support only one protocol; some offer a choice. The most common protocol is CLI over SSH. You set the communication protocol with the ``ansible_connection`` variable:

.. csv-table::
   :header: "Value of ansible_connection", "Protocol", "Requires", "Persistent?"
   :widths: 30, 10, 10, 10

   "network_cli", "CLI over SSH", "network_os setting", "yes"
   "netconf", "XML over SSH", "network_os setting", "yes"
   "httpapi", "API over HTTP/HTTPS", "network_os setting", "yes"
   "local", "depends on provider", "provider setting", "no"

Beginning with Ansible 2.6, we recommend using one of the persistent connection types listed above instead of ``local``. With persistent connections, you can define the hosts and credentials only once, rather than in every task. For more details on using each connection type on various platforms, see the :ref:`platform-specific <platform_options>` pages.


Modules Organized by Network Platform
================================================================================

A network platform is a set of network devices with a common operating system that can be managed by a collection of modules.  The modules for each network platform share a prefix, for example: 

- Arista: ``eos_``
- Cisco: ``ios_``, ``iosxr_``, ``nxos_``
- Juniper: ``junos_``
- VyOS ``vyos_``

All modules within a network platform share certain requirements. Some network platforms have specific differences - see the :ref:`platform-specific <platform_options>` documentation for details.


Privilege Escalation: ``enable`` mode, ``become``, and ``authorize``
================================================================================

Several network platforms support privilege escalation, where certain tasks must be done by a privileged user. On network devices this is called ``enable`` mode (the equivalent of ``sudo`` in \*nix administration). Ansible network modules offer privilege escalation for those network devices that support it. For details of which platforms support ``enable`` mode, with examples of how to use it, see the :ref:`platform-specific <platform_options>` documentation.

Using ``become`` for privilege escalation
-----------------------------------------

As of Ansible 2.6, you can use the top-level Ansible parameter ``become: yes`` with ``become_method: enable`` to run a task, play, or playbook with escalated privileges on any network platform that supports privilege escalation. You must use either ``connection: network_cli`` or ``connection: httpapi`` with ``become: yes`` with ``become_method: enable``. If you are using ``network_cli`` to connect Ansible to your network devices, a ``group_vars`` file would look like:

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: ios
   ansible_become: yes
   ansible_become_method: enable

Legacy playbooks: ``authorize`` for privilege escalation
-----------------------------------------------------------------

If you are running Ansible 2.5 or older, some network platforms support privilege escalation but not ``network_cli`` or ``httpapi`` connections. This includes all platforms in versions 2.4 and older, and HTTPS connections using ``eapi`` in version 2.5. With a ``local`` connection, you must use a ``provider`` dictionary and include ``authorize: yes`` and ``auth_pass: my_enable_password``. For that use case, a ``group_vars`` file looks like:

.. code-block:: yaml

   ansible_connection: local
   ansible_network_os: eos
   # provider settings
   eapi:
     authorize: yes
     auth_pass: " {{ secret_auth_pass }}"
     port: 80
     transport: eapi
     use_ssl: no

And you use the ``eapi`` variable in your task(s):

.. code-block:: yaml

   tasks:
   - name: provider demo with eos
     eos_banner:
       banner: motd
       text: |
         this is test
         of multiline
         string
       state: present
       provider: "{{ eapi }}"

Note that while Ansible 2.6 supports the use of ``connection: local`` with ``provider`` dictionaries, this usage will be deprecated in the future and eventually removed.

For more information, see :ref:`Become and Networks<become_network>`
