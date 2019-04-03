========================================
Ansible 2.7 "In the Light" Release Notes
========================================

.. contents:: Topics


v2.7.10
=======

Release Summary
---------------

| Release Date: 2019-04-03
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Catch all connection timeout related exceptions and raise AnsibleConnectionError instead
- openssl_pkcs12, openssl_privatekey, openssl_publickey - These modules no longer delete the output file before starting to regenerate the output, or when generating the output failed.

Bugfixes
--------

- Backport of https://github.com/ansible/ansible/pull/54105, pamd - fix idempotence issue when removing rules
- Use custom JSON encoder in conneciton.py so that ansible objects (AnsibleVaultEncryptedUnicode, for example) can be sent to the persistent connection process
- allow 'dict()' jinja2 global to function the same even though it has changed in jinja2 versions
- azure_rm inventory plugin - fix missing hostvars properties (https://github.com/ansible/ansible/pull/53046)
- azure_rm inventory plugin - fix no nic type in vmss nic. (https://github.com/ansible/ansible/pull/53496)
- deprecate {Get/Set}ManagerAttributes commands (https://github.com/ansible/ansible/issues/47590)
- flatpak_remote - Handle empty output in remote_exists, fixes https://github.com/ansible/ansible/issues/51481
- foreman - fix Foreman returning host parameters
- get_url - Fix issue with checksum validation when using a file to ensure we skip lines in the file that do not contain exactly 2 parts. Also restrict exception handling to the minimum number of necessary lines (https://github.com/ansible/ansible/issues/48790)
- grafana_datasource - Fixed an issue when running Python3 and using basic auth (https://github.com/ansible/ansible/issues/49147)
- include_tasks - Fixed an unexpected exception if no file was given to include.
- openssl_certificate - fix ``state=absent``.
- openssl_certificate, openssl_csr, openssl_pkcs12, openssl_privatekey, openssl_publickey - The modules are now able to overwrite write-protected files (https://github.com/ansible/ansible/issues/48656).
- openssl_dhparam - fix ``state=absent`` idempotency and ``changed`` flag.
- openssl_pkcs12, openssl_privatekey - These modules now accept the output file mode in symbolic form or as a octal string (https://github.com/ansible/ansible/issues/53476).
- openssl_publickey - fixed crash on Python 3 when OpenSSH private keys were used with passphrases.
- openstack inventory plugin: allow "constructed" functionality (``compose``, ``groups``, and ``keyed_groups``) to work as documented.
- random_mac - generate a proper MAC address when the provided vendor prefix is two or four characters (https://github.com/ansible/ansible/issues/50838)
- replace - fix behavior when ``before`` and ``after`` are used together (https://github.com/ansible/ansible/issues/31354)
- report correct CPU information on ARM systems (https://github.com/ansible/ansible/pull/52884)
- slurp - Fix issues when using paths on Windows with glob like characters, e.g. ``[``, ``]``
- ssh - Check the return code of the ssh process before raising AnsibleConnectionFailure, as the error message for the ssh process will likely contain more useful information. This will improve the missing interpreter messaging when using modules such as setup which have a larger payload to transfer when combined with pipelining. (https://github.com/ansible/ansible/issues/53487)
- tower_settings - 'name' and 'value' parameters are always required, module can not be used in order to get a setting
- win_acl - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_acl_inheritance - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_certificate_store - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_chocolatey - Fix incompatibilities with the latest release of Chocolatey ``v0.10.12+``
- win_copy - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_file - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_find - Ensure found files are sorted alphabetically by the path instead of it being random
- win_find - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_owner - Fix issues when using paths with glob like characters, e.g. ``[``, ``]``
- win_psexec - Support executables with a space in the path
- win_reboot - Fix reboot command validation failure when running under the psrp connection plugin
- win_tempfile - Always return the full NTFS absolute path and not a DOS 8.3 path.
- win_user_right - Fix output containing non json data - https://github.com/ansible/ansible/issues/54413
- windows - Fixed various module utils that did not work with path that had glob like chars
- yum - fix disable_excludes on systems with yum rhn plugin enabled (https://github.com/ansible/ansible/issues/53134)

v2.7.9
======

Release Summary
---------------

| Release Date: 2019-03-14
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Add missing import for ConnectionError in edge and routeros module_utils.
- ``to_yaml`` filter updated to maintain formatting consistency when used with ``pyyaml`` versions 5.1 and later (https://github.com/ansible/ansible/pull/53772)
- docker_image - set ``changed`` to ``false`` when using ``force: yes`` to tag or push an image that ends up being identical to one already present on the Docker host or Docker registry.
- jenkins_plugin - Set new default value for the update_url parameter (https://github.com/ansible/ansible/issues/52086)

Bugfixes
--------

- Fix bug where some inventory parsing tracebacks were missing or reported under the wrong plugin.
- Fix rabbitmq_plugin idempotence due to information message in new version of rabbitmq (https://github.com/ansible/ansible/pull/52166)
- Fixed KeyError issue in vmware_host_config_manager when a supported option isn't already set (https://github.com/ansible/ansible/issues/44561).
- Fixed issue related to --yaml flag in vmware_vm_inventory. Also fixed caching issue in vmware_vm_inventory (https://github.com/ansible/ansible/issues/52381).
- If large integers are passed as options to modules under Python 2, module argument parsing will reject them as they are of type ``long`` and not of type ``int``.
- allow nice error to work when auto plugin reads file w/o `plugin` field
- ansible-doc - Fix traceback on providing arguemnt --all to ansible-doc command
- azure_rm_virtualmachine_facts - fixed crash related to attached managed disks (https://github.com/ansible/ansible/issues/52181)
- basic - modify the correct variable when determining available hashing algorithms to avoid errors when md5 is not available (https://github.com/ansible/ansible/issues/51355)
- cloudscale - Fix compatibilty with Python3 in version 3.5 and lower.
- convert input into text to ensure valid comparisons in nmap inventory plugin
- dict2items - Allow dict2items to work with hostvars
- dnsimple - fixed a KeyError exception related to record types handling.
- docker_container - now returns warnings from docker daemon on container creation and updating.
- docker_swarm - Fixed node_id parameter not working for node removal (https://github.com/ansible/ansible/issues/53501)
- docker_swarm - do not crash with older docker daemons (https://github.com/ansible/ansible/issues/51175).
- docker_swarm - fixes idempotency for the ``ca_force_rotate`` option.
- docker_swarm - improve Swarm detection.
- docker_swarm - improve idempotency checking; ``rotate_worker_token`` and ``rotate_manager_token`` are now also used when all other parameters have not changed.
- docker_swarm - now supports docker-py 1.10.0 and newer for most operations, instead only docker 2.6.0 and newer.
- docker_swarm - properly implement check mode (it did apply changes).
- docker_swarm - the ``force`` option was ignored when ``state: present``.
- docker_swarm_service - do basic validation of ``publish`` option if specified (must be list of dicts).
- docker_swarm_service - don't crash when ``publish`` is not specified.
- docker_swarm_service - fix problem with docker daemons which do not return ``UpdateConfig`` in the swarm service spec.
- docker_swarm_service - the return value was documented as ``ansible_swarm_service``, but the module actually returned ``ansible_docker_service``. Documentation and code have been updated so that the variable is now called ``swarm_service``. In Ansible 2.7.x, the old name ``ansible_docker_service`` can still be used to access the result.
- ec2 - if the private_ip has been provided for the new network interface it shouldn't also be added to top level parameters for run_instances()
- fix DNSimple to ensure check works even when the number of records is larger than 100
- get_url - return no change in check mode when checksum matches
- inventory plugins - Fix creating groups from composed variables by getting the latest host variables
- inventory_aws_ec2 - fix no_log indentation so AWS temporary credentials aren't displayed in tests
- jenkins_plugin - Prevent plugin to be reinstalled when state=present (https://github.com/ansible/ansible/issues/43728)
- lvol - fixed ValueError when using float size (https://github.com/ansible/ansible/issues/32886, https://github.com/ansible/ansible/issues/29429)
- mysql - MySQLdb doesn't import the cursors module for its own purposes so it has to be imported in MySQL module utilities before it can be used in dependent modules like the proxysql module family.
- mysql - fixing unexpected keyword argument 'cursorclass' issue after migration from MySQLdb to PyMySQL.
- mysql_user: match backticks, single and double quotes when checking user privileges.
- onepassword_facts - Fixes issues which prevented this module working with 1Password CLI version 0.5.5 (or greater). Older versions of the CLI were deprecated by 1Password and will no longer function.
- openssl_certificate - ``has_expired`` correctly checks if the certificate is expired or not
- openssl_certificate - fix Python 3 string/bytes problems for `notBefore`/`notAfter` for self-signed and ownCA providers.
- openssl_certificate - make sure that extensions are actually present when their values should be checked.
- openssl_csr - improve ``subject`` validation.
- openssl_csr - improve error messages for invalid SANs.
- play order is now applied under all circumstances, fixes
- remote_management foreman - Fixed issue where it was impossible to createdelete a product because product was missing in dict choices ( https://github.com/ansible/ansible/issues/48594 )
- rhsm_repository - handle systems without any repos
- skip invalid plugin after warning in loader
- urpmi module - fixed issue
- win_certificate_store - Fix exception handling typo
- win_chocolatey - Fix issue when parsing a beta Chocolatey install - https://github.com/ansible/ansible/issues/52331
- win_chocolatey_source - fix bug where a Chocolatey source could not be disabled unless ``source`` was also set - https://github.com/ansible/ansible/issues/50133
- win_domain - Do not fail if DC is already promoted but a reboot is required, return ``reboot_required: True``
- win_domain - Fix when running without credential delegated authentication - https://github.com/ansible/ansible/issues/53182
- win_file - Fix issue when managing hidden files and directories - https://github.com/ansible/ansible/issues/42466
- winrm - attempt to recover from a WinRM send input failure if possible
- zabbix_hostmacro: fixes truncation of macro contexts that contain colons (see https://github.com/ansible/ansible/pull/51853)

New Plugins
-----------

Inventory
~~~~~~~~~

- vmware_vm_inventory - VMware Guest inventory source

v2.7.8
======

Release Summary
---------------

| Release Date: 2019-02-21
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Raise AnsibleConnectionError on winrm connnection errors

Bugfixes
--------

- Backport of https://github.com/ansible/ansible/pull/46478 , fixes name collision in haproxy module
- Fix aws_ec2 inventory plugin code to automatically populate regions when missing as documentation states, also leverage config system vs self default/type validation
- Fix unexpected error when using Jinja2 native types with non-strict constructed keyed_groups (https://github.com/ansible/ansible/issues/52158).
- If an ios module uses a section filter on a device which does not support it, retry the command without the filter.
- acme_challenge_cert_helper - the module no longer crashes when the required ``cryptography`` library cannot be found.
- azure_rm_managed_disk_facts - added missing implementation of listing managed disks by resource group
- azure_rm_mysqlserver - fixed issues with passing parameters while updating existing server instance
- azure_rm_postgresqldatabase - fix force_update bug (https://github.com/ansible/ansible/issues/50978).
- azure_rm_postgresqldatabase - fix force_update bug.
- azure_rm_postgresqlserver - fixed issues with passing parameters while updating existing server instance
- azure_rm_sqlserver - fix for tags support
- azure_rm_virtualmachine - fixed several crashes in module
- azure_rm_virtualmachine_facts - fix crash when vm created from custom image
- azure_rm_virtualmachine_facts - fixed crash related to VM with managed disk attached
- ec2 - Correctly sets the end date of the Spot Instance request. Sets `ValidUntil` value in proper way so it will be auto-canceled through `spot_wait_timeout` interval.
- openssl_csr - fixes idempotence problem with PyOpenSSL backend when no Subject Alternative Names were specified.
- openstack inventory plugin - send logs from sdk to stderr so they do not combine with output
- psrp - do not display bootstrap wrapper for each module exec run
- redfish_utils - get standard properties for firmware entries (https://github.com/ansible/ansible/issues/49832)
- remote home directory - Disallow use of remote home directories that include relative pathing by means of `..` (CVE-2019-3828) (https://github.com/ansible/ansible/pull/52133)
- ufw - when using ``state: reset`` in check mode, ``ufw --dry-run reset`` was executed, which causes a loss of firewall rules. The ``ufw`` module was adjusted to no longer run ``ufw --dry-run reset`` to prevent this from happening.
- ufw: make sure that only valid values for ``direction`` are passed on.
- update GetBiosBootOrder to use standard Redfish resources (https://github.com/ansible/ansible/issues/47571)
- win become - Fix some scenarios where become failed to create an elevated process
- win_psmodule - the NuGet package provider will be updated, if needed, to avoid issue under adding a repository
- yum - Remove incorrect disable_includes error message when using disable_excludes (https://github.com/ansible/ansible/issues/51697)
- yum - properly handle a proxy config in yum.conf for an unauthenticated proxy

v2.7.7
======

Release Summary
---------------

| Release Date: 2019-02-07
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Allow check_mode with supports_generate_diff capability in cli_config. (https://github.com/ansible/ansible/pull/51417)
- Fixed typo in vmware documentation fragment. Changed "supported added" to "support added".

Bugfixes
--------

- All K8S_AUTH_* environment variables are now properly loaded by the k8s lookup plugin
- Change backup file globbing for network _config modules so backing up one host's config will not delete the backed up config of any host whose hostname is a subset of the first host's hostname (e.g., switch1 and switch11)
- Fixes bug where nios_a_record wasn't getting deleted if an uppercase named a_record was being passed. (https://github.com/ansible/ansible/pull/51539)
- aci_aaa_user - Fix setting user description (https://github.com/ansible/ansible/issues/51406)
- apt_repository - fixed failure under Python 3.7 (https://github.com/ansible/ansible/pull/47219)
- archive - Fix check if archive is created in path to be removed
- azure_rm inventory plugin - fix azure batch request (https://github.com/ansible/ansible/pull/50006)
- cnos_backup - fixed syntax error (https://github.com/ansible/ansible/pull/47219)
- cnos_image - fixed syntax error (https://github.com/ansible/ansible/pull/47219)
- consul_kv - minor error-handling bugfix under Python 3.7 (https://github.com/ansible/ansible/pull/47219)
- copy - align invocation in return value between check and normal mode
- delegate_facts - fix to work properly under block and include_role (https://github.com/ansible/ansible/pull/51553)
- docker_swarm_service - fix ``endpoint_mode`` and ``publish`` idempotency.
- ec2_instance - Correctly adds description when adding a single ENI to the instance
- ensure we have a XDG_RUNTIME_DIR, as it is not handled correctly by some privilege escalation configurations
- file - Allow state=touch on file the user does not own https://github.com/ansible/ansible/issues/50943
- fix ansible-pull hanlding of extra args, complex quoting is needed for inline JSON
- fix ansible_connect_timeout variable in network_cli,netconf,httpapi and nxos_install_os timeout check
- netapp_e_storagepool - fixed failure under Python 3.7 (https://github.com/ansible/ansible/pull/47219)
- onepassword_facts - Fix an issue looking up some 1Password items which have a 'password' attribute alongside the 'fields' attribute, not inside it.
- prevent import_role from inserting dupe into `roles:` execution when duplicate signature role already exists in the section.
- reboot - Fix bug where the connection timeout was not reset in the same task after rebooting
- ssh connection - do not retry with invalid credentials to prevent account lockout (https://github.com/ansible/ansible/issues/48422)
- systemd - warn when exeuting in a chroot environment rather than failing (https://github.com/ansible/ansible/pull/43904)
- win_chocolatey - Fix hang when used with proxy for the first time - https://github.com/ansible/ansible/issues/47669
- win_power_plan - Fix issue where win_power_plan failed on newer Windows 10 builds - https://github.com/ansible/ansible/issues/43827

v2.7.6
======

Release Summary
---------------

| Release Date: 2019-01-17
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Added documentation about using VMware dynamic inventory plugin.
- Fixed bug around populating host_ip in hostvars in vmware_vm_inventory.
- Image reference change in Azure VMSS is detected and applied correctly.
- docker_volume - reverted changed behavior of ``force``, which was released in Ansible 2.7.1 to 2.7.5, and Ansible 2.6.8 to 2.6.11. Volumes are now only recreated if the parameters changed **and** ``force`` is set to ``true`` (instead of or). This is the behavior which has been described in the documentation all the time.
- set ansible_os_family from name variable in os-release
- yum and dnf can now handle installing packages from URIs that are proxy redirects and don't end in the .rpm file extension

Bugfixes
--------

- Added log message at -vvvv when using netconf connection listing connection details.
- Changes how ansible-connection names socket lock files. They now use the same name as the socket itself, and as such do not lock other attempts on connections to the same host, or cause issues with overly-long hostnames.
- Fix mandatory statement error for junos modules (https://github.com/ansible/ansible/pull/50138)
- Moved error in netconf connection plugin from at import to on connection.
- This reverts some changes from commit 723daf3. If a line is found in the file, exactly or via regexp matching, it must not be added again. `insertafter`/`insertbefore` options are used only when a line is to be inserted, to specify where it must be added.
- allow using openstack inventory plugin w/o a cache
- callbacks - Do not filter out exception, warnings, deprecations on failure when using debug (https://github.com/ansible/ansible/issues/47576)
- certificate_complete_chain - fix behavior when invalid file is parsed while reading intermediate or root certificates.
- copy - Ensure that the src file contents is converted to unicode in diff information so that it is properly wrapped by AnsibleUnsafeText to prevent unexpected templating of diff data in Python3 (https://github.com/ansible/ansible/issues/45717)
- correct behaviour of verify_file for vmware inventory plugin, it was always returning True
- dnf - fix issue where ``conf_file`` was not being loaded properly
- dnf - fix update_cache combined with install operation to not cause dnf transaction failure
- docker_container - fix ``network_mode`` idempotency if the ``container:<container-name>`` form is used (as opposed to ``container:<container-id>``) (https://github.com/ansible/ansible/issues/49794)
- docker_container - warning when non-string env values are found, avoiding YAML parsing issues. Will be made an error in Ansible 2.8. (https://github.com/ansible/ansible/issues/49802)
- docker_swarm_service - Document ``labels`` and ``container_labels`` with correct type.
- docker_swarm_service - Document ``limit_memory`` and ``reserve_memory`` correctly on how to specify sizes.
- docker_swarm_service - Document minimal API version for ``configs`` and ``secrets``.
- docker_swarm_service - fix use of Docker API so that services are not detected as present if there is an existing service whose name is a substring of the desired service
- docker_swarm_service - fixing falsely reporting ``update_order`` as changed when option is not used.
- document old option that was initally missed
- ec2_instance now respects check mode https://github.com/ansible/ansible/pull/46774
- fix for network_cli - ansible_command_timeout not working as expected (#49466)
- fix handling of firewalld port if protocol is missing
- fix lastpass lookup failure on python 3 (https://github.com/ansible/ansible/issues/42062)
- flatpak - Fixed Python 2/3 compatibility
- flatpak - Fixed issue where newer versions of flatpak failed on flatpak removal
- flatpak_remote - Fixed Python 2/3 compatibility
- gcp_compute_instance - fix crash when the instance metadata is not set
- grafana_dashboard - Fix a pair of unicode string handling issues with version checking (https://github.com/ansible/ansible/pull/49194)
- host execution order - Fix ``reverse_inventory`` not to change the order of the items before reversing on python2 and to not backtrace on python3
- icinga2_host - fixed the issue with not working ``use_proxy`` option of the module.
- influxdb_user - An unspecified password now sets the password to blank, except on existing users. This previously caused an unhandled exception.
- influxdb_user - Fixed unhandled exception when using invalid login credentials (https://github.com/ansible/ansible/issues/50131)
- openssl_* - fix error when ``path`` contains a file name without path.
- openssl_csr - fix problem with idempotency of keyUsage option.
- openssl_pkcs12 - now does proper path expansion for ``ca_certificates``.
- os_security_group_rule - os_security_group_rule doesn't exit properly when secgroup doesn't exist and state=absent (https://github.com/ansible/ansible/issues/50057)
- paramiko_ssh - add auth_timeout parameter to ssh.connect when supported by installed paramiko version. This will prevent "Authentication timeout" errors when a slow authentication step (>30s) happens with a host (https://github.com/ansible/ansible/issues/42596)
- purefa_facts and purefb_facts now correctly adds facts into main ansible_fact dictionary (https://github.com/ansible/ansible/pull/50349)
- reboot - add appropriate commands to make the plugin work with VMware ESXi (https://github.com/ansible/ansible/issues/48425)
- reboot - add support for rebooting AIX (https://github.com/ansible/ansible/issues/49712)
- reboot - gather distribution information in order to support Alpine and other distributions (https://github.com/ansible/ansible/issues/46723)
- reboot - search common paths for the shutdown command and use the full path to the binary rather than depending on the PATH of the remote system (https://github.com/ansible/ansible/issues/47131)
- reboot - use a common set of commands for older and newer Solaris and SunOS variants (https://github.com/ansible/ansible/pull/48986)
- redfish_utils - fix reference to local variable 'systems_service'
- setup - fix the rounding of the ansible_memtotal_mb value on VMWare vm's (https://github.com/ansible/ansible/issues/49608)
- vultr_server - fixed multiple ssh keys were not handled.
- win_copy - Fix copy of a dir that contains an empty directory - https://github.com/ansible/ansible/issues/50077
- win_firewall_rule - Remove invalid 'bypass' action
- win_lineinfile - Fix issue where a malformed json block was returned causing an error
- win_updates - Correctly report changes on success

v2.7.5
======

Release Summary
---------------

| Release Date: 2018-12-13
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Add warning about falling back to jinja2_native=false when Jinja2 version is lower than 2.10.
- Change the position to search os-release since clearlinux new versions are providing /etc/os-release too
- Fixed typo in ansible-galaxy info command.
- Improve the deprecation message for squashing, to not give misleading advice
- Update docs and return section of vmware_host_service_facts module.
- ansible-galaxy: properly warn when git isn't found in an installed bin path instead of traceback
- dnf module properly load and initialize dnf package manager plugins
- docker_swarm_service: use docker defaults for the ``user`` parameter if it is set to ``null``

Bugfixes
--------

- ACME modules: improve error messages in some cases (include error returned by server).
- Added unit test for VMware module_utils.
- Also check stdout for interpreter errors for more intelligent messages to user
- Backported support for Devuan-based distribution
- Convert hostvars data in OpenShift inventory plugin to be serializable by ansible-inventory
- Fix AttributeError (Python 3 only) when an exception occurs while rendering a template
- Fix N3K power supply facts (https://github.com/ansible/ansible/pull/49150).
- Fix NameError nxos_facts (https://github.com/ansible/ansible/pull/48981).
- Fix VMware module utils for self usage.
- Fix error in OpenShift inventory plugin when a pod has errored and is empty
- Fix if the route table changed to none (https://github.com/ansible/ansible/pull/49533)
- Fix iosxr netconf plugin response namespace (https://github.com/ansible/ansible/pull/49300)
- Fix issues with nxos_install_os module for nxapi (https://github.com/ansible/ansible/pull/48811).
- Fix lldp and cdp neighbors information (https://github.com/ansible/ansible/pull/48318)(https://github.com/ansible/ansible/pull/48087)(https://github.com/ansible/ansible/pull/49024).
- Fix nxos_interface and nxos_linkagg Idempotence issue (https://github.com/ansible/ansible/pull/46437).
- Fix traceback when updating facts and the fact cache plugin was nonfunctional
- Fix using vault encrypted data with jinja2_native (https://github.com/ansible/ansible/issues/48950)
- Fixed: Make sure that the files excluded when extracting the archive are not checked. https://github.com/ansible/ansible/pull/45122
- Fixes issue where a password parameter was not set to no_log
- Respect no_log on retry and high verbosity (CVE-2018-16876)
- aci_rest - Fix issue ignoring custom port
- acme_account, acme_account_facts - in some cases, it could happen that the modules return information on disabled accounts accidentally returned by the ACME server.
- docker_swarm - decreased minimal required API version from 1.35 to 1.25; some features require API version 1.30 though.
- docker_swarm_service: fails because of default "user: root" (https://github.com/ansible/ansible/issues/49199)
- ec2_metadata_facts - Parse IAM role name from the security credential field since the instance profile name is different
- fix azure_rm_image module use positional parameter (https://github.com/ansible/ansible/pull/49394)
- fixes an issue with dict_merge in network utils (https://github.com/ansible/ansible/pull/49474)
- gcp_utils - fix google auth scoping issue with application default credentials or google cloud engine credentials. Only scope credentials that can be scoped.
- mail - fix python 2.7 regression
- openstack - fix parameter handling when cloud provided as dict https://github.com/ansible/ansible/issues/42858
- os_user - Include domain parameter in user deletion https://github.com/ansible/ansible/issues/42901
- os_user - Include domain parameter in user lookup https://github.com/ansible/ansible/issues/42901
- ovirt_storage_connection - comparing passwords breaks idempotency in update_check (https://github.com/ansible/ansible/issues/48933)
- paramiko_ssh - improve log message to state the connection type
- reboot - use IndexError instead of TypeError in exception
- redis cache - Support version 3 of the redis python library (https://github.com/ansible/ansible/issues/49341)
- sensu_silence - Cast int for expire field to avoid call failure to sensu API.
- vmware_host_service_facts - handle exception when service package does not have package name.
- win_nssm - Switched to Argv-ToString for escaping NSSM credentials (https://github.com/ansible/ansible/issues/48728)
- zabbix_hostmacro - Added missing validate_certs logic for running module against Zabbix servers with untrused SSL certificates (https://github.com/ansible/ansible/issues/47611)
- zabbix_hostmacro - Fixed support for user macros with context (https://github.com/ansible/ansible/issues/46953)

v2.7.4
======

Release Summary
---------------

| Release Date: 2018-11-30
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Bugfixes
--------

- powershell - add ``lib/ansible/executor/powershell`` to the packaging data

v2.7.3
======

Release Summary
---------------

| Release Date: 2018-11-29
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Document Path and Port are mutually exclusive parameters in wait_for module.
- Puppet module remove ``--ignorecache`` to allow Puppet 6 support
- dnf properly support modularity appstream installation via overloaded group modifier syntax
- proxmox_kvm - fix exception.
- win_security_policy - warn users to use win_user_right instead when editing ``Privilege Rights``

Bugfixes
--------

- Fix the issue that FTD HTTP API retries authentication-related HTTP requests.
- Fix the issue that module fails when the Swagger model does not have required fields.
- Fix the issue with comparing string-like objects.
- Fix using omit on play keywords (https://github.com/ansible/ansible/issues/48673)
- Windows - prevent sensitive content from appearing in scriptblock logging (CVE 2018-16859)
- apt_key - Disable TTY requirement in GnuPG for the module to work correctly when SSH pipelining is enabled (https://github.com/ansible/ansible/pull/48580)
- better error message when bad type in config, deal with EVNAR= more gracefully https://github.com/ansible/ansible/issues/22470
- configuration retrieval would fail on non primed plugins
- cs_template - Fixed a KeyError on state=extracted.
- docker_container - fix idempotency problems with docker-py caused by previous ``init`` idempotency fix.
- docker_container - fix interplay of docker-py version check with argument_spec validation improvements.
- docker_network - ``driver_options`` containing Python booleans would cause Docker to throw exceptions.
- ec2_group - Fix comparison of determining which rules to purge by ignoring descriptions - https://github.com/ansible/ansible/issues/47904
- pip module - fix setuptools/distutils replacement (https://github.com/ansible/ansible/issues/47198)
- sysvinit - enabling a service should use "defaults" if no runlevels are specified

v2.7.2
======

Release Summary
---------------

| Release Date: 2018-11-15
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Fix documentation for cloning template.
- Parsing plugin filter may raise TypeError, gracefully handle this exception and let user know about the syntax error in plugin filter file.
- Scenario guide for VMware HTTP API usage.
- Update plugin filter documentation.
- fix yum and dnf autoremove input sanitization to properly warn user if invalid options passed and update documentation to match
- improve readability and fix privileges names on vmware scenario_clone_template.
- k8s - updated module documentation to mention how to avoid SSL validation errors
- yum - when checking for updates, now properly include Obsoletes (both old and new) package data in the module JSON output, fixes https://github.com/ansible/ansible/issues/39978

Bugfixes
--------

- ACME modules support `POST-as-GET <https://community.letsencrypt.org/t/acme-v2-scheduled-deprecation-of-unauthenticated-resource-gets/74380>`__ and will be able to access Let's Encrypt ACME v2 endpoint after November 1st, 2019.
- Add force disruptive option nxos_instal_os module (https://github.com/ansible/ansible/pull/47694).
- Avoid misleading PyVmomi error if requests import fails in vmware module utils.
- Fix argument spec for NetApp modules that are using the old version
- Fix consistency issue in grafana_dashboard module where the module would detect absence of 'dashboard' key on dashboard create but not dashboard update.
- Fix idempotency issues when setting BIOS attributes via redfish_config module (https://github.com/ansible/ansible/pull/47462)
- Fix issue getting output from failed ios commands when ``check_rc=False``
- Fix issue with HTTP redirects with redfish_facts module (https://github.com/ansible/ansible/pull/45704)
- Fix the password lookup when run from a FIPS enabled system.  FIPS forbids the use of md5 but we can use sha1 instead. https://github.com/ansible/ansible/issues/47297
- Fix trailing command in net_neighbors nxos_facts (https://github.com/ansible/ansible/pull/47548).
- Fixed an issue where ``os_router`` would attempt to recreate router, because lack of ``enabled_snat`` parameter was treated as difference, if default Neutron policy for snat is set. (https://github.com/ansible/ansible/issues/29903)
- Fixes issues with source and destination location for na_ontap_snapmirror
- Handle exception when there is no snapshot available in virtual machine or template while cloning using vmware_guest.
- Provides flexibility when retrieving redfish facts by not assuming that certains keys exist. Checks first if key exists before attempting to read from it.
- Restore timeout in set_vm_power_state operation in vmware_guest_powerstate module.
- aci_access_port_to_interface_policy_leaf_profile - Support missing policy_group
- aci_interface_policy_leaf_policy_group - Support missing aep
- aci_switch_leaf_selector - Support empty policy_group
- ansible-galaxy - support yaml extension for meta file (https://github.com/ansible/ansible/pull/46505)
- assert - add 'success_msg' to valid args (https://github.com/ansible/ansible/pull/47030)
- delegate_to - Fix issue where delegate_to was upplied via ``apply`` on an include, where a loop was present on the include
- django_manage - Changed the return type of the changed variable to bool.
- docker_container - ``init`` and ``shm_size`` are now checked for idempotency.
- docker_container - do not fail when removing a container which has ``auto_remove: yes``.
- docker_container - fix ``ipc_mode`` and ``pid_mode`` idempotency if the ``host:<container-name>`` form is used (as opposed to ``host:<container-id>``).
- docker_container - fix ``paused`` option (which never worked).
- docker_container - fixing race condition when ``detach`` and ``auto_remove`` are both ``true``.
- docker_container - refactored minimal docker-py/API version handling, and fixing such handling of some options.
- docker_container - some docker versions require containers to be unpaused before stopping or removing. Adds check to do this when docker returns a corresponding error on stopping or removing.
- docker_swarm - making ``advertise_addr`` optional, as it was already documented.
- docker_swarm_service - The ``publish``.``mode`` parameter was being ignored if docker-py version was < 3.0.0. Added a parameter validation test.
- docker_volume - ``labels`` now work (and are a ``dict`` and no longer a ``list``).
- ec2_instance: - Fixed issue where ebs_optimized was considered sub-option of the network parameter. (https://github.com/ansible/ansible/issues/48159)
- fix mail notification module when using starttls and py3.7
- ini_file: Options within no sections aren't included, deleted or modified. These are just unmanged. This pull request solves this. (see https://github.com/ansible/ansible/pull/44324)
- ldap_attr map to list (https://github.com/ansible/ansible/pull/48009)
- lvg - fixed an idempotency regression in the lvg module (https://github.com/ansible/ansible/issues/47301)
- net_put - fix when net_put module leaves temp files in some network OS cases e.g. routerOS
- nxos_evpn_vni check_mode (https://github.com/ansible/ansible/pull/46612).
- ovirt_host_network - Fix type conversion (https://github.com/ansible/ansible/pull/47617).
- ovirt_host_pm - Bug fixes for power management (https://github.com/ansible/ansible/pull/47659).
- pamd: fix state: args_present idempotence (see https://github.com/ansible/ansible/issues/47197)
- pamd: fix state: updated idempotence (see https://github.com/ansible/ansible/issues/47083)
- pamd: update regex to allow leading dash and retain EOF newline (see https://github.com/ansible/ansible/issues/47418)
- pip - idempotence in check mode now works correctly.
- reboot - change default reboot time command to prevent hanging on certain systems (https://github.com/ansible/ansible/issues/46562)
- redfish_config - do not automatically reboot when scheduling a BIOS configuration job
- remove rendundant path uniquifying in inventory plugins.  This removes use of md5 hashing and fixes inventory plugins when run in FIPS mode.
- replace renamed exceptions in multiple openstack modules
- uri - Ensure the ``uri`` module supports async (https://github.com/ansible/ansible/issues/47660)
- user - do not report changes every time when setting password_lock (https://github.com/ansible/ansible/issues/43670)
- user - properly remove expiration when set to a negative value (https://github.com/ansible/ansible/issues/47114)
- user - remove warning when creating a disabled account with '!' or '*' in the password field (https://github.com/ansible/ansible/issues/46334)
- vmware_host - fixes the retry mechanism of AddHost task.
- vultr - fixed the handling of an inconsistency in the response from Vultr API when it returns an unexpected empty list instead a empty dict.
- vultr_server_facts - fixed facts gathering fails if firewall is enabled.
- win_uri - stop junk output from being returned to Ansible - https://github.com/ansible/ansible/issues/47998
- yum - fix "package == version" syntax (https://github.com/ansible/ansible/pull/47744)

v2.7.1
======

Release Summary
---------------

| Release Date: 2018-10-25
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Fix yum module to properly check for empty conf_file value
- added capability to set the scheme for the consul_kv lookup.
- added optional certificate and certificate verification for consul_kv lookups
- dnf - properly handle modifying the enable/disable excludes data field
- dnf appropriately handles disable_excludes repoid argument
- dnf properly honor disable_gpg_check for local (on local disk of remote node) package installation
- fix yum module to handle list argument optional empty strings properly
- netconf_config - Make default_operation optional in netconf_config module (https://github.com/ansible/ansible/pull/46333)
- win_nssm - Drop support of literal YAML dictionnary for ``app_parameters`` option. Use the ``key=value;`` string form instead
- yum - properly handle proxy password and username embedded in url
- yum/dnf - fail when space separated string of names (https://github.com/ansible/ansible/pull/47109)

Bugfixes
--------

- Ansible JSON Decoder - Switch from decode to object_hook to support nested use of __ansible_vault and __ansible_unsafe (https://github.com/ansible/ansible/pull/45514)
- Don't parse parameters and options when ``state`` is ``absent`` (https://github.com/ansible/ansible/pull/45700).
- FieldAttribute - Do not use mutable defaults, instead allow supplying a callable for defaults of mutable types (https://github.com/ansible/ansible/issues/46824)
- Fix an issue with the default telnet prompt handling. The value needs to be escaped otherwise it does not work when converted to bytes.
- Fix calling deprecate with correct arguments (https://github.com/ansible/ansible/pull/46062).
- Fix iterator to list conversion in ldap_entry module.
- Fix nxos_ospf_vrf module auto-cost idempotency and module check mode (https://github.com/ansible/ansible/pull/47190).
- Fix pip module so that it can recognize multiple extras
- Fix prompt mismatch issue for ios (https://github.com/ansible/ansible/issues/47004)
- Fix the issue with refreshing the token by storing Authorization header inside HttpApi connection plugin.
- Fix the quoting of vhost and other names in rabbitmq_binding
- Fix the win_reboot plugin so that the post_reboot_delay parameter is honored
- Fixed an issue with ansible-doc -l failing when parsing some plugin documentation.
- Fixed: Appropriate code to expand value was missing so assigning SSL certificate is not working as described in the documentation. https://github.com/ansible/ansible/pull/45830
- Fixes an error that occurs when attempting to see if the netns already exists on the remote device. This change will now execute ``ip netns list`` and check if the desired namespace is in the output.
- Give user better error messages and more information on verbose about inventory plugin behaviour
- Hardware fact gathering now completes on Solaris 8.  Previously, it aborted with error `Argument 'args' to run_command must be list or string`.
- Ignore empty result of rabbitmqctl list_user_permissions.
- In systemd module, allow scope to default to 'system'
- In systemd module, fix check if a systemd+initd service is enabled - disabled in systemd means disabled
- Only access EC2 volume tags when set
- Only delete host key from redis in-memory cache if present.
- PLUGIN_FILTERS_CFG - Ensure that the value is treated as type=path, and that we use the standard section of ``defaults`` instead of ``default`` (https://github.com/ansible/ansible/pull/45994)
- Refactor virtual machine disk logic.
- Restore SIGPIPE to SIG_DFL when creating subprocesses to avoid it being ignored under Python 2.
- Rewrite get_resource_pool method for correct resource_pool selection.
- The docker_* modules more uniformly check versions of docker-py/docker and (if necessary) the docker API.
- Update callbacks to use Ansible's JSON encoder to avoid known serialization issues
- Update the signatures of many cliconf plugins' get() methods to support the check_all paramter. Specifically, aireos, aruba, asa, ce, cnos, dellos6, dellos9, dellos10, edgeos, enos, exos, ironware, nos, onyx, routeros, slxos, and voss were updated. This fixes the cli_command module for these platforms
- Vultr - fix for unreliable API behaviors resulting in timeouts (https://github.com/ansible/ansible/pull/45712/).
- ansible-connection - Clean up socket files if playbook aborted before connection is started.
- ansible-doc, removed local hardcoded listing, now uses the 'central' list from constants and other minor issues
- aws_ec2 - fixed issue where cache did not contain the computed groups
- aws_ssm_parameter_store - AWS Systems Manager Parameter Store may reach an internal limit before finding the expected parameter, causing misleading results. This is resolved by paginating the describe_parameters call.
- azure_rm_deployment - fixed regression that prevents resource group from being created (https://github.com/ansible/ansible/issues/45941)
- blockinfile - use bytes rather than a native string to prevent a stacktrace in Python 3 when writing to the file (https://github.com/ansible/ansible/issues/46237)
- chroot connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)
- cs_instance - Fix docs and typo in examples (https://github.com/ansible/ansible/pull/46035).
- cs_instance - Fix host migration without volume (https://github.com/ansible/ansible/pull/46115).
- delegate_to - When templating ``delegate_to`` in a loop, don't use the task for a cache, return a special cache through ``get_vars`` allowing looping over a hostvar (https://github.com/ansible/ansible/issues/47207)
- docker connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)
- docker_container - Fix idempotency problems with ``cap_drop`` and ``groups`` (when numeric group IDs were used).
- docker_container - Fix type conversion errors for ``log_options``.
- docker_container - Fixing various comparison/idempotency problems related to wrong comparisons. In particular, comparisons for ``command`` and ``entrypoint`` (both lists) no longer ignore missing elements during idempotency checks.
- docker_container - Makes ``blkio_weight``, ``cpuset_mems``, ``dns_opts`` and ``uts`` options actually work.
- docker_container - ``publish_ports: all`` was not used correctly when checking idempotency.
- docker_container - fail if ``ipv4_address`` or ``ipv6_address`` is used with a too old docker-py version.
- docker_container - fix ``memory_swappiness`` documentation.
- docker_container - fix behavior of ``detach: yes`` if ``auto_remove: yes`` is specified.
- docker_container - fix idempotency check for published_ports in some special cases.
- docker_container - the behavior is improved in case ``image`` is not specified, but needed for (re-)creating the container.
- docker_network - fixes idempotency issues (https://github.com/ansible/ansible/issues/33045) and name substring issue (https://github.com/ansible/ansible/issues/32926).
- docker_service - correctly parse string values for the `scale` parameter https://github.com/ansible/ansible/pull/45508
- docker_volume - fix ``force`` and change detection logic. If not both evaluated to ``True``, the volume was not recreated.
- dynamic includes - Use the copied and merged task for calculating task vars in the free strategy (https://github.com/ansible/ansible/issues/47024)
- ec2_group - There can be multiple security groups with the same name in different VPCs. Prior to 2.6 if a target group name was provided, the group matching the name and VPC had highest precedence. Restore this behavior by updated the dictionary with the groups matching the VPC last.
- ec2_group - support EC2-Classic by not assuming security groups have VPCs.
- ec2_metadata_facts - Parse IAM role name from metadata ARN instead of security credential field.
- fetch_url did not always return lower-case header names in case of HTTP errors (https://github.com/ansible/ansible/pull/45628).
- fix azure_rm_autoscale module can create a schedule with fixed start/end date (https://github.com/ansible/ansible/pull/47186)
- fix flatten to properly handle multiple lists in lists https://github.com/ansible/ansible/issues/46343
- get_url - improve code that parses checksums from a file so it is not fragile and reports a helpful error when no matching checksum is found
- handlers - fix crash when handler task include tasks
- jail connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)
- junos - fix terminal prompt regex (https://github.com/ansible/ansible/pull/47096)
- k8s - allow kubeconfig or context to be set without the other
- k8s_facts now returns a resources key in all situations
- k8s_facts: fix handling of unknown resource types
- kubectl connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)
- libvirt_lxc connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)
- lineinfile - fix index out of range error when using insertbefore on a file with only one line (https://github.com/ansible/ansible/issues/46043)
- mail - Fix regression when sending mail without TLS/SSL
- mysql_*, proxysql_* - PyMySQL (a pure-Python MySQL driver) is now a preferred dependency also supporting Python 3.X.
- netconf_config - Fix in confirmed_commit capability in netconf_config modules  (https://github.com/ansible/ansible/pull/46778)
- netconf_config - Fix netconf module_utils dict changed size issue (https://github.com/ansible/ansible/pull/46778)
- nmcli - fix syntax of vlan modification command (https://github.com/ansible/ansible/issues/42322)
- nxos_file_copy fix for binary files (https://github.com/ansible/ansible/pull/46822).
- openssl_csr - fix byte encoding issue on Python 3
- openssl_pkcs12 - fix byte encoding issue on Python 3
- os_router - ``enable_snat: no`` was ignored.
- ovirt_host_network - check for empty user_opts (https://github.com/ansible/ansible/pull/47283).
- ovirt_vm - Check next_run configuration update if exist (https://github.com/ansible/ansible/pull/47282/).
- ovirt_vm - Fix initialization of cloud init (https://github.com/ansible/ansible/pull/47354).
- ovirt_vm - Fix issue in SSO option (https://github.com/ansible/ansible/pull/47312).
- ovirt_vm - Fix issue in setting the custom_compatibility_version to NULL (https://github.com/ansible/ansible/pull/47388).
- pamd: add delete=False to NamedTemporaryFile() fixes OSError on module completion, and removes print statement from module code. (see https://github.com/ansible/ansible/pull/47281 and https://github.com/ansible/ansible/issues/47080)
- pamd: use module.tmpdir for NamedTemporaryFile() (see https://github.com/ansible/ansible/pull/47133 and https://github.com/ansible/ansible/issues/36954)
- postgresql_user - create pretty error message when creating a user without an encrypted password on newer PostgreSQL versions
- psexec - Handle socket.error exceptions properly
- psexec - give proper error message when the psexec requirements are not installed
- psrp - Fix UTF-8 output - https://github.com/ansible/ansible/pull/46998
- psrp - Fix issue when dealing with unicode values in the output for Python 2
- reboot - add reboot_timeout parameter to the list of parameters so it can be used.
- reboot - add support for OpenBSD
- reboot - use correct syntax for fetching a value from a dict and account for bare Linux systems (https://github.com/ansible/ansible/pull/45607#issuecomment-422403177)
- reboot - use unicode instead of bytes for stdout and stderr to match the type returned from low_level_execute()
- roles - Ensure that we don't overwrite roles that have been registered (from imports) while parsing roles under the roles header (https://github.com/ansible/ansible/issues/47454)
- route53 - fix CAA record ordering for idempotency.
- ssh connection - Support empty files with piped transfer_method (https://github.com/ansible/ansible/issues/45426)
- templar - Do not strip new lines in native jinja - https://github.com/ansible/ansible/issues/46743
- unsafe - Add special casing to sets, to support wrapping elements of sets correctly in Python 3 (https://github.com/ansible/ansible/issues/47372)
- use proper module_util to get Ansible version for Azure requests
- user - add documentation on what underlying tools are used on each platform (https://github.com/ansible/ansible/issues/44266)
- user module - do not pass ssh_key_passphrase on cmdline (CVE-2018-16837)
- vmware - honor "wait_for_ip_address" when powering on a VM
- vultr_server - fix diff for user data (https://github.com/ansible/ansible/pull/45753/).
- vyos_facts - fix vyos_facts not returning version number issue (https://github.com/ansible/ansible/pull/39115)
- win_copy - Fix issue where the dest return value would be enclosed in single quote when dest is a folder - https://github.com/ansible/ansible/issues/45281
- win_nssm - Add missing space between parameters with ``app_parameters``
- win_nssm - Correctly escape argument line when a parameter contains spaces, quotes or backslashes
- win_nssm - Fix error when several services were given to the ``dependencies`` option
- win_nssm - Fix extra space added in argument line with ``app_parameters`` or ``app_parameters_free_form`` when a parameter start by a dash and is followed by a period (https://github.com/ansible/ansible/issues/44079)
- win_nssm - Fix service not started when ``state=started`` (https://github.com/ansible/ansible/issues/35442)
- win_nssm - Fix several issues and idempotency problems (https://github.com/ansible/ansible/pull/44755)
- winrm - Only use pexpect for auto kerb auth if it is installed and contains the required kwargs - https://github.com/ansible/ansible/issues/43462
- zabbix_host - module was failing when zabbix host was updated with new interface and template depending on that interface at the same time
- zone connection - Support empty files with copying to target (https://github.com/ansible/ansible/issues/36725)

v2.7.0
======

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
- Fix timer in exponential backoff algorithm in vmware.py.
- Fixed group action idempotent transactions in dnf backend
- Fixed group actions in check mode to report correct changed state
- GCP Modules will do home path expansion on service account file paths
- In Ansible-2.4 and above, Ansible passes the temporary directory a module should use to the module.  This is done via a module parameter (_ansible_tmpdir).  An earlier version of this which was also prototyped in Ansible-2.4 development used an environment variable, ANSIBLE_REMOTE_TMP to pass this information to the module instead.  When we switched to using a module parameter, the environment variable was left in by mistake. Ansible-2.7 removes that variable.  Any third party modules which relied on it should use the module parameter instead.
- New config options `display_ok_hosts` and `display_failed_stderr` (along with the existing `display_skipped_hosts` option) allow more fine-grained control over the way that ansible displays output from a playbook (https://github.com/ansible/ansible/pull/41058)
- Removed an unnecessary import from the AnsiballZ wrapper
- Restore module_utils.basic.BOOLEANS variable for backwards compatibility with the module API in older ansible releases.
- Setting file attributes (via the file module amongst others) now accepts + and - modifiers to add or remove individual attributes. (https://github.com/ansible/ansible/issues/33838)
- Switch from zip to bc for certain package install/remove test cases in yum integration tests. The dnf depsolver downgrades python when you uninstall zip which alters the test environment and we have no control over that.
- The acme_account and acme_certificate modules now support two backends: the Python cryptograpy module or the OpenSSL binary. By default, the modules detect if a new enough cryptography module is available and use it, with the OpenSSL binary being a fallback. If the detection fails for some reason, the OpenSSL binary backend can be explicitly selected by setting select_crypto_backend to openssl.
- The apt, ec2_elb_lb, elb_classic_lb, and unarchive modules have been ported away from using __file__.  This is futureproofing as__file__ won't work if we switch to using python -m to invoke modules in the future or if we figure out a way to make a module never touch disk for pipelining purposes.
- The password_hash filter supports all parameters of passlib. This allows users to provide a rounds parameter. (https://github.com/ansible/ansible/issues/15326)
- action plugins strictly accept valid parameters and report invalid parameters
- allow user to customize default ansible-console prompt/msg default color
- aws_caller_facts - The module now outputs the "account_alias" as well
- aws_rds - Add new inventory plugin for RDS instances and clusters to match behavior in the ec2 inventory script.
- command module - Add support for check mode when passing creates or removes arguments. (https://github.com/ansible/ansible/pull/40428)
- dnf - group removal does not work if group was installed with Ansible because of dnf upstream bug https://bugzilla.redhat.com/show_bug.cgi?id=1620324
- ec2_group - Add diff mode support with and without check mode. This feature is preview and may change when a common framework is adopted for AWS modules.
- elasticsearch_plugin - Add the possibility to use the elasticsearch_plugin installation batch mode to install plugins with advanced privileges without user interaction.
- gather_subset - removed deprecated functionality for using comma separated list with gather_subset (https://github.com/ansible/ansible/pull/44320)
- get_url - implement [expend checksum format to <algorithm>:(<checksum>|<url>)] (https://github.com/ansible/ansible/issues/27617)
- import_tasks - Do not allow import_tasks to transition to dynamic if the file is missing (https://github.com/ansible/ansible/issues/44822)
- lineinfile - add warning when using an empty regexp (https://github.com/ansible/ansible/issues/29443)
- onepassword/onepassword_raw - accept subdomain and vault_password to allow Ansible to unlock 1Password vaults
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
- win_disk_image - return a list of mount paths with the return value ``mount_paths``, this will always be a list and contain all mount points in an image
- win_psexec - Added the ``session`` option to specify a session to start the process in
- winrm - change the _reset() method to use reset() that is part of ConnectionBase

Deprecated Features
-------------------

- Modules will no longer be able to rely on the __file__ attribute pointing to a real file.  If your third party module is using __file__ for something it should be changed before 2.8.  See the 2.7 porting guide for more information.
- The `skippy`, `full_skip`, `actionable`, and `stderr` callback plugins have been deprecated in favor of config options that influence the behavior of the `default` callback plugin (https://github.com/ansible/ansible/pull/41058)
- win_disk_image - the return value ``mount_path`` is deprecated and will be removed in 2.11, this can be accessed through ``mount_paths[0]`` instead.

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
- Add ambiguous command check as the error message is not persistent on nexus devices (https://github.com/ansible/ansible/pull/45337).
- Add argspec to aws_application_scaling_policy module to handle metric specifications, scaling cooldowns, and target values. https://github.com/ansible/ansible/pull/45235
- Additional checks ensure that there is always a result of hashing passwords in the password_hash filter and vars_prompt, otherwise an error is returned. Some modules (like user module) interprets None as no password at all, which can be dangerous if the password given above is passed directly into those modules.
- Allow arbitrary ``log_driver`` for docker_container (https://github.com/ansible/ansible/pull/33579).
- Avoids deprecated functionality of passlib with newer library versions.
- Changed the admin_users config option to not include "admin" by default as admin is frequently used for a non-privileged account  (https://github.com/ansible/ansible/pull/41164)
- Fix alt linux detection/matching
- Fix an atomic_move error that is 'true', but  misleading. Now we show all 3 files involved and clarify what happened.
- Fix ec2_group support for multi-account and peered VPC security groups. Reported in https://github.com/ansible/ansible/issue/44788 and fixed in https://github.com/ansible/ansible/pull/45296
- Fix ecs_taskdefinition handling of changed role_arn. If the task role in a ECS task definition changes ansible should create a new revsion of the task definition. https://github.com/ansible/ansible/pull/45317
- Fix glob path of rc.d Some distribtuions like SUSE has the rc%.d directories under /etc/init.d
- Fix health check parameter handling in elb_target_group per https://github.com/ansible/ansible/issues/43244 about health_check_port. Fixed in https://github.com/ansible/ansible/pull/45314
- Fix lambda_policy updates when principal is an account number. Backport of https://github.com/ansible/ansible/pull/44871
- Fix lxd module to be idempotent when the given configuration for the lxd container has not changed (https://github.com/ansible/ansible/pull/38166)
- Fix python2.6 `nothing to repeat` nxos terminal plugin bug (https://github.com/ansible/ansible/pull/45271).
- Fix s3_lifecycle module backwards compatibility without providing prefix. Blank prefixes regression was introduced in boto3 rewrite. https://github.com/ansible/ansible/pull/45318
- Fix terminal plugin regex nxos, iosxr (https://github.com/ansible/ansible/pull/45135).
- Fix the mount module's handling of swap entries in fstab (https://github.com/ansible/ansible/pull/42837)
- Fixed an issue where ``ansible_facts.pkg_mgr`` would incorrectly set to ``zypper`` on Debian/Ubuntu systems that happened to have the command installed.
- Fixed runtime module to be able to handle syslog_facility properly when python systemd module installed in a target system. (https://github.com/ansible/ansible/pull/41078)
- Grafana dashboard module compatible with grafana 5 (https://github.com/ansible/ansible/pull/41249)
- On Python2, loading config values from environment variables could lead to a traceback if there were nonascii characters present.  Converted them to text strings so that no traceback will occur (https://github.com/ansible/ansible/pull/43468)
- Remove spurious `changed=True` returns when ec2_group module is used with numeric ports. https://github.com/ansible/ansible/pull/45240
- Support key names that contain spaces in ec2_metadata_facts module. https://github.com/ansible/ansible/pull/45313
- The docker_* modules respect the DOCKER_* environment variables again (https://github.com/ansible/ansible/pull/42641).
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
- cloudfront_distribution - replace call to nonexistent method 'validate_distribution_id_from_caller_reference' with 'validate_distribution_from_caller_reference' and set the distribution_id variable to the distribution's 'Id' key.
- corrected and clarified 'user' option deprecation in systemd module in favor of 'scope' option.
- delegate_to - ensure if we get a non-Task object in _get_delegated_vars, we return early (https://github.com/ansible/ansible/pull/44934)
- docker_container: fixing ``working_dir`` idempotency problem (https://github.com/ansible/ansible/pull/42857)
- docker_container: makes unit parsing for memory sizes more consistent, and fixes idempotency problem when ``kernel_memory`` is set (see https://github.com/ansible/ansible/pull/16748 and https://github.com/ansible/ansible/issues/42692)
- ec2_group - Sanitize the ingress and egress rules before operating on them by flattening any lists within lists describing the target CIDR(s) into a list of strings. Prior to Ansible 2.6 the ec2_group module accepted a list of strings, a list of lists, or a combination of strings and lists within a list. https://github.com/ansible/ansible/pull/45594
- ec2_vpc_route_table - check the origin before replacing routes. Routes with the origin 'EnableVgwRoutePropagation' may not be replaced.
- elasticsearch_plugin - Improve error messages and show stderr of elasticsearch commands
- elb_application_lb - Fix a dangerous behavior of deleting an ELB if state was omitted from the task. Now state defaults to 'present', which is typical throughout AWS modules.
- elb_target_group - cast target ports to integers before making API calls after the key 'Targets' is in params.
- file module - The touch subcommand had its diff output broken during the 2.6.x development cycle.  The patch to fix that broke check mode. This is now fixed (https://github.com/ansible/ansible/issues/42111)
- file module - The touch subcommand had its diff output broken during the 2.6.x development cycle.  This is now fixed (https://github.com/ansible/ansible/issues/41755)
- fix async for the aws_s3 module by adding async support to the action plugin (https://github.com/ansible/ansible/pull/40826)
- fix azure storage blob cannot create blob container in non-public azure cloud environment. (https://github.com/ansible/ansible/issues/35223)
- fix azure_rm_autoscale module can use dict to identify target (https://github.com/ansible/ansible/pull/45477)
- fix decrypting vault files for the aws_s3 module (https://github.com/ansible/ansible/pull/39634)
- fix default SSL version for docker modules https://github.com/ansible/ansible/issues/42897
- fix for the bundled selectors module (used in the ssh and local connection plugins) when a syscall is restarted after being interrupted by a signal (https://github.com/ansible/ansible/issues/41630)
- fix mail module for python 3.7.0 (https://github.com/ansible/ansible/pull/44552)
- fix nxos_facts indefinite hang for text based output (https://github.com/ansible/ansible/pull/45845).
- fix the enable_snat parameter that is only supposed to be used by an user with the right policies. https://github.com/ansible/ansible/pull/44418
- fix the remote tmp folder permissions issue when becoming a non admin user - https://github.com/ansible/ansible/issues/41340, https://github.com/ansible/ansible/issues/42117
- fixed typo in config that prevented keys matching
- fixes docker_container check and debug mode (https://github.com/ansible/ansible/pull/42380)
- flatten filter - use better method of type checking allowing flattening of mutable and non-mutable sequences (https://github.com/ansible/ansible/pull/44331)
- gce_net - Fix sorting of allowed ports (https://github.com/ansible/ansible/pull/41567)
- get_url - Don't re-download files unnecessarily when force=no (https://github.com/ansible/ansible/issues/45491)
- get_url - fix the bug that get_url does not change mode when checksum matches (https://github.com/ansible/ansible/issues/29614)
- get_url - support remote checksum files with paths specified with leading dots (`./path/to/file`)
- get_url / uri - Use custom rfc2822 date format function instead of locale specific strftime (https://github.com/ansible/ansible/issues/44857)
- improved block docs
- improves docker_container idempotency (https://github.com/ansible/ansible/pull/44808)
- include - Change order of where the new block is inserted with apply so that apply args are not applied to the include also (https://github.com/ansible/ansible/pull/44912)
- includes - ensure we do not double register handlers from includes to prevent exception (https://github.com/ansible/ansible/issues/44848)
- inventory - When using an inventory directory, ensure extension comparison uses text types (https://github.com/ansible/ansible/pull/42475)
- loop - Ensure that a loop with a when condition that evaluates to false and delegate_to, will short circuit if the loop references an undefined variable. This matches the behavior in the same scenario without delegate_to (https://github.com/ansible/ansible/issues/45189)
- loop - Ensure we only cache the loop when the task had a loop and delegate_to was templated (https://github.com/ansible/ansible/issues/44874)
- made irc module python3 compatible https://github.com/ansible/ansible/issues/42256
- nclu - no longer runs net on empty lines in templates (https://github.com/ansible/ansible/pull/43024)
- nicer message when we are missing interpreter
- password_hash does not hard-code the salt-length, which fixes bcrypt in connection with passlib as bcrypt requires a salt with length 22.
- pause - do not set stdout to raw mode when redirecting to a file (https://github.com/ansible/ansible/issues/41717)
- pause - nest try except when importing curses to gracefully fail if curses is not present (https://github.com/ansible/ansible/issues/42004)
- plugins/inventory/openstack.py - Do not create group with empty name if region is not set
- preseve delegation info on nolog https://github.com/ansible/ansible/issues/42344
- remove ambiguity when it comes to 'the source'
- script inventory plugin - Don't pass file_name to DataLoader.load, which will prevent misleading error messages (https://github.com/ansible/ansible/issues/34164)
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
- win_group_membership - fix intermittent issue where it failed to convert the ADSI object to the .NET object after using it once
- win_iis_webapppool - redirect some module output to null so Ansible can read the output JSON https://github.com/ansible/ansible/issues/40874
- win_lineinfile - changed `-Path` to `-LiteralPath` so that square brackes in the path are interpreted literally -  https://github.com/ansible/ansible/issues/44508
- win_psexec - changed code to not escape the command option when building the args - https://github.com/ansible/ansible/issues/43839
- win_reboot - fix for handling an already scheduled reboot and other minor log formatting issues
- win_reboot - fix issue when overridding connection timeout hung the post reboot uptime check - https://github.com/ansible/ansible/issues/42185 https://github.com/ansible/ansible/issues/42294
- win_reboot - handle post reboots when running test_command - https://github.com/ansible/ansible/issues/41713
- win_say - fix syntax error in module and get tests working
- win_security_policy - allows an empty string to reset a policy value https://github.com/ansible/ansible/issues/40869
- win_updates - Fixed issue where running win_updates on async fails without any error
- win_updates - fixed module return value is lost in error in some cases (https://github.com/ansible/ansible/pull/42647)
- win_uri: Fix support for JSON output when charset is set
- win_user - Use LogonUser to validate the password as it does not rely on SMB/RPC to be available https://github.com/ansible/ansible/issues/24884
- win_wait_for - fix issue where timeout doesn't wait unless state=drained - https://github.com/ansible/ansible/issues/43446
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

- cpm_metering - Get Power and Current data from WTI OOB/Combo and PDU devices
- cpm_status - Get status and parameters from WTI OOB and PDU devices.
- grafana_dashboard - list or search grafana dashboards
- nios_next_network - Return the next available network range for a network-container

Strategy
~~~~~~~~

- host_pinned - Executes tasks on each host without interruption

New Modules
-----------

Cloud
~~~~~

amazon
^^^^^^

- aws_eks_cluster - Manage Elastic Kubernetes Service Clusters
- cloudformation_stack_set - Manage groups of CloudFormation stacks
- elb_target_facts - Gathers which target groups a target is associated with.
- rds_instance - Manage RDS instances

azure
^^^^^

- azure_rm_appgateway - Manage Application Gateway instance.
- azure_rm_appserviceplan - Manage App Service Plan
- azure_rm_appserviceplan_facts - Get azure app service plan facts.
- azure_rm_autoscale - Manage Azure autoscale setting.
- azure_rm_autoscale_facts - Get Azure Auto Scale Setting facts.
- azure_rm_containerregistry_facts - Get Azure Container Registry facts.
- azure_rm_mysqldatabase_facts - Get Azure MySQL Database facts.
- azure_rm_mysqlserver_facts - Get Azure MySQL Server facts.
- azure_rm_postgresqldatabase_facts - Get Azure PostgreSQL Database facts.
- azure_rm_postgresqlserver_facts - Get Azure PostgreSQL Server facts.
- azure_rm_route - Manage Azure route resource.
- azure_rm_routetable - Manage Azure route table resource.
- azure_rm_routetable_facts - Get route table facts.
- azure_rm_sqlfirewallrule - Manage Firewall Rule instance.
- azure_rm_trafficmanagerendpoint - Manage Azure Traffic Manager endpoint.
- azure_rm_trafficmanagerendpoint_facts - Get Azure Traffic Manager endpoint facts
- azure_rm_trafficmanagerprofile - Manage Azure Traffic Manager profile.
- azure_rm_trafficmanagerprofile_facts - Get Azure Traffic Manager profile facts
- azure_rm_virtualmachine_facts - Get virtual machine facts.
- azure_rm_webapp - Manage Web App instance.
- azure_rm_webapp_facts - Get azure web app facts.

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
- gcp_compute_router - Creates a GCP Router
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
- gcp_spanner_database - Creates a GCP Database
- gcp_spanner_instance - Creates a GCP Instance
- gcp_sql_database - Creates a GCP Database
- gcp_sql_instance - Creates a GCP Instance
- gcp_sql_user - Creates a GCP User

online
^^^^^^

- online_user_facts - Gather facts about Online user.

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
- vmware_host_ntp_facts - Gathers facts about NTP configuration on an ESXi host
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

- onepassword_facts - Fetch facts from 1Password items

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

fortimanager
^^^^^^^^^^^^

- fmgr_provisioning - Provision devices via FortiMananger

ftd
^^^

- ftd_configuration - Manages configuration on Cisco FTD devices over REST API
- ftd_file_download - Downloads files from Cisco FTD devices over HTTP(S)
- ftd_file_upload - Uploads files to Cisco FTD devices over HTTP(S)

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

opx
^^^

- opx_cps - CPS operations on networking device running Openswitch (OPX)

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
- cobbler_system - Manage system objects in Cobbler

cpm
^^^

- cpm_user - Get various status and parameters from WTI OOB and PDU devices

redfish
^^^^^^^

- redfish_command - Manages Out-Of-Band controllers using Redfish APIs
- redfish_config - Manages Out-Of-Band controllers using Redfish APIs
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

- ibm_sa_host - Adds hosts to or removes them from IBM Spectrum Accelerate storage systems.
- ibm_sa_pool - Handles pools on an IBM Spectrum Accelerate storage array.
- ibm_sa_vol - Handle volumes on an IBM Spectrum Accelerate storage array

netapp
^^^^^^

- na_elementsw_access_group - NetApp Element Software Manage Access Groups
- na_elementsw_account - NetApp Element Software Manage Accounts
- na_elementsw_admin_users - NetApp Element Software Manage Admin Users
- na_elementsw_backup - NetApp Element Software Create Backups
- na_elementsw_check_connections - NetApp Element Software Check connectivity to MVIP and SVIP.
- na_elementsw_cluster - NetApp Element Software Create Cluster
- na_elementsw_cluster_pair - NetApp Element Software Manage Cluster Pair
- na_elementsw_drive - NetApp Element Software Manage Node Drives
- na_elementsw_ldap - NetApp Element Software Manage ldap admin users
- na_elementsw_network_interfaces - NetApp Element Software Configure Node Network Interfaces
- na_elementsw_node - NetApp Element Software Node Operation
- na_elementsw_snapshot - NetApp Element Software Manage Snapshots
- na_elementsw_snapshot_restore - NetApp Element Software Restore Snapshot
- na_elementsw_snapshot_schedule - NetApp Element Software Snapshot Schedules
- na_elementsw_vlan - NetApp Element Software Manage VLAN
- na_elementsw_volume - NetApp Element Software Manage Volumes
- na_elementsw_volume_clone - NetApp Element Software Create Volume Clone
- na_elementsw_volume_pair - NetApp Element Software Volume Pair
- na_ontap_autosupport - NetApp ONTAP manage Autosupport
- na_ontap_cg_snapshot - NetApp ONTAP manage consistency group snapshot
- na_ontap_cluster_peer - NetApp ONTAP Manage Cluster peering
- na_ontap_command - NetApp ONTAP Run any cli command
- na_ontap_disks - NetApp ONTAP Assign disks to nodes
- na_ontap_dns - NetApp ONTAP Create, delete, modify DNS servers.
- na_ontap_fcp - NetApp ONTAP Start, Stop and Enable FCP services.
- na_ontap_firewall_policy - NetApp ONTAP Manage a firewall policy
- na_ontap_gather_facts - NetApp information gatherer
- na_ontap_motd - Setup motd on cDOT
- na_ontap_node - NetApp ONTAP Rename a node.
- na_ontap_snapmirror - NetApp ONTAP Manage SnapMirror
- na_ontap_software_update - NetApp ONTAP Update Software
- na_ontap_svm_options - NetApp ONTAP Modify SVM Options
- na_ontap_vserver_peer - NetApp ONTAP Vserver peering
- netapp_e_alerts - NetApp E-Series manage email notification settings
- netapp_e_asup - NetApp E-Series manage auto-support settings
- netapp_e_auditlog - NetApp E-Series manage audit-log configuration
- netapp_e_global - NetApp E-Series manage global settings configuration
- netapp_e_iscsi_interface - NetApp E-Series manage iSCSI interface configuration
- netapp_e_iscsi_target - NetApp E-Series manage iSCSI target configuration
- netapp_e_ldap - NetApp E-Series manage LDAP integration to use for authentication
- netapp_e_mgmt_interface - NetApp E-Series management interface configuration
- netapp_e_syslog - NetApp E-Series manage syslog settings

purestorage
^^^^^^^^^^^

- purefb_facts - Collect facts from Pure Storage FlashBlade

System
~~~~~~

- java_keystore - Create or delete a Java keystore in JKS format.
- python_requirements_facts - Show python path and assert dependency versions
- reboot - Reboot a machine

Web Infrastructure
~~~~~~~~~~~~~~~~~~

ansible_tower
^^^^^^^^^^^^^

- tower_credential_type - Create, update, or destroy custom Ansible Tower credential type.
- tower_inventory_source - create, update, or destroy Ansible Tower inventory source.
- tower_settings - Modify Ansible Tower settings.
- tower_workflow_template - create, update, or destroy Ansible Tower workflow template.

Windows
~~~~~~~

- win_chocolatey_config - Manages Chocolatey config settings
- win_chocolatey_feature - Manages Chocolatey features
- win_chocolatey_source - Manages Chocolatey sources
- win_wait_for_process - Waits for a process to exist or not exist before continuing.
- win_xml - Add XML fragment to an XML parent
