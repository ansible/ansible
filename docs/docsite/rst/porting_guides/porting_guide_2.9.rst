
.. _porting_2.9_guide:

*************************
Ansible 2.9 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.8 and Ansible 2.9.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.9 <https://github.com/ansible/ansible/blob/stable-2.9/changelogs/CHANGELOG-v2.9.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics


Playbook
========

Inventory
---------

 * ``hash_behaviour`` now affects inventory sources. If you have it set to ``merge``, the data you get from inventory might change and you will have to update playbooks accordingly. If you're using the default setting (``overwrite``), you will see no changes. Inventory was ignoring this setting.

Loops
-----

Ansible 2.9 handles "unsafe" data more robustly, ensuring that data marked "unsafe" is not templated. In previous versions, Ansible recursively marked all data returned by the direct use of ``lookup()`` as "unsafe", but only marked structured data returned by indirect lookups using ``with_X`` style loops as "unsafe" if the returned elements were strings. Ansible 2.9 treats these two approaches consistently.

As a result, if you use ``with_dict`` to return keys with templatable values, your templates may no longer work as expected in Ansible 2.9.

To allow the old behavior, switch from using ``with_X`` to using ``loop`` with a filter as described at :ref:`migrating_to_loop`.

Command Line
============

* The location of the Galaxy token file has changed from ``~/.ansible_galaxy`` to ``~/.ansible/galaxy_token``. You can configure both path and file name with the :ref:`galaxy_token_path` config.


Deprecated
==========

No notable changes


Collection loader changes
=========================

The way to import a PowerShell or C# module util from a collection has changed in the Ansible 2.9 release. In Ansible
2.8 a util was imported with the following syntax:

.. code-block:: powershell

    #AnsibleRequires -CSharpUtil AnsibleCollections.namespace_name.collection_name.util_filename
    #AnsibleRequires -PowerShell AnsibleCollections.namespace_name.collection_name.util_filename

In Ansible 2.9 this was changed to:

.. code-block:: powershell

    #AnsibleRequires -CSharpUtil ansible_collections.namespace_name.collection_name.plugins.module_utils.util_filename
    #AnsibleRequires -PowerShell ansible_collections.namespace_name.collection_name.plugins.module_utils.util_filename

The change in the collection import name also requires any C# util namespaces to be updated with the newer name
format. This is more verbose but is designed to make sure we avoid plugin name conflicts across separate plugin types
and to standardise how imports work in PowerShell with how Python modules work.


Modules
=======

* The ``win_get_url`` and ``win_uri`` module now sends requests with a default ``User-Agent`` of ``ansible-httpget``. This can be changed by using the ``http_agent`` key.
* The ``apt`` module now honors ``update_cache=false`` while installing its own dependency and skips the cache update. Explicitly setting ``update_cache=true`` or omitting the param ``update_cache`` will result in a cache update while installing its own dependency.

* Version 2.9.12 of Ansible changed the default mode of file-based tasks to ``0o600 & ~umask`` when the user did not specify a ``mode`` parameter on file-based tasks. This was in response to a CVE report which we have reconsidered. As a result, the mode change has been reverted in 2.9.13, and mode will now default to ``0o666 & ~umask`` as in previous versions of Ansible.
* If you changed any tasks to specify less restrictive permissions while using 2.9.12, those changes will be unnecessary (but will do no harm) in 2.9.13.
* To avoid the issue raised in CVE-2020-1736, specify a ``mode`` parameter in all file-based tasks that accept it.

* ``dnf`` and ``yum`` - As of version 2.9.13, the ``dnf`` module (and ``yum`` action when it uses ``dnf``) now correctly validates GPG signatures of packages (CVE-2020-14365). If you see an error such as ``Failed to validate GPG signature for [package name]``, please ensure that you have imported the correct GPG key for the DNF repository and/or package you are using. One way to do this is with the ``rpm_key`` module. Although we discourage it, in some cases it may be necessary to disable the GPG check. This can be done by explicitly adding ``disable_gpg_check: yes`` in your ``dnf`` or ``yum`` task.


Renaming from ``_facts`` to ``_info``
--------------------------------------

Ansible 2.9 renamed a lot of modules from ``<something>_facts`` to ``<something>_info``, because the modules do not return :ref:`Ansible facts <vars_and_facts>`. Ansible facts relate to a specific host. For example, the configuration of a network interface, the operating system on a unix server, and the list of packages installed on a Windows box are all Ansible facts. The renamed modules return values that are not unique to the host. For example, account information or region data for a cloud provider. Renaming these modules should provide more clarity about the types of return values each set of modules offers.

Writing modules
---------------

* Module and module_utils files can now use relative imports to include other module_utils files.
  This is useful for shortening long import lines, especially in collections.

  Example of using a relative import in collections:

  .. code-block:: python

    # File: ansible_collections/my_namespace/my_collection/plugins/modules/my_module.py
    # Old way to use an absolute import to import module_utils from the collection:
    from ansible_collections.my_namespace.my_collection.plugins.module_utils import my_util
    # New way using a relative import:
    from ..module_utils import my_util

  Modules and module_utils shipped with Ansible can use relative imports as well but the savings
  are smaller:

  .. code-block:: python

    # File: ansible/modules/system/ping.py
    # Old way to use an absolute import to import module_utils from core:
    from ansible.module_utils.basic import AnsibleModule
    # New way using a relative import:
    from ...module_utils.basic import AnsibleModule

  Each single dot (``.``) represents one level of the tree (equivalent to ``../`` in filesystem relative links).

  .. seealso:: `The Python Relative Import Docs <https://www.python.org/dev/peps/pep-0328/#guido-s-decision>`_ go into more detail of how to write relative imports.


Modules removed
---------------

The following modules no longer exist:

* Apstra's ``aos_*`` modules.  See the new modules at  `https://github.com/apstra <https://github.com/apstra>`_.
* ec2_ami_find use :ref:`ec2_ami_facts <ansible_2_9:ec2_ami_facts_module>` instead.
* kubernetes use :ref:`k8s <ansible_2_9:k8s_module>` instead.
* nxos_ip_interface use :ref:`nxos_l3_interface <ansible_2_9:nxos_l3_interface_module>` instead.
* nxos_portchannel use :ref:`nxos_linkagg <ansible_2_9:nxos_linkagg_module>` instead.
* nxos_switchport use :ref:`nxos_l2_interface <ansible_2_9:nxos_l2_interface_module>` instead.
* oc use :ref:`k8s <ansible_2_9:k8s_module>` instead.
* panos_nat_policy use :ref:`panos_nat_rule <ansible_2_9:panos_nat_rule_module>` instead.
* panos_security_policy use :ref:`panos_security_rule <ansible_2_9:panos_security_rule_module>` instead.
* vsphere_guest use :ref:`vmware_guest <ansible_2_9:vmware_guest_module>` instead.


