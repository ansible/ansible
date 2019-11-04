
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


Modules removed
---------------

The following modules no longer exist:

* letsencrypt use :ref:`acme_certificate <acme_certificate_module>` instead.


Deprecation notices
-------------------

The following functionality will be removed in Ansible 2.14. Please update update your playbooks accordingly.

* The :ref:`openssl_csr <openssl_csr_module>` module's option ``version`` no longer supports values other than ``1`` (the current only standardized CSR version).
* :ref:`docker_container <docker_container_module>`: the ``trust_image_content`` option will be removed. It has always been ignored by the module.
* :ref:`iam_managed_policy <iam_managed_policy_module>`: the ``fail_on_delete`` option wil be removed.  It has always been ignored by the module.
* :ref:`s3_lifecycle <s3_lifecycle_module>`: the ``requester_pays`` option will be removed. It has always been ignored by the module.
* :ref:`s3_sync <s3_sync_module>`: the ``retries`` option will be removed. It has always been ignored by the module.
* The return values ``err`` and ``out`` of :ref:`docker_stack <docker_stack_module>` have been deprecated. Use ``stdout`` and ``stderr`` from now on instead.
* :ref:`cloudformation <cloudformation_module>`: the ``template_format`` option will be removed. It has been ignored by the module since Ansible 2.3.
* :ref:`data_pipeline <data_pipeline_module>`: the ``version`` option will be removed. It has always been ignored by the module.
* :ref:`ec2_eip <ec2_eip_module>`: the ``wait_timeout`` option will be removed. It has had no effect since Ansible 2.3.
* :ref:`ec2_key <ec2_key_module>`: the ``wait`` option will be removed. It has had no effect since Ansible 2.5.
* :ref:`ec2_key <ec2_key_module>`: the ``wait_timeout`` option will be removed. It has had no effect since Ansible 2.5.
* :ref:`ec2_lc <ec2_lc_module>`: the ``associate_public_ip_address`` option will be removed. It has always been ignored by the module.

The following functionality will change in Ansible 2.14. Please update update your playbooks accordingly.

* The :ref:`docker_container <docker_container_module>` module has a new option, ``container_default_behavior``, whose default value will change from ``compatibility`` to ``no_defaults``. Set to an explicit value to avoid deprecation warnings.


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
