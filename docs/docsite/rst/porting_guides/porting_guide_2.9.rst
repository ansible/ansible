
.. _porting_2.9_guide:

*************************
Ansible 2.9 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.8 and Ansible 2.9.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.9 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.9.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics


Playbook
========

No notable changes


Command Line
============

No notable changes


Deprecated
==========

No notable changes


Modules
=======

No notable changes


Modules removed
---------------

The following modules no longer exist:

* Apstra's ``aos_*`` modules.  See the new modules at  `https://github.com/apstra <https://github.com/apstra>`_.
* ec2_ami_find use :ref:`ec2_ami_facts <ec2_ami_facts_module>` instead.
* kubernetes use :ref:`k8s_raw <k8s_raw_module>` instead.
* nxos_ip_interface use :ref:`nxos_l3_interface <nxos_l3_interface_module>` instead.
* nxos_portchannel use :ref:`nxos_linkagg <nxos_linkagg_module>` instead.
* nxos_switchport use :ref:`nxos_l2_interface <nxos_l2_interface_module>` instead.
* oc use :ref:`openshift_raw <openshift_raw_module>` instead.
* panos_nat_policy use :ref:`panos_nat_rule <panos_nat_rule_module>` instead.
* panos_security_policy use :ref:`panos_security_rule <panos_security_rule_module>` instead.
* vsphere_guest use :ref:`vmware_guest <vmware_guest_module>` instead.


Deprecation notices
-------------------

No notable changes


Noteworthy module changes
-------------------------

* `vmware_dvswitch <vmware_dvswitch_module>` accepts `folder` parameter to place dvswitch in user defined folder. This option makes `datacenter` as an optional parameter.
* `vmware_datastore_cluster <vmware_datastore_cluster_module>` accepts `folder` parameter to place datastore cluster in user defined folder. This option makes `datacenter` as an optional parameter.


Plugins
=======

No notable changes


Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes
