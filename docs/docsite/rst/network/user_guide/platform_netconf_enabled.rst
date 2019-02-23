.. _netconf_enabled_platform_options:

***************************************
Netconf enabled Platform Options
***************************************

This page offers details on how the netconf connection works in Ansible and how to use it.

.. contents:: Topics

Connections Available
================================================================================

+----------------------------+----------------------------------------------------------------------------------------------------+
| |                          | | NETCONF                                                                                          |
| |                          | | * all modules except ``junos_netconf``, which enables NETCONF                                    |
+============================+====================================================================================================+
| **Protocol**               | XML over SSH                                                                                       |
+----------------------------+----------------------------------------------------------------------------------------------------+
| | **Credentials**          | | uses SSH keys / SSH-agent if present                                                             |
| |                          | | accepts ``-u myuser -k`` if using password                                                       |
+----------------------------+----------------------------------------------------------------------------------------------------+
| **Indirect Access**        | via a bastion (jump host)                                                                          |
+----------------------------+----------------------------------------------------------------------------------------------------+
| **Connection Settings**    |   ``ansible_connection: netconf``                                                                  |
+----------------------------+----------------------------------------------------------------------------------------------------+

For legacy playbooks, Ansible still supports ``ansible_connection=local`` for the netconf_config module only. We recommend modernizing to use ``ansible_connection=netconf`` as soon as possible.

Using NETCONF in Ansible
========================

Enabling NETCONF
----------------

Before you can use NETCONF to connect to a switch, you must:

- install the ``ncclient`` Python package on your control node(s) with ``pip install ncclient``
- enable NETCONF on the Junos OS device(s)

To enable NETCONF on a new switch via Ansible, use the platform specific module via the CLI connection or set it manually.
For example set up your platform-level variables just like in the CLI example above, then run a playbook task like this:

.. code-block:: yaml

   - name: Enable NETCONF
     connection: network_cli
     junos_netconf:
     when: ansible_network_os == 'junos'

Once NETCONF is enabled, change your variables to use the NETCONF connection.

Example NETCONF inventory ``[junos:vars]``
------------------------------------------

.. code-block:: yaml

   [junos:vars]
   ansible_connection=netconf
   ansible_network_os=junos
   ansible_user=myuser
   ansible_password=!vault |


Example NETCONF Task
--------------------

.. code-block:: yaml

   - name: Backup current switch config
     netconf_config:
       backup: yes
     register: backup_junos_location

Example NETCONF Task with configurable variables
------------------------------------------------

.. code-block:: yaml

   - name: configure interface while providing different private key file path
     netconf_config:
       backup: yes
     register: backup_junos_location
     vars:
       ansible_private_key_file: /home/admin/.ssh/newprivatekeyfile

Note: For nectonf connection plugin configurable variables .. _Refer: https://docs.ansible.com/ansible/latest/plugins/connection/netconf.html

.. include:: shared_snippets/SSH_warning.txt
