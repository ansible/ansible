.. _voss_platform_options:

***************************************
VOSS Platform Options
***************************************

Extreme VOSS is part of the `community.network <https://galaxy.ansible.com/community/network>`_ collection and only supports CLI connections today. This page offers details on how to
use ``ansible.netcommon.network_cli`` on VOSS in Ansible.

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

    Connection Settings   ``ansible_connection: ansible.netcommon.network_cli``

    |enable_mode|         supported: use ``ansible_become: yes``
                          with ``ansible_become_method: enable``

    Returned Data Format  ``stdout[0].``
    ====================  ==========================================

.. |enable_mode| replace:: Enable Mode |br| (Privilege Escalation)


VOSS does not support ``ansible_connection: local``. You must use ``ansible_connection: ansible.netcommon.network_cli``.

Using CLI in Ansible
====================

Example CLI ``group_vars/voss.yml``
-----------------------------------

.. code-block:: yaml

   ansible_connection: ansible.netcommon.network_cli
   ansible_network_os: community.network.voss
   ansible_user: myuser
   ansible_become: yes
   ansible_become_method: enable
   ansible_password: !vault...
   ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI task
----------------

.. code-block:: yaml

   - name: Retrieve VOSS info
     community.network.voss_command:
       commands: show sys-info
     when: ansible_network_os == 'community.network.voss'

.. include:: shared_snippets/SSH_warning.txt

.. seealso::

       :ref:`timeout_options`
