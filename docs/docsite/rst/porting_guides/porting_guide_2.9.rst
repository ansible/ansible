
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

 * ``hash_behaviour`` now affects inventory sources. If you have it set to ``merge``, the data you get from inventory might change and you will have to update playbooks accordingly. If you're using the default setting (``overwrite``), you will see no changes. Inventory was ignoring this setting.


Command Line
============

No notable changes


Deprecated
==========

No notable changes


Modules
=======

* The ``win_get_url`` and ``win_uri`` module now sends requests with a default ``User-Agent`` of ``ansible-httpget``. This can be changed by using the ``http_agent`` key.


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

The following modules will be removed in Ansible 2.13. Please update update your playbooks accordingly.

* nxos_linkagg use :ref:`nxos_lag_interfaces <nxos_lag_interfaces_module>` instead.

* vyos_interface use :ref:`vyos_interfaces <vyos_interfaces_module>` instead.
 
* vyos_l3_interface use :ref:`vyos_l3_interfaces <vyos_l3_interfaces_module>` instead.

The following functionality will be removed in Ansible 2.12. Please update update your playbooks accordingly.

* ``vmware_cluster`` DRS, HA and VSAN configuration; use `vmware_cluster_drs <vmware_cluster_drs_module>`, `vmware_cluster_ha <vmware_cluster_ha_module>` and `vmware_cluster_vsan <vmware_cluster_vsan_module>` instead.


Noteworthy module changes
-------------------------

* :ref:`vmware_cluster <vmware_cluster_module>` was refactored for easier maintenance/bugfixes. Use the three new, specialized modules to configure clusters. Configure DRS with :ref:`vmware_cluster_drs <vmware_cluster_drs_module>`, HA with :ref:`vmware_cluster_ha <vmware_cluster_ha_module>` and vSAN with :ref:`vmware_cluster_vsan <vmware_cluster_vsan_module>`.
* `vmware_dvswitch <vmware_dvswitch_module>` accepts `folder` parameter to place dvswitch in user defined folder. This option makes `datacenter` as an optional parameter.
* `vmware_datastore_cluster <vmware_datastore_cluster_module>` accepts `folder` parameter to place datastore cluster in user defined folder. This option makes `datacenter` as an optional parameter.
* `mysql_db <mysql_db_module>` returns new `db_list` parameter in addition to `db` parameter. This `db_list` parameter refers to list of database names. `db` parameter will be deprecated in version `2.13`.
* `snow_record <snow_record_module>` and `snow_record_find <snow_record_find_module>` now takes environment variables for `instance`, `username` and `password` parameters. This change marks these parameters as optional.
* The ``python_requirements_facts`` module was renamed to :ref:`python_requirements_info <python_requirements_info_module>`.
* The ``jenkins_job_facts`` module was renamed to :ref:`jenkins_job_info <jenkins_job_info_module>`.
* The ``intersight_facts`` module was renamed to :ref:`intersight_info <intersight_info_module>`.
* The ``zabbix_group_facts`` module was renamed to :ref:`zabbix_group_info <zabbix_group_info_module>`.
* The ``zabbix_host_facts`` module was renamed to :ref:`zabbix_host_info <zabbix_host_info_module>`.
* The ``github_webhook_facts`` module was renamed to :ref:`github_webhook_info <github_webhook_info_module>`.
* The ``k8s_facts`` module was renamed to :ref:`k8s_info <k8s_info_module>`.
* The ``bigip_device_facts`` module was renamed to :ref:`bigip_device_info <bigip_device_info_module>`.
* The ``bigiq_device_facts`` module was renamed to :ref:`bigiq_device_info <bigiq_device_info_module>`.
* The ``memset_memstore_facts`` module was renamed to :ref:`memset_memstore_info <memset_memstore_info_module>`.
* The ``memset_server_facts`` module was renamed to :ref:`memset_server_info <memset_server_info_module>`.
* The ``one_image_facts`` module was renamed to :ref:`one_image_info <one_image_info_module>`.
* The ``ali_instance_facts`` module was renamed to :ref:`ali_instance_info <ali_instance_info_module>`.
* The ``xenserver_guest_facts`` module was renamed to :ref:`xenserver_guest_info <xenserver_guest_info_module>`.
* The ``azure_rm_resourcegroup_facts`` module was renamed to :ref:`azure_rm_resourcegroup_info <azure_rm_resourcegroup_info_module>`.
* The ``gcpubsub_facts`` module was renamed to :ref:`gcpubsub_info <gcpubsub_info_module>`.
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
* The ``aws_acm_facts`` module was renamed to :ref:`aws_acm_info <aws_acm_info_module>`.
* The ``aws_az_facts`` module was renamed to :ref:`aws_az_info <aws_az_info_module>`.
* The ``aws_caller_facts`` module was renamed to :ref:`aws_caller_info <aws_caller_info_module>`.
* The ``aws_kms_facts`` module was renamed to :ref:`aws_kms_info <aws_kms_info_module>`.
* The ``aws_region_facts`` module was renamed to :ref:`aws_region_info <aws_region_info_module>`.
* The ``aws_sgw_facts`` module was renamed to :ref:`aws_sgw_info <aws_sgw_info_module>`.
* The ``aws_waf_facts`` module was renamed to :ref:`aws_waf_info <aws_waf_info_module>`.
* The ``cloudwatchlogs_log_group_facts`` module was renamed to :ref:`cloudwatchlogs_log_group_info <cloudwatchlogs_log_group_info_module>`.
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
* The ``ecs_taskdefinition_facts`` module was renamed to :ref:`ecs_taskdefinition_info <ecs_taskdefinition_info_module>`.
* The ``elasticache_facts`` module was renamed to :ref:`elasticache_info <elasticache_info_module>`.
* The ``elb_application_lb_facts`` module was renamed to :ref:`elb_application_lb_info <elb_application_lb_info_module>`.
* The ``elb_classic_lb_facts`` module was renamed to :ref:`elb_classic_lb_info <elb_classic_lb_info_module>`.
* The ``elb_target_facts`` module was renamed to :ref:`elb_target_info <elb_target_info_module>`.
* The ``elb_target_group_facts`` module was renamed to :ref:`elb_target_group_info <elb_target_group_info_module>`.
* The ``iam_mfa_device_facts`` module was renamed to :ref:`iam_mfa_device_info <iam_mfa_device_info_module>`.
* The ``iam_role_facts`` module was renamed to :ref:`iam_role_info <iam_role_info_module>`.
* The ``iam_server_certificate_facts`` module was renamed to :ref:`iam_server_certificate_info <iam_server_certificate_info_module>`.
* The ``rds_instance_facts`` module was renamed to :ref:`rds_instance_info <rds_instance_info_module>`.
* The ``rds_snapshot_facts`` module was renamed to :ref:`rds_snapshot_info <rds_snapshot_info_module>`.
* The ``redshift_facts`` module was renamed to :ref:`redshift_info <redshift_info_module>`.
* The ``route53_facts`` module was renamed to :ref:`route53_info <route53_info_module>`.
* The deprecated ``force`` option in ``win_firewall_rule`` has been removed.


Plugins
=======

No notable changes


Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes
