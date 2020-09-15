.. _iosxr_platform_options:

***************************************
IOS-XR Platform Options
***************************************

IOS-XR supports multiple connections. This page offers details on how each connection works in Ansible and how to use it.

.. contents:: Topic

Connections Available
================================================================================

.. table::
    :class: documentation-table

    ====================  ==========================================  =========================
    ..                    CLI                                         NETCONF

                                                                      only for modules ``iosxr_banner``, 
                                                                      ``iosxr_interface``, ``iosxr_logging``, 
                                                                      ``iosxr_system``, ``iosxr_user``
    ====================  ==========================================  =========================
    Protocol              SSH                                         XML over SSH

    Credentials           uses SSH keys / SSH-agent if present        uses SSH keys / SSH-agent if present

                          accepts ``-u myuser -k`` if using password  accepts ``-u myuser -k`` if using password

    Indirect Access       via a bastion (jump host)                   via a bastion (jump host)

    Connection Settings   ``ansible_connection: network_cli``         ``ansible_connection: netconf``

    |enable_mode|         not supported                               not supported

    Returned Data Format  Refer to individual module documentation    Refer to individual module documentation
    ====================  ==========================================  =========================

.. |enable_mode| replace:: Enable Mode |br| (Privilege Escalation)


For legacy playbooks, Ansible still supports ``ansible_connection=local`` on all IOS-XR modules. We recommend modernizing to use ``ansible_connection=netconf`` or ``ansible_connection=network_cli`` as soon as possible.

Using CLI in Ansible
====================

Example CLI inventory ``[iosxr:vars]``
--------------------------------------

.. code-block:: yaml

   [iosxr:vars]
   ansible_connection=network_cli
   ansible_network_os=iosxr
   ansible_user=myuser
   ansible_password=!vault...
   ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI Task
----------------

.. code-block:: yaml

   - name: Retrieve IOS-XR version
     iosxr_command:
       commands: show version
     when: ansible_network_os == 'iosxr'


Using NETCONF in Ansible
========================

Enabling NETCONF
----------------

Before you can use NETCONF to connect to a switch, you must:

- install the ``ncclient`` python package on your control node(s) with ``pip install ncclient``
- enable NETCONF on the Cisco IOS-XR device(s)

To enable NETCONF on a new switch via Ansible, use the ``iosxr_netconf`` module via the CLI connection. Set up your platform-level variables just like in the CLI example above, then run a playbook task like this:

.. code-block:: yaml

   - name: Enable NETCONF
     connection: network_cli
     iosxr_netconf:
     when: ansible_network_os == 'iosxr'

Once NETCONF is enabled, change your variables to use the NETCONF connection.

Example NETCONF inventory ``[iosxr:vars]``
------------------------------------------

.. code-block:: yaml

   [iosxr:vars]
   ansible_connection=netconf
   ansible_network_os=iosxr
   ansible_user=myuser
   ansible_password=!vault |
   ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


Example NETCONF Task
--------------------

.. code-block:: yaml

   - name: Configure hostname and domain-name
     iosxr_system:
       hostname: iosxr01
       domain_name: test.example.com
       domain_search:
         - ansible.com
         - redhat.com
         - cisco.com

.. include:: shared_snippets/SSH_warning.txt