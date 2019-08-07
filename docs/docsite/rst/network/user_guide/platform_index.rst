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
   platform_icx
   platform_ios
   platform_ironware
   platform_junos
   platform_netvisor
   platform_nos
   platform_nxos
   platform_routeros
   platform_slxos
   platform_voss
   platform_netconf_enabled

.. _settings_by_platform:

Settings by Platform
================================

=============================  =======================  ===========  =======  =======  ==================
..                             ..                       ``ansible_connection:`` settings available
-----------------------------  -----------------------  -------------------------------------------------
Network OS                     ``ansible_network_os:``  network_cli  netconf  httpapi  local
=============================  =======================  ===========  =======  =======  ==================
Arista EOS [1]_                ``eos``                  ✓                     ✓        ✓
Cisco ASA                      ``asa``                  ✓                              ✓
Cisco IOS [1]_                 ``ios``                  ✓                              ✓
Cisco IOS XR [1]_              ``iosxr``                ✓                              ✓
Cisco NX-OS [1]_               ``nxos``                 ✓                     ✓        ✓
Dell OS6                       ``dellos6``              ✓                              ✓
Dell OS9                       ``dellos9``              ✓                              ✓
Dell OS10                      ``dellos10``             ✓                              ✓
Ericsson ECCLI                 ``eric_eccli``           ✓                              ✓
Extreme EXOS                   ``exos``                 ✓                     ✓
Extreme IronWare               ``ironware``             ✓                              ✓
Extreme NOS                    ``nos``                  ✓
Extreme SLX-OS                 ``slxos``                ✓
Extreme VOSS                   ``voss``                 ✓
F5 BIG-IP                                                                              ✓
F5 BIG-IQ                                                                              ✓
Junos OS [1]_                  ``junos``                ✓            ✓                 ✓
Lenovo CNOS                    ``cnos``                 ✓                              ✓
Lenovo ENOS                    ``enos``                 ✓                              ✓
MikroTik RouterOS              ``routeros``             ✓
Nokia SR OS                    ``sros``                 ✓                              ✓
Pluribus Netvisor              ``netvisor``             ✓
Ruckus ICX [1]_                ``icx``                  ✓
VyOS [1]_                      ``vyos``                 ✓                              ✓
OS that supports Netconf [1]_  ``<network-os>``                      ✓                 ✓
=============================  =======================  ===========  =======  =======  ==================

.. [1] Maintained by Ansible Network Team
