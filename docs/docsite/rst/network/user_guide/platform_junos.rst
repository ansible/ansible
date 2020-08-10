.. _junos_platform_options:

***************************************
Junos OS Platform Options
***************************************

The `Juniper Junos OS <https://galaxy.ansible.com/junipernetworks/junos>`_ supports multiple connections. This page offers details on how each connection works in Ansible and how to use it.

.. contents::
  :local:

Connections available
================================================================================

.. table::
    :class: documentation-table

    ====================  ==========================================  =========================
    ..                    CLI                                         NETCONF

                          ``junos_netconf`` & ``junos_command``       all modules except ``junos_netconf``,
                          modules only                                which enables NETCONF
    ====================  ==========================================  =========================
    Protocol              SSH                                         XML over SSH

    Credentials           uses SSH keys / SSH-agent if present        uses SSH keys / SSH-agent if present

                          accepts ``-u myuser -k`` if using password  accepts ``-u myuser -k`` if using password

    Indirect Access       via a bastion (jump host)                   via a bastion (jump host)

    Connection Settings   ``ansible_connection:                       ``ansible_connection:
                          ``ansible.netcommon.network_cli``           ``ansible.netcommon.netconf``

    |enable_mode|         not supported by Junos OS                   not supported by Junos OS

    Returned Data Format  ``stdout[0].``                              * json: ``result[0]['software-information'][0]['host-name'][0]['data'] foo lo0``
                                                                      * text: ``result[1].interface-information[0].physical-interface[0].name[0].data foo lo0``
                                                                      * xml: ``result[1].rpc-reply.interface-information[0].physical-interface[0].name[0].data foo lo0``
    ====================  ==========================================  =========================

.. |enable_mode| replace:: Enable Mode |br| (Privilege Escalation)


The ``ansible_connection: local`` has been deprecated. Please use ``ansible_connection: ansible.netcommon.network_cli`` or ``ansible_connection: ansible.netcommon.netconf`` instead.

Using CLI in Ansible
====================

Example CLI inventory ``[junos:vars]``
--------------------------------------

.. code-block:: yaml

   [junos:vars]
   ansible_connection=ansible.netcommon.network_cli
   ansible_network_os=junipernetworks.junos.junos
   ansible_user=myuser
   ansible_password=!vault...
   ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI task
----------------

.. code-block:: yaml

   - name: Retrieve Junos OS version
     junipernetworks.junos.junos_command:
       commands: show version
     when: ansible_network_os == 'junipernetworks.junos.junos'


Using NETCONF in Ansible
========================

Enabling NETCONF
----------------

Before you can use NETCONF to connect to a switch, you must:

- install the ``ncclient`` python package on your control node(s) with ``pip install ncclient``
- enable NETCONF on the Junos OS device(s)

To enable NETCONF on a new switch via Ansible, use the ``junipernetworks.junos.junos_netconf`` module through the CLI connection. Set up your platform-level variables just like in the CLI example above, then run a playbook task like this:

.. code-block:: yaml

   - name: Enable NETCONF
     connection: ansible.netcommon.network_cli
     junipernetworks.junos.junos_netconf:
     when: ansible_network_os == 'junipernetworks.junos.junos'

Once NETCONF is enabled, change your variables to use the NETCONF connection.

Example NETCONF inventory ``[junos:vars]``
------------------------------------------

.. code-block:: yaml

   [junos:vars]
   ansible_connection=ansible.netcommon.netconf
   ansible_network_os=junipernetworks.junos.junos
   ansible_user=myuser
   ansible_password=!vault |
   ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


Example NETCONF task
--------------------

.. code-block:: yaml

   - name: Backup current switch config (junos)
     junipernetworks.junos.junos_config:
       backup: yes
     register: backup_junos_location
     when: ansible_network_os == 'junipernetworks.junos.junos'


.. include:: shared_snippets/SSH_warning.txt

.. seealso::

       :ref:`timeout_options`
