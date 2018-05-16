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
   :header: "Value of ansible_connection", "Protocol", "Requires"
   :widths: 30, 10, 10

   "network_cli", "CLI over SSH", "network_os setting"
   "netconf", "XML over SSH", "network_os setting"
   "httpapi", "API over HTTP/HTTPS", "network_os setting"

Beginning with Ansible 2.6, we recommend updating all plays and tasks that use ``ansible_connection: local`` to use one of the persistent connection types listed above. For more details on using each connection type on various platforms, see the :ref:`platform-specific <platform_options>` pages.


Modules Organized by Network Platform
================================================================================

A network platform is a set of network devices with a common operating system that can be managed by a collection of modules.  The modules for each network platform share a prefix, for example: 

- Arista: ``eos_``
- Cisco: ``ios_``, ``iosxr_``, ``nxos_``
- Juniper: ``junos_``
- VyOS ``vyos_``

All modules within a network platform share certain requirements. Some network platforms have specific differences - see the :ref:`platform-specific <platform_options>` documentation for details.


Privilege Escalation: ``enable`` mode and ``become``
================================================================================

Several network platforms support privilege escalation, where certain tasks must be done by a privileged user. On network devices this is generally known as ``enable`` mode (the equivalent of ``sudo`` in \*nix administration). Ansible network modules offer privilege escalation for those network devices that support it. 

As of Ansible 2.6, you can use the top-level Ansible parameter ``become: yes`` with ``become_method: enable`` to run a task, play, or playbook with escalated privileges on any network platform that supports privilege escalation. 

Network platforms that support ``connection: network_cli`` and privilege escalation use the top-level Ansible parameter ``become: yes`` with ``become_method: enable``. If you are using ``network_cli`` to connect Ansible to your network devices, a ``group_vars`` file would look like:

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: ios
   ansible_become: yes
   ansible_become_method: enable

If you are running an older version of Ansible, some network platforms support privilege escalation but not ``network_cli`` or ``httpapi`` connections. This includes all platforms in versions 2.4 and older, and HTTPS connections using ``eapi`` in version 2.5. Ansible recommends you upgrade to version 2.6 as soon as possible.

For more information, see :ref:`Become and Networks<become-network>`
