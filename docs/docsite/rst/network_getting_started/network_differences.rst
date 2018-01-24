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

Because they execute on the control node instead of on the managed nodes, network modules can support multiple communication protocols. The communication protocol (SSH, HTTPS) selected for each network module depends on the platform and the purpose of the module. Some network modules support only one protocol; some offer a choice. The most common protocol is SSH. The :doc:`module_docs/list_of_network_modules` detail which modules support which protocols. The communication protocol is determined by the value of the `ansible_connection` variable:

ansible_connection setting		communication protocol
local							SSH


Network Platforms
```````````````````````````````````````````````````````````````

Network modules are organized by platforms. A network platform is a set of network devices with a common operating system that can be managed by a collection of modules. The modules for each network platform share a prefix, for example: eos_ (Arista), ios_, iosxr_, nxos_ (Cisco), junos_ (Junpier), vyos_ (VyOS). Some network platforms have specific differences - see the platform-specific documentation for details.

Conditional Comparison in Network Modules
```````````````````````````````````````````````````````````````

Conditional statements in Ansible evaluate the output from a managed node to determine what happens next in a playbook. Linux/Unix and Windows modules use mathematical symbols (for example, `==`, `<`, and `>`) for comparison. However, network modules use different conditional comparisons. The conditional tests for network modules are:

- eq - Equal
- neq - Not equal
- gt - Greater than
- ge - Greater than or equal
- lt - Less than
- le - Less than or equal
- contains - Object contains specified item