Deprecation notices
-------------------

The following modules will be removed in Ansible 2.13. Please update update your playbooks accordingly.

* cs_instance_facts use :ref:`cs_instance_info <cs_instance_info_module>` instead.

* cs_zone_facts use :ref:`cs_zone_info <cs_zone_info_module>` instead.

* digital_ocean_sshkey_facts use :ref:`digital_ocean_sshkey_info <digital_ocean_sshkey_info_module>` instead.

* eos_interface use :ref:`eos_interfaces <eos_interfaces_module>` instead.

* eos_l2_interface use :ref:`eos_l2_interfaces <eos_l2_interfaces_module>` instead.

* eos_l3_interface use :ref:`eos_l3_interfaces <eos_l3_interfaces_module>` instead.

* eos_linkagg use :ref:`eos_lag_interfaces <eos_lag_interfaces_module>` instead.

* eos_lldp_interface use :ref:`eos_lldp_interfaces <eos_lldp_interfaces_module>` instead.

* eos_vlan use :ref:`eos_vlans <eos_vlans_module>` instead.

* ios_interface use :ref:`ios_interfaces <ios_interfaces_module>` instead.

* ios_l2_interface use :ref:`ios_l2_interfaces <ios_l2_interfaces_module>` instead.

* ios_l3_interface use :ref:`ios_l3_interfaces <ios_l3_interfaces_module>` instead.

* ios_vlan use :ref:`ios_vlans <ios_vlans_module>` instead.

* iosxr_interface use :ref:`iosxr_interfaces <iosxr_interfaces_module>` instead.

* junos_interface use :ref:`junos_interfaces <junos_interfaces_module>` instead.

* junos_l2_interface use :ref:`junos_l2_interfaces <junos_l2_interfaces_module>` instead.

* junos_l3_interface use :ref:`junos_l3_interfaces <junos_l3_interfaces_module>` instead.

* junos_linkagg use :ref:`junos_lag_interfaces <junos_lag_interfaces_module>` instead.

* junos_lldp use :ref:`junos_lldp_global <junos_lldp_global_module>` instead.

* junos_lldp_interface use :ref:`junos_lldp_interfaces <junos_lldp_interfaces_module>` instead.

* junos_vlan use :ref:`junos_vlans <junos_vlans_module>` instead.

* lambda_facts use :ref:`lambda_info <lambda_info_module>` instead.

* na_ontap_gather_facts use :ref:`na_ontap_info <na_ontap_info_module>` instead.

* net_banner use the platform-specific [netos]_banner modules instead.

* net_interface use the new platform-specific [netos]_interfaces modules instead.

* net_l2_interface use the new platform-specific [netos]_l2_interfaces modules instead.

* net_l3_interface use the new platform-specific [netos]_l3_interfaces modules instead.

* net_linkagg use the new platform-specific [netos]_lag modules instead.

* net_lldp use the new platform-specific [netos]_lldp_global modules instead.

* net_lldp_interface use the new platform-specific [netos]_lldp_interfaces modules instead.

* net_logging use the platform-specific [netos]_logging modules instead.

* net_static_route use the platform-specific [netos]_static_route modules instead.

* net_system use the platform-specific [netos]_system modules instead.

* net_user use the platform-specific [netos]_user modules instead.

* net_vlan use the new platform-specific [netos]_vlans modules instead.

* net_vrf use the platform-specific [netos]_vrf modules instead.

* nginx_status_facts use :ref:`nginx_status_info <nginx_status_info_module>` instead.

* nxos_interface use :ref:`nxos_interfaces <nxos_interfaces_module>` instead.

* nxos_l2_interface use :ref:`nxos_l2_interfaces <nxos_l2_interfaces_module>` instead.

* nxos_l3_interface use :ref:`nxos_l3_interfaces <nxos_l3_interfaces_module>` instead.

* nxos_linkagg use :ref:`nxos_lag_interfaces <nxos_lag_interfaces_module>` instead.

* nxos_vlan use :ref:`nxos_vlans <nxos_vlans_module>` instead.

* online_server_facts use :ref:`online_server_info <online_server_info_module>` instead.

* online_user_facts use :ref:`online_user_info <online_user_info_module>` instead.

* purefa_facts use :ref:`purefa_info <purefa_info_module>` instead.

* purefb_facts use :ref:`purefb_info <purefb_info_module>` instead.

* scaleway_image_facts use :ref:`scaleway_image_info <scaleway_image_info_module>` instead.

* scaleway_ip_facts use :ref:`scaleway_ip_info <scaleway_ip_info_module>` instead.

* scaleway_organization_facts use :ref:`scaleway_organization_info <scaleway_organization_info_module>` instead.

* scaleway_security_group_facts use :ref:`scaleway_security_group_info <scaleway_security_group_info_module>` instead.

* scaleway_server_facts use :ref:`scaleway_server_info <scaleway_server_info_module>` instead.

* scaleway_snapshot_facts use :ref:`scaleway_snapshot_info <scaleway_snapshot_info_module>` instead.

* scaleway_volume_facts use :ref:`scaleway_volume_info <scaleway_volume_info_module>` instead.

* vcenter_extension_facts use :ref:`vcenter_extension_info <vcenter_extension_info_module>` instead.

* vmware_about_facts use :ref:`vmware_about_info <vmware_about_info_module>` instead.

* vmware_category_facts use :ref:`vmware_category_info <vmware_category_info_module>` instead.

* vmware_drs_group_facts use :ref:`vmware_drs_group_info <vmware_drs_group_info_module>` instead.

* vmware_drs_rule_facts use :ref:`vmware_drs_rule_info <vmware_drs_rule_info_module>` instead.

* vmware_dvs_portgroup_facts use :ref:`vmware_dvs_portgroup_info <vmware_dvs_portgroup_info_module>` instead.

* vmware_guest_boot_facts use :ref:`vmware_guest_boot_info <vmware_guest_boot_info_module>` instead.

* vmware_guest_customization_facts use :ref:`vmware_guest_customization_info <vmware_guest_customization_info_module>` instead.

* vmware_guest_disk_facts use :ref:`vmware_guest_disk_info <vmware_guest_disk_info_module>` instead.

* vmware_host_capability_facts use :ref:`vmware_host_capability_info <vmware_host_capability_info_module>` instead.

* vmware_host_config_facts use :ref:`vmware_host_config_info <vmware_host_config_info_module>` instead.

* vmware_host_dns_facts use :ref:`vmware_host_dns_info <vmware_host_dns_info_module>` instead.

* vmware_host_feature_facts use :ref:`vmware_host_feature_info <vmware_host_feature_info_module>` instead.

* vmware_host_firewall_facts use :ref:`vmware_host_firewall_info <vmware_host_firewall_info_module>` instead.

* vmware_host_ntp_facts use :ref:`vmware_host_ntp_info <vmware_host_ntp_info_module>` instead.

* vmware_host_package_facts use :ref:`vmware_host_package_info <vmware_host_package_info_module>` instead.

* vmware_host_service_facts use :ref:`vmware_host_service_info <vmware_host_service_info_module>` instead.

* vmware_host_ssl_facts use :ref:`vmware_host_ssl_info <vmware_host_ssl_info_module>` instead.

* vmware_host_vmhba_facts use :ref:`vmware_host_vmhba_info <vmware_host_vmhba_info_module>` instead.

* vmware_host_vmnic_facts use :ref:`vmware_host_vmnic_info <vmware_host_vmnic_info_module>` instead.

* vmware_local_role_facts use :ref:`vmware_local_role_info <vmware_local_role_info_module>` instead.

* vmware_local_user_facts use :ref:`vmware_local_user_info <vmware_local_user_info_module>` instead.

* vmware_portgroup_facts use :ref:`vmware_portgroup_info <vmware_portgroup_info_module>` instead.

* vmware_resource_pool_facts use :ref:`vmware_resource_pool_info <vmware_resource_pool_info_module>` instead.

* vmware_target_canonical_facts use :ref:`vmware_target_canonical_info <vmware_target_canonical_info_module>` instead.

* vmware_vmkernel_facts use :ref:`vmware_vmkernel_info <vmware_vmkernel_info_module>` instead.

* vmware_vswitch_facts use :ref:`vmware_vswitch_info <vmware_vswitch_info_module>` instead.

* vultr_account_facts use :ref:`vultr_account_info <vultr_account_info_module>` instead.

* vultr_block_storage_facts use :ref:`vultr_block_storage_info <vultr_block_storage_info_module>` instead.

* vultr_dns_domain_facts use :ref:`vultr_dns_domain_info <vultr_dns_domain_info_module>` instead.

* vultr_firewall_group_facts use :ref:`vultr_firewall_group_info <vultr_firewall_group_info_module>` instead.

* vultr_network_facts use :ref:`vultr_network_info <vultr_network_info_module>` instead.

* vultr_os_facts use :ref:`vultr_os_info <vultr_os_info_module>` instead.

* vultr_plan_facts use :ref:`vultr_plan_info <vultr_plan_info_module>` instead.

* vultr_region_facts use :ref:`vultr_region_info <vultr_region_info_module>` instead.

* vultr_server_facts use :ref:`vultr_server_info <vultr_server_info_module>` instead.

* vultr_ssh_key_facts use :ref:`vultr_ssh_key_info <vultr_ssh_key_info_module>` instead.

* vultr_startup_script_facts use :ref:`vultr_startup_script_info <vultr_startup_script_info_module>` instead.

* vultr_user_facts use :ref:`vultr_user_info <vultr_user_info_module>` instead.

* vyos_interface use :ref:`vyos_interfaces <vyos_interfaces_module>` instead.

* vyos_l3_interface use :ref:`vyos_l3_interfaces <vyos_l3_interfaces_module>` instead.

* vyos_linkagg use :ref:`vyos_lag_interfaces <vyos_lag_interfaces_module>` instead.

* vyos_lldp use :ref:`vyos_lldp_global <vyos_lldp_global_module>` instead.

* vyos_lldp_interface use :ref:`vyos_lldp_interfaces <vyos_lldp_interfaces_module>` instead.


The following functionality will be removed in Ansible 2.12. Please update update your playbooks accordingly.

* ``vmware_cluster`` DRS, HA and VSAN configuration; use :ref:`vmware_cluster_drs <vmware_cluster_drs_module>`, :ref:`vmware_cluster_ha <vmware_cluster_ha_module>` and :ref:`vmware_cluster_vsan <vmware_cluster_vsan_module>` instead.


The following functionality will be removed in Ansible 2.13. Please update update your playbooks accordingly.

* ``openssl_certificate`` deprecates the ``assertonly`` provider.
  Please see the :ref:`openssl_certificate <openssl_certificate_module>` documentation examples on how to
  replace the provider with the :ref:`openssl_certificate_info <openssl_certificate_info_module>`,
  :ref:`openssl_csr_info <openssl_csr_info_module>`, :ref:`openssl_privatekey_info <openssl_privatekey_info_module>`
  and :ref:`assert <assert_module>` modules.


For the following modules, the PyOpenSSL-based backend ``pyopenssl`` has been deprecated and will be
removed in Ansible 2.13:

* :ref:`get_certificate <get_certificate_module>`
* :ref:`openssl_certificate <openssl_certificate_module>`
* :ref:`openssl_certificate_info <openssl_certificate_info_module>`
* :ref:`openssl_csr <openssl_csr_module>`
* :ref:`openssl_csr_info <openssl_csr_info_module>`
* :ref:`openssl_privatekey <openssl_privatekey_module>`
* :ref:`openssl_privatekey_info <openssl_privatekey_info_module>`
* :ref:`openssl_publickey <openssl_publickey_module>`


Renamed modules
^^^^^^^^^^^^^^^

The following modules have been renamed. The old name is deprecated and will
be removed in Ansible 2.13. Please update update your playbooks accordingly.

* The ``ali_instance_facts`` module was renamed to :ref:`ali_instance_info <ali_instance_info_module>`.
* The ``aws_acm_facts`` module was renamed to :ref:`aws_acm_info <aws_acm_info_module>`.
* The ``aws_az_facts`` module was renamed to :ref:`aws_az_info <aws_az_info_module>`.
* The ``aws_caller_facts`` module was renamed to :ref:`aws_caller_info <aws_caller_info_module>`.
* The ``aws_kms_facts`` module was renamed to :ref:`aws_kms_info <aws_kms_info_module>`.
* The ``aws_region_facts`` module was renamed to :ref:`aws_region_info <aws_region_info_module>`.
* The ``aws_s3_bucket_facts`` module was renamed to :ref:`aws_s3_bucket_info <aws_s3_bucket_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``aws_sgw_facts`` module was renamed to :ref:`aws_sgw_info <aws_sgw_info_module>`.
* The ``aws_waf_facts`` module was renamed to :ref:`aws_waf_info <aws_waf_info_module>`.
* The ``azure_rm_aks_facts`` module was renamed to :ref:`azure_rm_aks_info <azure_rm_aks_info_module>`.
* The ``azure_rm_aksversion_facts`` module was renamed to :ref:`azure_rm_aksversion_info <azure_rm_aksversion_info_module>`.
* The ``azure_rm_applicationsecuritygroup_facts`` module was renamed to :ref:`azure_rm_applicationsecuritygroup_info <azure_rm_applicationsecuritygroup_info_module>`.
* The ``azure_rm_appserviceplan_facts`` module was renamed to :ref:`azure_rm_appserviceplan_info <azure_rm_appserviceplan_info_module>`.
* The ``azure_rm_automationaccount_facts`` module was renamed to :ref:`azure_rm_automationaccount_info <azure_rm_automationaccount_info_module>`.
* The ``azure_rm_autoscale_facts`` module was renamed to :ref:`azure_rm_autoscale_info <azure_rm_autoscale_info_module>`.
* The ``azure_rm_availabilityset_facts`` module was renamed to :ref:`azure_rm_availabilityset_info <azure_rm_availabilityset_info_module>`.
* The ``azure_rm_cdnendpoint_facts`` module was renamed to :ref:`azure_rm_cdnendpoint_info <azure_rm_cdnendpoint_info_module>`.
* The ``azure_rm_cdnprofile_facts`` module was renamed to :ref:`azure_rm_cdnprofile_info <azure_rm_cdnprofile_info_module>`.
* The ``azure_rm_containerinstance_facts`` module was renamed to :ref:`azure_rm_containerinstance_info <azure_rm_containerinstance_info_module>`.
* The ``azure_rm_containerregistry_facts`` module was renamed to :ref:`azure_rm_containerregistry_info <azure_rm_containerregistry_info_module>`.
* The ``azure_rm_cosmosdbaccount_facts`` module was renamed to :ref:`azure_rm_cosmosdbaccount_info <azure_rm_cosmosdbaccount_info_module>`.
* The ``azure_rm_deployment_facts`` module was renamed to :ref:`azure_rm_deployment_info <azure_rm_deployment_info_module>`.
* The ``azure_rm_resourcegroup_facts`` module was renamed to :ref:`azure_rm_resourcegroup_info <azure_rm_resourcegroup_info_module>`.
* The ``bigip_device_facts`` module was renamed to :ref:`bigip_device_info <bigip_device_info_module>`.
* The ``bigiq_device_facts`` module was renamed to :ref:`bigiq_device_info <bigiq_device_info_module>`.
* The ``cloudformation_facts`` module was renamed to :ref:`cloudformation_info <cloudformation_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``cloudfront_facts`` module was renamed to :ref:`cloudfront_info <cloudfront_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``cloudwatchlogs_log_group_facts`` module was renamed to :ref:`cloudwatchlogs_log_group_info <cloudwatchlogs_log_group_info_module>`.
* The ``digital_ocean_account_facts`` module was renamed to :ref:`digital_ocean_account_info <digital_ocean_account_info_module>`.
* The ``digital_ocean_certificate_facts`` module was renamed to :ref:`digital_ocean_certificate_info <digital_ocean_certificate_info_module>`.
* The ``digital_ocean_domain_facts`` module was renamed to :ref:`digital_ocean_domain_info <digital_ocean_domain_info_module>`.
* The ``digital_ocean_firewall_facts`` module was renamed to :ref:`digital_ocean_firewall_info <digital_ocean_firewall_info_module>`.
* The ``digital_ocean_floating_ip_facts`` module was renamed to :ref:`digital_ocean_floating_ip_info <digital_ocean_floating_ip_info_module>`.
* The ``digital_ocean_image_facts`` module was renamed to :ref:`digital_ocean_image_info <digital_ocean_image_info_module>`.
* The ``digital_ocean_load_balancer_facts`` module was renamed to :ref:`digital_ocean_load_balancer_info <digital_ocean_load_balancer_info_module>`.
* The ``digital_ocean_region_facts`` module was renamed to :ref:`digital_ocean_region_info <digital_ocean_region_info_module>`.
* The ``digital_ocean_size_facts`` module was renamed to :ref:`digital_ocean_size_info <digital_ocean_size_info_module>`.
* The ``digital_ocean_snapshot_facts`` module was renamed to :ref:`digital_ocean_snapshot_info <digital_ocean_snapshot_info_module>`.
* The ``digital_ocean_tag_facts`` module was renamed to :ref:`digital_ocean_tag_info <digital_ocean_tag_info_module>`.
* The ``digital_ocean_volume_facts`` module was renamed to :ref:`digital_ocean_volume_info <digital_ocean_volume_info_module>`.
* The ``ec2_ami_facts`` module was renamed to :ref:`ec2_ami_info <ec2_ami_info_module>`.
* The ``ec2_asg_facts`` module was renamed to :ref:`ec2_asg_info <ec2_asg_info_module>`.
* The ``ec2_customer_gateway_facts`` module was renamed to :ref:`ec2_customer_gateway_info <ec2_customer_gateway_info_module>`.
* The ``ec2_eip_facts`` module was renamed to :ref:`ec2_eip_info <ec2_eip_info_module>`.
* The ``ec2_elb_facts`` module was renamed to :ref:`ec2_elb_info <ec2_elb_info_module>`.
* The ``ec2_eni_facts`` module was renamed to :ref:`ec2_eni_info <ec2_eni_info_module>`.
* The ``ec2_group_facts`` module was renamed to :ref:`ec2_group_info <ec2_group_info_module>`.
* The ``ec2_instance_facts`` module was renamed to :ref:`ec2_instance_info <ec2_instance_info_module>`.
* The ``ec2_lc_facts`` module was renamed to :ref:`ec2_lc_info <ec2_lc_info_module>`.
* The ``ec2_placement_group_facts`` module was renamed to :ref:`ec2_placement_group_info <ec2_placement_group_info_module>`.
* The ``ec2_snapshot_facts`` module was renamed to :ref:`ec2_snapshot_info <ec2_snapshot_info_module>`.
* The ``ec2_vol_facts`` module was renamed to :ref:`ec2_vol_info <ec2_vol_info_module>`.
* The ``ec2_vpc_dhcp_option_facts`` module was renamed to :ref:`ec2_vpc_dhcp_option_info <ec2_vpc_dhcp_option_info_module>`.
* The ``ec2_vpc_endpoint_facts`` module was renamed to :ref:`ec2_vpc_endpoint_info <ec2_vpc_endpoint_info_module>`.
* The ``ec2_vpc_igw_facts`` module was renamed to :ref:`ec2_vpc_igw_info <ec2_vpc_igw_info_module>`.
* The ``ec2_vpc_nacl_facts`` module was renamed to :ref:`ec2_vpc_nacl_info <ec2_vpc_nacl_info_module>`.
* The ``ec2_vpc_nat_gateway_facts`` module was renamed to :ref:`ec2_vpc_nat_gateway_info <ec2_vpc_nat_gateway_info_module>`.
* The ``ec2_vpc_net_facts`` module was renamed to :ref:`ec2_vpc_net_info <ec2_vpc_net_info_module>`.
* The ``ec2_vpc_peering_facts`` module was renamed to :ref:`ec2_vpc_peering_info <ec2_vpc_peering_info_module>`.
* The ``ec2_vpc_route_table_facts`` module was renamed to :ref:`ec2_vpc_route_table_info <ec2_vpc_route_table_info_module>`.
* The ``ec2_vpc_subnet_facts`` module was renamed to :ref:`ec2_vpc_subnet_info <ec2_vpc_subnet_info_module>`.
* The ``ec2_vpc_vgw_facts`` module was renamed to :ref:`ec2_vpc_vgw_info <ec2_vpc_vgw_info_module>`.
* The ``ec2_vpc_vpn_facts`` module was renamed to :ref:`ec2_vpc_vpn_info <ec2_vpc_vpn_info_module>`.
* The ``ecs_service_facts`` module was renamed to :ref:`ecs_service_info <ecs_service_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ecs_taskdefinition_facts`` module was renamed to :ref:`ecs_taskdefinition_info <ecs_taskdefinition_info_module>`.
* The ``efs_facts`` module was renamed to :ref:`efs_info <efs_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``elasticache_facts`` module was renamed to :ref:`elasticache_info <elasticache_info_module>`.
* The ``elb_application_lb_facts`` module was renamed to :ref:`elb_application_lb_info <elb_application_lb_info_module>`.
* The ``elb_classic_lb_facts`` module was renamed to :ref:`elb_classic_lb_info <elb_classic_lb_info_module>`.
* The ``elb_target_facts`` module was renamed to :ref:`elb_target_info <elb_target_info_module>`.
* The ``elb_target_group_facts`` module was renamed to :ref:`elb_target_group_info <elb_target_group_info_module>`.
* The ``gcp_bigquery_dataset_facts`` module was renamed to :ref:`gcp_bigquery_dataset_info <gcp_bigquery_dataset_info_module>`.
* The ``gcp_bigquery_table_facts`` module was renamed to :ref:`gcp_bigquery_table_info <gcp_bigquery_table_info_module>`.
* The ``gcp_cloudbuild_trigger_facts`` module was renamed to :ref:`gcp_cloudbuild_trigger_info <gcp_cloudbuild_trigger_info_module>`.
* The ``gcp_compute_address_facts`` module was renamed to :ref:`gcp_compute_address_info <gcp_compute_address_info_module>`.
* The ``gcp_compute_backend_bucket_facts`` module was renamed to :ref:`gcp_compute_backend_bucket_info <gcp_compute_backend_bucket_info_module>`.
* The ``gcp_compute_backend_service_facts`` module was renamed to :ref:`gcp_compute_backend_service_info <gcp_compute_backend_service_info_module>`.
* The ``gcp_compute_disk_facts`` module was renamed to :ref:`gcp_compute_disk_info <gcp_compute_disk_info_module>`.
* The ``gcp_compute_firewall_facts`` module was renamed to :ref:`gcp_compute_firewall_info <gcp_compute_firewall_info_module>`.
* The ``gcp_compute_forwarding_rule_facts`` module was renamed to :ref:`gcp_compute_forwarding_rule_info <gcp_compute_forwarding_rule_info_module>`.
* The ``gcp_compute_global_address_facts`` module was renamed to :ref:`gcp_compute_global_address_info <gcp_compute_global_address_info_module>`.
* The ``gcp_compute_global_forwarding_rule_facts`` module was renamed to :ref:`gcp_compute_global_forwarding_rule_info <gcp_compute_global_forwarding_rule_info_module>`.
* The ``gcp_compute_health_check_facts`` module was renamed to :ref:`gcp_compute_health_check_info <gcp_compute_health_check_info_module>`.
* The ``gcp_compute_http_health_check_facts`` module was renamed to :ref:`gcp_compute_http_health_check_info <gcp_compute_http_health_check_info_module>`.
* The ``gcp_compute_https_health_check_facts`` module was renamed to :ref:`gcp_compute_https_health_check_info <gcp_compute_https_health_check_info_module>`.
* The ``gcp_compute_image_facts`` module was renamed to :ref:`gcp_compute_image_info <gcp_compute_image_info_module>`.
* The ``gcp_compute_instance_facts`` module was renamed to :ref:`gcp_compute_instance_info <gcp_compute_instance_info_module>`.
* The ``gcp_compute_instance_group_facts`` module was renamed to :ref:`gcp_compute_instance_group_info <gcp_compute_instance_group_info_module>`.
* The ``gcp_compute_instance_group_manager_facts`` module was renamed to :ref:`gcp_compute_instance_group_manager_info <gcp_compute_instance_group_manager_info_module>`.
* The ``gcp_compute_instance_template_facts`` module was renamed to :ref:`gcp_compute_instance_template_info <gcp_compute_instance_template_info_module>`.
* The ``gcp_compute_interconnect_attachment_facts`` module was renamed to :ref:`gcp_compute_interconnect_attachment_info <gcp_compute_interconnect_attachment_info_module>`.
* The ``gcp_compute_network_facts`` module was renamed to :ref:`gcp_compute_network_info <gcp_compute_network_info_module>`.
* The ``gcp_compute_region_disk_facts`` module was renamed to :ref:`gcp_compute_region_disk_info <gcp_compute_region_disk_info_module>`.
* The ``gcp_compute_route_facts`` module was renamed to :ref:`gcp_compute_route_info <gcp_compute_route_info_module>`.
* The ``gcp_compute_router_facts`` module was renamed to :ref:`gcp_compute_router_info <gcp_compute_router_info_module>`.
* The ``gcp_compute_ssl_certificate_facts`` module was renamed to :ref:`gcp_compute_ssl_certificate_info <gcp_compute_ssl_certificate_info_module>`.
* The ``gcp_compute_ssl_policy_facts`` module was renamed to :ref:`gcp_compute_ssl_policy_info <gcp_compute_ssl_policy_info_module>`.
* The ``gcp_compute_subnetwork_facts`` module was renamed to :ref:`gcp_compute_subnetwork_info <gcp_compute_subnetwork_info_module>`.
* The ``gcp_compute_target_http_proxy_facts`` module was renamed to :ref:`gcp_compute_target_http_proxy_info <gcp_compute_target_http_proxy_info_module>`.
* The ``gcp_compute_target_https_proxy_facts`` module was renamed to :ref:`gcp_compute_target_https_proxy_info <gcp_compute_target_https_proxy_info_module>`.
* The ``gcp_compute_target_pool_facts`` module was renamed to :ref:`gcp_compute_target_pool_info <gcp_compute_target_pool_info_module>`.
* The ``gcp_compute_target_ssl_proxy_facts`` module was renamed to :ref:`gcp_compute_target_ssl_proxy_info <gcp_compute_target_ssl_proxy_info_module>`.
* The ``gcp_compute_target_tcp_proxy_facts`` module was renamed to :ref:`gcp_compute_target_tcp_proxy_info <gcp_compute_target_tcp_proxy_info_module>`.
* The ``gcp_compute_target_vpn_gateway_facts`` module was renamed to :ref:`gcp_compute_target_vpn_gateway_info <gcp_compute_target_vpn_gateway_info_module>`.
* The ``gcp_compute_url_map_facts`` module was renamed to :ref:`gcp_compute_url_map_info <gcp_compute_url_map_info_module>`.
* The ``gcp_compute_vpn_tunnel_facts`` module was renamed to :ref:`gcp_compute_vpn_tunnel_info <gcp_compute_vpn_tunnel_info_module>`.
* The ``gcp_container_cluster_facts`` module was renamed to :ref:`gcp_container_cluster_info <gcp_container_cluster_info_module>`.
* The ``gcp_container_node_pool_facts`` module was renamed to :ref:`gcp_container_node_pool_info <gcp_container_node_pool_info_module>`.
* The ``gcp_dns_managed_zone_facts`` module was renamed to :ref:`gcp_dns_managed_zone_info <gcp_dns_managed_zone_info_module>`.
* The ``gcp_dns_resource_record_set_facts`` module was renamed to :ref:`gcp_dns_resource_record_set_info <gcp_dns_resource_record_set_info_module>`.
* The ``gcp_iam_role_facts`` module was renamed to :ref:`gcp_iam_role_info <gcp_iam_role_info_module>`.
* The ``gcp_iam_service_account_facts`` module was renamed to :ref:`gcp_iam_service_account_info <gcp_iam_service_account_info_module>`.
* The ``gcp_pubsub_subscription_facts`` module was renamed to :ref:`gcp_pubsub_subscription_info <gcp_pubsub_subscription_info_module>`.
* The ``gcp_pubsub_topic_facts`` module was renamed to :ref:`gcp_pubsub_topic_info <gcp_pubsub_topic_info_module>`.
* The ``gcp_redis_instance_facts`` module was renamed to :ref:`gcp_redis_instance_info <gcp_redis_instance_info_module>`.
* The ``gcp_resourcemanager_project_facts`` module was renamed to :ref:`gcp_resourcemanager_project_info <gcp_resourcemanager_project_info_module>`.
* The ``gcp_sourcerepo_repository_facts`` module was renamed to :ref:`gcp_sourcerepo_repository_info <gcp_sourcerepo_repository_info_module>`.
* The ``gcp_spanner_database_facts`` module was renamed to :ref:`gcp_spanner_database_info <gcp_spanner_database_info_module>`.
* The ``gcp_spanner_instance_facts`` module was renamed to :ref:`gcp_spanner_instance_info <gcp_spanner_instance_info_module>`.
* The ``gcp_sql_database_facts`` module was renamed to :ref:`gcp_sql_database_info <gcp_sql_database_info_module>`.
* The ``gcp_sql_instance_facts`` module was renamed to :ref:`gcp_sql_instance_info <gcp_sql_instance_info_module>`.
* The ``gcp_sql_user_facts`` module was renamed to :ref:`gcp_sql_user_info <gcp_sql_user_info_module>`.
* The ``gcp_tpu_node_facts`` module was renamed to :ref:`gcp_tpu_node_info <gcp_tpu_node_info_module>`.
* The ``gcpubsub_facts`` module was renamed to :ref:`gcpubsub_info <gcpubsub_info_module>`.
* The ``github_webhook_facts`` module was renamed to :ref:`github_webhook_info <github_webhook_info_module>`.
* The ``gluster_heal_facts`` module was renamed to :ref:`gluster_heal_info <gluster_heal_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``hcloud_datacenter_facts`` module was renamed to :ref:`hcloud_datacenter_info <hcloud_datacenter_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``hcloud_floating_ip_facts`` module was renamed to :ref:`hcloud_floating_ip_info <hcloud_floating_ip_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``hcloud_image_facts`` module was renamed to :ref:`hcloud_image_info <hcloud_image_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``hcloud_location_facts`` module was renamed to :ref:`hcloud_location_info <hcloud_location_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``hcloud_server_facts`` module was renamed to :ref:`hcloud_server_info <hcloud_server_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``hcloud_server_type_facts`` module was renamed to :ref:`hcloud_server_type_info <hcloud_server_type_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``hcloud_ssh_key_facts`` module was renamed to :ref:`hcloud_ssh_key_info <hcloud_ssh_key_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``hcloud_volume_facts`` module was renamed to :ref:`hcloud_volume_info <hcloud_volume_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``hpilo_facts`` module was renamed to :ref:`hpilo_info <hpilo_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``iam_mfa_device_facts`` module was renamed to :ref:`iam_mfa_device_info <iam_mfa_device_info_module>`.
* The ``iam_role_facts`` module was renamed to :ref:`iam_role_info <iam_role_info_module>`.
* The ``iam_server_certificate_facts`` module was renamed to :ref:`iam_server_certificate_info <iam_server_certificate_info_module>`.
* The ``idrac_redfish_facts`` module was renamed to :ref:`idrac_redfish_info <idrac_redfish_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``intersight_facts`` module was renamed to :ref:`intersight_info <intersight_info_module>`.
* The ``jenkins_job_facts`` module was renamed to :ref:`jenkins_job_info <jenkins_job_info_module>`.
* The ``k8s_facts`` module was renamed to :ref:`k8s_info <k8s_info_module>`.
* The ``memset_memstore_facts`` module was renamed to :ref:`memset_memstore_info <memset_memstore_info_module>`.
* The ``memset_server_facts`` module was renamed to :ref:`memset_server_info <memset_server_info_module>`.
* The ``one_image_facts`` module was renamed to :ref:`one_image_info <one_image_info_module>`.
* The ``onepassword_facts`` module was renamed to :ref:`onepassword_info <onepassword_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``oneview_datacenter_facts`` module was renamed to :ref:`oneview_datacenter_info <oneview_datacenter_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``oneview_enclosure_facts`` module was renamed to :ref:`oneview_enclosure_info <oneview_enclosure_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``oneview_ethernet_network_facts`` module was renamed to :ref:`oneview_ethernet_network_info <oneview_ethernet_network_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``oneview_fc_network_facts`` module was renamed to :ref:`oneview_fc_network_info <oneview_fc_network_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``oneview_fcoe_network_facts`` module was renamed to :ref:`oneview_fcoe_network_info <oneview_fcoe_network_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``oneview_logical_interconnect_group_facts`` module was renamed to :ref:`oneview_logical_interconnect_group_info <oneview_logical_interconnect_group_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``oneview_network_set_facts`` module was renamed to :ref:`oneview_network_set_info <oneview_network_set_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``oneview_san_manager_facts`` module was renamed to :ref:`oneview_san_manager_info <oneview_san_manager_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``os_flavor_facts`` module was renamed to :ref:`os_flavor_info <os_flavor_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``os_image_facts`` module was renamed to :ref:`os_image_info <os_image_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``os_keystone_domain_facts`` module was renamed to :ref:`os_keystone_domain_info <os_keystone_domain_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``os_networks_facts`` module was renamed to :ref:`os_networks_info <os_networks_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``os_port_facts`` module was renamed to :ref:`os_port_info <os_port_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``os_project_facts`` module was renamed to :ref:`os_project_info <os_project_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``os_server_facts`` module was renamed to :ref:`os_server_info <os_server_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``os_subnets_facts`` module was renamed to :ref:`os_subnets_info <os_subnets_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``os_user_facts`` module was renamed to :ref:`os_user_info <os_user_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_affinity_label_facts`` module was renamed to :ref:`ovirt_affinity_label_info <ovirt_affinity_label_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_api_facts`` module was renamed to :ref:`ovirt_api_info <ovirt_api_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_cluster_facts`` module was renamed to :ref:`ovirt_cluster_info <ovirt_cluster_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_datacenter_facts`` module was renamed to :ref:`ovirt_datacenter_info <ovirt_datacenter_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_disk_facts`` module was renamed to :ref:`ovirt_disk_info <ovirt_disk_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_event_facts`` module was renamed to :ref:`ovirt_event_info <ovirt_event_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_external_provider_facts`` module was renamed to :ref:`ovirt_external_provider_info <ovirt_external_provider_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_group_facts`` module was renamed to :ref:`ovirt_group_info <ovirt_group_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_host_facts`` module was renamed to :ref:`ovirt_host_info <ovirt_host_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_host_storage_facts`` module was renamed to :ref:`ovirt_host_storage_info <ovirt_host_storage_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_network_facts`` module was renamed to :ref:`ovirt_network_info <ovirt_network_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_nic_facts`` module was renamed to :ref:`ovirt_nic_info <ovirt_nic_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_permission_facts`` module was renamed to :ref:`ovirt_permission_info <ovirt_permission_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_quota_facts`` module was renamed to :ref:`ovirt_quota_info <ovirt_quota_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_scheduling_policy_facts`` module was renamed to :ref:`ovirt_scheduling_policy_info <ovirt_scheduling_policy_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_snapshot_facts`` module was renamed to :ref:`ovirt_snapshot_info <ovirt_snapshot_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_storage_domain_facts`` module was renamed to :ref:`ovirt_storage_domain_info <ovirt_storage_domain_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_storage_template_facts`` module was renamed to :ref:`ovirt_storage_template_info <ovirt_storage_template_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_storage_vm_facts`` module was renamed to :ref:`ovirt_storage_vm_info <ovirt_storage_vm_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_tag_facts`` module was renamed to :ref:`ovirt_tag_info <ovirt_tag_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_template_facts`` module was renamed to :ref:`ovirt_template_info <ovirt_template_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_user_facts`` module was renamed to :ref:`ovirt_user_info <ovirt_user_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_vm_facts`` module was renamed to :ref:`ovirt_vm_info <ovirt_vm_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``ovirt_vmpool_facts`` module was renamed to :ref:`ovirt_vmpool_info <ovirt_vmpool_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``python_requirements_facts`` module was renamed to :ref:`python_requirements_info <python_requirements_info_module>`.
* The ``rds_instance_facts`` module was renamed to :ref:`rds_instance_info <rds_instance_info_module>`.
* The ``rds_snapshot_facts`` module was renamed to :ref:`rds_snapshot_info <rds_snapshot_info_module>`.
* The ``redfish_facts`` module was renamed to :ref:`redfish_info <redfish_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``redshift_facts`` module was renamed to :ref:`redshift_info <redshift_info_module>`.
* The ``route53_facts`` module was renamed to :ref:`route53_info <route53_info_module>`.
* The ``smartos_image_facts`` module was renamed to :ref:`smartos_image_info <ali_instance_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``vertica_facts`` module was renamed to :ref:`vertica_info <vertica_info_module>`.
  When called with the new name, the module no longer returns ``ansible_facts``.
  To access return values, :ref:`register a variable <registered_variables>`.
