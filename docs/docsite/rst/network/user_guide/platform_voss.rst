.. _voss_platform_options:

***************************************
VOSS Platform Options
***************************************

Extreme VOSS Ansible modules only support CLI connections today. This page offers details on how to
use ``network_cli`` on VOSS in Ansible >= 2.7.

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
| |                         | |                                             |
| |                         | |                                             |
+---------------------------+-----------------------------------------------+
| | **Enable Mode**         | | supported - use ``ansible_become: yes``     |
| | (Privilege Escalation)  | | with ``ansible_become_method: enable``      |
+---------------------------+-----------------------------------------------+
| **Returned Data Format**  | ``stdout[0].``                                |
+---------------------------+-----------------------------------------------+

VOSS does not support ``ansible_connection: local``. You must use ``ansible_connection: network_cli``.

Using CLI in Ansible >= 2.7
================================================================================

Example CLI ``group_vars/voss.yml``
-----------------------------------

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: voss
   ansible_user: myuser
   ansible_become: yes
   ansible_become_method: enable
   ansible_ssh_pass: !vault...
   ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_ssh_pass`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI Task
----------------

.. code-block:: yaml

   - name: Retrieve VOSS info
     voss_command:
       commands: show sys-info
     when: ansible_network_os == 'voss'

.. include:: shared_snippets/SSH_warning.txt
