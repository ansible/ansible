.. _ce_platform_options:

***************************************
CloudEngine OS Platform Options
***************************************

CloudEngine CE OS is part of the `community.network <https://galaxy.ansible.com/community/network>`_ collection and supports multiple connections. This page offers details on how each connection works in Ansible and how to use it.

.. contents::
  :local:

Connections available
================================================================================

.. table::
    :class: documentation-table

    ====================  ==========================================  =========================
    ..                    CLI                                         NETCONF


    ====================  ==========================================  =========================
    Protocol              SSH                                         XML over SSH

    Credentials           uses SSH keys / SSH-agent if present        uses SSH keys / SSH-agent if present

                          accepts ``-u myuser -k`` if using password  accepts ``-u myuser -k`` if using password

    Indirect Access       via a bastion (jump host)                   via a bastion (jump host)

    Connection Settings   ``ansible_connection:``                     ``ansible_connection:``
                            ``ansible.netcommon.network_cli``           ``ansible.netcommon.netconf``

    |enable_mode|         not supported by ce OS                      not supported by ce OS

    Returned Data Format  Refer to individual module documentation    Refer to individual module documentation
    ====================  ==========================================  =========================

.. |enable_mode| replace:: Enable Mode |br| (Privilege Escalation)

The ``ansible_connection: local`` has been deprecated. Please use  ``ansible_connection: ansible.netcommon.netconf`` or ``ansible_connection=ansible.netcommon.network_cli`` instead.

Using CLI in Ansible
====================

Example CLI inventory ``[ce:vars]``
--------------------------------------

.. code-block:: yaml

   [ce:vars]
   ansible_connection=ansible.netcommon.network_cli
   ansible_network_os=community.network.ce
   ansible_user=myuser
   ansible_password=!vault...
   ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI task
----------------

.. code-block:: yaml

   - name: Retrieve CE OS version
     community.network.ce_command:
       commands: display version
     when: ansible_network_os == 'community.network.ce'


Using NETCONF in Ansible
========================

Enabling NETCONF
----------------

Before you can use NETCONF to connect to a switch, you must:

- install the ``ncclient`` python package on your control node(s) with ``pip install ncclient``
- enable NETCONF on the CloudEngine OS device(s)

To enable NETCONF on a new switch using Ansible, use the ``community.network.ce_config`` module with the CLI connection. Set up your platform-level variables just like in the CLI example above, then run a playbook task like this:

.. code-block:: yaml

   - name: Enable NETCONF
     connection: ansible.netcommon.network_cli
     community.network.ce_config:
       lines:
         - snetconf server enable
     when: ansible_network_os == 'community.network.ce'

Once NETCONF is enabled, change your variables to use the NETCONF connection.

Example NETCONF inventory ``[ce:vars]``
------------------------------------------

.. code-block:: yaml

   [ce:vars]
   ansible_connection=ansible.netcommon.netconf
   ansible_network_os=community.network.ce
   ansible_user=myuser
   ansible_password=!vault |
   ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


Example NETCONF task
--------------------

.. code-block:: yaml

   - name: Create a vlan, id is 50(ce)
     community.network.ce_vlan:
       vlan_id: 50
       name: WEB
     when: ansible_network_os == 'community.network.ce'


Notes
========================

Modules that work with ``ansible.netcommon.network_cli``
---------------------------------------------------------

.. code-block:: yaml

   community.network.ce_acl_interface
   community.network.ce_command
   community.network.ce_config
   community.network.ce_evpn_bgp
   community.network.ce_evpn_bgp_rr
   community.network.ce_evpn_global
   community.network.ce_facts
   community.network.ce_mlag_interface
   community.network.ce_mtu
   community.network.ce_netstream_aging
   community.network.ce_netstream_export
   community.network.ce_netstream_global
   community.network.ce_netstream_template
   community.network.ce_ntp_auth
   community.network.ce_rollback
   community.network.ce_snmp_contact
   community.network.ce_snmp_location
   community.network.ce_snmp_traps
   community.network.ce_startup
   community.network.ce_stp
   community.network.ce_vxlan_arp
   community.network.ce_vxlan_gateway
   community.network.ce_vxlan_global


Modules that work with ``ansible.netcommon.netconf``
-----------------------------------------------------

.. code-block:: yaml

   community.network.ce_aaa_server
   community.network.ce_aaa_server_host
   community.network.ce_acl
   community.network.ce_acl_advance
   community.network.ce_bfd_global
   community.network.ce_bfd_session
   community.network.ce_bfd_view
   community.network.ce_bgp
   community.network.ce_bgp_af
   community.network.ce_bgp_neighbor
   community.network.ce_bgp_neighbor_af
   community.network.ce_dldp
   community.network.ce_dldp_interface
   community.network.ce_eth_trunk
   community.network.ce_evpn_bd_vni
   community.network.ce_file_copy
   community.network.ce_info_center_debug
   community.network.ce_info_center_global
   community.network.ce_info_center_log
   community.network.ce_info_center_trap
   community.network.ce_interface
   community.network.ce_interface_ospf
   community.network.ce_ip_interface
   community.network.ce_lacp
   community.network.ce_link_status
   community.network.ce_lldp
   community.network.ce_lldp_interface
   community.network.ce_mlag_config
   community.network.ce_netconf
   community.network.ce_ntp
   community.network.ce_ospf
   community.network.ce_ospf_vrf
   community.network.ce_reboot
   community.network.ce_sflow
   community.network.ce_snmp_community
   community.network.ce_snmp_target_host
   community.network.ce_snmp_user
   community.network.ce_static_route
   community.network.ce_static_route_bfd
   community.network.ce_switchport
   community.network.ce_vlan
   community.network.ce_vrf
   community.network.ce_vrf_af
   community.network.ce_vrf_interface
   community.network.ce_vrrp
   community.network.ce_vxlan_tunnel
   community.network.ce_vxlan_vap

.. include:: shared_snippets/SSH_warning.txt

.. seealso::

       :ref:`timeout_options`
