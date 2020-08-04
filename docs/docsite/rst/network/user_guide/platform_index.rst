.. _platform_options:

****************
Platform Options
****************

Some Ansible Network platforms support multiple connection types, privilege escalation (``enable`` mode), or other options. The pages in this section offer standardized guides to understanding available options on each network platform. We welcome contributions from community-maintained platforms to this section.

.. toctree::
   :maxdepth: 2
   :caption: Platform Options

   platform_ce
   platform_cnos
   platform_dellos6
   platform_dellos9
   platform_dellos10
   platform_enos
   platform_eos
   platform_eric_eccli
   platform_exos
   platform_frr
   platform_icx
   platform_ios
   platform_iosxr
   platform_ironware
   platform_junos
   platform_meraki
   platform_netvisor
   platform_nos
   platform_nxos
   platform_routeros
   platform_slxos
   platform_voss
   platform_vyos
   platform_netconf_enabled

.. _settings_by_platform:

Settings by Platform
================================

.. raw:: html

    <style>
    /* Style for this single table.  Add delimiters between header columns */
    table#network-platform-table thead tr th.head {
      border-left-width: 1px;
      border-left-color: rgb(225, 228, 229);
      border-left-style: solid;
    }
    </style>

.. table::
    :name: network-platform-table

    ===============================  =======================  ===========  =======  =======  ===========
    ..                                                        ``ansible_connection:`` settings available
    --------------------------------------------------------  ------------------------------------------
    Network OS                       ``ansible_network_os:``  network_cli  netconf  httpapi  local
    ===============================  =======================  ===========  =======  =======  ===========
    `Arista EOS`_ `[†]`_                ``eos``                  ✓                     ✓        ✓
    `Ciena SAOS6`_                      ``saos6``                ✓                              ✓
    `Cisco ASA`_ `[†]`_                      ``asa``                  ✓                              ✓
    `Cisco IOS`_ `[†]`_                 ``ios``                  ✓                              ✓
    `Cisco IOS XR`_ `[†]`_              ``iosxr``                ✓                              ✓
    `Cisco NX-OS`_ `[†]`_               ``nxos``                 ✓                     ✓        ✓
    `Cloudengine OS`_                   ``ce``                   ✓            ✓                 ✓
    `Dell OS6`_                         ``dellos6``              ✓                              ✓
    `Dell OS9`_                        ``dellos9``              ✓                              ✓
    `Dell OS10`_                        ``dellos10``             ✓                              ✓
    `Ericsson ECCLI`_                   ``eric_eccli``           ✓                              ✓
    `Extreme EXOS`_                     ``exos``                 ✓                     ✓
    `Extreme IronWare`_                 ``ironware``             ✓                              ✓
    `Extreme NOS`_                     ``nos``                  ✓
    `Extreme SLX-OS`_                   ``slxos``                ✓
    `Extreme VOSS`_                     ``voss``                 ✓
    `F5 BIG-IP`_                                                                                ✓
    `F5 BIG-IQ`_                                                                                ✓
    `Junos OS`_ `[†]`_                  ``junos``                ✓            ✓                 ✓
    `Lenovo CNOS`_                      ``cnos``                 ✓                              ✓
    `Lenovo ENOS`_                      ``enos``                 ✓                              ✓
    `Meraki`_                           ``meraki``                                              ✓
    `MikroTik RouterOS`_                ``routeros``             ✓
    `Nokia SR OS`_                      ``sros``                 ✓                              ✓
    `Pluribus Netvisor`_                ``netvisor``             ✓
    `Ruckus ICX`_                       ``icx``                  ✓
    `VyOS`_ `[†]`_                      ``vyos``                 ✓                              ✓
    OS that supports Netconf `[†]`_  ``<network-os>``                      ✓                 ✓
    ===============================  =======================  ===========  =======  =======  ===========

.. _Arista EOS: https://galaxy.ansible.com/arista/eos
.. _Ciena SAOS6: https://galaxy.ansible.com/ciena/saos6
.. _Cisco ASA: https://galaxy.ansible.com/cisco/asa
.. _Cisco IOS: https://galaxy.ansible.com/cisco/ios
.. _Cisco IOS XR: https://galaxy.ansible.com/cisco/iosxr
.. _Cisco NX-OS: https://galaxy.ansible.com/cisco/nxos
.. _Cloudengine OS: https://galaxy.ansible.com/community/network
.. _Dell OS6: https://github.com/ansible-collections/dellemc.os6
.. _Dell OS9: https://github.com/ansible-collections/dellemc.os9
.. _Dell OS10: https://galaxy.ansible.com/dellemc_networking/os10
.. _Ericsson ECCLI: https://galaxy.ansible.com/community/network
.. _Extreme EXOS: https://galaxy.ansible.com/community/network
.. _Extreme IronWare: https://galaxy.ansible.com/community/network
.. _Extreme NOS: https://galaxy.ansible.com/community/network
.. _Extreme SLX-OS: https://galaxy.ansible.com/community/network
.. _Extreme VOSS: https://galaxy.ansible.com/community/network
.. _F5 BIG-IP: https://galaxy.ansible.com/f5networks/f5_modules
.. _F5 BIG-IQ: https://galaxy.ansible.com/f5networks/f5_modules
.. _Junos OS: https://galaxy.ansible.com/junipernetworks/junos
.. _Lenovo CNOS: https://galaxy.ansible.com/community/network
.. _Lenovo ENOS: https://galaxy.ansible.com/community/network
.. _Meraki: https://galaxy.ansible.com/cisco/meraki
.. _MikroTik RouterOS: https://galaxy.ansible.com/community/network
.. _Nokia SR OS: https://galaxy.ansible.com/community/network
.. _Pluribus Netvisor: https://galaxy.ansible.com/community/network
.. _Ruckus ICX: https://galaxy.ansible.com/community/network
.. _VyOS: https://galaxy.ansible.com/vyos/vyos
.. _`[†]`:

**[†]** Maintained by Ansible Network Team
