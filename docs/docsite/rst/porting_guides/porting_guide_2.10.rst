
.. _porting_2.10_guide:

**************************
Ansible 2.10 Porting Guide
**************************

This section discusses the behavioral changes between Ansible 2.9 and Ansible 2.10.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.10 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.10.rst>`_ to understand what updates you may need to make.

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

* letsencrypt use :ref:`acme_certificate <acme_certificate_module>` instead.


Deprecation notices
-------------------

No notable changes


Noteworthy module changes
-------------------------

* :ref:`vmware_datastore_maintenancemode <vmware_datastore_maintenancemode_module>` now returns ``datastore_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_host_kernel_manager <vmware_host_kernel_manager_module>` now returns ``host_kernel_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_host_ntp <vmware_host_ntp_module>` now returns ``host_ntp_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_host_service_manager <vmware_host_service_manager_module>` now returns ``host_service_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_tag <vmware_tag_module>` now returns ``tag_status`` instead of Ansible internal key ``results``.
* The deprecated ``recurse`` option in :ref:`pacman <pacman_module>` module has been removed, you should use ``extra_args=--recursive`` instead.
* :ref:`vmware_guest_custom_attributes <vmware_guest_custom_attributes_module>` module does not require VM name which was a required parameter for releases prior to Ansible 2.10.

Plugins
=======

No notable changes


Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes
