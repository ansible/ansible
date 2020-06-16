
.. _porting_2.10_guide:

**************************
Ansible 2.10 Porting Guide
**************************

.. warning::

	Links on this page may not point to the most recent versions of modules. In preparation for the release of 2.10, many plugins and modules have migrated to Collections on  `Ansible Galaxy <https://galaxy.ansible.com>`_. For the current development status of Collections and FAQ see `Ansible Collections Community Guide <https://github.com/ansible-collections/general/blob/master/README.rst>`_. We expect the 2.10 Porting Guide to change frequently up to the 2.10 release. Follow the conversations about collections on our various :ref:`communication` channels for the latest information on the status of the ``devel`` branch.

This section discusses the behavioral changes between Ansible 2.9 and Ansible 2.10.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.10 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.10.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics


Playbook
========

* Fixed a bug on boolean keywords that made random strings return 'False', now they should return an error if they are not a proper boolean
  Example: `diff: yes-` was returning `False`.
* A new fact, ``ansible_processor_nproc`` reflects the number of vcpus
  available to processes (falls back to the number of vcpus available to
  the scheduler).


Command Line
============

No notable changes


Deprecated
==========

* Windows Server 2008 and 2008 R2 will no longer be supported or tested in the next Ansible release, see :ref:`windows_faq_server2008`.
* The :ref:`win_stat <win_stat_module>` module has removed the deprecated ``get_md55`` option and ``md5`` return value.
* The :ref:`win_psexec <win_psexec_module>` module has removed the deprecated ``extra_opts`` option.


Modules
=======

.. warning::

	Links on this page may not point to the most recent versions of modules. We will update them when we can.

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.14. Please update your playbooks accordingly.

* ldap_attr use ldap_attrs instead.
* vyos_static_route use vyos_static_routes instead.

The following functionality will be removed in Ansible 2.14. Please update update your playbooks accordingly.

* :ref:`iam_managed_policy <iam_managed_policy_module>`: the ``fail_on_delete`` option will be removed.  It has always been ignored by the module.
* :ref:`s3_lifecycle <s3_lifecycle_module>`: the ``requester_pays`` option will be removed. It has always been ignored by the module.
* :ref:`s3_sync <s3_sync_module>`: the ``retries`` option will be removed. It has always been ignored by the module.
* :ref:`cloudformation <cloudformation_module>`: the ``template_format`` option will be removed. It has been ignored by the module since Ansible 2.3.
* :ref:`data_pipeline <data_pipeline_module>`: the ``version`` option will be removed. It has always been ignored by the module.
* :ref:`ec2_eip <ec2_eip_module>`: the ``wait_timeout`` option will be removed. It has had no effect since Ansible 2.3.
* :ref:`ec2_key <ec2_key_module>`: the ``wait`` option will be removed. It has had no effect since Ansible 2.5.
* :ref:`ec2_key <ec2_key_module>`: the ``wait_timeout`` option will be removed. It has had no effect since Ansible 2.5.
* :ref:`ec2_lc <ec2_lc_module>`: the ``associate_public_ip_address`` option will be removed. It has always been ignored by the module.
* :ref:`ec2_tag <ec2_tag_module>`: Support for ``list`` as a state has been deprecated.  The ``ec2_tag_info`` can be used to fetch the tags on an EC2 resource.
* :ref:`iam_policy <iam_policy_module>`: the ``policy_document`` option will be removed. To maintain the existing behavior use the ``policy_json`` option and read the file with the ``lookup`` plugin.
* :ref:`win_domain_controller <win_domain_controller_module>`: the ``log_path`` option will be removed. This was undocumented and only related to debugging information for module development.
* :ref:`win_package <win_package_module>`: the ``username`` and ``password`` options will be removed. The same functionality can be done by using ``become: yes`` and ``become_flags: logon_type=new_credentials logon_flags=netcredentials_only`` on the task.
* :ref:`win_package <win_package_module>`: the ``ensure`` alias for the ``state`` option will be removed. Please use ``state`` instead of ``ensure``.
* :ref:`win_package <win_package_module>`: the ``productid`` alias for the ``product_id`` option will be removed. Please use ``product_id`` instead of ``productid``.



The following functionality will change in Ansible 2.14. Please update update your playbooks accordingly.

* :ref:`ec2 <ec2_module>`: the ``group`` and ``group_id`` options will become mutually exclusive.  Currently ``group_id`` is ignored if you pass both.
* :ref:`iam_policy <iam_policy_module>`: the default value for the ``skip_duplicates`` option will change from ``true`` to ``false``.  To maintain the existing behavior explicitly set it to ``true``.
* :ref:`iam_role <iam_role_module>`: the ``purge_policies`` option (also know as ``purge_policy``) default value will change from ``true`` to ``false``
* :ref:`elb_network_lb <elb_network_lb_module>`: the default behaviour for the ``state`` option will change from ``absent`` to ``present``.  To maintain the existing behavior explicitly set state to ``absent``.
* :ref:`vmware_tag_info <vmware_tag_info_module>`: the module will not return ``tag_facts`` since it does not return multiple tags with the same name and different category id. To maintain the existing behavior use ``tag_info`` which is a list of tag metadata.

