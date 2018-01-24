Network Getting Started: Working with Inventory
===============================================

A fully-featured inventory file can serve as the source of truth for your network. Using an inventory file, a single playbook can maintain hundreds of network devices with a single command. This page shows you how to build an inventory file, step by step.

First, group your devices by OS and/or by function. You can group groups using the syntax `metagroupname:children` and listing groups as members of the metagroup. In this tiny example data center, the group `network` includes all leafs and all spines; the group `datacenter` includes all network devices plus all webservers.

.. code-block:: yaml

   [leafs]
   leaf01
   leaf02

   [spines]
   spine01
   spine02

   [network:children]
   leafs
   spines

   [webservers]
   webserver01
   webserver02

   [datacenter:children]
   leafs
   spines
   webservers


Next, you can set values for many of the variables you needed in your first Ansible command in the inventory, so you can skip them in the ansible-playbook command. In this example, the inventory includes each network device's IP, OS, and SSH user. If your network devices are only accessible by IP, you must add the IP to the inventory file. If you access your network devices using hostnames, the IP isn't necessary. In an inventory file you **must** use the syntax `key=value` for variable values.

.. code-block:: yaml

[leafs]
leaf01 ansible_host=10.16.10.11 ansible_network_os=vyos ansible_user=my_vyos_user
leaf02 ansible_host=10.16.10.12 ansible_network_os=vyos ansible_user=my_vyos_user

[spines]
spine01 ansible_host=10.16.10.13 ansible_network_os=vyos ansible_user=my_vyos_user
spine02 ansible_host=10.16.10.14 ansible_network_os=vyos ansible_user=my_vyos_user

[network:children]
leafs
spines

[servers]
server01 ansible_host=10.16.10.15 ansible_user=my_server_user
server02 ansible_host=10.16.10.16 ansible_user=my_server_user

[datacenter:children]
leafs
spines
servers

When devices in a group share the same variable values, such as OS or SSH user, you can reduce duplication and simplify maintenance by consolidating these into group variables:

.. code-block:: yaml

[leafs]
leaf01 ansible_host=10.16.10.11
leaf02 ansible_host=10.16.10.12

[leafs:vars]
ansible_network_os=vyos
ansible_user=my_vyos_user

[spines]
spine01 ansible_host=10.16.10.13
spine02 ansible_host=10.16.10.14

[spines:vars]
ansible_network_os=vyos
ansible_user=my_vyos_user

[network:children]
leafs
spines

[servers]
server01 ansible_host=10.16.10.15
server02 ansible_host=10.16.10.16

[datacenter:children]
leafs
spines
servers


As your inventory file grows, you can ease maintenance by moving the `vars` sections into YAML files of their own, called `group_vars` - this is highly recommended. Name each group_vars file after the group it describes and save it in a directory called `group_vars`. In this case, you would create a file called `group_vars/leafs` and another called `group_vars/spines`. For more details on building inventory files, see :doc:`the introduction to inventory<../intro_inventory>`.