* The ``vmware_cluster_facts`` module was renamed to :ref:`vmware_cluster_info <vmware_cluster_info_module>`.
* The ``vmware_datastore_facts`` module was renamed to :ref:`vmware_datastore_info <vmware_datastore_info_module>`.
* The ``vmware_guest_facts`` module was renamed to :ref:`vmware_guest_info <vmware_guest_info_module>`.
* The ``vmware_guest_snapshot_facts`` module was renamed to :ref:`vmware_guest_snapshot_info <vmware_guest_snapshot_info_module>`.
* The ``vmware_tag_facts`` module was renamed to :ref:`vmware_tag_info <vmware_tag_info_module>`.
* The ``vmware_vm_facts`` module was renamed to :ref:`vmware_vm_info <vmware_vm_info_module>`.
* The ``xenserver_guest_facts`` module was renamed to :ref:`xenserver_guest_info <xenserver_guest_info_module>`.
* The ``zabbix_group_facts`` module was renamed to :ref:`zabbix_group_info <zabbix_group_info_module>`.
* The ``zabbix_host_facts`` module was renamed to :ref:`zabbix_host_info <zabbix_host_info_module>`.

Noteworthy module changes
-------------------------

* :ref:`vmware_cluster <vmware_cluster_module>` was refactored for easier maintenance/bugfixes. Use the three new, specialized modules to configure clusters. Configure DRS with :ref:`vmware_cluster_drs <vmware_cluster_drs_module>`, HA with :ref:`vmware_cluster_ha <vmware_cluster_ha_module>` and vSAN with :ref:`vmware_cluster_vsan <vmware_cluster_vsan_module>`.
* :ref:`vmware_dvswitch <vmware_dvswitch_module>` accepts ``folder`` parameter to place dvswitch in user defined folder. This option makes ``datacenter`` as an optional parameter.
* :ref:`vmware_datastore_cluster <vmware_datastore_cluster_module>` accepts ``folder`` parameter to place datastore cluster in user defined folder. This option makes ``datacenter`` as an optional parameter.
* :ref:`mysql_db <mysql_db_module>` returns new ``db_list`` parameter in addition to ``db`` parameter. This ``db_list`` parameter refers to list of database names. ``db`` parameter will be deprecated in version 2.13.
* :ref:`snow_record <snow_record_module>` and :ref:`snow_record_find <snow_record_find_module>` now takes environment variables for ``instance``, ``username`` and ``password`` parameters. This change marks these parameters as optional.
* The deprecated ``force`` option in ``win_firewall_rule`` has been removed.
* :ref:`openssl_certificate <openssl_certificate_module>`'s ``ownca`` provider creates authority key identifiers if not explicitly disabled with ``ownca_create_authority_key_identifier: no``. This is only the case for the ``cryptography`` backend, which is selected by default if the ``cryptography`` library is available.
* :ref:`openssl_certificate <openssl_certificate_module>`'s ``ownca`` and ``selfsigned`` providers create subject key identifiers if not explicitly disabled with ``ownca_create_subject_key_identifier: never_create`` resp. ``selfsigned_create_subject_key_identifier: never_create``. If a subject key identifier is provided by the CSR, it is taken; if not, it is created from the public key. This is only the case for the ``cryptography`` backend, which is selected by default if the ``cryptography`` library is available.
* :ref:`openssh_keypair <openssh_keypair_module>` now applies the same file permissions and ownership to both public and private keys (both get the same ``mode``, ``owner``, ``group``, and so on). If you need to change permissions / ownership on one key, use the :ref:`file <file_module>` to modify it after it is created.


