.. _platform_options:

****************
Platform Options
****************

Some Ansible Network platforms support multiple connection types, privilege escalation (``enable`` mode), or other options. The pages in this section offer standardized guides to understanding available options on each network platform. We welcome contributions from community-maintained platforms to this section.

.. toctree::
   :maxdepth: 2
   :caption: Platform Options

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
    Arista EOS `[†]`_                ``eos``                  ✓                     ✓        ✓
    Cisco ASA                        ``asa``                  ✓                              ✓
    Cisco IOS `[†]`_                 ``ios``                  ✓                              ✓
    Cisco IOS XR `[†]`_              ``iosxr``                ✓                              ✓
    Cisco NX-OS `[†]`_               ``nxos``                 ✓                     ✓        ✓
    Dell OS6                         ``dellos6``              ✓                              ✓
    Dell OS9                         ``dellos9``              ✓                              ✓
    Dell OS10                        ``dellos10``             ✓                              ✓
    Ericsson ECCLI                   ``eric_eccli``           ✓                              ✓
    Extreme EXOS                     ``exos``                 ✓                     ✓
    Extreme IronWare                 ``ironware``             ✓                              ✓
    Extreme NOS                      ``nos``                  ✓
    Extreme SLX-OS                   ``slxos``                ✓
    Extreme VOSS                     ``voss``                 ✓
    F5 BIG-IP                                                                                ✓
    F5 BIG-IQ                                                                                ✓
    Junos OS `[†]`_                  ``junos``                ✓            ✓                 ✓
    Lenovo CNOS                      ``cnos``                 ✓                              ✓
    Lenovo ENOS                      ``enos``                 ✓                              ✓
    Meraki                           ``meraki``                                              ✓
    MikroTik RouterOS                ``routeros``             ✓
    Nokia SR OS                      ``sros``                 ✓                              ✓
    Pluribus Netvisor                ``netvisor``             ✓
    Ruckus ICX `[†]`_                ``icx``                  ✓
    VyOS `[†]`_                      ``vyos``                 ✓                              ✓
    OS that supports Netconf `[†]`_  ``<network-os>``                      ✓                 ✓
    ===============================  =======================  ===========  =======  =======  ===========

.. _`[†]`:

**[†]** Maintained by Ansible Network Team
