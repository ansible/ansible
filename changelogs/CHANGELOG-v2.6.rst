========================================
Ansible 2.6 "Heartbreaker" Release Notes
========================================

v2.6.16
=======

Release Summary
---------------

| Release Date: 2019-04-03
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Catch all connection timeout related exceptions and raise AnsibleConnectionError instead

Bugfixes
--------

- openssl_publickey - fixed crash on Python 3 when OpenSSH private keys were used with passphrases.
- slurp - Fix issues when using paths on Windows with glob like characters, e.g. ``[``, ``]``
- win_acl - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_acl_inheritance - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_certificate_store - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_chocolatey - Fix incompatibilities with the latest release of Chocolatey ``v0.10.12+``
- win_copy - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_file - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_find - Ensure found files are sorted alphabetically by the path instead of it being random
- win_find - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_owner - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_tempfile - Always return the full NTFS absolute path and not a DOS 8.3 path.
- win_user_right - Fix output containing non json data - https://github.com/ansible/ansible/issues/54413
- windows - Fixed various module utils that did not work with path that had glob like chars

v2.6.15
=======

Release Summary
---------------

| Release Date: 2019-03-14
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- ``to_yaml`` filter updated to maintain formatting consistency when used with ``pyyaml`` versions 5.1 and later (https://github.com/ansible/ansible/pull/53772)

Bugfixes
--------

- inventory_aws_ec2 - fix no_log indentation so AWS temporary credentials aren't displayed in tests
- mysql_user: match backticks, single and double quotes when checking user privileges.
- win_domain - Do not fail if DC is already promoted but a reboot is required, return ``reboot_required: True``
- win_domain - Fix when running without credential delegated authentication - https://github.com/ansible/ansible/issues/53182
- win_file - Fix issue when managing hidden files and directories - https://github.com/ansible/ansible/issues/42466
- winrm - attempt to recover from a WinRM send input failure if possible
- zypper - Fix Python 3 compatibility issues

v2.6.14
=======

Release Summary
---------------

| Release Date: 2019-02-21
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Raise AnsibleConnectionError on winrm connnection errors

Bugfixes
--------

- azure_rm_managed_disk_facts - added missing implementation of listing managed disks by resource group
- azure_rm_postgresqldatabase - fix force_update bug (https://github.com/ansible/ansible/issues/50978).
- azure_rm_postgresqldatabase - fix force_update bug.
- azure_rm_sqlserver - fix for tags support
- remote home directory - Disallow use of remote home directories that include relative pathing by means of `..` (CVE-2019-3828) (https://github.com/ansible/ansible/pull/52133)
- win become - Fix some scenarios where become failed to create an elevated process
- win_psmodule - the NuGet package provider will be updated, if needed, to avoid issue under adding a repository

v2.6.13
=======

Release Summary
---------------

| Release Date: 2019-02-07
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Fixed typo in vmware documentation fragment. Changed "supported added" to "support added".

Bugfixes
--------

- Fix mandatory statement error for junos modules (https://github.com/ansible/ansible/pull/50138)
- fix ansible-pull hanlding of extra args, complex quoting is needed for inline JSON
- ssh connection - do not retry with invalid credentials to prevent account lockout (https://github.com/ansible/ansible/issues/48422)
- systemd - warn when exeuting in a chroot environment rather than failing (https://github.com/ansible/ansible/pull/43904)
- win_power_plan - Fix issue where win_power_plan failed on newer Windows 10 builds - https://github.com/ansible/ansible/issues/43827

v2.6.12
=======

Release Summary
---------------

| Release Date: 2019-01-17
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- docker_volume - reverted changed behavior of ``force``, which was released in Ansible 2.7.1 to 2.7.5, and Ansible 2.6.8 to 2.6.11. Volumes are now only recreated if the parameters changed **and** ``force`` is set to ``true`` (instead of or). This is the behavior which has been described in the documentation all the time.

Bugfixes
--------

- This reverts some changes from commit 723daf3. If a line is found in the file, exactly or via regexp matching, it must not be added again. `insertafter`/`insertbefore` options are used only when a line is to be inserted, to specify where it must be added.
- allow using openstack inventory plugin w/o a cache
- document old option that was initally missed
- win_copy - Fix copy of a dir that contains an empty directory - https://github.com/ansible/ansible/issues/50077
- win_firewall_rule - Remove invalid 'bypass' action
- win_lineinfile - Fix issue where a malformed json block was returned causing an error
- win_updates - Correctly report changes on success

v2.6.11
=======

Release Summary
---------------

| Release Date: 2018-12-13
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Fixed typo in ansible-galaxy info command.
- Update docs and return section of vmware_host_service_facts module.

Bugfixes
--------

- Added unit test for VMware module_utils.
- Fix N3K power supply facts (https://github.com/ansible/ansible/pull/49150).
- Fix NameError nxos_facts (https://github.com/ansible/ansible/pull/48981).
- Fix VMware module utils for self usage.
- Fix issues with nxos_install_os module for nxapi (https://github.com/ansible/ansible/pull/48811).
- Fix lldp and cdp neighbors information (https://github.com/ansible/ansible/pull/48318)(https://github.com/ansible/ansible/pull/48087)(https://github.com/ansible/ansible/pull/49024).
- Fix nxos_interface and nxos_linkagg Idempotence issue (https://github.com/ansible/ansible/pull/46437).
- ec2_metadata_facts - Parse IAM role name from the security credential field since the instance profile name is different
- now no log is being respected on retry and high verbosity.  CVE-2018-16876
- vmware_host_service_facts - handle exception when service package does not have package name.

v2.6.10
=======

Release Summary
---------------

| Release Date: 2018-11-30
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Bugfixes
--------

- powershell - add ``lib/ansible/executor/powershell`` to the packaging data

v2.6.9
======

Release Summary
---------------

| Release Date: 2018-11-29
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Bugfixes
--------

- Fix calling deprecate with correct arguments (https://github.com/ansible/ansible/pull/46062).
- Windows - prevent sensitive content from appearing in scriptblock logging (CVE 2018-16859)
- apt_key - Disable TTY requirement in GnuPG for the module to work correctly when SSH pipelining is enabled (https://github.com/ansible/ansible/pull/48580)
- sysvinit - enabling a service should use "defaults" if no runlevels are specified
- user - do not report changes every time when setting password_lock (https://github.com/ansible/ansible/issues/43670)
- user - properly remove expiration when set to a negative value (https://github.com/ansible/ansible/issues/47114)

v2.6.8
======

Release Summary
---------------

| Release Date: 2018-11-15
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Update plugin filter documentation.

Bugfixes
--------

- ACME modules support `POST-as-GET <https://community.letsencrypt.org/t/acme-v2-scheduled-deprecation-of-unauthenticated-resource-gets/74380>`__ and will be able to access Let's Encrypt ACME v2 endpoint after November 1st, 2019.
- Add force disruptive option nxos_instal_os module (https://github.com/ansible/ansible/pull/47694).
- Avoid misleading PyVmomi error if requests import fails in vmware module utils.
- Fix for StrategyModule object has no attribute _cond_not_supported_warn (https://github.com/ansible/ansible/issues/46275)
- Fix trailing command in net_neighbors nxos_facts (https://github.com/ansible/ansible/pull/47548).
- Restore timeout in set_vm_power_state operation in vmware_guest_powerstate module.
- aws_ec2 - fixed issue where cache did not contain the computed groups
- docker_container - do not fail when removing a container which has ``auto_remove: yes``.
- docker_container - fail if ``ipv4_address`` or ``ipv6_address`` is used with a too old docker-py version.
- docker_container - fix ``ipc_mode`` and ``pid_mode`` idempotency if the ``host:<container-name>`` form is used (as opposed to ``host:<container-id>``).
- docker_container - fix ``memory_swappiness`` documentation.
- docker_container - fix ``paused`` option (which never worked).
- docker_container - fix behavior of ``detach: yes`` if ``auto_remove: yes`` is specified.
- docker_container - fixing race condition when ``detach`` and ``auto_remove`` are both ``true``.
- docker_network - fixes idempotency issues (https://github.com/ansible/ansible/issues/33045) and name substring issue (https://github.com/ansible/ansible/issues/32926).
- docker_service - correctly parse string values for the `scale` parameter https://github.com/ansible/ansible/pull/45508
- docker_volume - fix ``force`` and change detection logic. If not both evaluated to ``True``, the volume was not recreated.
- junos - fix terminal prompt regex (https://github.com/ansible/ansible/pull/47096)
- lvg - fixed an idempotency regression in the lvg module (https://github.com/ansible/ansible/issues/47301)
- nxos_evpn_vni check_mode (https://github.com/ansible/ansible/pull/46612).
- nxos_file_copy fix for binary files (https://github.com/ansible/ansible/pull/46822).
- openssl_csr - fix byte encoding issue on Python 3
- postgresql_user - create pretty error message when creating a user without an encrypted password on newer PostgreSQL versions
- psexec - Handle socket.error exceptions properly
- psexec - give proper error message when the psexec requirements are not installed
- win_uri - stop junk output from being returned to Ansible - https://github.com/ansible/ansible/issues/47998
- zabbix_host - module was failing when zabbix host was updated with new interface and template depending on that interface at the same time

v2.6.7
======

Release Summary
---------------

| Release Date: 2018-10-31
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


Bugfixes
--------

- user module - do not pass ssh_key_passphrase on cmdline (CVE-2018-16837)

v2.6.6
======

Release Summary
---------------

| Release Date: 2018-10-19
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


Minor Changes
-------------

- win_nssm - Drop support of literal YAML dictionnary for ``app_parameters`` option. Use the ``key=value;`` string form instead

Bugfixes
--------

- Ignore empty result of rabbitmqctl list_user_permissions.
- In systemd module, fix check if a systemd+initd service is enabled - disabled in systemd means disabled
- Update callbacks to use Ansible's JSON encoder to avoid known serialization issues
- blockinfile - use bytes rather than a native string to prevent a stacktrace in Python 3 when writing to the file (https://github.com/ansible/ansible/issues/46237)
- docker_container - ``publish_ports: all`` was not used correctly when checking idempotency.
- docker_container - fix idempotency check for published_ports in some special cases.
- docker_container - the behavior is improved in case ``image`` is not specified, but needed for (re-)creating the container.
- dynamic includes - Use the copied and merged task for calculating task vars in the free strategy (https://github.com/ansible/ansible/issues/47024)
- fix flatten to properly handle multiple lists in lists https://github.com/ansible/ansible/issues/46343
- lineinfile - fix index out of range error when using insertbefore on a file with only one line (https://github.com/ansible/ansible/issues/46043)
- os_router - ``enable_snat: no`` was ignored.
- route53 - fix CAA record ordering for idempotency.
- use proper module_util to get Ansible version for Azure requests
- user - add documentation on what underlying tools are used on each platform (https://github.com/ansible/ansible/issues/44266)
- win_nssm - Add missing space between parameters with ``app_parameters``
- win_nssm - Correctly escape argument line when a parameter contains spaces, quotes or backslashes
- win_nssm - Fix error when several services were given to the ``dependencies`` option
- win_nssm - Fix extra space added in argument line with ``app_parameters`` or ``app_parameters_free_form`` when a parameter start by a dash and is followed by a period (https://github.com/ansible/ansible/issues/44079)
- win_nssm - Fix service not started when ``state=started`` (https://github.com/ansible/ansible/issues/35442)
- win_nssm - Fix several issues and idempotency problems (https://github.com/ansible/ansible/pull/44755)

v2.6.5
======

Release Summary
---------------

| Release Date: 2018-09-28
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


Bugfixes
--------

- Add ambiguous command check as the error message is not persistent on nexus devices (https://github.com/ansible/ansible/pull/45337).
- Ansible JSON Decoder - Switch from decode to object_hook to support nested use of __ansible_vault and __ansible_unsafe (https://github.com/ansible/ansible/pull/45514)
- Don't parse parameters and options when ``state`` is ``absent`` (https://github.com/ansible/ansible/pull/45700).
- Fix python2.6 `nothing to repeat` nxos terminal plugin bug (https://github.com/ansible/ansible/pull/45271).
- Fix referenced before assignment in sysvinit module
- PLUGIN_FILTERS_CFG - Ensure that the value is treated as type=path, and that we use the standard section of ``defaults`` instead of ``default`` (https://github.com/ansible/ansible/pull/45994)
- The patch fixing the regression of no longer preferring matching security groups in the same VPC https://github.com/ansible/ansible/pull/45787 (which was also backported to 2.6) broke EC2-Classic accounts. https://github.com/ansible/ansible/pull/46242 removes the assumption that security groups must be in a VPC.
- azure_rm_deployment - fixed regression that prevents resource group from being created (https://github.com/ansible/ansible/issues/45941)
- chroot connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)
- cloudfront - fix bug when CloudFrontOriginAccessIdentityList is missing (https://github.com/ansible/ansible/pull/44984)
- docker connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)
- docker_container - Fix idempotency problems with ``cap_drop`` and ``groups`` (when numeric group IDs were used).
- docker_container - Fix type conversion errors for ``log_options``.
- docker_container - Fixing various comparison/idempotency problems related to wrong comparisons. In particular, comparisons for ``command`` and ``entrypoint`` (both lists) no longer ignore missing elements during idempotency checks.
- docker_container - Makes ``blkio_weight``, ``cpuset_mems``, ``dns_opts`` and ``uts`` options actually work.
- ec2_group - Sanitize the ingress and egress rules before operating on them by flattening any lists within lists describing the target CIDR(s) into a list of strings. Prior to Ansible 2.6 the ec2_group module accepted a list of strings, a list of lists, or a combination of strings and lists within a list. https://github.com/ansible/ansible/pull/45594
- ec2_group - There can be multiple security groups with the same name in different VPCs. Prior to 2.6 if a target group name was provided, the group matching the name and VPC had highest precedence. Restore this behavior by updated the dictionary with the groups matching the VPC last.
- fetch_url did not always return lower-case header names in case of HTTP errors (https://github.com/ansible/ansible/pull/45628).
- fix nxos_facts indefinite hang for text based output (https://github.com/ansible/ansible/pull/45845).
- get_url - Don't re-download files unnecessarily when force=no (https://github.com/ansible/ansible/issues/45491)
- jail connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)
- kubectl connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)
- libvirt_lxc connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)
- loop - Ensure that a loop with a when condition that evaluates to false and delegate_to, will short circuit if the loop references an undefined variable. This matches the behavior in the same scenario without delegate_to (https://github.com/ansible/ansible/issues/45189)
- mysql_*, proxysql_* - PyMySQL (a pure-Python MySQL driver) is now a preferred dependency also supporting Python 3.X.
- powershell - Fix issue where setting ANSIBLE_KEEP_REMOTE_FILES fails when using Python 2.6 - https://github.com/ansible/ansible/issues/45490
- script inventory plugin - Don't pass file_name to DataLoader.load, which will prevent misleading error messages (https://github.com/ansible/ansible/issues/34164)
- ssh connection - Support empty files with piped transfer_method (https://github.com/ansible/ansible/issues/45426)
- vyos_facts - fix vyos_facts not returning version number issue (https://github.com/ansible/ansible/pull/39115)
- win_copy - Fix issue where the dest return value would be enclosed in single quote when dest is a folder - https://github.com/ansible/ansible/issues/45281
- win_group_membership - fix intermittent issue where it failed to convert the ADSI object to the .NET object after using it once
- win_say - fix syntax error in module and get tests working
- winrm - Only use pexpect for auto kerb auth if it is installed and contains the required kwargs - https://github.com/ansible/ansible/issues/43462
- zone connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)

v2.6.4
======

Release Summary
---------------

| Release Date: 2018-09-06
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


Minor Changes
-------------

- add azure_rm_storageaccount support to StorageV2 kind. (https://github.com/ansible/ansible/pull/44242)
- import_tasks - Do not allow import_tasks to transition to dynamic if the file is missing (https://github.com/ansible/ansible/issues/44822)

Bugfixes
--------

- Add md5sum check in nxos_file_copy module (https://github.com/ansible/ansible/pull/43423).
- Allow arbitrary ``log_driver`` for docker_container (https://github.com/ansible/ansible/pull/33579).
- Fix Python2.6 regex bug terminal plugin nxos, iosxr (https://github.com/ansible/ansible/pull/45135).
- Fix check_mode in nxos_static_route module (https://github.com/ansible/ansible/pull/44252).
- Fix glob path of rc.d Some distribtuions like SUSE has the rc%.d directories under /etc/init.d
- Fix network config diff issue for lines (https://github.com/ansible/ansible/pull/43889)
- Fixed an issue where ``ansible_facts.pkg_mgr`` would incorrectly set to ``zypper`` on Debian/Ubuntu systems that happened to have the command installed.
- The docker_* modules respect the DOCKER_* environment variables again (https://github.com/ansible/ansible/pull/42641).
- The fix for `CVE-2018-10875 <https://access.redhat.com/security/cve/cve-2018-10875>`_ prints out a warning message about skipping a config file from a world writable current working directory.  However, if the user is in a world writable current working directory which does not contain a config file, it should not print a warning message.  This release fixes that extaneous warning.
- To resolve nios_network issue where vendor-encapsulated-options can not have a use_option flag. (https://github.com/ansible/ansible/pull/43925)
- To resolve the issue of handling exception for Nios lookup gracefully. (https://github.com/ansible/ansible/pull/44078)
- always correctly template no log for tasks https://github.com/ansible/ansible/issues/43294
- ansible-galaxy - properly list all roles in roles_path (https://github.com/ansible/ansible/issues/43010)
- basic.py - catch ValueError in case a FIPS enabled platform raises this exception - https://github.com/ansible/ansible/issues/44447
- docker_container: fixing ``working_dir`` idempotency problem (https://github.com/ansible/ansible/pull/42857)
- docker_container: makes unit parsing for memory sizes more consistent, and fixes idempotency problem when ``kernel_memory`` is set (see https://github.com/ansible/ansible/pull/16748 and https://github.com/ansible/ansible/issues/42692)
- fix  example code for AWS lightsail documentation
- fix the enable_snat parameter that is only supposed to be used by an user with the right policies. https://github.com/ansible/ansible/pull/44418
- fixes docker_container check and debug mode (https://github.com/ansible/ansible/pull/42380)
- improves docker_container idempotency (https://github.com/ansible/ansible/pull/44808)
- ios_l2_interface - fix bug when list of vlans ends with comma (https://github.com/ansible/ansible/pull/43879)
- ios_l2_interface - fix issue with certain interface types (https://github.com/ansible/ansible/pull/43819)
- ios_user - fix unable to delete user admin issue (https://github.com/ansible/ansible/pull/44904)
- ios_vlan - fix unable to work on certain interface types issue (https://github.com/ansible/ansible/pull/43819)
- nxos_facts test lldp feature and fix nxapi check_rc (https://github.com/ansible/ansible/pull/44104).
- nxos_interface port-channel idempotence fix for mode (https://github.com/ansible/ansible/pull/44248).
- nxos_linkagg mode fix (https://github.com/ansible/ansible/pull/44294).
- nxos_system idempotence fix (https://github.com/ansible/ansible/pull/44752).
- nxos_vlan refactor to support non structured output (https://github.com/ansible/ansible/pull/43805).
- one_host - fixes settings via environment variables (https://github.com/ansible/ansible/pull/44568)
- use retry_json nxos_banner (https://github.com/ansible/ansible/pull/44376).
- user - Strip trailing comments in /etc/default/passwd (https://github.com/ansible/ansible/pull/43931)
- user - when creating a new user without an expiration date, properly set no expiration rather that expirining the account (https://github.com/ansible/ansible/issues/44155)
- win_domain_computer - fixed deletion of computer active directory object that have dependent objects (https://github.com/ansible/ansible/pull/44500)
- win_domain_computer - fixed error in diff_support
- win_domain_computer - fixed error when description parameter is empty (https://github.com/ansible/ansible/pull/44054)
- win_psexec - changed code to not escape the command option when building the args - https://github.com/ansible/ansible/issues/43839
- win_uri -- Fix support for JSON output when charset is set
- win_wait_for - fix issue where timeout doesn't wait unless state=drained - https://github.com/ansible/ansible/issues/43446

v2.6.3
======

Release Summary
---------------

| Release Date: 2018-08-16
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


Bugfixes
--------

- Fix lxd module to be idempotent when the given configuration for the lxd container has not changed (https://github.com/ansible/ansible/pull/38166)
- Fix setting value type to str to avoid conversion during template read. Fix Idempotency in case of 'no key'.
- Fix the mount module's handling of swap entries in fstab (https://github.com/ansible/ansible/pull/42837)
- The fix for `CVE-2018-10875 <https://access.redhat.com/security/cve/cve-2018-10875>`_ prints out a warning message about skipping a config file from a world writable current working directory.  However, if the user explicitly specifies that the config file should be used via the ANSIBLE_CONFIG environment variable then Ansible would honor that but still print out the warning message.  This has been fixed so that Ansible honors the user's explicit wishes and does not print a warning message in that circumstance.
- To fix the bug where existing host_record was deleted when existing record name is used with different IP. (https://github.com/ansible/ansible/pull/43235)
- VMware handle pnic in proxyswitch (https://github.com/ansible/ansible/pull/42996)
- fix azure security group cannot add rules when purge_rule set to false. (https://github.com/ansible/ansible/pull/43699)
- fix azure_rm_deployment collect tags from existing Resource Group. (https://github.com/ansible/ansible/pull/26104)
- fix azure_rm_loadbalancer_facts list takes at least 2 arguments. (https://github.com/ansible/ansible/pull/29050)
- fix for the bundled selectors module (used in the ssh and local connection plugins) when a syscall is restarted after being interrupted by a signal (https://github.com/ansible/ansible/issues/41630)
- get_url - fix the bug that get_url does not change mode when checksum matches (https://github.com/ansible/ansible/issues/29614)
- nicer error when multiprocessing breaks https://github.com/ansible/ansible/issues/43090
- openssl_certificate - Convert valid_date to bytes for conversion
- openstack_inventory.py dynamic inventory file fixed the plugin to the script so that it will work with current ansible-inventory. Also redirect stdout before dumping the ouptput, because not doing so will cause JSON parse errors in some cases. (https://github.com/ansible/ansible/pull/43432)
- slack callback - Fix invocation by looking up data from cli.options (https://github.com/ansible/ansible/pull/43542)
- sysvinit module: handle values of optional parameters (https://github.com/ansible/ansible/pull/42786). Don't disable service when `enabled` parameter isn't set. Fix command when `arguments` parameter isn't set.
- vars_prompt - properly template play level variables in vars_prompt (https://github.com/ansible/ansible/issues/37984)
- win_domain - ensure the Netlogon service is up and running after promoting host to controller - https://github.com/ansible/ansible/issues/39235
- win_domain_controller - ensure the Netlogon service is up and running after promoting host to controller - https://github.com/ansible/ansible/issues/39235

v2.6.2
======

Release Summary
---------------

| Release Date: 2018-07-27
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


Minor Changes
-------------

- Scenario guide for removing an existing virtual machine is added.
- lineinfile - add warning when using an empty regexp (https://github.com/ansible/ansible/issues/29443)

Bugfixes
--------

- Add text output along with structured output in nxos_facts (https://github.com/ansible/ansible/pull/42886).
- Allow more than one page of results by using the right pagination indicator ('NextMarker' instead of 'NextToken').
- Fix an atomic_move error that is 'true', but  misleading. Now we show all 3 files involved and clarify what happened.
- Fix eos_l2_interface eapi (https://github.com/ansible/ansible/pull/42270).
- Fix fetching old style facts in junos_facts module (https://github.com/ansible/ansible/pull/42351)
- Fix get_device_info nxos zero or more whitespace regex (https://github.com/ansible/ansible/pull/43178).
- Fix nxos CI failures (https://github.com/ansible/ansible/pull/42240).
- Fix nxos_nxapi default http behavior (https://github.com/ansible/ansible/pull/41817).
- Fix nxos_vxlan_vtep_vni (https://github.com/ansible/ansible/pull/42240).
- Fix regex network_os_platform nxos (https://github.com/ansible/ansible/pull/42288).
- Refactor nxos cliconf get_device_info for non structured output supported devices (https://github.com/ansible/ansible/pull/42089).
- To fix the NoneType error raised in ios_l2_interface when Access Mode VLAN is unassigned (https://github.com/ansible/ansible/pull/42312)
- emtpy host/group name is an error https://github.com/ansible/ansible/issues/42044
- fix default SSL version for docker modules https://github.com/ansible/ansible/issues/42897
- fix mail module when using starttls https://github.com/ansible/ansible/issues/42338
- fix nmap config example https://github.com/ansible/ansible/pull/42925
- fix ps detection of service https://github.com/ansible/ansible/pull/43014
- fix the remote tmp folder permissions issue when becoming a non admin user - https://github.com/ansible/ansible/issues/41340, https://github.com/ansible/ansible/issues/42117
- fix typoe in sysvinit that breaks update.rc-d detection https://github.com/ansible/ansible/issues/42734
- fixes docker_container compatibilty with docker-py < 2.2
- get_capabilities in nxapi module_utils should not return empty dictionary (https://github.com/ansible/ansible/pull/42688).
- inventory - When using an inventory directory, ensure extension comparison uses text types (https://github.com/ansible/ansible/pull/42475)
- ios_vlan - fix unable to identify correct vlans issue (https://github.com/ansible/ansible/pull/42247)
- nxos_facts warning message improved (https://github.com/ansible/ansible/pull/42969).
- openvswitch_db - make 'key' argument optional https://github.com/ansible/ansible/issues/42108
- pause - do not set stdout to raw mode when redirecting to a file (https://github.com/ansible/ansible/issues/41717)
- pause - nest try except when importing curses to gracefully fail if curses is not present (https://github.com/ansible/ansible/issues/42004)
- plugins/inventory/openstack.py - Do not create group with empty name if region is not set
- preseve delegation info on nolog https://github.com/ansible/ansible/issues/42344
- remove ambiguity when it comes to 'the source'
- remove dupes from var precedence
- restores filtering out conflicting facts https://github.com/ansible/ansible/issues/41684
- user - fix bug that resulted in module always reporting a change when specifiying the home directory on FreeBSD (https://github.com/ansible/ansible/issues/42484)
- user - use correct attribute name in FreeBSD for creat_home (https://github.com/ansible/ansible/pull/42711)
- vultr - Do not fail trying to load configuration from ini files if required variables have been set as environment variables.
- vyos_command correcting conditionals looping (https://github.com/ansible/ansible/pull/43331).
- win_chocolatey - enable TLSv1.2 support when downloading the Chocolatey installer https://github.com/ansible/ansible/issues/41906
- win_reboot - fix for handling an already scheduled reboot and other minor log formatting issues
- win_reboot - fix issue when overridding connection timeout hung the post reboot uptime check - https://github.com/ansible/ansible/issues/42185 https://github.com/ansible/ansible/issues/42294
- win_reboot - handle post reboots when running test_command - https://github.com/ansible/ansible/issues/41713
- win_security_policy - allows an empty string to reset a policy value https://github.com/ansible/ansible/issues/40869
- win_share - discard any cmdlet output we don't use to ensure only the return json is received by Ansible
- win_unzip - discard any cmdlet output we don't use to ensure only the return json is received by Ansible
- win_updates - fixed module return value is lost in error in some cases (https://github.com/ansible/ansible/pull/42647)
- win_user - Use LogonUser to validate the password as it does not rely on SMB/RPC to be available https://github.com/ansible/ansible/issues/24884

v2.6.1
======

Release Summary
---------------

| Release Date: 2018-07-05
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


Minor Changes
-------------

- Restore module_utils.basic.BOOLEANS variable for backwards compatibility with the module API in older ansible releases.

Bugfixes
--------

- **Security Fix** - avoid loading host/group vars from cwd when not specifying a playbook or playbook base dir
- **Security Fix** - avoid using ansible.cfg in a world writable dir.
- Fix junos_config confirm commit timeout issue (https://github.com/ansible/ansible/pull/41527)
- file module - The touch subcommand had its diff output broken during the 2.6.x development cycle.  The patch to fix that broke check mode. This is now fixed (https://github.com/ansible/ansible/issues/42111)
- inventory manager - This fixes required options being populated before the inventory config file is read, so the required options may be set in the config file.
- nsupdate - allow hmac-sha384 https://github.com/ansible/ansible/pull/42209
- win_domain - fixes typo in one of the AD cmdlets https://github.com/ansible/ansible/issues/41536
- win_group_membership - uses the internal Ansible SID conversion logic and uses that when comparing group membership instead of the name https://github.com/ansible/ansible/issues/40649

v2.6.0
======

Release Summary
---------------

| Release Date: 2018-06-28
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


Minor Changes
-------------

- Added an ``encoding`` option to the ``b64encode`` and ``b64decode`` filters to specify the encoding of the string that is base64 encoded.
- PowerShell modules that use Convert-ToSID in Ansible.ModuleUtils.SID.psm1 like win_user_right now accept an actual SID as an input string. This means any local or domain accounts that are named like a SID need to be prefixed with the domain, hostname, or . to ensure it converts to that accounts SID https://github.com/ansible/ansible/issues/38502
- Raise AnsibleParserError which was missing previously
- The aws_ses_identity module supports check mode
- ``postgresql_user`` module changed ``encrypted=yes`` to be the default. This shouldn't break any current playbooks, the module will just store passwords hashed by default. This change was done because Postgres 10 dropped support for ``UNENCRYPTED`` passwords and because all versions since Postgres 7.2 support storing encrypted passwords.
- azure_rm_loadbalancer - add support for sku
- azure_rm_publicipaddress - add support for sku
- cloudflare_dns module - Removed restriction from protocol to allow other protocols than tcp and udp to be specified.
- command module - Added argv option to allow command to be specified as a list vs. a string (https://github.com/ansible/ansible/issues/19392)
- gem - add ability to specify a custom directory for installing gems (https://github.com/ansible/ansible/pull/38195)
- import/include - Cache task_vars to speed up IncludedFile.process_include_results (https://github.com/ansible/ansible/pull/39026)
- postgresql_user module - Changed encrypted=yes to be the default. This shouldn't break any current playbooks, the module will just store passwords hashed by default. This change was done because Postgres 10 dropped support for UNENCRYPTED passwords and because all versions since Postgres 7.2 support storing encrypted passwords.
- vmware_target_canonical_facts module - The target_id parameter is an optional parameter.

Deprecated Features
-------------------

- nxos_igmp_interface module - The oif_prefix and oif_source properties are deprecated. Use the oif_ps parameter with a dictionary of prefix and source to values instead.

Removed Features (previously deprecated)
----------------------------------------

- removed the deprecated always_run task option, please use ``check_mode: no`` instead
- win_chocolatey - removed deprecated upgrade option and choco_* output return values
- win_feature - removed deprecated reboot option
- win_iis_webapppool - removed the ability to supply attributes as a string in favour of a dictionary
- win_package - removed deprecated name option
- win_regedit - removed deprecated support for specifying HKCC as HCCC

Bugfixes
--------

- **Security Fix** - Some connection exceptions would cause no_log specified on a task to be ignored.  If this happened, the task information, including any private information could have been displayed to stdout and (if enabled, not the default) logged to a log file specified in ansible.cfg's log_path. Additionally, sites which redirected stdout from ansible runs to a log file may have stored that private information onto disk that way as well. (https://github.com/ansible/ansible/pull/41414)
- Changed the admin_users config option to not include "admin" by default as admin is frequently used for a non-privileged account  (https://github.com/ansible/ansible/pull/41164)
- Changed the output to "text" for "show vrf" command as default "json" output format with respect to "eapi" transport was failing (https://github.com/ansible/ansible/pull/41470)
- Document mode=preserve for both the copy and template module
- Fix added for Digital Ocean Volumes API change causing Ansible to recieve an unexpected value in the response. (https://github.com/ansible/ansible/pull/41431)
- Fix an encoding issue when parsing the examples from a plugins' documentation
- Fix iosxr_config module to handle route-policy, community-set, prefix-set, as-path-set and rd-set blocks. All these blocks are part of route-policy language of iosxr.
- Fix mode=preserve with remote_src=True for the copy module
- Implement mode=preserve for the template module
- The yaml callback plugin now allows non-ascii characters to be displayed.
- Various grafana_* modules - Port away from the deprecated b64encodestring function to the b64encode function instead. https://github.com/ansible/ansible/pull/38388
- added missing 'raise' to exception definition https://github.com/ansible/ansible/pull/41690
- allow custom endpoints to be used in the aws_s3 module (https://github.com/ansible/ansible/pull/36832)
- allow set_options to be called multiple times https://github.com/ansible/ansible/pull/41913
- ansible-doc - fixed traceback on missing plugins (https://github.com/ansible/ansible/pull/41167)
- cast the device_mapping volume size to an int in the ec2_ami module (https://github.com/ansible/ansible/pull/40938)
- copy - fixed copy to only follow symlinks for files in the non-recursive case
- copy module - The copy module was attempting to change the mode of files for remote_src=True even if mode was not set as a parameter.  This failed on filesystems which do not have permission bits (https://github.com/ansible/ansible/pull/40099)
- copy module - fixed recursive copy with relative paths (https://github.com/ansible/ansible/pull/40166)
- correct debug display for all cases https://github.com/ansible/ansible/pull/41331
- correctly check hostvars for vars term https://github.com/ansible/ansible/pull/41819
- correctly handle yaml inventory files when entries are null dicts https://github.com/ansible/ansible/issues/41692
- dynamic includes - Allow inheriting attributes from static parents (https://github.com/ansible/ansible/pull/38827)
- dynamic includes - Don't treat undefined vars for conditional includes as truthy (https://github.com/ansible/ansible/pull/39377)
- dynamic includes - Fix IncludedFile comparison for free strategy (https://github.com/ansible/ansible/pull/37083)
- dynamic includes - Improved performance by fixing re-parenting on copy (https://github.com/ansible/ansible/pull/38747)
- dynamic includes - Use the copied and merged task for calculating task vars (https://github.com/ansible/ansible/pull/39762)
- file - fixed the default follow behaviour of file to be true
- file module - Eliminate an error if we're asked to remove a file but something removes it while we are processing the request (https://github.com/ansible/ansible/pull/39466)
- file module - Fix error when recursively assigning permissions and a symlink to a nonexistent file is present in the directory tree (https://github.com/ansible/ansible/issues/39456)
- file module - Fix error when running a task which assures a symlink to a nonexistent file exists for the second and subsequent times (https://github.com/ansible/ansible/issues/39558)
- file module - The file module allowed the user to specify src as a parameter when state was not link or hard.  This is documented as only applying to state=link or state=hard but in previous Ansible, this could have an effect in rare cornercases.  For instance, "ansible -m file -a 'state=directory path=/tmp src=/var/lib'" would create /tmp/lib.  This has been disabled and a warning emitted (will change to an error in Ansible-2.10).
- file module - The touch subcommand had its diff output broken during the 2.6.x development cycle.  This is now fixed (https://github.com/ansible/ansible/issues/41755)
- fix BotoCoreError exception handling
- fix apt-mark on debian6 (https://github.com/ansible/ansible/pull/41530)
- fix async for the aws_s3 module by adding async support to the action plugin (https://github.com/ansible/ansible/pull/40826)
- fix decrypting vault files for the aws_s3 module (https://github.com/ansible/ansible/pull/39634)
- fix errors with S3-compatible APIs if they cannot use ACLs for buckets or objects
- fix permission handling to try to download a file even if the user does not have permission to list all objects in the bucket
- fixed config required handling, specifically for _terms in lookups https://github.com/ansible/ansible/pull/41740
- gce_net - Fix sorting of allowed ports (https://github.com/ansible/ansible/pull/41567)
- group_by - support implicit localhost (https://github.com/ansible/ansible/pull/41860)
- import/include - Ensure role handlers have the proper parent, allowing for correct attribute inheritance (https://github.com/ansible/ansible/pull/39426)
- import_playbook - Pass vars applied to import_playbook into parsing of the playbook as they may be needed to parse the imported plays (https://github.com/ansible/ansible/pull/39521)
- include_role/import_role - Don't overwrite included role handlers with play handlers on parse (https://github.com/ansible/ansible/pull/39563)
- include_role/import_role - Fix parameter templating (https://github.com/ansible/ansible/pull/36372)
- include_role/import_role - Use the computed role name for include_role/import_role so to diffentiate between names computed from host vars (https://github.com/ansible/ansible/pull/39516)
- include_role/import_role - improved performance and recursion depth (https://github.com/ansible/ansible/pull/36470)
- lineinfile - fix insertbefore when used with BOF to not insert duplicate lines (https://github.com/ansible/ansible/issues/38219)
- password lookup - Do not load password lookup in network filters, allowing the password lookup to be overriden (https://github.com/ansible/ansible/pull/41907)
- pause - ensure ctrl+c interrupt works in all cases (https://github.com/ansible/ansible/issues/35372)
- powershell - use the tmpdir set by ``remote_tmp`` for become/async tasks instead of the generic $env:TEMP - https://github.com/ansible/ansible/pull/40210
- selinux - correct check mode behavior to report same changes as normal mode (https://github.com/ansible/ansible/pull/40721)
- spwd - With python 3.6 spwd.getspnam returns PermissionError instead of KeyError if user does not have privileges (https://github.com/ansible/ansible/issues/39472)
- synchronize - Ensure the local connection created by synchronize uses _remote_is_local=True, which causes ActionBase to build a local tmpdir (https://github.com/ansible/ansible/pull/40833)
- template - Fix for encoding issues when a template path contains non-ascii characters and using the template path in ansible_managed (https://github.com/ansible/ansible/issues/27262)
- template action plugin - fix the encoding of filenames to avoid tracebacks on Python2 when characters that are not present in the user's locale are present. (https://github.com/ansible/ansible/pull/39424)
- user - only change the expiration time when necessary (https://github.com/ansible/ansible/issues/13235)
- uses correct conn info for reset_connection  https://github.com/ansible/ansible/issues/27520
- win_environment - Fix for issue where the environment value was deleted when a null value or empty string was set - https://github.com/ansible/ansible/issues/40450
- win_file - fix issue where special chars like [ and ] were not being handled correctly https://github.com/ansible/ansible/pull/37901
- win_get_url - fixed a few bugs around authentication and force no when using an FTP URL
- win_iis_webapppool - redirect some module output to null so Ansible can read the output JSON https://github.com/ansible/ansible/issues/40874
- win_template - fix when specifying the dest option as a directory with and without the trailing slash https://github.com/ansible/ansible/issues/39886
- win_updates - Added the ability to run on a scheduled task for older hosts so async starts working again - https://github.com/ansible/ansible/issues/38364
- win_updates - Fix logic when using a whitelist for multiple updates
- win_updates - Fix typo that hid the download error when a download failed
- win_updates - Fixed issue where running win_updates on async fails without any error
- windows become - Show better error messages when the become process fails
- winrm - Add better error handling when the kinit process fails
- winrm - allow ``ansible_user`` or ``ansible_winrm_user`` to override ``ansible_ssh_user`` when both are defined in an inventory - https://github.com/ansible/ansible/issues/39844
- winrm - ensure pexpect is set to not echo the input on a failure and have a manual sanity check afterwards https://github.com/ansible/ansible/issues/41865
- winrm connection plugin - Fix exception messages sometimes raising a traceback when the winrm connection plugin encounters an unrecoverable error.  https://github.com/ansible/ansible/pull/39333
- xenserver_facts - ensure module works with newer versions of XenServer (https://github.com/ansible/ansible/pull/35821)

New Plugins
-----------

Callback
~~~~~~~~

- cgroup_memory_recap - Profiles maximum memory usage of tasks and full execution using cgroups
- grafana_annotations - send ansible events as annotations on charts to grafana over http api.
- sumologic - Sends task result events to Sumologic

Connection
~~~~~~~~~~

- httpapi - Use httpapi to run command on network appliances

Inventory
~~~~~~~~~

- foreman - foreman inventory source
- gcp_compute - Google Cloud Compute Engine inventory source
- generator - Uses Jinja2 to construct hosts and groups from patterns
- nmap - Uses nmap to find hosts to target

Lookup
~~~~~~

- onepassword - fetch field values from 1Password
- onepassword_raw - fetch raw json data from 1Password

New Modules
-----------

Cloud
~~~~~

amazon
^^^^^^

- aws_caller_facts - Get facts about the user and account being used to make AWS calls.
- aws_config_aggregation_authorization - Manage cross-account AWS Config authorizations
- aws_config_aggregator - Manage AWS Config aggregations across multiple accounts
- aws_config_delivery_channel - Manage AWS Config delivery channels
- aws_config_recorder - Manage AWS Config Recorders
- aws_config_rule - Manage AWS Config resources
- aws_glue_connection - Manage an AWS Glue connection
- aws_glue_job - Manage an AWS Glue job
- aws_inspector_target - Create, Update and Delete Amazon Inspector Assessment Targets
- aws_ses_identity_policy - Manages SES sending authorization policies
- aws_sgw_facts - Fetch AWS Storage Gateway facts
- ec2_eip_facts - List EC2 EIP details
- ec2_vpc_vpn_facts - Gather facts about VPN Connections in AWS.
- elb_network_lb - Manage a Network Load Balancer
- rds_instance_facts - obtain facts about one or more RDS instances
- rds_snapshot_facts - obtain facts about one or more RDS snapshots

azure
^^^^^

- azure_rm_aks - Manage a managed Azure Container Service (AKS) Instance.
- azure_rm_aks_facts - Get Azure Kubernetes Service facts.
- azure_rm_resource - Create any Azure resource.
- azure_rm_resource_facts - Generic facts of Azure resources.

cloudstack
^^^^^^^^^^

- cs_role_permission - Manages role permissions on Apache CloudStack based clouds.

digital_ocean
^^^^^^^^^^^^^

- digital_ocean_account_facts - Gather facts about DigitalOcean User account
- digital_ocean_certificate_facts - Gather facts about DigitalOcean certificates
- digital_ocean_domain_facts - Gather facts about DigitalOcean Domains
- digital_ocean_image_facts - Gather facts about DigitalOcean images
- digital_ocean_load_balancer_facts - Gather facts about DigitalOcean load balancers
- digital_ocean_region_facts - Gather facts about DigitalOcean regions
- digital_ocean_size_facts - Gather facts about DigitalOcean Droplet sizes
- digital_ocean_snapshot_facts - Gather facts about DigitalOcean Snapshot
- digital_ocean_tag_facts - Gather facts about DigitalOcean tags
- digital_ocean_volume_facts - Gather facts about DigitalOcean volumes

google
^^^^^^

- gcp_compute_address - Creates a GCP Address
- gcp_compute_backend_bucket - Creates a GCP BackendBucket
- gcp_compute_backend_service - Creates a GCP BackendService
- gcp_compute_disk - Creates a GCP Disk
- gcp_compute_firewall - Creates a GCP Firewall
- gcp_compute_forwarding_rule - Creates a GCP ForwardingRule
- gcp_compute_global_address - Creates a GCP GlobalAddress
- gcp_compute_global_forwarding_rule - Creates a GCP GlobalForwardingRule
- gcp_compute_health_check - Creates a GCP HealthCheck
- gcp_compute_http_health_check - Creates a GCP HttpHealthCheck
- gcp_compute_https_health_check - Creates a GCP HttpsHealthCheck
- gcp_compute_image - Creates a GCP Image
- gcp_compute_instance - Creates a GCP Instance
- gcp_compute_instance_group - Creates a GCP InstanceGroup
- gcp_compute_instance_group_manager - Creates a GCP InstanceGroupManager
- gcp_compute_instance_template - Creates a GCP InstanceTemplate
- gcp_compute_network - Creates a GCP Network
- gcp_compute_route - Creates a GCP Route
- gcp_compute_ssl_certificate - Creates a GCP SslCertificate
- gcp_compute_subnetwork - Creates a GCP Subnetwork
- gcp_compute_target_http_proxy - Creates a GCP TargetHttpProxy
- gcp_compute_target_https_proxy - Creates a GCP TargetHttpsProxy
- gcp_compute_target_pool - Creates a GCP TargetPool
- gcp_compute_target_ssl_proxy - Creates a GCP TargetSslProxy
- gcp_compute_target_tcp_proxy - Creates a GCP TargetTcpProxy
- gcp_compute_url_map - Creates a GCP UrlMap
- gcp_container_cluster - Creates a GCP Cluster
- gcp_container_node_pool - Creates a GCP NodePool
- gcp_dns_resource_record_set - Creates a GCP ResourceRecordSet
- gcp_pubsub_subscription - Creates a GCP Subscription
- gcp_pubsub_topic - Creates a GCP Topic
- gcp_storage_bucket - Creates a GCP Bucket
- gcp_storage_bucket_access_control - Creates a GCP BucketAccessControl

heroku
^^^^^^

- heroku_collaborator - Add or delete app collaborators on Heroku

memset
^^^^^^

- memset_dns_reload - Request reload of Memset's DNS infrastructure,
- memset_zone - Creates and deletes Memset DNS zones.
- memset_zone_domain - Create and delete domains in Memset DNS zones.
- memset_zone_record - Create and delete records in Memset DNS zones.

misc
^^^^

- cloud_init_data_facts - Retrieve facts of cloud-init.

opennebula
^^^^^^^^^^

- one_host - Manages OpenNebula Hosts
- one_image - Manages OpenNebula images
- one_image_facts - Gather facts about OpenNebula images
- one_service - Deploy and manage OpenNebula services
- one_vm - Creates or terminates OpenNebula instances

openstack
^^^^^^^^^

- os_server_metadata - Add/Update/Delete Metadata in Compute Instances from OpenStack
- os_volume_snapshot - Create/Delete Cinder Volume Snapshots

scaleway
^^^^^^^^

- scaleway_compute - Scaleway compute management module
- scaleway_sshkey - Scaleway SSH keys management module

vmware
^^^^^^

- vmware_cluster_facts - Gather facts about clusters available in given vCenter
- vmware_datastore_cluster - Manage VMware vSphere datastore clusters
- vmware_datastore_maintenancemode - Place a datastore into maintenance mode
- vmware_guest_disk_facts - Gather facts about disks of given virtual machine
- vmware_guest_snapshot_facts - Gather facts about virtual machine's snapshots in vCenter
- vmware_host_capability_facts - Gathers facts about an ESXi host's capability information
- vmware_host_powerstate - Manages power states of host systems in vCenter
- vmware_local_user_facts - Gather facts about users on the given ESXi host
- vmware_portgroup_facts - Gathers facts about an ESXi host's portgroup configuration
- vmware_resource_pool_facts - Gathers facts about resource pool information
- vmware_tag - Manage VMware tags
- vmware_tag_facts - Manage VMware tag facts
- vmware_vswitch_facts - Gathers facts about an ESXi host's vswitch configurations

Clustering
~~~~~~~~~~

k8s
^^^

- k8s - Manage Kubernetes (K8s) objects

Commands
~~~~~~~~

- psexec - Runs commands on a remote Windows host based on the PsExec model

Monitoring
~~~~~~~~~~

- spectrum_device - Creates/deletes devices in CA Spectrum.

zabbix
^^^^^^

- zabbix_group_facts - Gather facts about Zabbix hostgroup

Net Tools
~~~~~~~~~

ldap
^^^^

- ldap_passwd - Set passwords in LDAP.

Network
~~~~~~~

aci
^^^

- aci_l3out - Manage Layer 3 Outside (L3Out) objects (l3ext:Out)

avi
^^^

- avi_autoscalelaunchconfig - Module for setup of AutoScaleLaunchConfig Avi RESTful Object
- avi_l4policyset - Module for setup of L4PolicySet Avi RESTful Object
- avi_useraccount - Avi UserAccount Module

cnos
^^^^

- cnos_command - Run arbitrary commands on Lenovo CNOS devices
- cnos_config - Manage Lenovo CNOS configuration sections

exos
^^^^

- exos_command - Run commands on remote devices running Extreme EXOS

f5
^^

- bigip_data_group - Manage data groups on a BIG-IP
- bigip_device_license - Manage license installation and activation on BIG-IP devices
- bigip_gtm_global - Manages global GTM settings
- bigip_gtm_monitor_bigip - Manages F5 BIG-IP GTM BIG-IP monitors
- bigip_gtm_monitor_external - Manages external GTM monitors on a BIG-IP
- bigip_gtm_monitor_firepass - Manages F5 BIG-IP GTM FirePass monitors
- bigip_gtm_monitor_http - Manages F5 BIG-IP GTM http monitors
- bigip_gtm_monitor_https - Manages F5 BIG-IP GTM https monitors
- bigip_gtm_monitor_tcp - Manages F5 BIG-IP GTM tcp monitors
- bigip_gtm_monitor_tcp_half_open - Manages F5 BIG-IP GTM tcp half-open monitors
- bigip_gtm_pool_member - Manage GTM pool member settings
- bigip_gtm_virtual_server - Manages F5 BIG-IP GTM virtual servers
- bigip_log_destination - Manages log destinations on a BIG-IP.
- bigip_log_publisher - Manages log publishers on a BIG-IP
- bigip_management_route - Manage system management routes on a BIG-IP
- bigip_monitor_external - Manages external LTM monitors on a BIG-IP
- bigip_profile_dns - Manage DNS profiles on a BIG-IP
- bigip_profile_tcp - Manage TCP profiles on a BIG-IP
- bigip_profile_udp - Manage UDP profiles on a BIG-IP
- bigip_service_policy - Manages service policies on a BIG-IP.
- bigip_smtp - Manages SMTP settings on the BIG-IP
- bigip_snmp_community - Manages SNMP communities on a BIG-IP.
- bigip_timer_policy - Manage timer policies on a BIG-IP
- bigip_trunk - Manage trunks on a BIG-IP
- bigiq_application_fasthttp - Manages BIG-IQ FastHTTP applications
- bigiq_application_fastl4_tcp - Manages BIG-IQ FastL4 TCP applications
- bigiq_application_fastl4_udp - Manages BIG-IQ FastL4 UDP applications
- bigiq_application_http - Manages BIG-IQ HTTP applications
- bigiq_application_https_offload - Manages BIG-IQ HTTPS offload applications
- bigiq_application_https_waf - Manages BIG-IQ HTTPS WAF applications
- bigiq_regkey_license_assignment - Manage regkey license assignment on BIG-IPs from a BIG-IQ.
- bigiq_utility_license - Manage utility licenses on a BIG-IQ

files
^^^^^

- net_get - Copy a file from a network device to Ansible Controller
- net_put - Copy a file from Ansible Controller to a network device

fortios
^^^^^^^

- fortios_webfilter - Configure webfilter capabilities of FortiGate and FortiOS.

meraki
^^^^^^

- meraki_admin - Manage administrators in the Meraki cloud
- meraki_network - Manage networks in the Meraki cloud
- meraki_organization - Manage organizations in the Meraki cloud
- meraki_snmp - Manage organizations in the Meraki cloud

netconf
^^^^^^^

- netconf_get - Fetch configuration/state data from NETCONF enabled network devices.
- netconf_rpc - Execute operations on NETCONF enabled network devices.

slxos
^^^^^

- slxos_command - Run commands on remote devices running Extreme Networks SLX-OS
- slxos_config - Manage Extreme Networks SLX-OS configuration sections
- slxos_facts - Collect facts from devices running Extreme SLX-OS
- slxos_interface - Manage Interfaces on Extreme SLX-OS network devices
- slxos_l2_interface - Manage Layer-2 interface on Extreme Networks SLXOS devices.
- slxos_l3_interface - Manage L3 interfaces on Extreme Networks SLXOS network devices.
- slxos_linkagg - Manage link aggregation groups on Extreme Networks SLXOS network devices
- slxos_vlan - Manage VLANs on Extreme Networks SLX-OS network devices

Packaging
~~~~~~~~~

language
^^^^^^^^

- yarn - Manage node.js packages with Yarn

os
^^

- flatpak - Manage flatpaks
- flatpak_remote - Manage flatpak repository remotes

Source Control
~~~~~~~~~~~~~~

- gitlab_deploy_key - Manages GitLab project deploy keys.
- gitlab_hooks - Manages GitLab project hooks.

Storage
~~~~~~~

glusterfs
^^^^^^^^^

- gluster_peer - Attach/Detach peers to/from the cluster

netapp
^^^^^^

- na_ontap_aggregate - Manage NetApp ONTAP aggregates.
- na_ontap_broadcast_domain - Manage NetApp ONTAP broadcast domains.
- na_ontap_broadcast_domain_ports - Manage NetApp Ontap broadcast domain ports
- na_ontap_cifs - Manage NetApp cifs-share
- na_ontap_cifs_acl - Manage NetApp cifs-share-access-control
- na_ontap_cifs_server - cifs server configuration
- na_ontap_cluster - Create/Join ONTAP cluster. Apply license to cluster
- na_ontap_cluster_ha - Manage HA status for cluster
- na_ontap_export_policy - Manage NetApp ONTAP export-policy
- na_ontap_export_policy_rule - Manage ONTAP Export rules
- na_ontap_igroup - ONTAP iSCSI igroup configuration
- na_ontap_interface - ONTAP LIF configuration
- na_ontap_iscsi - Manage NetApp Ontap iscsi service
- na_ontap_job_schedule - Manage NetApp Ontap Job Schedule
- na_ontap_license - Manage NetApp ONTAP protocol and feature licenses
- na_ontap_lun - Manage  NetApp Ontap luns
- na_ontap_lun_map - Manage NetApp Ontap lun maps
- na_ontap_net_ifgrp - Create, modify, destroy the network interface group
- na_ontap_net_port - Manage NetApp Ontap network ports.
- na_ontap_net_routes - Manage NetApp Ontap network routes
- na_ontap_net_vlan - Manage NetApp Ontap network vlan
- na_ontap_nfs - Manage Ontap NFS status
- na_ontap_ntp - Create/Delete/modify_version ONTAP NTP server
- na_ontap_qtree - Manage qtrees
- na_ontap_service_processor_network - Manage NetApp Ontap service processor network
- na_ontap_snapshot - Manage NetApp Sanpshots
- na_ontap_snmp - Manage NetApp SNMP community
- na_ontap_svm - Manage NetApp Ontap svm
- na_ontap_ucadapter - ONTAP UC adapter configuration
- na_ontap_user - useradmin configuration and management
- na_ontap_user_role - useradmin configuration and management
- na_ontap_volume - Manage NetApp ONTAP volumes.
- na_ontap_volume_clone - Manage NetApp Ontap volume clones.

purestorage
^^^^^^^^^^^

- purefa_ds - Configure FlashArray Directory Service
- purefa_facts - Collect facts from Pure Storage FlashArray
- purefa_pgsnap - Manage protection group snapshots on Pure Storage FlashArrays
- purefb_fs - Manage filesystemon Pure Storage FlashBlade`
- purefb_snap - Manage filesystem snapshots on Pure Storage FlashBlades

System
~~~~~~

- sysvinit - Manage SysV services.

Web Infrastructure
~~~~~~~~~~~~~~~~~~

- acme_account - Create, modify or delete accounts with Let's Encrypt

Windows
~~~~~~~

- win_domain_computer - Manage computers in Active Directory
- win_hostname - Manages local Windows computer name.
- win_pester - Run Pester tests on Windows hosts