Plugins
=======

Removed Lookup Plugins
----------------------

* ``redis_kv`` use :ref:`redis <redis_lookup>` instead.


Porting custom scripts
======================

No notable changes


Networking
==========

Network resource modules
------------------------

Ansible 2.9 introduced the first batch of network resource modules. Sections of a network device's configuration can be thought of as a resource provided by that device. Network resource modules are intentionally scoped to configure a single resource and you can combine them as building blocks to configure complex network services. The older modules are deprecated in Ansible 2.9 and will be removed in Ansible 2.13. You should scan the list of deprecated modules above and replace them with the new network resource modules in your playbooks. See `Ansible Network Features in 2.9 <https://www.ansible.com/blog/network-features-coming-soon-in-ansible-engine-2.9>`_ for details.

Improved ``gather_facts`` support for network devices
-----------------------------------------------------

In Ansible 2.9, the ``gather_facts`` keyword now supports gathering network device facts in standardized key/value pairs. You can feed these network facts into further tasks to manage the network device. You can also use the new ``gather_network_resources`` parameter with the network ``*_facts`` modules (such as :ref:`eos_facts <eos_facts_module>`) to return just a subset of the device configuration.  See :ref:`network_gather_facts` for an example.

Top-level connection arguments removed in 2.9
---------------------------------------------

Top-level connection arguments like ``username``, ``host``, and ``password`` are  removed in version 2.9.

**OLD** In Ansible < 2.4

.. code-block:: yaml

    - name: example of using top-level options for connection properties
      ios_command:
        commands: show version
        host: "{{ inventory_hostname }}"
        username: cisco
        password: cisco
        authorize: yes
        auth_pass: cisco


Change your playbooks to the connection types ``network_cli`` and ``netconf`` using standard Ansible connection properties, and setting those properties in inventory by group. As you update your playbooks and inventory files, you can easily make the change to ``become`` for privilege escalation (on platforms that support it). For more information, see the :ref:`using become with network modules<become_network>` guide and the :ref:`platform documentation<platform_options>`.
