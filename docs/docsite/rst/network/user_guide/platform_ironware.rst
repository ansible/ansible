.. _ironware_platform_options:

***************************************
IronWare Platform Options
***************************************

IronWare supports Enable Mode (Privilege Escalation). This page offers details on how to use Enable Mode on IronWare in Ansible 2.7. 

.. contents:: Topics

Connections Available
================================================================================

+---------------------------+-----------------------------------------------+
|..                         | CLI                                           |
+===========================+===============================================+
| **Protocol**              |  SSH                                          |
+---------------------------+-----------------------------------------------+
| | **Credentials**         | | uses SSH keys / SSH-agent if present        |
| |                         | | accepts ``-u myuser -k`` if using password  |
+---------------------------+-----------------------------------------------+
| **Indirect Access**       | via a bastion (jump host)                     |
+---------------------------+-----------------------------------------------+
| | **Connection Settings** | | ``ansible_connection: network_cli``         |
| |                         | |                                             |
| |                         | |                                             |
+---------------------------+-----------------------------------------------+
| | **Enable Mode**         | | supported - use ``ansible_become: yes``     |
| | (Privilege Escalation)  | | with ``ansible_become_method: enable``      |
| |                         | | and ``ansible_become_pass:``                |
+---------------------------+-----------------------------------------------+
| **Returned Data Format**  | ``stdout[0].``                                |
+---------------------------+-----------------------------------------------+

For legacy playbooks, IronWare still supports ``ansible_connection: local``. We recommend modernizing to use ``ansible_connection: network_cli`` as soon as possible.

Using CLI in Ansible 2.6
================================================================================

Example CLI ``group_vars/mlx.yml``
----------------------------------

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: ironware
   ansible_user: myuser
   ansible_ssh_pass: !vault...
   ansible_become: yes
   ansible_become_method: enable
   ansible_become_pass: !vault...
   ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_ssh_pass`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI Task
----------------

.. code-block:: yaml

   - name: Backup current switch config (ironware)
     ironware_config:
       backup: yes
     register: backup_ironware_location
     when: ansible_network_os == 'ironware'

.. include:: shared_snippets/SSH_warning.txt
