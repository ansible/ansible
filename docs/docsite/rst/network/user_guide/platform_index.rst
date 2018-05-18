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

Connections Settings by Platform 

+----------------+----------------------+----------------------+------------------+------------------+
|..              | network_cli          | netconf              | httpapi          | local            |
+================+======================+======================+==================+==================+
| EOS*           | in v. >=2.5          | no                   | in v. >=2.6      |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| IOS*           | in v. >=2.5          | no                   | no               |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| IOS-XR*        | in v. >=2.5          | no                   | no               |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| JUNOS*         | in v. >=2.5          | in v. >=2.5          | no               |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| NXOS*          | in v. >=2.5          | no                   | in v. >=2.6      |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+
| VYOS*          | in v. >=2.5          | no                   | no               |  in v. >=2.4     |
+----------------+----------------------+----------------------+------------------+------------------+

* Maintained by Ansible Network Team