***************************************
Basic Concepts
***************************************

These concepts are common to all uses of Ansible, including network automation. You need to understand them to use Ansible for network automation. This basic introduction provides the background you need to follow the examples in this guide.

.. contents:: Topics

Control Node
================================================================================

Any machine with Ansible installed. You can run commands and playbooks, invoking ``/usr/bin/ansible`` or ``/usr/bin/ansible-playbook``, from any control node. You can use any computer that has Python installed on it as a control node - laptops, shared desktops, and servers can all run Ansible. However, you cannot use a Windows machine as a control node. You can have multiple control nodes.

Managed Nodes
================================================================================

The network devices (and/or servers) you manage with Ansible. Managed nodes are also sometimes called "hosts". Ansible is not installed on managed nodes.

Inventory
================================================================================

A list of managed nodes. An inventory file is also sometimes called a "hostfile". Your inventory can specify information like IP address for each managed node. An inventory can also organize managed nodes, creating and nesting groups for easier scaling. To learn more about inventory, see :doc:`the Working with Inventory<../../user_guide/intro_inventory>` pages.

Modules
================================================================================

The units of code Ansible executes. Each module has a particular use, from administering users on a specific type of database to managing VLAN interfaces on a specific type of network device. You can invoke a single module with a task, or invoke several different modules in a playbook. For an idea of how many modules Ansible includes, take a look at the :doc:`list of all modules<../../modules/modules_by_category>` or the :doc:`list of network modules<../../modules/list_of_network_modules>`.

Tasks
================================================================================

The units of action in Ansible. You can execute a single task once with an ad-hoc command. 

Playbooks
================================================================================

Ordered lists of tasks, saved so you can run those tasks in that order repeatedly. Playbooks can include variables as well as tasks. Playbooks are written in YAML and are easy to read, write, share and understand. To learn more about playbooks, see :doc:`../../user_guide/playbooks_intro`.
