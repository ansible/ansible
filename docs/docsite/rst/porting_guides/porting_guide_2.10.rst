
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

* Windows Server 2008 and 2008 R2 will no longer be supported or tested in the next Ansible release, see :ref:`windows_faq_server2008`.


Modules
=======


Modules removed
---------------

The following modules no longer exist:

* letsencrypt use :ref:`acme_certificate <acme_certificate_module>` instead.


Deprecation notices
-------------------

The following modules will be removed in Ansible 2.14. Please update your playbooks accordingly.

* ldap_attr use :ref:`ldap_attrs <ldap_attrs_module>` instead.


The following functionality will be removed in Ansible 2.14. Please update update your playbooks accordingly.

* The :ref:`openssl_csr <openssl_csr_module>` module's option ``version`` no longer supports values other than ``1`` (the current only standardized CSR version).
* :ref:`docker_container <docker_container_module>`: the ``trust_image_content`` option will be removed. It has always been ignored by the module.
* :ref:`iam_managed_policy <iam_managed_policy_module>`: the ``fail_on_delete`` option will be removed.  It has always been ignored by the module.
* :ref:`s3_lifecycle <s3_lifecycle_module>`: the ``requester_pays`` option will be removed. It has always been ignored by the module.
* :ref:`s3_sync <s3_sync_module>`: the ``retries`` option will be removed. It has always been ignored by the module.
* The return values ``err`` and ``out`` of :ref:`docker_stack <docker_stack_module>` have been deprecated. Use ``stdout`` and ``stderr`` from now on instead.
* :ref:`cloudformation <cloudformation_module>`: the ``template_format`` option will be removed. It has been ignored by the module since Ansible 2.3.
* :ref:`data_pipeline <data_pipeline_module>`: the ``version`` option will be removed. It has always been ignored by the module.
* :ref:`ec2_eip <ec2_eip_module>`: the ``wait_timeout`` option will be removed. It has had no effect since Ansible 2.3.
* :ref:`ec2_key <ec2_key_module>`: the ``wait`` option will be removed. It has had no effect since Ansible 2.5.
* :ref:`ec2_key <ec2_key_module>`: the ``wait_timeout`` option will be removed. It has had no effect since Ansible 2.5.
* :ref:`ec2_lc <ec2_lc_module>`: the ``associate_public_ip_address`` option will be removed. It has always been ignored by the module.
* :ref:`iam_policy <iam_policy_module>`: the ``policy_document`` option will be removed. To maintain the existing behavior use the ``policy_json`` option and read the file with the ``lookup`` plugin.
* :ref:`redfish_config <redfish_config_module>`: the ``bios_attribute_name`` and ``bios_attribute_value`` options will be removed. To maintain the existing behavior use the ``bios_attributes`` option instead.
* :ref:`clc_aa_policy <clc_aa_policy_module>`: the ``wait`` parameter will be removed. It has always been ignored by the module.
* :ref:`redfish_config <redfish_config_module>`, :ref:`redfish_command <redfish_command_module>`: the behavior to select the first System, Manager, or Chassis resource to modify when multiple are present will be removed. Use the new ``resource_id`` option to specify target resource to modify.



The following functionality will change in Ansible 2.14. Please update update your playbooks accordingly.

* The :ref:`docker_container <docker_container_module>` module has a new option, ``container_default_behavior``, whose default value will change from ``compatibility`` to ``no_defaults``. Set to an explicit value to avoid deprecation warnings.
* The :ref:`docker_container <docker_container_module>` module's ``network_mode`` option will be set by default to the name of the first network in ``networks`` if at least one network is given and ``networks_cli_compatible`` is ``true`` (will be default from Ansible 2.12 on). Set to an explicit value to avoid deprecation warnings if you specify networks and set ``networks_cli_compatible`` to ``true``. The current default (not specifying it) is equivalent to the value ``default``.
* :ref:`iam_policy <iam_policy_module>`: the default value for the ``skip_duplicates`` option will change from ``true`` to ``false``.  To maintain the existing behavior explicitly set it to ``true``.
* :ref:`iam_role <iam_role_module>`: the ``purge_policies`` option (also know as ``purge_policy``) default value will change from ``true`` to ``false``
* :ref:`elb_network_lb <elb_network_lb_module>`: the default behaviour for the ``state`` option will change from ``absent`` to ``present``.  To maintain the existing behavior explicitly set state to ``absent``.


The following modules will be removed in Ansible 2.14. Please update your playbooks accordingly.

* ``vmware_dns_config`` use :ref:`vmware_host_dns <vmware_host_dns_module>` instead.


Noteworthy module changes
-------------------------

* :ref:`vmware_datastore_maintenancemode <vmware_datastore_maintenancemode_module>` now returns ``datastore_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_host_kernel_manager <vmware_host_kernel_manager_module>` now returns ``host_kernel_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_host_ntp <vmware_host_ntp_module>` now returns ``host_ntp_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_host_service_manager <vmware_host_service_manager_module>` now returns ``host_service_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_tag <vmware_tag_module>` now returns ``tag_status`` instead of Ansible internal key ``results``.
* The deprecated ``recurse`` option in :ref:`pacman <pacman_module>` module has been removed, you should use ``extra_args=--recursive`` instead.
* :ref:`vmware_guest_custom_attributes <vmware_guest_custom_attributes_module>` module does not require VM name which was a required parameter for releases prior to Ansible 2.10.
* :ref:`zabbix_action <zabbix_action_module>` no longer requires ``esc_period`` and ``event_source`` arguments when ``state=absent``.
* :ref:`gitlab_user <gitlab_user_module>` no longer requires ``name``, ``email`` and ``password`` arguments when ``state=absent``.
* :ref:`win_pester <win_pester_module>` no longer runs all ``*.ps1`` file in the directory specified due to it executing potentially unknown scripts. It will follow the default behaviour of only running tests for files that are like ``*.tests.ps1`` which is built into Pester itself
* :ref:`win_find <win_find_module>` has been refactored to better match the behaviour of the ``find`` module. Here is what has changed:
    * When the directory specified by ``paths`` does not exist or is a file, it will no longer fail and will just warn the user
    * Junction points are no longer reported as ``islnk``, use ``isjunction`` to properly report these files. This behaviour matches the :ref:`win_stat <win_stat_module>`
    * Directories no longer return a ``size``, this matches the ``stat`` and ``find`` behaviour and has been removed due to the difficulties in correctly reporting the size of a directory

Plugins
=======


Noteworthy plugin changes
-------------------------

* The ``hashi_vault`` lookup plugin now returns the latest version when using the KV v2 secrets engine. Previously, it returned all versions of the secret which required additional steps to extract and filter the desired version.

Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes
