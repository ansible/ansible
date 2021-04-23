.. _weos4_platform_options:

***************************************
WeOS 4 Platform Options
***************************************

Westermo WeOS 4 is part of the `community.network <https://galaxy.ansible.com/community/network>`_ collection and only supports CLI connections.
This page offers details on how to use ``ansible.netcommon.network_cli`` on WeOS 4 in Ansible.

.. contents::
  :local:

Connections available
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

    Connection Settings   ``ansible_connection: community.netcommon.network_cli``

    |enable_mode|         not supported by WeOS 4

    Returned Data Format  ``stdout[0].``
    ====================  ==========================================

.. |enable_mode| replace:: Enable Mode |br| (Privilege Escalation)

WeOS 4 does not support ``ansible_connection: local``. You must use ``ansible_connection: ansible.netcommon.network_cli``.

Using CLI in Ansible
====================

Example CLI ``group_vars/weos4.yml``
------------------------------------

.. code-block:: yaml

   ansible_connection: ansible.netcommon.network_cli
   ansible_network_os: community.network.weos4
   ansible_user: myuser
   ansible_password: !vault...
   ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI task
----------------

.. code-block:: yaml

   - name: Get version information (WeOS 4)
     ansible.netcommon.cli_command:
       commands: "show version"
     register: show_ver
     when: ansible_network_os == 'community.network.weos4'

Example Configuration task
--------------------------

.. code-block:: yaml

   - name: Replace configuration with file on ansible host (WeOS 4)
     ansible.netcommon.cli_config:
       config: "{{ lookup('file', 'westermo.conf') }}"
       replace: "yes"
       diff_match: exact
       diff_replace: config
     when: ansible_network_os == 'community.network.weos4'

.. include:: shared_snippets/SSH_warning.txt

.. seealso::

       :ref:`timeout_options`
