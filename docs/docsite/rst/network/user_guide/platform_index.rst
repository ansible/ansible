.. _platform_options:

****************
Platform Options
****************

Some Ansible Network platforms support multiple connection types, privilege escalation (``enable`` mode), or other options. The pages in this section offer standardized guides to understanding available options on each network platform. We welcome contributions from community-maintained platforms to this section.

.. toctree::
   :maxdepth: 2
   :caption: Platform Options

   platform_eos
   platform_ios
   platform_junos
   platform_nxos

.. _connections_by_platform:

Connections Settings by Platform
================================

+----------------+----------------------+----------------------+------------------+------------------+
|..              | network_cli          | netconf              | httpapi          | local            |
+================+======================+======================+==================+==================+
| Cisco ASA      | in v. >=2.5          | N/A                  | N/A              |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| Arista EOS*    | in v. >=2.5          | N/A                  | in v. >=2.6      |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| Cisco IOS*     | in v. >=2.5          | N/A                  | N/A              |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| Cisco IOS XR*  | in v. >=2.5          | N/A                  | N/A              |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| Junos OS*      | in v. >=2.5          | in v. >=2.5          | N/A              |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| Cisco NX-OS*   | in v. >=2.5          | N/A                  | in v. >=2.6      |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| VyOS*          | in v. >=2.5          | N/A                  | N/A              |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+

`*` Maintained by Ansible Network Team