.. _vyos_platform_options:

***************************************
VyOS Platform Options
***************************************

This page offers details on connection options to manage VyOS using Ansible.

.. contents:: Topics

Connections Available
================================================================================

.. table::
    :class: documentation-table

    ====================  ==========================================
    ..                    CLI
    ====================  ==========================================
    Protocol              SSH

    Credentials           uses SSH keys / SSH-agent if present

                          accepts ``-u myuser -k`` if using password

    Indirect Access       via a bastion (jump host)

    Connection Settings   ``ansible_connection: network_cli``

    |enable_mode|         not supported                               

    Returned Data Format  Refer to individual module documentation 
    ====================  ==========================================

.. |enable_mode| replace:: Enable Mode |br| (Privilege Escalation)


For legacy playbooks, VyOS still supports ``ansible_connection: local``. We recommend modernizing to use ``ansible_connection: network_cli`` as soon as possible.

Using CLI in Ansible
====================

Example CLI ``group_vars/vyos.yml``
-----------------------------------

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: vyos
   ansible_user: myuser
   ansible_password: !vault...
   ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI Task
----------------

.. code-block:: yaml

   - name: Retrieve VyOS version info
     vyos_command:
       commands: show version
     when: ansible_network_os == 'vyos'

.. include:: shared_snippets/SSH_warning.txt
