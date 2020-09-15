.. _dellos10_platform_options:

***************************************
Dell OS10 Platform Options
***************************************

OS10 supports Enable Mode (Privilege Escalation). This page offers details on how to use Enable Mode on OS10 in Ansible.

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

    |enable_mode|         supported: use ``ansible_become: yes``
                          with ``ansible_become_method: enable``
                          and ``ansible_become_password:``

    Returned Data Format  ``stdout[0].``
    ====================  ==========================================

.. |enable_mode| replace:: Enable Mode |br| (Privilege Escalation)

For legacy playbooks, OS10 still supports ``ansible_connection: local``. We recommend modernizing to use ``ansible_connection: network_cli`` as soon as possible.

Using CLI in Ansible
================================================================================

Example CLI ``group_vars/dellos10.yml``
---------------------------------------

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: dellos10
   ansible_user: myuser
   ansible_password: !vault...
   ansible_become: yes
   ansible_become_method: enable
   ansible_become_password: !vault...
   ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI Task
----------------

.. code-block:: yaml

   - name: Backup current switch config (dellos10)
     dellos10_config:
       backup: yes
     register: backup_dellos10_location
     when: ansible_network_os == 'dellos10'

.. include:: shared_snippets/SSH_warning.txt
