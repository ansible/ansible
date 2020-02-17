.. _ce_platform_options:

***************************************
CloudEngine OS Platform Options
***************************************

CloudEngine CE OS supports multiple connections. This page offers details on how each connection works in Ansible and how to use it.

.. contents:: Topics

Connections Available
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

    Connection Settings   ``ansible_connection: network_cli``         ``ansible_connection: netconf``

    |enable_mode|         not supported by ce OS                      not supported by ce OS

    Returned Data Format  Refer to individual module documentation    Refer to individual module documentation
    ====================  ==========================================  =========================

.. |enable_mode| replace:: Enable Mode |br| (Privilege Escalation)

For legacy playbooks, Ansible still supports ``ansible_connection=local`` on all CloudEngine modules. We recommend modernizing to use ``ansible_connection=netconf`` or ``ansible_connection=network_cli`` as soon as possible.

Using CLI in Ansible
====================

Example CLI inventory ``[ce:vars]``
--------------------------------------

.. code-block:: yaml

   [ce:vars]
   ansible_connection=network_cli
   ansible_network_os=ce
   ansible_user=myuser
   ansible_password=!vault...
   ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI Task
----------------

.. code-block:: yaml

   - name: Retrieve CE OS version
     ce_command:
       commands: display version
     when: ansible_network_os == 'ce'


Using NETCONF in Ansible
========================

Enabling NETCONF
----------------

Before you can use NETCONF to connect to a switch, you must:

- install the ``ncclient`` python package on your control node(s) with ``pip install ncclient``
- enable NETCONF on the CloudEngine OS device(s)

To enable NETCONF on a new switch via Ansible, use the ``ce_config`` module via the CLI connection. Set up your platform-level variables just like in the CLI example above, then run a playbook task like this:

.. code-block:: yaml

   - name: Enable NETCONF
     connection: network_cli
     ce_config:
       lines:
         - snetconf server enable
     when: ansible_network_os == 'ce'

Once NETCONF is enabled, change your variables to use the NETCONF connection.

Example NETCONF inventory ``[ce:vars]``
------------------------------------------

.. code-block:: yaml

   [ce:vars]
   ansible_connection=netconf
   ansible_network_os=ce
   ansible_user=myuser
   ansible_password=!vault |
   ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


Example NETCONF Task
--------------------

.. code-block:: yaml

   - name: Create a vlan, id is 50(ce)
     ce_vlan:
       vlan_id: 50
       name: WEB
     when: ansible_network_os == 'ce'


Notes
========================

Modules work with connection C(network_cli)
--------------------------------------------

.. code-block:: yaml

   ce_acl_interface
   ce_command
   ce_config
   ce_evpn_bgp
   ce_evpn_bgp_rr
   ce_evpn_global
   ce_facts
   ce_mlag_interface
   ce_mtu
   ce_netstream_aging
   ce_netstream_export
   ce_netstream_global
   ce_netstream_template
   ce_ntp_auth
   ce_rollback
   ce_snmp_contact
   ce_snmp_location
   ce_snmp_traps
   ce_startup
   ce_stp
   ce_vxlan_arp
   ce_vxlan_gateway
   ce_vxlan_global


Modules work with connection C(netconf)
--------------------------------------------

.. code-block:: yaml

   ce_aaa_server
   ce_aaa_server_host
   ce_acl
   ce_acl_advance
   ce_bfd_global
   ce_bfd_session
   ce_bfd_view
   ce_bgp
   ce_bgp_af
   ce_bgp_neighbor
   ce_bgp_neighbor_af
   ce_dldp
   ce_dldp_interface
   ce_eth_trunk
   ce_evpn_bd_vni
   ce_file_copy
   ce_info_center_debug
   ce_info_center_global
   ce_info_center_log
   ce_info_center_trap
   ce_interface
   ce_interface_ospf
   ce_ip_interface
   ce_lacp
   ce_link_status
   ce_lldp
   ce_lldp_interface
   ce_mlag_config
   ce_netconf
   ce_ntp
   ce_ospf
   ce_ospf_vrf
   ce_reboot
   ce_sflow
   ce_snmp_community
   ce_snmp_target_host
   ce_snmp_user
   ce_static_route
   ce_static_route_bfd
   ce_switchport
   ce_vlan
   ce_vrf
   ce_vrf_af
   ce_vrf_interface
   ce_vrrp
   ce_vxlan_tunnel
   ce_vxlan_vap

.. include:: shared_snippets/SSH_warning.txt

.. seealso::

       :ref:`timeout_options`
