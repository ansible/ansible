========================================
Ansible 2.7 "In the Light" Release Notes
========================================

v2.7.0.a1
=========

Release Summary
---------------

| Release Date: 2018-10-04
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Major Changes
-------------

- Allow config to enable native jinja types (https://github.com/ansible/ansible/pull/32738)
- Extends `module_defaults` by adding a prefix to defaults `group/` which denotes a builtin or user-specified list of modules, such as `group/aws` or `group/gcp`
- New keyword `ignore_unreachable` for plays and blocks. Allows ignoring tasks that fail due to unreachable hosts, and check results with `is unreachable` test.
- New yumdnf module defines the shared argument specification for both yum and dnf modules and provides an entry point to share code when applicable
- Remove support for simplejson (https://github.com/ansible/ansible/issues/42761)
- Support for running an Ansible controller with Python-2.6 has been dropped. You can still manage machines which use Python-2.6 but you will have to manage them from a machine which has Python-2.7 or Python-3.5 or greater installed.  See the `porting guide <https://docs.ansible.com/ansible/devel/porting_guides/porting_guide_2.7.html>`_ if you need more information.
- new yum action plugin enables the yum module to work with both yum3 and dnf-based yum4 by detecting the backend package manager and routing commands through the correct Ansible module for that python API
- yum and dnf modules now at feature parity

Minor Changes
-------------

- ActionBase - removed deprecated _fixup_perms method (https://github.com/ansible/ansible/pull/44320)
- Add `is_boto3_error_code` function to `module_utils/aws/core.py` to make it easier for modules to handle special AWS error codes.
- Add use_backend to yum module/action plugin
- Added PrivilegeUtil PowerShell module util to easily control Windows Privileges in a process
- Added capability to skip ssl verification on zabbix host with dynamic inventory
- Added inventory.any_unparsed_is_failed configuration setting. In an inventory with a static hosts file and (say) ec2.py, enabling this setting will cause a failure instead of a warning if ec2.py fails.
- Added new filter to generate random MAC addresses from a given string acting as a prefix. Refer to the appropriate entry which has been added to user_guide playbook_filters.rst document.
- Added the from_yaml_all filter to parse multi-document yaml strings. Refer to the appropriate entry which as been added to user_guide playbooks_filters.rst document.
- Ansible-2.7 changes the Ansiballz strategy for running modules remotely so that invoking a module only needs to invoke python once per module on the remote machine instead of twice.
- Better error handling for depsolve and transaction errors in DNF
- Changed the prefix of all Vultr modules from vr to vultr (https://github.com/ansible/ansible/issues/42942).
- Enable installroot tests for yum4(dnf) integration testing, dnf backend now supports that
- Explicit encoding for the output of the template module, to be able to generate non-utf8 files from a utf-8 template. (https://github.com/ansible/proposals/issues/121)
- File locking feature added, making it possible to gain exclusive access to given file through module_utils.common.file.FileLock (https://github.com/ansible/ansible/issues/29962)
- Fix dnf handling of autoremove to be compatible with yum
- Fixed group action idempotent transactions in dnf backend
- Fixed group actions in check mode to report correct changed state
- In Ansible-2.4 and above, Ansible passes the temporary directory a module should use to the module.  This is done via a module parameter (_ansible_tmpdir).  An earlier version of this which was also prototyped in Ansible-2.4 development used an environment variable, ANSIBLE_REMOTE_TMP to pass this information to the module instead.  When we switched to using a module parameter, the environment variable was left in by mistake. Ansible-2.7 removes that variable.  Any third party modules which relied on it should use the module parameter instead.
- New config options `display_ok_hosts` and `display_failed_stderr` (along with the existing `display_skipped_hosts` option) allow more fine-grained control over the way that ansible displays output from a playbook (https://github.com/ansible/ansible/pull/41058)
- Removed an unnecessary import from the AnsiballZ wrapper
- Restore module_utils.basic.BOOLEANS variable for backwards compatibility with the module API in older ansible releases.
- Setting file attributes (via the file module amongst others) now accepts + and - modifiers to add or remove individual attributes. (https://github.com/ansible/ansible/issues/33838)
- Switch from zip to bc for certain package install/remove test cases in yum integration tests. The dnf depsolver downgrades python when you uninstall zip which alters the test environment and we have no control over that.
- The acme_account and acme_certificate modules now support two backends: the Python cryptograpy module or the OpenSSL binary. By default, the modules detect if a new enough cryptography module is available and use it, with the OpenSSL binary being a fallback. If the detection fails for some reason, the OpenSSL binary backend can be explicitly selected by setting select_crypto_backend to openssl.
- The apt, ec2_elb_lb, elb_classic_lb, and unarchive modules have been ported away from using __file__.  This is futureproofing as__file__ won't work if we switch to using python -m to invoke modules in the future or if we figure out a way to make a module never touch disk for pipelining purposes.
- The password_hash filter supports all parameters of passlib. This allows users to provide a rounds parameter. (https://github.com/ansible/ansible/issues/15326)
- allow user to customize default ansible-console prompt/msg default color
- aws_caller_facts - The module now outputs the "account_alias" as well
- aws_rds - Add new inventory plugin for RDS instances and clusters to match behavior in the ec2 inventory script.
- command module - Add support for check mode when passing creates or removes arguments. (https://github.com/ansible/ansible/pull/40428)
- ec2_group - Add diff mode support with and without check mode. This feature is preview and may change when a common framework is adopted for AWS modules.
- elasticsearch_plugin - Add the possibility to use the elasticsearch_plugin installation batch mode to install plugins with advanced privileges without user interaction.
- gather_subset - removed deprecated functionality for using comma separated list with gather_subset (https://github.com/ansible/ansible/pull/44320)
- get_url - implement [expend checksum format to <algorithm>:(<checksum>|<url>)] (https://github.com/ansible/ansible/issues/27617)
- lineinfile - add warning when using an empty regexp (https://github.com/ansible/ansible/issues/29443)
- password_hash is not restricted to the subset provided by crypt.crypt (https://github.com/ansible/ansible/issues/17266)
- passwordstore - Add backup option when overwriting password (off by default)
- puppet - Add support for --debug, --verbose, --summarize https://github.com/ansible/ansible/issues/37986
- puppet - Add support for setting logdest to both stdout and syslog via 'all'
- replace copy.deepcopy in high workload areas with a custom function to improve performance (https://github.com/ansible/ansible/pull/44337)
- roles - removed deprecated functionality for non YAML role specs (https://github.com/ansible/ansible/pull/44320)
- roles - removed deprecated special casing functionality of connection, port, and remote_user for role params (https://github.com/ansible/ansible/pull/44320)
- service - removed deprecated state=running (https://github.com/ansible/ansible/pull/44320)
- shell module - Add support for check mode when passing creates or removes arguments. (https://github.com/ansible/ansible/pull/40428)
- sns_topic - Port sns_topic module to boto3 and add an integration test suite.
- ssh - reset connection will show a warning instead of failing for older OpenSSH versions
- to_nice_json - specify separators to json.dumps to normalize the output between python2 and python3 (https://github.com/ansible/ansible/pull/42633)
- user - backup shadow file on platforms where the module modifies it directly (https://github.com/ansible/ansible/issues/40696)
- user module - add a sanity check for the user's password and a more helpful warning message (https://github.com/ansible/ansible/pull/43615)
- vars_prompt - removed deprecated functionality supporting 'short form' for vars_prompt (https://github.com/ansible/ansible/pull/44320)
- vault - removed deprecated functionality for insecure VaultAES class (https://github.com/ansible/ansible/pull/44320)
- win_chocolatey - Add support for installing Chocolatey itself from a source feed
- win_chocolatey - Add support for username and password on source feeds
- win_chocolatey - Added ability to specify multiple packages as a list in 1 module invocation
- win_chocolatey - Removed the need to manually escape double quotes in the proxy username and password
- win_chocolatey - Will no longer upgrade Chocolatey in check mode
- win_chocolatey - set the rc return value to always be returned, default to 0 https://github.com/ansible/ansible/issues/41758
- winrm - change the _reset() method to use reset() that is part of ConnectionBase

Deprecated Features
-------------------

- Modules will no longer be able to rely on the __file__ attribute pointing to a real file.  If your third party module is using __file__ for something it should be changed before 2.8.  See the 2.7 porting guide for more information.
- The `skippy`, `full_skip`, `actionable`, and `stderr` callback plugins have been deprecated in favor of config options that influence the behavior of the `default` callback plugin (https://github.com/ansible/ansible/pull/41058)

Removed Features (previously deprecated)
----------------------------------------

- The configuration toggle, ``merge_multiple_cli_tags``, has been removed. This setting controlled whether specifying ``--tags`` or ``--skip-tags`` multiple times on the commandline would merge the specified tags or use the old behaviour of overwriting the previous entry.  The overwriting behaviour was deprecated in 2.3 and the default value of the config option became merge in 2.4.
- ec2_facts - deprecated module removed (https://github.com/ansible/ansible/pull/44536)
- s3 - deprecated module removed (https://github.com/ansible/ansible/pull/44537)

Bugfixes
--------

- **Security Fix** - Some connection exceptions would cause no_log specified on a task to be ignored.  If this happened, the task information, including any private information could have been displayed to stdout and (if enabled, not the default) logged to a log file specified in ansible.cfg's log_path. Additionally, sites which redirected stdout from ansible runs to a log file may have stored that private information onto disk that way as well. (https://github.com/ansible/ansible/pull/41414)
- **Security Fix** - avoid loading host/group vars from cwd when not specifying a playbook or playbook base dir
- **Security Fix** - avoid using ansible.cfg in a world writable dir.
- Additional checks ensure that there is always a result of hashing passwords in the password_hash filter and vars_prompt, otherwise an error is returned. Some modules (like user module) interprets None as no password at all, which can be dangerous if the password given above is passed directly into those modules.
- Avoids deprecated functionality of passlib with newer library versions.
- Changed the admin_users config option to not include "admin" by default as admin is frequently used for a non-privileged account  (https://github.com/ansible/ansible/pull/41164)
- Fix alt linux detection/matching
- Fix an atomic_move error that is 'true', but  misleading. Now we show all 3 files involved and clarify what happened.
- Fix glob path of rc.d Some distribtuions like SUSE has the rc%.d directories under /etc/init.d
- Fix lxd module to be idempotent when the given configuration for the lxd container has not changed (https://github.com/ansible/ansible/pull/38166)
- Fix the mount module's handling of swap entries in fstab (https://github.com/ansible/ansible/pull/42837)
- Fixed an issue where ``ansible_facts.pkg_mgr`` would incorrectly set to ``zypper`` on Debian/Ubuntu systems that happened to have the command installed.
- Fixed runtime module to be able to handle syslog_facility properly when python systemd module installed in a target system. (https://github.com/ansible/ansible/pull/41078)
- Grafana dashboard module compatible with grafana 5 (https://github.com/ansible/ansible/pull/41249)
- On Python2, loading config values from environment variables could lead to a traceback if there were nonascii characters present.  Converted them to text strings so that no traceback will occur (https://github.com/ansible/ansible/pull/43468)
- The fix for `CVE-2018-10875 <https://access.redhat.com/security/cve/cve-2018-10875>`__ prints out a warning message about skipping a config file from a world writable current working directory.  However, if the user explicitly specifies that the config file should be used via the ANSIBLE_CONFIG environment variable then Ansible would honor that but still print out the warning message.  This has been fixed so that Ansible honors the user's explicit wishes and does not print a warning message in that circumstance.
- The fix for `CVE-2018-10875 <https://access.redhat.com/security/cve/cve-2018-10875>`__ prints out a warning message about skipping a config file from a world writable current working directory.  However, if the user is in a world writable current working directory which does not contain a config file, it should not print a warning message.  This release fixes that extaneous warning.
- The ssh connection plugin was categorizing all 255 exit statuses as an ssh error but modules can return exit code 255 as well.  The connection plugin has now been changed to know that certain instances of exit code 255 are not ssh-related.  (https://github.com/ansible/ansible/pull/41716)
- allow custom endpoints to be used in the aws_s3 module (https://github.com/ansible/ansible/pull/36832)
- allow gathering env exception to work even when injection is off
- always correctly template no log for tasks https://github.com/ansible/ansible/issues/43294
- ansible-galaxy - properly list all roles in roles_path (https://github.com/ansible/ansible/issues/43010)
- authorized_key now have an option for following symlinks, default behaviour (False) can be changed by setting follow True/False
- basic.py - catch ValueError in case a FIPS enabled platform raises this exception - https://github.com/ansible/ansible/issues/44447
- become runas - changed runas process so it does not create a temporary file on the disk during execution
- elasticsearch_plugin - Improve error messages and show stderr of elasticsearch commands
- elb_application_lb - Fix a dangerous behavior of deleting an ELB if state was omitted from the task. Now state defaults to 'present', which is typical throughout AWS modules.
- file module - The touch subcommand had its diff output broken during the 2.6.x development cycle.  The patch to fix that broke check mode. This is now fixed (https://github.com/ansible/ansible/issues/42111)
- file module - The touch subcommand had its diff output broken during the 2.6.x development cycle.  This is now fixed (https://github.com/ansible/ansible/issues/41755)
- fix async for the aws_s3 module by adding async support to the action plugin (https://github.com/ansible/ansible/pull/40826)
- fix decrypting vault files for the aws_s3 module (https://github.com/ansible/ansible/pull/39634)
- fix default SSL version for docker modules https://github.com/ansible/ansible/issues/42897
- fix for the bundled selectors module (used in the ssh and local connection plugins) when a syscall is restarted after being interrupted by a signal (https://github.com/ansible/ansible/issues/41630)
- fix mail module for python 3.7.0 (https://github.com/ansible/ansible/pull/44552)
- fix the enable_snat parameter that is only supposed to be used by an user with the right policies. https://github.com/ansible/ansible/pull/44418
- fix the remote tmp folder permissions issue when becoming a non admin user - https://github.com/ansible/ansible/issues/41340, https://github.com/ansible/ansible/issues/42117
- flatten filter - use better method of type checking allowing flattening of mutable and non-mutable sequences (https://github.com/ansible/ansible/pull/44331)
- gce_net - Fix sorting of allowed ports (https://github.com/ansible/ansible/pull/41567)
- get_url - fix the bug that get_url does not change mode when checksum matches (https://github.com/ansible/ansible/issues/29614)
- inventory - When using an inventory directory, ensure extension comparison uses text types (https://github.com/ansible/ansible/pull/42475)
- made irc module python3 compatible https://github.com/ansible/ansible/issues/42256
- nclu - no longer runs net on empty lines in templates (https://github.com/ansible/ansible/pull/43024)
- nicer message when we are missing interpreter
- password_hash does not hard-code the salt-length, which fixes bcrypt in connection with passlib as bcrypt requires a salt with length 22.
- pause - do not set stdout to raw mode when redirecting to a file (https://github.com/ansible/ansible/issues/41717)
- pause - nest try except when importing curses to gracefully fail if curses is not present (https://github.com/ansible/ansible/issues/42004)
- plugins/inventory/openstack.py - Do not create group with empty name if region is not set
- preseve delegation info on nolog https://github.com/ansible/ansible/issues/42344
- remove ambiguity when it comes to 'the source'
- urls - Only assume GET method if data is empty, otherwise POST
- user - Strip trailing comments in /etc/default/passwd (https://github.com/ansible/ansible/pull/43931)
- user - fix bug that resulted in module always reporting a change when specifiying the home directory on FreeBSD (https://github.com/ansible/ansible/issues/42484)
- user - use correct attribute name in FreeBSD for creat_home (https://github.com/ansible/ansible/pull/42711)
- vars_prompt - properly template play level variables in vars_prompt (https://github.com/ansible/ansible/issues/37984)
- vars_prompt with encrypt does not require passlib for the algorithms supported by crypt.
- vault - fix error message encoding, and ensure we present a friendlier error when the EDITOR is missing (https://github.com/ansible/ansible/pull/44423)
- win_chocolatey - enable TLSv1.2 support when downloading the Chocolatey installer https://github.com/ansible/ansible/issues/41906
- win_chocolatey - fix issue where state=downgrade would upgrade a package if no version was set
- win_domain - ensure the Netlogon service is up and running after promoting host to controller - https://github.com/ansible/ansible/issues/39235
- win_domain - fixes typo in one of the AD cmdlets https://github.com/ansible/ansible/issues/41536
- win_domain_computer - fixed deletion of computer active directory object that have dependent objects (https://github.com/ansible/ansible/pull/44500)
- win_domain_controller - ensure the Netlogon service is up and running after promoting host to controller - https://github.com/ansible/ansible/issues/39235
- win_iis_webapppool - redirect some module output to null so Ansible can read the output JSON https://github.com/ansible/ansible/issues/40874
- win_lineinfile - changed `-Path` to `-LiteralPath` so that square brackes in the path are interpreted literally -  https://github.com/ansible/ansible/issues/44508
- win_reboot - fix for handling an already scheduled reboot and other minor log formatting issues
- win_reboot - fix issue when overridding connection timeout hung the post reboot uptime check - https://github.com/ansible/ansible/issues/42185 https://github.com/ansible/ansible/issues/42294
- win_reboot - handle post reboots when running test_command - https://github.com/ansible/ansible/issues/41713
- win_security_policy - allows an empty string to reset a policy value https://github.com/ansible/ansible/issues/40869
- win_updates - Fixed issue where running win_updates on async fails without any error
- win_updates - fixed module return value is lost in error in some cases (https://github.com/ansible/ansible/pull/42647)
- win_user - Use LogonUser to validate the password as it does not rely on SMB/RPC to be available https://github.com/ansible/ansible/issues/24884
- winrm - ensure pexpect is set to not echo the input on a failure and have a manual sanity check afterwards https://github.com/ansible/ansible/issues/41865
- winrm - running async with become on a Server 2008 or 2008 R2 host will now work

New Plugins
-----------

Callback
~~~~~~~~

- counter_enabled - adds counters to the output items (tasks and hosts/task)
- logdna - Sends playbook logs to LogDNA
- splunk - Sends task result events to Splunk HTTP Event Collector

Connection
~~~~~~~~~~

- psrp - Run tasks over Microsoft PowerShell Remoting Protocol

Inventory
~~~~~~~~~

- tower - Ansible dynamic inventory plugin for Ansible Tower.

Lookup
~~~~~~

- cpm_status - Get status and parameters from WTI OOB and PDU devices.
- grafana_dashboard - list or search grafana dashboards
- nios_next_network - Return the next available network range for a network-container

New Modules
-----------

Cloud
~~~~~

amazon
^^^^^^

- aws_eks_cluster - Manage Elastic Kubernetes Service Clusters
- cloudformation_stack_set - Manage groups of CloudFormation stacks

azure
^^^^^

- azure_rm_appgateway - Manage Application Gateway instance.
- azure_rm_appserviceplan - Manage App Service Plan
- azure_rm_appserviceplan_facts - Get azure app service plan facts.
- azure_rm_mysqldatabase_facts - Get Azure MySQL Database facts.
- azure_rm_mysqlserver_facts - Get Azure MySQL Server facts.
- azure_rm_postgresqldatabase_facts - Get Azure PostgreSQL Database facts.
- azure_rm_postgresqlserver_facts - Get Azure PostgreSQL Server facts.
- azure_rm_route - Manage Azure route resource.
- azure_rm_routetable - Manage Azure route table resource.
- azure_rm_routetable_facts - Get route table facts.
- azure_rm_virtualmachine_facts - Get virtual machine facts.
- azure_rm_webapp - Manage Web App instance.

cloudstack
^^^^^^^^^^

- cs_disk_offering - Manages disk offerings on Apache CloudStack based clouds.

docker
^^^^^^

- docker_swarm - Manage Swarm cluster
- docker_swarm_service - docker swarm service

google
^^^^^^

- gcp_compute_address_facts - Gather facts for GCP Address
- gcp_compute_backend_bucket_facts - Gather facts for GCP BackendBucket
- gcp_compute_backend_service_facts - Gather facts for GCP BackendService
- gcp_compute_disk_facts - Gather facts for GCP Disk
- gcp_compute_firewall_facts - Gather facts for GCP Firewall
- gcp_compute_forwarding_rule_facts - Gather facts for GCP ForwardingRule
- gcp_compute_global_address_facts - Gather facts for GCP GlobalAddress
- gcp_compute_global_forwarding_rule_facts - Gather facts for GCP GlobalForwardingRule
- gcp_compute_health_check_facts - Gather facts for GCP HealthCheck
- gcp_compute_http_health_check_facts - Gather facts for GCP HttpHealthCheck
- gcp_compute_https_health_check_facts - Gather facts for GCP HttpsHealthCheck
- gcp_compute_image_facts - Gather facts for GCP Image
- gcp_compute_instance_facts - Gather facts for GCP Instance
- gcp_compute_instance_group_facts - Gather facts for GCP InstanceGroup
- gcp_compute_instance_group_manager_facts - Gather facts for GCP InstanceGroupManager
- gcp_compute_instance_template_facts - Gather facts for GCP InstanceTemplate
- gcp_compute_network_facts - Gather facts for GCP Network
- gcp_compute_route_facts - Gather facts for GCP Route
- gcp_compute_router_facts - Gather facts for GCP Router
- gcp_compute_ssl_certificate_facts - Gather facts for GCP SslCertificate
- gcp_compute_ssl_policy - Creates a GCP SslPolicy
- gcp_compute_ssl_policy_facts - Gather facts for GCP SslPolicy
- gcp_compute_subnetwork_facts - Gather facts for GCP Subnetwork
- gcp_compute_target_http_proxy_facts - Gather facts for GCP TargetHttpProxy
- gcp_compute_target_https_proxy_facts - Gather facts for GCP TargetHttpsProxy
- gcp_compute_target_pool_facts - Gather facts for GCP TargetPool
- gcp_compute_target_ssl_proxy_facts - Gather facts for GCP TargetSslProxy
- gcp_compute_target_tcp_proxy_facts - Gather facts for GCP TargetTcpProxy
- gcp_compute_target_vpn_gateway - Creates a GCP TargetVpnGateway
- gcp_compute_target_vpn_gateway_facts - Gather facts for GCP TargetVpnGateway
- gcp_compute_url_map_facts - Gather facts for GCP UrlMap
- gcp_compute_vpn_tunnel - Creates a GCP VpnTunnel
- gcp_compute_vpn_tunnel_facts - Gather facts for GCP VpnTunnel

openstack
^^^^^^^^^

- os_coe_cluster_template - Add/Remove COE cluster template from OpenStack Cloud
- os_listener - Add/Delete a listener for a load balancer from OpenStack Cloud
- os_loadbalancer - Add/Delete load balancer from OpenStack Cloud
- os_member - Add/Delete a member for a pool in load balancer from OpenStack Cloud
- os_pool - Add/Delete a pool in the load balancing service from OpenStack Cloud

scaleway
^^^^^^^^

- scaleway_image_facts - Gather facts about the Scaleway images available.
- scaleway_ip_facts - Gather facts about the Scaleway ips available.
- scaleway_organization_facts - Gather facts about the Scaleway organizations available.
- scaleway_security_group_facts - Gather facts about the Scaleway security groups available.
- scaleway_server_facts - Gather facts about the Scaleway servers available.
- scaleway_snapshot_facts - Gather facts about the Scaleway snapshots available.
- scaleway_volume - Scaleway volumes management module
- scaleway_volume_facts - Gather facts about the Scaleway volumes available.

vmware
^^^^^^

- vmware_about_facts - Provides information about VMware server to which user is connecting to
- vmware_category - Manage VMware categories
- vmware_category_facts - Gather facts about VMware tag categories
- vmware_deploy_ovf - Deploys a VMware virtual machine from an OVF or OVA file
- vmware_guest_boot_facts - Gather facts about boot options for the given virtual machine
- vmware_guest_boot_manager - Manage boot options for the given virtual machine
- vmware_guest_custom_attribute_defs - Manage custom attributes definitions for virtual machine from VMWare
- vmware_guest_custom_attributes - Manage custom attributes from VMWare for the given virtual machine
- vmware_guest_move - Moves virtual machines in vCenter
- vmware_host_ssl_facts - Gather facts of ESXi host system about SSL
- vmware_local_role_facts - Gather facts about local roles on an ESXi host

vultr
^^^^^

- vultr_block_storage - Manages block storage volumes on Vultr.
- vultr_block_storage_facts - Gather facts about the Vultr block storage volumes available.
- vultr_dns_domain_facts - Gather facts about the Vultr DNS domains available.
- vultr_firewall_group_facts - Gather facts about the Vultr firewall groups available.
- vultr_network - Manages networks on Vultr.
- vultr_network_facts - Gather facts about the Vultr networks available.
- vultr_os_facts - Gather facts about the Vultr OSes available.
- vultr_plan_facts - Gather facts about the Vultr plans available.
- vultr_region_facts - Gather facts about the Vultr regions available.
- vultr_server_facts - Gather facts about the Vultr servers available.
- vultr_ssh_key_facts - Gather facts about the Vultr SSH keys available.
- vultr_startup_script_facts - Gather facts about the Vultr startup scripts available.
- vultr_user_facts - Gather facts about the Vultr user available.

Clustering
~~~~~~~~~~

k8s
^^^

- k8s_facts - Describe Kubernetes (K8s) objects

Crypto
~~~~~~

- certificate_complete_chain - Complete certificate chain given a set of untrusted and root certificates
- openssl_pkcs12 - Generate OpenSSL PKCS#12 archive.

acme
^^^^

- acme_account_facts - Retrieves information on ACME accounts
- acme_certificate_revoke - Revoke certificates with the ACME protocol
- acme_challenge_cert_helper - Prepare certificates required for ACME challenges such as C(tls-alpn-01)

Identity
~~~~~~~~

ipa
^^^

- ipa_config - Manage Global FreeIPA Configuration Settings
- ipa_vault - Manage FreeIPA vaults

Monitoring
~~~~~~~~~~

zabbix
^^^^^^

- zabbix_host_facts - Gather facts about Zabbix host

Net Tools
~~~~~~~~~

- netcup_dns - manage Netcup DNS records

nios
^^^^

- nios_a_record - Configure Infoblox NIOS A records
- nios_cname_record - Configure Infoblox NIOS CNAME records
- nios_mx_record - Configure Infoblox NIOS MX records
- nios_naptr_record - Configure Infoblox NIOS NAPTR records
- nios_ptr_record - Configure Infoblox NIOS PTR records
- nios_srv_record - Configure Infoblox NIOS SRV records
- nios_txt_record - Configure Infoblox NIOS txt records

Network
~~~~~~~

aci
^^^

- aci_interface_policy_ospf - Manage OSPF interface policies (ospf:IfPol)

cli
^^^

- cli_command - Run a cli command on cli-based network devices
- cli_config - Push text based configuration to network devices over network_cli

exos
^^^^

- exos_config - Manage Extreme Networks EXOS configuration sections
- exos_facts - Collect facts from devices running Extreme EXOS

f5
^^

- bigip_appsvcs_extension - Manage application service deployments
- bigip_cli_alias - Manage CLI aliases on a BIG-IP
- bigip_cli_script - Manage CLI scripts on a BIG-IP
- bigip_device_auth - Manage system authentication on a BIG-IP
- bigip_device_facts - Collect facts from F5 BIG-IP devices
- bigip_firewall_dos_profile - Manage AFM DoS profiles on a BIG-IP
- bigip_firewall_policy - Manage AFM security firewall policies on a BIG-IP
- bigip_firewall_rule - Manage AFM Firewall rules
- bigip_firewall_rule_list - Manage AFM security firewall policies on a BIG-IP
- bigip_monitor_dns - Manage DNS monitors on a BIG-IP
- bigip_profile_http - Manage HTTP profiles on a BIG-IP
- bigip_profile_http_compression - Manage HTTP compression profiles on a BIG-IP
- bigip_profile_oneconnect - Manage OneConnect profiles on a BIG-IP
- bigip_profile_persistence_src_addr - Manage source address persistence profiles
- bigip_remote_role - Manage remote roles on a BIG-IP
- bigip_software_image - Manage software images on a BIG-IP
- bigip_software_install - Install software images on a BIG-IP
- bigip_tunnel - Manage tunnels on a BIG-IP
- bigiq_utility_license_assignment - Manage utility license assignment on BIG-IPs from a BIG-IQ

meraki
^^^^^^

- meraki_config_template - Manage configuration templates in the Meraki cloud
- meraki_device - Manage devices in the Meraki cloud
- meraki_mr_l3_firewall - Manage MR access point layer 3 firewalls in the Meraki cloud
- meraki_mx_l3_firewall - Manage MX appliance layer 3 firewalls in the Meraki cloud
- meraki_ssid - Manage wireless SSIDs in the Meraki cloud
- meraki_switchport - Manage switchports on a switch in the Meraki cloud
- meraki_vlan - Manage VLANs in the Meraki cloud

nos
^^^

- nos_command - Run commands on remote devices running Extreme Networks NOS
- nos_config - Manage Extreme Networks NOS configuration sections
- nos_facts - Collect facts from devices running Extreme NOS

nxos
^^^^

- nxos_rpm - Install patch or feature rpms on Cisco NX-OS devices.

onyx
^^^^

- onyx_igmp - Configures IGMP globl parameters

panos
^^^^^

- panos_set - Execute arbitrary commands on a PAN-OS device using XPath and element

routeros
^^^^^^^^

- routeros_command - Run commands on remote devices running MikroTik RouterOS

slxos
^^^^^

- slxos_lldp - Manage LLDP configuration on Extreme Networks SLX-OS network devices.

voss
^^^^

- voss_command - Run commands on remote devices running Extreme VOSS
- voss_facts - Collect facts from remote devices running Extreme VOSS

Remote Management
~~~~~~~~~~~~~~~~~

cobbler
^^^^^^^

- cobbler_sync - Sync Cobbler
- cobbler_system - Manage system ojects in Cobbler

redfish
^^^^^^^

- redfish_facts - Manages Out-Of-Band controllers using Redfish APIs

ucs
^^^

- ucs_ntp_server - Configures NTP server on Cisco UCS Manager
- ucs_storage_profile - Configures storage profiles on Cisco UCS Manager
- ucs_timezone - Configures timezone on Cisco UCS Manager
- ucs_uuid_pool - Configures server UUID pools on Cisco UCS Manager

Storage
~~~~~~~

emc
^^^

- emc_vnx_sg_member - Manage storage group member on EMC VNX

ibm
^^^

- ibm_sa_vol - Handle volumes on an IBM Spectrum Accelerate storage array

netapp
^^^^^^

- na_elementsw_backup - NetApp Element Software Create Backups
- na_elementsw_cluster_pair - NetApp Element Software Manage Cluster Pair
- na_elementsw_snapshot_schedule - NetApp Element Software Snapshot Schedules
- na_elementsw_vlan - NetApp Element Software Manage VLAN
- na_elementsw_volume - NetApp Element Software Manage Volumes
- na_elementsw_volume_pair - NetApp Element Software Volume Pair
- na_ontap_cg_snapshot - Create consistency group snapshot
- na_ontap_dns - NetApp ONTAP Create, delete, modify DNS servers.
- na_ontap_fcp - NetApp ONTAP Start, Stop and Enable FCP services.
- na_ontap_snapmirror - NetApp ONTAP Manage SnapMirror
- na_ontap_software_update - NetApp ONTAP Update software
- na_ontap_svm_options - NetApp ONTAP Modify Options
- na_ontap_vserver_peer - Manage NetApp Vserver peering

System
~~~~~~

- java_keystore - Create or delete a Java keystore in JKS format.
- python_requirements_facts - Show python path and assert dependency versions
- reboot - Reboot a machine

Web Infrastructure
~~~~~~~~~~~~~~~~~~

ansible_tower
^^^^^^^^^^^^^

- tower_inventory_source - create, update, or destroy Ansible Tower inventory source.

Windows
~~~~~~~

- win_chocolatey_config - Manages Chocolatey config settings
- win_chocolatey_feature - Manages Chocolatey features
- win_chocolatey_source - Manages Chocolatey sources