The following modules will be removed in Ansible 2.14. Please update your playbooks accordingly.

* ``vmware_dns_config`` use vmware_host_dns instead.


Noteworthy module changes
-------------------------

* The ``datacenter`` option has been removed from :ref:`vmware_guest_find <vmware_guest_find_module>`
* The options ``ip_address`` and ``subnet_mask`` have been removed from :ref:`vmware_vmkernel <vmware_vmkernel_module>`; use the suboptions ``ip_address`` and ``subnet_mask`` of the ``network`` option instead.
* Ansible modules created with ``add_file_common_args=True`` added a number of undocumented arguments which were mostly there to ease implementing certain action plugins. The undocumented arguments ``src``, ``follow``, ``force``, ``content``, ``backup``, ``remote_src``, ``regexp``, ``delimiter``, and ``directory_mode`` are now no longer added. Modules relying on these options to be added need to specify them by themselves.
* The ``AWSRetry`` decorator no longer catches ``NotFound`` exceptions by default.  ``NotFound`` exceptions need to be explicitly added using ``catch_extra_error_codes``.  Some AWS modules may see an increase in transient failures due to AWS's eventual consistency model.
* :ref:`vmware_datastore_maintenancemode <vmware_datastore_maintenancemode_module>` now returns ``datastore_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_host_kernel_manager <vmware_host_kernel_manager_module>` now returns ``host_kernel_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_host_ntp <vmware_host_ntp_module>` now returns ``host_ntp_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_host_service_manager <vmware_host_service_manager_module>` now returns ``host_service_status`` instead of Ansible internal key ``results``.
* :ref:`vmware_tag <vmware_tag_module>` now returns ``tag_status`` instead of Ansible internal key ``results``.
* The deprecated ``recurse`` option in :ref:`pacman <pacman_module>` module has been removed, you should use ``extra_args=--recursive`` instead.
* :ref:`vmware_guest_custom_attributes <vmware_guest_custom_attributes_module>` module does not require VM name which was a required parameter for releases prior to Ansible 2.10.
* :ref:`win_pester <win_pester_module>` no longer runs all ``*.ps1`` file in the directory specified due to it executing potentially unknown scripts. It will follow the default behaviour of only running tests for files that are like ``*.tests.ps1`` which is built into Pester itself
* :ref:`win_find <win_find_module>` has been refactored to better match the behaviour of the ``find`` module. Here is what has changed:
    * When the directory specified by ``paths`` does not exist or is a file, it will no longer fail and will just warn the user
    * Junction points are no longer reported as ``islnk``, use ``isjunction`` to properly report these files. This behaviour matches the :ref:`win_stat <win_stat_module>`
    * Directories no longer return a ``size``, this matches the ``stat`` and ``find`` behaviour and has been removed due to the difficulties in correctly reporting the size of a directory
* :ref:`purefb_fs <purefb_fs_module>` no longer supports the deprecated ``nfs`` option. This has been superceeded by ``nfsv3``.
* :ref:`nxos_igmp_interface <nxos_igmp_interface_module>` no longer supports the deprecated ``oif_prefix`` and ``oif_source`` options. These have been superceeded by ``oif_ps``.
* :ref:`aws_s3 <aws_s3_module>` can now delete versioned buckets even when they are not empty - set mode to delete to delete a versioned bucket and everything in it.
* The parameter ``message`` in :ref:`grafana_dashboard <grafana_dashboard_module>` module is renamed to ``commit_message`` since ``message`` is used by Ansible Core engine internally.
* Ansible no longer looks for Python modules in the current working directory (typically the ``remote_user``'s home directory) when an Ansible module is run. This is to fix becoming an unprivileged user on OpenBSD and to mitigate any attack vector if the current working directory is writable by a malicious user. Install any Python modules needed to run the Ansible modules on the managed node in a system-wide location or in another directory which is in the ``remote_user``'s ``$PYTHONPATH`` and readable by the ``become_user``.


Plugins
=======

Lookup plugin names case-sensitivity
------------------------------------

* Prior to Ansible ``2.10`` lookup plugin names passed in as an argument to the ``lookup()`` function were treated as case-insensitive as opposed to lookups invoked via ``with_<lookup_name>``. ``2.10`` brings consistency to ``lookup()`` and ``with_`` to be both case-sensitive.

Noteworthy plugin changes
-------------------------

* Cache plugins in collections can be used to cache data from inventory plugins. Previously, cache plugins in collections could only be used for fact caching.
* Some undocumented arguments from ``FILE_COMMON_ARGUMENTS`` have been removed; plugins using these, in particular action plugins, need to be adjusted. The undocumented arguments which were removed are ``src``, ``follow``, ``force``, ``content``, ``backup``, ``remote_src``, ``regexp``, ``delimiter``, and ``directory_mode``.

Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes
