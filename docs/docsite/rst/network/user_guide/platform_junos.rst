.. _junos_platform_options:

***************************************
Junos OS Platform Options
***************************************

Juniper Junos OS supports multiple connections. This page offers details on how each connection works in Ansible 2.6 and how to use it. 

.. contents:: Topics

Connections Available
================================================================================

+----------------------------+--------------------------------------------------------+----------------------------------------------------------------------------------------------------+
| |                          | | CLI                                                  | | NETCONF                                                                                          |
| |                          | | * ``junos_netconf`` & ``junos_command`` modules only | | * all modules except ``junos_netconf``, which enables NETCONF                                    |
+============================+========================================================+====================================================================================================+
| **Protocol**               | SSH                                                    | XML over SSH                                                                                       |
+----------------------------+--------------------------------------------------------+----------------------------------------------------------------------------------------------------+
| | **Credentials**          | | uses SSH keys / SSH-agent if present                 | | uses SSH keys / SSH-agent if present                                                             |
| |                          | | accepts ``-u myuser -k`` if using password           | | accepts ``-u myuser -k`` if using password                                                       |
+----------------------------+--------------------------------------------------------+----------------------------------------------------------------------------------------------------+
| **Indirect Access**        | via a bastion (jump host)                              | via a bastion (jump host)                                                                          |
+----------------------------+--------------------------------------------------------+----------------------------------------------------------------------------------------------------+
| **Connection Settings**    |   ``ansible_connection: network_cli``                  |   ``ansible_connection: netconf``                                                                  |
+----------------------------+--------------------------------------------------------+----------------------------------------------------------------------------------------------------+
| | **Enable Mode**          | | not supported by Junos OS                            | | not supported by Junos OS                                                                        |
| | (Privilege Escalation)   | |                                                      | |                                                                                                  |
+----------------------------+--------------------------------------------------------+----------------------------------------------------------------------------------------------------+
| | **Returned Data Format** | | ``stdout[0].``                                       | | json: ``result[0]['software-information'][0]['host-name'][0]['data'] foo lo0``                   |
| |                          | |                                                      | | text: ``result[1].interface-information[0].physical-interface[0].name[0].data foo lo0``          |
| |                          | |                                                      | | xml: ``result[1].rpc-reply.interface-information[0].physical-interface[0].name[0].data foo lo0`` |
+----------------------------+--------------------------------------------------------+----------------------------------------------------------------------------------------------------+

For legacy playbooks, Ansible still supports ``ansible_connection=local`` on all JUNOS modules. We recommend modernizing to use ``ansible_connection=netconf`` or ``ansible_connection=network_cli`` as soon as possible.

Using CLI in Ansible 2.6
================================================================================

Example CLI inventory ``[junos:vars]``
--------------------------------------

.. code-block:: yaml

   [junos:vars]
   ansible_connection=network_cli
   ansible_network_os=junos
   ansible_user=myuser
   ansible_ssh_pass=!vault...
   ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_ssh_pass`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI Task
----------------

.. code-block:: yaml

   - name: Retrieve Junos OS version
     junos_command:
       commands: show version
     when: ansible_network_os == 'junos'


Using NETCONF in Ansible 2.6
================================================================================

Enabling NETCONF
----------------

Before you can use NETCONF to connect to a switch, you must:

- install the ``ncclient`` python package on your control node(s) with ``pip install ncclient``
- enable NETCONF on the Junos OS device(s)

To enable NETCONF on a new switch via Ansible, use the ``junos_netconf`` module via the CLI connection. Set up your platform-level variables just like in the CLI example above, then run a playbook task like this:

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
   ansible_ssh_pass=!vault | 
   ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


Example NETCONF Task
--------------------

.. code-block:: yaml

   - name: Backup current switch config (junos)
     junos_config:
       backup: yes
     register: backup_junos_location
     when: ansible_network_os == 'junos'


.. include:: shared_snippets/SSH_warning.txt
