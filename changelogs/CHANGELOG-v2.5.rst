===================================
Ansible 2.5 "Kashmir" Release Notes
===================================

.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.4:

v2.5.4
======

.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.4_Release Summary:

Release Summary
---------------

| Release Date: 2018-05-31
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.4_Bugfixes:

Bugfixes
--------

- jenkins_plugin - fix plugin always updated even if already uptodate (https://github.com/ansible/ansible/pull/40645)

- ec2_asg - wait for lifecycle hooks to complete (https://github.com/ansible/ansible/issues/37281)

- edgeos_config - check for a corresponding set command when issuing delete commands to ensure the desired state is met (https://github.com/ansible/ansible/issues/40437)

- iptables - use suboptions to properly join tcp_flags options (https://github.com/ansible/ansible/issues/36490)

- known_hosts - add better checking and error reporting to the host field (https://github.com/ansible/ansible/pull/38307)

- Fix legacy Nexus 3k integration test and module issues (https://github.com/ansible/ansible/pull/40322).

- Skip N35 and N3L platforms for nxos_evpn_global test (https://github.com/ansible/ansible/pull/40333).

- Add normalize_interface in module_utils and fix nxos_l3_interface module (https://github.com/ansible/ansible/pull/40598).

- Fix nxos_interface Disable switchport for loopback/svi (https://github.com/ansible/ansible/pull/40314).

- fixes bug with matching nxos prompts (https://github.com/ansible/ansible/pull/40655).

- fix nxos_vrf and migrate get_interface_type to module_utils (https://github.com/ansible/ansible/pull/40825).

- Fix nxos_vlan vlan creation failure (https://github.com/ansible/ansible/pull/40822).

- pause - ensure ctrl+c interrupt works in all cases (https://github.com/ansible/ansible/issues/35372)

- user - With python 3.6 spwd.getspnam returns PermissionError instead of KeyError if user does not have privileges (https://github.com/ansible/ansible/issues/39472)

- synchronize - Ensure the local connection created by synchronize uses _remote_is_local=True, which causes ActionBase to build a local tmpdir (https://github.com/ansible/ansible/pull/40833)

- win_get_url - fixed issue when authenticating when force=yes https://github.com/ansible/ansible/pull/40641

- winrm - allow `ansible_user` or `ansible_winrm_user` to override `ansible_ssh_user` when both are defined in an inventory - https://github.com/ansible/ansible/issues/39844

- winrm - Add better error handling when the kinit process fails

- xenserver_facts - ensure module works with newer versions of XenServer (https://github.com/ansible/ansible/pull/35821)


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.3:

v2.5.3
======

.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.3_Release Summary:

Release Summary
---------------

| Release Date: 2018-05-17
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.3_Bugfixes:

Bugfixes
--------

- openstack.os_stack - extend failure message with the server response (https://github.com/ansible/ansible/pull/39660).

- vmware_guest - typecast VLAN ID to match various conditions. (https://github.com/ansible/ansible/pull/39793)

- vmware_guest - Do not update cpu/memory allocation in configspec if there is no change (https://github.com/ansible/ansible/pull/39865)

- Fix unset 'ansible_virtualization_role' fact while setting virtualization facts for real hardware.

- loop_control - update template vars for loop_control fields on each loop iteration (https://github.com/ansible/ansible/pull/39818).

- template - Fix for encoding issues when a template path contains non-ascii characters and using the template path in ansible_managed (https://github.com/ansible/ansible/issues/27262)

- apt - Auto install of python-apt without recommends (https://github.com/ansible/ansible/pull/37121)

- apt - Mark installed packages manual (https://github.com/ansible/ansible/pull/37751)

- async - Ensure that the implicit async_status gets the env from a task with async (https://github.com/ansible/ansible/pull/39764)

- Fallback to instance role STS credentials if none are explicitly provided for the aws_ec2 inventory plugin

- Support tag values as hostnames in aws_ec2 inventory plugin

- Fix regression in aws_s3 to allow uploading files on the remote host to an S3 bucket

- ec2_vpc_route_table - fix regression by skipping routes without DestinationCidrBlock (https://github.com/ansible/ansible/pull/37010)

- Use custom waiters

- Add integration tests for check mode

- Fix non-monotonic AWS behavior by waiting until attributes are the correct value before returning the subnet

- Don't use custom waiter configs for older versions of botocore

- Fix an encoding issue when parsing the examples from a plugins' documentation

- Fix misuse of self in module_utils/network/eos/eos.py (https://github.com/ansible/ansible/pull/39074)

- eos_vlan - Fix eos_vlan associated interface name check (https://github.com/ansible/ansible/pull/39661)

- file module - Fix error when running a task which assures a symlink to a nonexistent file exists for the second and subsequent times (https://github.com/ansible/ansible/issues/39558)

- file module - Fix error when recursively assigning permissions and a symlink to a nonexistent file is present in the directory tree (https://github.com/ansible/ansible/issues/39456)

- file - Eliminate an error if we're asked to remove a file but something removes it while we are processing the request (https://github.com/ansible/ansible/pull/39466)

- Fix interfaces_file to support `allow-` https://github.com/ansible/ansible/pull/37847

- ios cliconf plugin fix regex for version (https://github.com/ansible/ansible/pull/40066)

- ios_config - If defaults is enabled append default flag to command (https://github.com/ansible/ansible/pull/39741)

- ios_config - Fix ios get_config to fetch config without defaults (https://github.com/ansible/ansible/pull/39475)

- ios_iosxr_terminal - fixed issue with ios and iosxr terminal prompt regex

- iosxr_config - handle configuration block with mis-indented sublevel command (https://github.com/ansible/ansible/pull/39673)

- iosxr_* modules do not work with iosxr version >= 6.3.2 as cisco has deprecated 'show version brief'

- Fix junos_config confirm timeout issue (https://github.com/ansible/ansible/pull/40238)

- Fix nested noop block padding in dynamic includes (https://github.com/ansible/ansible/pull/38814)

- nio_lookup_error - fixed nios lookup errors out when there are no results

- nxos_feature - Handle nxos_feature issue where json isn't supported (https://github.com/ansible/ansible/pull/39150)

- nxos_ntp - Fix nxos_ntp issues (https://github.com/ansible/ansible/pull/39178)

- nxos_interface - Fix AttributeError NoneType object has no attribute group (https://github.com/ansible/ansible/pull/38544)

- nxos_snmp_community - Fix nxos_snmp_community issues (https://github.com/ansible/ansible/pull/39258)

- nxos_l2_interface - Add aggregate example in nxos_l2_interface module doc (https://github.com/ansible/ansible/pull/39275)

- nxos_snmp_host - Fix for nxos_snmp_host issues (https://github.com/ansible/ansible/pull/39642)

- nxos_snmp_traps - Fix nxos_snmp_traps issues (https://github.com/ansible/ansible/pull/39444)

- nxos_linkagg - nxos_linkagg abbreviated form issue (https://github.com/ansible/ansible/pull/39591)

- nxos_snmp_user - Fix nxos_snmp_user (https://github.com/ansible/ansible/pull/39760)

- nxos_logging - remove purge from nxos_logging doc, argspec (https://github.com/ansible/ansible/pull/39947)

- nxos_ping - Fix nxos_ping issues (https://github.com/ansible/ansible/pull/40028)

- nxos_vxlan_vtep_vni - Fix nxos_vxlan_vtep_vni test (https://github.com/ansible/ansible/pull/39968)

- nxos_snapshot - Fix logic for save_snapshot_locally (https://github.com/ansible/ansible/pull/40227)

- Fix nxos terminal plugin regex (https://github.com/ansible/ansible/pull/39659)

- template action plugin - fix the encoding of filenames to avoid tracebacks on Python2 when characters that are not present in the user's locale are present. (https://github.com/ansible/ansible/pull/39424)

- ufw - "route" has to be the first option in ufw command https://github.com/ansible/ansible/pull/31756

- user - only change the expiration time when necessary (https://github.com/ansible/ansible/issues/13235)

- firewalld - fixed fw_offline undefined error (https://github.com/ansible/ansible/pull/39394)

- ansible-connection - properly unlock the socket file lock (https://github.com/ansible/ansible/pull/39223)

- apt - added --no-install-recommends to PYTHON_APT dep installation (https://github.com/ansible/ansible/pull/39409)

- ec2_vpc_route_table - updated matching_count parsing (https://github.com/ansible/ansible/pull/39899)

- ovirt - fixed quota_id check (https://github.com/ansible/ansible/pull/40081)

- vdirect_file - deal with invalid upload source (https://github.com/ansible/ansible/pull/37461)

- win_file - fix issue where special chars like [ and ] were not being handled correctly https://github.com/ansible/ansible/pull/37901

- win_get_url - fixed a few bugs around authentication and force no when using an FTP URL

- win_template - fix when specifying the dest option as a directory with and without the trailing slash https://github.com/ansible/ansible/issues/39886

- win_updates - Fix typo that hid the download error when a download failed

- win_updates - Fix logic when using a whitelist for multiple updates

- windows become - Show better error messages when the become process fails


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.2:

v2.5.2
======

.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.2_Release Summary:

Release Summary
---------------

| Release Date: 2018-04-26
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.2_Minor Changes:

Minor Changes
-------------

- Return virtual_facts after VMware platform detection, otherwise we're falling back to 'NA' for virtualization type and virtualization role.


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.2_Bugfixes:

Bugfixes
--------

- copy - fixed copy to only follow symlinks for files in the non-recursive case

- file - fixed the default follow behaviour of file to be true

- docker modules - Error with useful message is both docker and docker-py are found to both be installed (https://github.com/ansible/ansible/pull/38884)

- dynamic includes - Improved performance by fixing re-parenting on copy (https://github.com/ansible/ansible/pull/38747)

- dynamic includes - Fix IncludedFile comparison for free strategy (https://github.com/ansible/ansible/pull/37083)

- dynamic includes - Allow inheriting attributes from static parents (https://github.com/ansible/ansible/pull/38827)

- Fix ios and iosxr terminal prompt regex (https://github.com/ansible/ansible/pull/39063)

- set_fact/include_vars - allow incremental update for vars in loop (https://github.com/ansible/ansible/pull/38302)

- cloudfront_distribution - support missing protocol versions (https://github.com/ansible/ansible/pull/38990)

- slice filter - removed Ansible-provided impl in favor of Jinja builtin (https://github.com/ansible/ansible/pull/37944)

- ovirt_host_networks - fix removing of network attachments (https://github.com/ansible/ansible/pull/38816)

- ovirt_disk - support removing unmanaged networks (https://github.com/ansible/ansible/pull/38726)

- ovirt_disk - FCP storage domains don't have to have target (https://github.com/ansible/ansible/pull/38882)

- Ansible.ModuleUtils.FileUtil - support using Test-AnsiblePath with non file system providers (https://github.com/ansible/ansible/pull/39200)

- win_get_url - Compare the UTC time of the web file to the local UTC time (https://github.com/ansible/ansible/pull/39152)


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.1:

v2.5.1
======

.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.1_Release Summary:

Release Summary
---------------

| Release Date: 2018-04-18
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`_


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.1_Minor Changes:

Minor Changes
-------------

- Updated example in vcenter_license module.

- Updated virtual machine facts with instanceUUID which is unique for each VM irrespective of name and BIOS UUID.


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.1_Bugfixes:

Bugfixes
--------

- EOS can not check configuration without use of config session (ANSIBLE_EOS_USE_SESSIONS=0). Fix is to throw error when hiting into this exception case. Configs would neither be checked nor be played on the eos device.

- Adds exception handling which is raised when user does not have correct set of permissions/privileges to read virtual machine facts.

- onyx_pfc_interface - Add support for changes in pfc output in onyx 3.6.6000 https://github.com/ansible/ansible/pull/37651

- Fix mlag summary json parsing for onyx version 3.6.6000 and above https://github.com/ansible/ansible/pull/38191

- Update documentation related to datacenter in vmware_guest_find module. Mark datacenter as optional.

- Set default network type as 'dhcp' if user has not specified any.

- nmcli change default value of autoconnect

- azure_rm_image - Allow Azure images to be created with tags, bug was introduced in Ansible v2.5.0

- azure_rm_networkinterface - Network interface can attach an existing NSG or create a new NSG with specified name in Ansible v2.5.0.

- azure_rm_virtualmachine - removed docs note that says on marketplace images can be used, custom images were added in 2.5

- Improve keyed groups for complex inventory

- Made separator configurable

- Fixed some exception types

- Better error messages

- backup options doc change to reflect backup directory location in case playbook is run from a role

- filters - Don't overwrite builtin jinja2 filters with tests (https://github.com/ansible/ansible/pull/37881)

- edgeos_command - add action plugin to backup config (https://github.com/ansible/ansible/pull/37619)

- eos_vlan - fixed eos_vlan not working when having more than 6 interfaces (https://github.com/ansible/ansible/pull/38347)

- Various grafana_* modules - Port away from the deprecated b64encodestring function to the b64encode function instead. (https://github.com/ansible/ansible/pull/38388)

- include_role - Fix parameter templating (https://github.com/ansible/ansible/pull/36372)

- include_vars - Call DataLoader.load with the correct signature to prevent hang on error processing (https://github.com/ansible/ansible/pull/38194)

- ios_interface - neighbors option now include CDP neighbors (https://github.com/ansible/ansible/pull/37667)

- ios_l2_interface - fix removal of trunk vlans (https://github.com/ansible/ansible/pull/37389)

- ios_l2_interface - use show run instead of section pipeline ios_l2_interface (https://github.com/ansible/ansible/pull/39658)

- Add supported connection in junos module documentation (https://github.com/ansible/ansible/pull/38813)

- _nxos_switchport - fix removal of trunk vlans (https://github.com/ansible/ansible/pull/37328)

- nxos_l2_interface - fix removal of trunk vlans (https://github.com/ansible/ansible/pull/37336)

- nxos_snapshot - fix documentation and add required parameter logic (https://github.com/ansible/ansible/pull/37232, https://github.com/ansible/ansible/pull/37248)

- Improve integration test - Ensure each transport test runs only once (https://github.com/ansible/ansible/pull/37462)

- nxos_user - Integration test (https://github.com/ansible/ansible/pull/37852)

- nxos_bgp_af - Fix UnboundLocalError (https://github.com/ansible/ansible/pull/37610)

- nxos_vrf - Fix nxos_vrf issues (https://github.com/ansible/ansible/pull/37092)

- nxos_vrf_af - Fix nxos_vrf_af issues (https://github.com/ansible/ansible/pull/37211)

- nxos_udld - Fix nxos_udld issues (https://github.com/ansible/ansible/pull/37418)

- nxos_vlan - Fix nxos_vlan issues (https://github.com/ansible/ansible/pull/38008)

- nxos_vlan - nxos_vlan purge (https://github.com/ansible/ansible/pull/38202)

- nxos_aaa_server - Fix nxos_aaa_server (https://github.com/ansible/ansible/pull/38117)

- nxos_aaa_server_host - Fix nxos_aaa_server_host (https://github.com/ansible/ansible/pull/38188)

- nxos_acl - Fix nxos_acl (https://github.com/ansible/ansible/pull/38283)

- nxos_static_route - Fix nxos_static_route (https://github.com/ansible/ansible/pull/37614)

- nxos_acl_interface test - Fix nxos_acl_interface test (https://github.com/ansible/ansible/pull/38230)

- nxos_igmp - Fix nxos_igmp (https://github.com/ansible/ansible/pull/38496)

- nxos_hsrp - Fix nxos_hsrp (https://github.com/ansible/ansible/pull/38410)

- nxos_igmp_snooping - Fix nxos_igmp_snooping (https://github.com/ansible/ansible/pull/38566)

- nxos_ntp_auth - Fix nxos_ntp_auth issues (https://github.com/ansible/ansible/pull/38824)

- nxos_ntp_options - Fix nxos_ntp_options issues (https://github.com/ansible/ansible/pull/38695)

- Fix onyx_config action plugin when used on Python 3 https://github.com/ansible/ansible/pull/38343

- openssl-certificate - Add space between arguments for acme-tiny (https://github.com/ansible/ansible/pull/36739)

- Fix traceback when creating or stopping ovirt vms (https://github.com/ansible/ansible/pull/37249)

- Fix for consul_kv idempotence on Python3 https://github.com/ansible/ansible/issues/35893

- Fix csvfile lookup plugin when used on Python3 https://github.com/ansible/ansible/pull/37625

- ec2 - Fix ec2 user_data parameter to properly convert to base64 on python3 (https://github.com/ansible/ansible/pull/37628)

- Fix to send and receive bytes over a socket in the haproxy module which was causing tracebacks on Python3 https://github.com/ansible/ansible/pull/35176

- jira module - Fix bytes/text handling for base64 encoding authentication tokens (https://github.com/ansible/ansible/pull/33862)

- ansible-pull - fixed a bug checking for changes when we've pulled from the git repository on python3 https://github.com/ansible/ansible/issues/36962

- Fix bytes/text handling in vagrant dynamic inventory https://github.com/ansible/ansible/pull/37631

- wait_for_connection - Fix python3 compatibility bug (https://github.com/ansible/ansible/pull/37646)

- restore stderr ouput even if script module run is successful (https://github.com/ansible/ansible/pull/38177)

- ec2_asg - no longer terminates an instance before creating a replacement (https://github.com/ansible/ansible/pull/36679)

- ec2_group - security groups in default VPCs now have a default egress rule (https://github.com/ansible/ansible/pull/38018)

- inventory correctly removes hosts from 'ungrouped' group (https://github.com/ansible/ansible/pull/37617)

- letsencrypt - fixed domain matching authorization (https://github.com/ansible/ansible/pull/37558)

- letsencrypt - improved elliptic curve account key parsing (https://github.com/ansible/ansible/pull/37275)

- facts are no longer processed more than once for each action (https://github.com/ansible/ansible/issues/37535)

- cs_vpc_offering - only return VPC offferings matching name arg (https://github.com/ansible/ansible/pull/37783)

- cs_configuration - filter names inside the module instead of relying on API (https://github.com/ansible/ansible/pull/37910)

- various fixes to networking module connection subsystem (https://github.com/ansible/ansible/pull/37529)

- ios_* - fixed netconf issues (https://github.com/ansible/ansible/pull/38155)

- ovirt_* - various bugfixes (https://github.com/ansible/ansible/pull/38341)

- ansible-vault no longer requires '--encrypt-vault-id' with edit (https://github.com/ansible/ansible/pull/35923)

- k8s lookup plugin now uses same auth method as other k8s modules (https://github.com/ansible/ansible/pull/37533)

- ansible-inventory now properly displays group_var graph (https://github.com/ansible/ansible/pull/38744)

- setup - FreeBSD fact gathering no longer fails on missing dmesg, sysctl, etc (https://github.com/ansible/ansible/pull/37194)

- inventory scripts now read passwords without byte interpolation (https://github.com/ansible/ansible/pull/35582)

- user - fixed password expiration support in FreeBSD

- meta - inventory_refresh now works properly on YAML inventory plugins (https://github.com/ansible/ansible/pull/38242)

- foreman callback plugin - fixed API options (https://github.com/ansible/ansible/pull/38138)

- win_certificate_store - fixed a typo that stopped it from getting the key_storage values

- win_copy - Preserve the local tmp folder instead of deleting it so future tasks can use it (https://github.com/ansible/ansible/pull/37964)

- win_environment - Fix for issue where the environment value was deleted when a null value or empty string was set - https://github.com/ansible/ansible/issues/40450

- Ansible.ModuleUtils.FileUtil - Catch DirectoryNotFoundException with Test-AnsiblePath (https://github.com/ansible/ansible/pull/37968)

- win_exec_wrapper - support loading of Windows modules different different line endings than the core modules (https://github.com/ansible/ansible/pull/37291)

- win_reboot - fix deprecated warning message to show version in correct spot (https://github.com/ansible/ansible/pull/37898)

- win_regedit - wait for garbage collection to finish before trying to unload the hive in case handles didn't unload in time (https://github.com/ansible/ansible/pull/38912)

- win_service - Fix bug with win_service not being able to handle special chars like '[' (https://github.com/ansible/ansible/pull/37897)

- win_setup - Use connection name for network interfaces as interface name isn't helpful (https://github.com/ansible/ansible/pull/37327)

- win_setup - fix bug where getting the machine SID would take a long time in large domain environments (https://github.com/ansible/ansible/pull/38646)

- win_updates - handle if the module fails to load and return the error message (https://github.com/ansible/ansible/pull/38363)

- win_uri - do not override existing header when using the ``headers`` key. (https://github.com/ansible/ansible/pull/37845)

- win_uri - convert status code values to an int before validating them in server response (https://github.com/ansible/ansible/pull/38080)

- windows - display UTF-8 characters correctly in Windows return json (https://github.com/ansible/ansible/pull/37229)

- winrm - when managing Kerberos tickets in Ansible, get a forwardable ticket if delegation is set (https://github.com/ansible/ansible/pull/37815)


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0:

v2.5.0
======

.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_Release Summary:

Release Summary
---------------

| Release Date: 2018-03-22


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_Major Changes:

Major Changes
-------------

- Ansible Network improvements
  
  * Created new connection plugins ``network_cli`` and ``netconf`` to replace ``connection=local``. ``connection=local`` will continue to work for a number of Ansible releases.
  * No more ``unable to open shell``. A clear and descriptive message will be displayed in normal ansible-playbook output without needing to enable debug mode
  * Loads of documentation, see `Ansible for Network Automation Documentation <http://docs.ansible.com/ansible/2.5/network/>`_.
  * Refactor common network shared code into package under ``module_utils/network/``
  * Filters: Add a filter to convert XML response from a network device to JSON object.
  * Loads of bug fixes.
  * Plus lots more.

- New simpler and more intuitive 'loop' keyword for task loops. The ``with_<lookup>`` loops will likely be deprecated in the near future and eventually removed.

- Added fact namespacing; from now on facts will be available under ``ansible_facts`` namespace (for example: ``ansible_facts.os_distribution``)
  without the ``ansible_`` prefix. They will continue to be added into the main namespace directly, but now with a configuration toggle to
  enable this. This is currently on by default, but in the future it will default to off.

- Added a configuration file that a site administrator can use to specify modules to exclude from being used.


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_Minor Changes:

Minor Changes
-------------

- ansible-inventory - now supports a ``--export`` option to preserve group_var data (https://github.com/ansible/ansible/pull/36188)

- Added a few new magic vars corresponding to configuration/command
  line options: ``ansible_diff_mode``, ``ansible_inventory_sources``,
  ``ansible_limit``, ``ansible_run_tags`` , ``ansible_forks`` and
  ``ansible_skip_tags``

- Updated the bundled copy of the six library to 1.11.0

- Added support to ``become`` ``NT AUTHORITY\System``,
  ``NT AUTHORITY\LocalService``, and ``NT AUTHORITY\NetworkService`` on Windows hosts

- Fixed ``become`` to work with async on Windows hosts

- Improved ``become`` elevation process to work on standard
  Administrator users without disabling UAC on Windows hosts

- The jenkins\_plugin and yum\_repository plugins had their ``params``
  option removed because they circumvented Ansible's option processing.

- The combine filter now accepts a list of dicts as well as dicts directly

- New CLI options for ansible-inventory, ansible-console and ansible to
  allow specifying a playbook\_dir to be used for relative search
  paths.

- `The `stat`` and ``win_stat`` modules have changed the default value of
  ``get_md5`` to ``False`` which will result in the ``md5`` return
  value not being returned. This option will be removed altogether in
  Ansible 2.9. Use ``get_checksum: True`` with
  ``checksum_algorithm: md5`` to return an md5 hash of the file under
  the ``checksum`` return value.

- The ``osx_say`` module was renamed into ``say``.

- Task debugger functionality was moved into ``StrategyBase``, and
  extended to allow explicit invocation from use of the ``debugger``
  keyword. The ``debug`` strategy is still functional, and is now just
  a trigger to enable this functionality.

- The documentation has undergone a major overhaul. Content has been moved into
  targeted guides; the table of contents has been cleaned up and streamlined; 
  the CSS theme has been updated to a custom version of the most recent 
  ReadTheDocs theme, and the underlying directory structure for the RST files 
  has been reorganized. 

- The ANSIBLE\_REMOTE\_TMP environment variable has been added to
  supplement (and override) ANSIBLE\_REMOTE\_TEMP. This matches with
  the spelling of the config value. ANSIBLE\_REMOTE\_TEMP will be
  deprecated in the future.

- aci_* modules - added signature based authentication

- aci_* modules - included dedicated ACI documentation

- aci_* modules - improved ACI return values


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_Deprecated Features:

Deprecated Features
-------------------

- Apstra's ``aos_*`` modules are deprecated as they do not work with AOS 2.1 or higher. See new modules at `https://github.com/apstra <https://github.com/apstra>`_.

- Previously deprecated 'hostfile' config settings have been
  're-deprecated' because previously code did not warn about deprecated
  configuration settings.

- Using Ansible-provided Jinja tests as filters is deprecated and will
  be removed in Ansible 2.9.

- The ``stat`` and ``win_stat`` modules have deprecated ``get_md5`` and the ``md5``
  return values. These options will become undocumented in Ansible
  2.9 and removed in a later version.

- The ``redis_kv`` lookup has been deprecated in favor of new ``redis`` lookup

- Passing arbitrary parameters that begin with ``HEADER_`` to the uri
  module, used for passing http headers, is deprecated. Use the
  ``headers`` parameter with a dictionary of header names to value
  instead. This will be removed in Ansible 2.9

- Passing arbitrary parameters to the zfs module to set zfs properties
  is deprecated. Use the ``extra_zfs_properties`` parameter with a
  dictionary of property names to values instead. This will be removed
  in Ansible 2.9.

- Use of the AnsibleModule parameter ``check\_invalid\_arguments`` in custom modules is deprecated. In the future, all parameters will be
  checked to see whether they are listed in the arg spec and an error raised if they are not listed. This behaviour is the current and
  future default so most custom modules can simply remove ``check\_invalid\_arguments`` if they set it to the default value of True.
  The ``check\_invalid\_arguments`` parameter will be removed in Ansible 2.9.

- The nxos\_ip\_interface module is deprecated in Ansible 2.5. Use nxos\_l3\_interface module instead.

- The nxos\_portchannel module is deprecated in Ansible 2.5. Use nxos\_linkagg module instead.

- The nxos\_switchport module is deprecated in Ansible 2.5. Use nxos\_l2\_interface module instead.

- The ec2\_ami\_find has been deprecated; use ec2\_ami\_facts instead.

- panos\_security\_policy: Use panos\_security\_rule - the old module uses deprecated API calls

- vsphere\_guest is deprecated in Ansible 2.5 and will be removed in Ansible-2.9. Use vmware\_guest module instead.


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_Removed Features (previously deprecated):

Removed Features (previously deprecated)
----------------------------------------

- accelerate.

- boundary\_meter: There was no deprecation period for this but the
  hosted service it relied on has gone away so the module has been
  removed. `#29387 <https://github.com/ansible/ansible/issues/29387>`__

- cl\_ : cl\_interface, cl\_interface\_policy, cl\_bridge,
  cl\_img\_install, cl\_ports, cl\_license, cl\_bond. Use ``nclu``
  instead

- docker. Use docker\_container and docker\_image instead.

- ec2\_vpc.

- ec2\_ami\_search, use ec2\_ami\_facts instead.

- nxos\_mtu. Use nxos\_system's ``system_mtu`` option instead. To specify an interface's MTU use nxos\_interface.

- panos\_nat\_policy: Use panos\_nat\_rule the old module uses deprecated API calls


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_New Lookup Plugins:

New Lookup Plugins
------------------

- aws\_account\_attribute: Query AWS account attributes such as EC2-Classic availability

- aws\_service\_ip\_ranges: Query AWS IP ranges for services such as EC2/S3

- aws\_ssm: Query AWS ssm data

- config: Lookup Ansible settings

- conjur\_variable: Fetch credentials from CyberArk Conjur

- k8s: Query the K8s API

- nios: Query Infoblox NIOS objects

- openshift: Return info from Openshift installation

- redis: look up date from Redis DB, deprecates the redis\_kv one.


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_New Callback Plugins:

New Callback Plugins
--------------------

- null

- unixy

- yaml


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_New Connection Plugins:

New Connection Plugins
----------------------

- kubectl

- oc

- netconf

- network\_cli
   - The existing network\_cli and netconf connection plugins can now be used directly with network modules. See
     `Network Best Practices for Ansible 2.5 <http://docs.ansible.com/ansible/devel/network_best_practices_2.5.html>`_ for more details.


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_New Filter Plugins:

New Filter Plugins
------------------

- parse\_xml


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_New Modules:

New Modules
-----------

- Cloud (amazon)
    -  aws\_acm\_facts
    -  aws\_application\_scaling\_policy
    -  aws\_az\_facts
    -  aws\_batch\_compute\_environment
    -  aws\_batch\_job\_definition
    -  aws\_batch\_job\_queue
    -  aws\_direct\_connect\_gateway
    -  aws\_direct\_connect\_virtual\_interface
    -  aws\_elasticbeanstalk\_app
    -  aws\_kms\_facts
    -  aws\_region\_facts
    -  aws\_s3\_cors
    -  aws\_ses\_identity
    -  aws\_ssm\_parameter\_store
    -  aws\_waf\_condition
    -  aws\_waf\_rule
    -  aws\_waf\_web\_acl
    -  cloudfront\_distribution
    -  cloudfront\_invalidation
    -  cloudfront\_origin\_access\_identity
    -  cloudwatchlogs\_log\_group
    -  cloudwatchlogs\_log\_group\_facts
    -  ec2\_ami\_facts
    -  ec2\_asg\_lifecycle\_hook
    -  ec2\_customer\_gateway\_facts
    -  ec2\_instance
    -  ec2\_placement\_group
    -  ec2\_placement\_group\_facts
    -  ec2\_vpc\_egress\_igw
    -  ecs\_taskdefinition\_facts
    -  elasticache\_facts
    -  elb\_target
    -  iam\_role\_facts
    -  iam\_user

- Cloud (azure)
    -  azure\_rm\_containerinstance
    -  azure\_rm\_containerregistry
    -  azure\_rm\_image
    -  azure\_rm\_keyvault
    -  azure\_rm\_keyvaultkey
    -  azure\_rm\_keyvaultsecret
    -  azure\_rm\_mysqldatabase
    -  azure\_rm\_mysqlserve
    -  azure\_rm\_postgresqldatabase
    -  azure\_rm\_postgresqlserver
    -  azure\_rm\_sqldatabase
    -  azure\_rm\_sqlserver
    -  azure\_rm\_sqlserver\_facts

- Cloud (cloudstack)
     -  cs\_network\_offering
     -  cs\_service\_offering
     -  cs\_vpc\_offering
     -  cs\_vpn\_connection
     -  cs\_vpn\_customer\_gateway

- Cloud (digital\_ocean)
     -  digital\_ocean\_certificate
     -  digital\_ocean\_floating\_ip\_facts
     -  digital\_ocean\_sshkey\_facts

- Cloud (google)
     -  gcp\_dns\_managed\_zone

- Cloud (misc)
     -  cloudscale\_floating\_ip
     -  spotinst\_aws\_elastigroup
     -  terraform

- Cloud (oneandone)
     -  oneandone\_firewall\_policy
     -  oneandone\_load\_balancer
     -  oneandone\_monitoring\_policy
     -  oneandone\_private\_network
     -  oneandone\_public\_ip
     -  oneandone\_server

- Cloud (openstack)
     -  os\_keystone\_endpoint
     -  os\_project\_access

- Cloud (ovirt)
     -  ovirt\_api\_facts
     -  ovirt\_disk\_facts

- Cloud (vmware)
     -  vcenter\_folder
     -  vmware\_cfg\_backup
     -  vmware\_datastore\_facts
     -  vmware\_drs\_rule\_facts
     -  vmware\_guest\_file\_operation
     -  vmware\_guest\_powerstate
     -  vmware\_host\_acceptance
     -  vmware\_host\_config\_facts
     -  vmware\_host\_config\_manager
     -  vmware\_host\_datastore
     -  vmware\_host\_dns\_facts
     -  vmware\_host\_facts
     -  vmware\_host\_firewall\_facts
     -  vmware\_host\_firewall\_manager
     -  vmware\_host\_lockdown
     -  vmware\_host\_ntp
     -  vmware\_host\_package\_facts
     -  vmware\_host\_service\_facts
     -  vmware\_host\_service\_manager
     -  vmware\_host\_vmnic\_facts
     -  vmware\_local\_role\_manager
     -  vmware\_vm\_vm\_drs\_rule
     -  vmware\_vmkernel\_facts

- Cloud (vultr)
     -  vr\_account\_facts
     -  vr\_dns\_domain
     -  vr\_dns\_record
     -  vr\_firewall\_group
     -  vr\_firewall\_rule
     -  vr\_server
     -  vr\_ssh\_key
     -  vr\_startup\_script
     -  vr\_user

- Clustering
    -  etcd3
    -  k8s
    -  k8s\_raw
    -  k8s\_scale
    -  openshift
    -  openshift\_raw
    -  openshift\_scale

- Crypto
    -  openssl\_dhparam

- Database
    -  influxdb
    -  influxdb\_query
    -  influxdb\_user
    -  influxdb\_write

- Identity
    -  ipa
    -  ipa\_dnszone
    -  ipa\_service
    -  ipa\_subca
    -  keycloak
    -  keycloak\_client
    -  keycloak\_clienttemplate

- Monitoring
    -  grafana\_dashboard
    -  grafana\_datasource
    -  grafana\_plugin
    -  icinga2\_host
    -  zabbix
    -  zabbix\_proxy
    -  zabbix\_template

- Net Tools
    -  ip\_netns
    -  nios
    -  nios\_dns\_view
    -  nios\_host\_record
    -  nios\_network
    -  nios\_network\_view
    -  nios\_zone

- Network (aci)
    -  aci\_aaa\_user
    -  aci\_aaa\_user\_certificate
    -  aci\_access\_port\_to\_interface\_policy\_leaf\_profile
    -  aci\_aep\_to\_domain
    -  aci\_domain
    -  aci\_domain\_to\_encap\_pool
    -  aci\_domain\_to\_vlan\_pool
    -  aci\_encap\_pool
    -  aci\_encap\_pool\_range
    -  aci\_fabric\_node
    -  aci\_firmware\_source
    -  aci\_interface\_policy\_leaf\_policy\_group
    -  aci\_interface\_policy\_leaf\_profile
    -  aci\_interface\_selector\_to\_switch\_policy\_leaf\_profile
    -  aci\_static\_binding\_to\_epg
    -  aci\_switch\_leaf\_selector
    -  aci\_switch\_policy\_leaf\_profile
    -  aci\_switch\_policy\_vpc\_protection\_group
    -  aci\_vlan\_pool
    -  aci\_vlan\_pool\_encap\_block

- Network (avi)
    -  avi\_api\_version
    -  avi\_clusterclouddetails
    -  avi\_customipamdnsprofile
    -  avi\_errorpagebody
    -  avi\_errorpageprofile
    -  avi\_gslbservice\_patch\_member
    -  avi\_wafpolicy
    -  avi\_wafprofile

- Network (dimension data)
    -  dimensiondata\_vlan

- Network (edgeos)
    -  edgeos\_command
    -  edgeos\_config
    -  edgeos\_facts

- Network (enos)
    -  enos\_command
    -  enos\_config
    -  enos\_facts

- Network (eos)
    -  eos\_interface
    -  eos\_l2\_interface
    -  eos\_l3\_interface
    -  eos\_linkagg
    -  eos\_lldp
    -  eos\_static\_route

- Network (f5)
    -  bigip\_asm\_policy
    -  bigip\_device\_connectivity
    -  bigip\_device\_group
    -  bigip\_device\_group\_member
    -  bigip\_device\_httpd
    -  bigip\_device\_trust
    -  bigip\_gtm\_server
    -  bigip\_iapplx\_package
    -  bigip\_monitor\_http
    -  bigip\_monitor\_https
    -  bigip\_monitor\_snmp\_dca
    -  bigip\_monitor\_udp
    -  bigip\_partition
    -  bigip\_policy
    -  bigip\_policy\_rule
    -  bigip\_profile\_client\_ssl
    -  bigip\_remote\_syslog
    -  bigip\_security\_address\_list
    -  bigip\_security\_port\_list
    -  bigip\_software\_update
    -  bigip\_ssl\_key
    -  bigip\_static\_route
    -  bigip\_traffic\_group
    -  bigip\_ucs\_fetch
    -  bigip\_vcmp\_guest
    -  bigip\_wait
    -  bigiq\_regkey\_license
    -  bigiq\_regkey\_pool

- Network (fortimanager)
    -  fmgr\_script

- Network (ios)
    -  ios\_l2\_interface
    -  ios\_l3\_interface
    -  ios\_linkagg
    -  ios\_lldp
    -  ios\_vlan

- Network (iosxr)
    -  iosxr\_netconf

- Network (ironware)
    -  ironware\_command
    -  ironware\_config
    -  ironware\_facts

- Network (junos)
    -  junos\_l2\_interface
    -  junos\_scp

- Network (netact)
    -  netact\_cm\_command

- Network (netscaler)
    -  netscaler\_nitro\_request

- Network (nso)
    -  nso\_action
    -  nso\_config
    -  nso\_query
    -  nso\_show
    -  nso\_verify

- Network (nxos)
    -  nxos\_l2\_interface
    -  nxos\_l3\_interface
    -  nxos\_linkagg
    -  nxos\_lldp

- Network (onyx)
    -  onyx\_bgp
    -  onyx\_command
    -  onyx\_config
    -  onyx\_facts
    -  onyx\_interface
    -  onyx\_l2\_interface
    -  onyx\_l3\_interface
    -  onyx\_linkagg
    -  onyx\_lldp
    -  onyx\_lldp\_interface
    -  onyx\_magp
    -  onyx\_mlag\_ipl
    -  onyx\_mlag\_vip
    -  onyx\_ospf
    -  onyx\_pfc\_interface
    -  onyx\_protocol
    -  onyx\_vlan

- Network (panos)
    -  panos\_dag\_tags
    -  panos\_match\_rule
    -  panos\_op
    -  panos\_query\_rules

- Network (radware)
    -  vdirect\_commit
    -  vdirect\_runnable

- Network (vyos)
    -  vyos\_vlan

- Notification
    -  logentries\_msg
    -  say
    -  snow\_record

- Packaging
    -  os
    -  package\_facts
    -  rhsm\_repository

- Remote Management (manageiq)
    -  manageiq\_alert\_profiles
    -  manageiq\_alerts
    -  manageiq\_policies
    -  manageiq\_tags

- Remote Management (oneview)
    -  oneview\_datacenter\_facts
    -  oneview\_enclosure\_facts
    -  oneview\_logical\_interconnect\_group
    -  oneview\_logical\_interconnect\_group\_facts
    -  oneview\_san\_manager\_facts

- Remote Management (ucs)
    -  ucs\_ip\_pool
    -  ucs\_lan\_connectivity
    -  ucs\_mac\_pool
    -  ucs\_san\_connectivity
    -  ucs\_vhba\_template
    -  ucs\_vlans
    -  ucs\_vnic\_template
    -  ucs\_vsans
    -  ucs\_wwn\_pool

- System
    -  mksysb
    -  nosh
    -  service\_facts
    -  vdo

- Web Infrastructure
    -  jenkins\_job\_facts

- Windows
    -  win\_audit\_policy\_system
    -  win\_audit\_rule
    -  win\_certificate\_store
    -  win\_disk\_facts
    -  win\_product\_facts
    -  win\_scheduled\_task\_stat
    -  win\_whoami


.. _Ansible 2.5 "Kashmir" Release Notes_v2.5.0_Bugfixes:

Bugfixes
--------

- tower_* modules - fix credentials to work with v1 and v2 of Ansible Tower API

- azure_rm modules - updated with internal changes to use API profiles and kwargs for future Azure Stack support and better stability between SDK updates. (https://github.com/ansible/ansible/pull/35538)

- fixed memory bloat on nested includes by preventing blocks from self-parenting (https://github.com/ansible/ansible/pull/36075)

- updated to ensure displayed messages under peristent connections are returned to the controller (https://github.com/ansible/ansible/pull/36064)

- docker_container, docker_image, docker_network modules - Update to work with Docker SDK 3.1

- edgeos_facts - fix error when there are no commit revisions (https://github.com/ansible/ansible/issues/37123)

- eos_vrf and eos_eapi - fixed vrf parsing (https://github.com/ansible/ansible/pull/35791)

- include_role - improved performance and recursion depth (https://github.com/ansible/ansible/pull/36470)

- interface_file - now accepts interfaces without address family or method (https://github.com/ansible/ansible/pull/34200)

- lineinfile - fixed insertion if pattern already exists (https://github.com/ansible/ansible/pull/33393)

- lineinfile - fixed regexp used with insert(before|after) inserting duplicate lines (https://github.com/ansible/ansible/pull/36156)

- Connection error messages may contain characters that jinja2 would interpret as a template.  Wrap the error string so this doesn't happen (https://github.com/ansible/ansible/pull/37329)

- nxos_evpn_vni - fixed a number of issues (https://github.com/ansible/ansible/pull/35930)

- nxos_igmp_interface - fixed response handling for different nxos versions (https://github.com/ansible/ansible/pull/35959)

- nxos_interface_ospf - added various bugfixes (https://github.com/ansible/ansible/pull/35988)

- Fix onyx_linkagg module writing debugging information to a tempfile on the remote machine (https://github.com/ansible/ansible/pull/37308)

- openshift modules - updated to client version 0.4.0 (https://github.com/ansible/ansible/pull/35127)

- setup.py - Ensure we install ansible-config and ansible-inventory with `pip install -e` (https://github.com/ansible/ansible/pull/37151)

- Fix for ansible_*_interpreter on Python3 when using non-newstyle modules. Those include old-style ansible modules and Ansible modules written in non-python scripting languages (https://github.com/ansible/ansible/pull/36541)

- Fix bytes/text handling in maven_artifact that was causing tracebacks on Python3

- znode - fixed a bug calling the zookeeper API under Python3 https://github.com/ansible/ansible/pull/36999

- Fix for unarchive when users use the --strip-components extra_opt to tar causing ansible to set permissions on the wrong directory. (https://github.com/ansible/ansible/pull/37048)

- fixed templating issues in loop_control (https://github.com/ansible/ansible/pull/36124)

- ansible-config - fixed traceback when no config file is present (https://github.com/ansible/ansible/issues/35965)

- added various fixes to Linux virtualization facts (https://github.com/ansible/ansible/issues/36038)

- fixed failure when remote_tmp is a subdir of a system tempdir (https://github.com/ansible/ansible/pull/36143)

- ios_ping - updated to allow for count > 70 (https://github.com/ansible/ansible/pull/36142)

- fix for ansible-vault always requesting passwords (https://github.com/ansible/ansible/issues/33027)

- ios CLI - fixed prompt detection (https://github.com/ansible/ansible/issues/35662)

- nxos_user - fixed structured output issue (https://github.com/ansible/ansible/pull/36193)

- nxos_* modules - various fixes (https://github.com/ansible/ansible/pull/36340)

- nxos_* modules - various fixes (https://github.com/ansible/ansible/pull/36374)

- nxos_install_os - kickstart_image_file is no longer required (https://github.com/ansible/ansible/pull/36319)

- script/patch - fixed tempfile ownership issues (https://github.com/ansible/ansible/issues/36398)

- nxos_bgp_neighbor - fixed various module arg issues (https://github.com/ansible/ansible/pull/36318)

- vyos_l3_interface - fixed issues with multiple addresses on an interface (https://github.com/ansible/ansible/pull/36377)

- nxos_banner - fixed issues with unstructured output (https://github.com/ansible/ansible/pull/36411)

- nxos_bgp_neighbor_af - fixed various issues (https://github.com/ansible/ansible/pull/36472)

- vyos_config - fixed IndexError in sanitize_config (https://github.com/ansible/ansible/pull/36375)

- cs_user - fixed user_api_secret return for ACS 4.10+ (https://github.com/ansible/ansible/pull/36447)

- nxos_* modules - various fixes (https://github.com/ansible/ansible/pull/36514)

- fix cases where INVENTORY_UNPARSED_IS_FAILED didn't fail (https://github.com/ansible/ansible/issues/36034)

- aws_ses_identity - fixed failure on missing identity info (https://github.com/ansible/ansible/issues/36065)

- ec2_vpc_net_facts - fixed traceback for regions other than us-east-1 (https://github.com/ansible/ansible/pull/35302)

- aws_waf_* - fixed traceback on WAFStaleDataException (https://github.com/ansible/ansible/pull/36405)

- ec2_group - fixed check_mode when using tags (https://github.com/ansible/ansible/pull/36503)

- loop item labels will now update if templated (https://github.com/ansible/ansible/pull/36430)

- (network)_vlan / (network)_vrf - decouple config/state check (https://github.com/ansible/ansible/pull/36704)

- nxos_vlan / nxos_linkagg - fixed various issues (https://github.com/ansible/ansible/pull/36711)

- nios - allow ib_spec attrs to be filtered in update (https://github.com/ansible/ansible/pull/36673)

- nso_config / nso_verify - fixed various issues (https://github.com/ansible/ansible/pull/36583)

- cs_sshkeypair - fixed ssh key rename (https://github.com/ansible/ansible/pull/36726)

- cliconf - fixed get_config traceback (https://github.com/ansible/ansible/pull/36682)

- impi_boot - added floppy option (https://github.com/ansible/ansible/pull/36174)

- nso_config - fixed ordering issues (https://github.com/ansible/ansible/pull/36774)

- nxos_facts - fixed ipv6 parsing issues on new nxos releases (https://github.com/ansible/ansible/pull/36796)

- nso_config - fixed dependency sort cycle issue (https://github.com/ansible/ansible/pull/36828)

- ovirt_* - various fixes (https://github.com/ansible/ansible/pull/36828)

- aws_ssm_parameter_store - added no_log to value arg (https://github.com/ansible/ansible/pull/36828)

- openshift_raw - fixed creation of RoleBinding resources (https://github.com/ansible/ansible/pull/36887)

- nxos_interface - fixed multiple issues (https://github.com/ansible/ansible/pull/36827)

- junos_command - fixed Python3 issues (https://github.com/ansible/ansible/pull/36782)

- ios_static_route - fixed idempotence issue (https://github.com/ansible/ansible/pull/35912)

- terraform - fixed typo in module result stdout value (https://github.com/ansible/ansible/pull/37253)

- setup - ensure that `ansible_lo` is properly nested under ansible_facts (https://github.com/ansible/ansible/pull/37360)

- vmware_guest_snapshot - updated to always check for root snapshot (https://github.com/ansible/ansible/pull/36001)

- vyos - added fixes to check mode support (https://github.com/ansible/ansible/pull/35977)

- vyos_l3_interface - added support for localhost (https://github.com/ansible/ansible/pull/36141)

- win_domain_controller - updated to only specify ReadOnlyReplica when necessary (https://github.com/ansible/ansible/pull/36017)

- win_feature - will display a more helpful error when it fails during execution (https://github.com/ansible/ansible/pull/36491)

- win_lineinfile - fixed issue where \r and \n as a string was converted to newline (https://github.com/ansible/ansible/pull/35100)

- win_updates - fixed regression with string category names (https://github.com/ansible/ansible/pull/36015)

- win_uri - return response info and content on a non 200 message

- win_uri - fixed issues with the creates and removes options (https://github.com/ansible/ansible/pull/36016)

- win_wait_for - fixed issue when trying to check a localport when the port is not available externally

