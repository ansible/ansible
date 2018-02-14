Network Getting Started: How Network Automation is Different
================================================================

Network automation leverages the basic Ansible concepts, but there are important differences in how the network modules work. This introduction prepares you to understand the exercises in this guide.

Execution on the Control Node 
```````````````````````````````````````````````````````````````

Unlike most Ansible modules, network modules do not run on the managed nodes. On the front end, network modules work with ad-hoc commands, playbooks, and roles. Behind the scenes, however, network modules use a different methodology than the other (Linux/Unix and Windows) modules use. Ansible is written and executed in Python. Because the majority of network devices can not run Python, the Ansible network modules are executed on the Ansible control node. 

Execution on the control node shapes two other differences in how network modules function:

- Network modules do not run every task in a playbook. They request current config first, compare current config to the state described by the task or playbook, and execute a task only if it changes the state of the managed node.

- Network modules that offer a backup option write the backup files onto the control node. With Linux/Unix modules, where a configuration file already exists on the managed node(s), the backup file gets written by default in the same directory as the new, changed file. Network modules do not update configuration files on the managed nodes, because network configuration is not written in files. Network modules write backup files on the control node, in the `backup` directory under the playbook root directory.

Multiple Communication Protocols
```````````````````````````````````````````````````````````````

Because they execute on the control node instead of on the managed nodes, network modules can support multiple communication protocols. The communication protocol (XML over SSH, CLI over SSH, API over HTTPS) selected for each network module depends on the platform and the purpose of the module. Some network modules support only one protocol; some offer a choice. The most common protocol is CLI over SSH. You set the communication protocol with the ``ansible_connection`` variable:

.. csv-table::
   :header: "Value of ansible_connection", "Protocol", "Requires"
   :widths: 30, 10, 10

   "network_cli", "CLI over SSH", "network_os setting"
   "netconf", "XML over SSH", "network_os setting"
   "local", "depends on provider", "provider setting"


Modules Organized by Network Platform
```````````````````````````````````````````````````````````````

A network platform is a set of network devices with a common operating system that can be managed by a collection of modules.  The modules for each network platform share a prefix, for example: eos_ (Arista), ios_, iosxr_, nxos_ (Cisco), junos_ (Juniper), vyos_ (VyOS). All modules within a network platform share certain requirements. Some network platforms have specific differences - see the platform-specific documentation for details.

