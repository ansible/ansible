.. _qnos_platform_options:

***************************************
QNOS Platform Options
***************************************

QNOS supports Enable Mode (Privilege Escalation). This page offers details on how to use Enable Mode on QNOS in Ansible.

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
| |                         | | and ``ansible_become_password:``            |
+---------------------------+-----------------------------------------------+
| **Returned Data Format**  | ``stdout[0].``                                |
+---------------------------+-----------------------------------------------+


Using CLI in Ansible
====================

Example CLI ``group_vars/qnos.yml``
-----------------------------------

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: qnos
   ansible_user: myuser
   ansible_password: !vault...


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Options
-------
- See L(cli_command module,../../modules/cli_command_module.html).
- See L(cli_config module,../../modules/cli_config_module.html).


Example CLI Task
----------------

.. code-block:: yaml

   - name: setup
     cli_config:
       config: 
         hostname rdserver
 
   - name: get hostname
     cli_command:
       command: show running-config | include hostname
     register: result
 
   - assert:
       that:
        - result.stdout.find('rdserver') != -1
 
.. include:: shared_snippets/SSH_warning.txt
