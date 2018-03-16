===================================
Ansible 2.5 "Kashmir" Release Notes
===================================

v2.5.0rc3
=========

Release Summary
---------------

| Release Date: 2018-03-15
| Estimated Final Release: 2018-03-22
| `Porting Guide <http://docs.ansible.com/ansible/devel/porting_guides.html>`_


Bugfixes
--------

- Connection error messages may contain characters that jinja2 would interpret as a template.  Wrap the error string so this doesn't happen (https://github.com/ansible/ansible/pull/37329)

- Fix onyx_linkagg module writing debugging information to a tempfile on the remote machine (https://github.com/ansible/ansible/pull/37308)

- terraform - fixed typo in module result stdout value (https://github.com/ansible/ansible/pull/37253)

- setup - ensure that `ansible_lo` is properly nested under ansible_facts (https://github.com/ansible/ansible/pull/37360)


v2.5.0rc2
=========

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


Bugfixes
--------

- tower_* modules - fix credentials to work with v1 and v2 of Ansible Tower API

- docker_container, docker_image, docker_network modules - Update to work with Docker SDK 3.1

- edgeos_facts - fix error when there are no commit revisions (https://github.com/ansible/ansible/issues/37123)

- setup.py - Ensure we install ansible-config and ansible-inventory with `pip install -e` (https://github.com/ansible/ansible/pull/37151)

- Fix bytes/text handling in maven_artifact that was causing tracebacks on Python3

- znode - fixed a bug calling the zookeeper API under Python3 https://github.com/ansible/ansible/pull/36999

- Fix for unarchive when users use the --strip-components extra_opt to tar causing ansible to set permissions on the wrong directory. https://github.com/ansible/ansible/pull/37048

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

- win_lineinfile - fixed issue where \r and \n as a string was converted to newline (https://github.com/ansible/ansible/pull/35100)

- win_uri - return response info and content on a non 200 message

- win_wait_for - fixed issue when trying to check a localport when the port is not available externally


v2.5.0rc1
=========

Minor Changes
-------------

- aci_* modules - added signature based authentication

- aci_* modules - included dedicated ACI documentation

- aci_* modules - improved ACI return values


Deprecated Features
-------------------

- Apstra's ``aos_*`` modules are deprecated as they do not work with AOS 2.1 or higher. See new modules at `https://github.com/apstra <https://github.com/apstra>`_.


Bugfixes
--------

- include_role - improved performance and recursion depth (https://github.com/ansible/ansible/pull/36470)

- lineinfile - fixed regexp used with insert(before|after) inserting duplicate lines (https://github.com/ansible/ansible/pull/36156)

- Fix for ansible_*_interpreter on Python3 when using non-newstyle modules. Those include old-style ansible modules and Ansible modules written in non-python scripting languages (https://github.com/ansible/ansible/pull/36541)

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

- win_feature - will display a more helpful error when it fails during execution (https://github.com/ansible/ansible/pull/36491)


v2.5.0b2
========

Major Changes
-------------

- New simpler and more intuitive 'loop' keyword for task loops. The ``with_<lookup>`` loops will likely be deprecated in the near future and eventually removed.

- Added fact namespacing; from now on facts will be available under ``ansible_facts`` namespace (for example: ``ansible_facts.os_distribution``)
  without the ``ansible_`` prefix. They will continue to be added into the main namespace directly, but now with a configuration toggle to
  enable this. This is currently on by default, but in the future it will default to off.

- Added a configuration file that a site administrator can use to specify modules to exclude from being used.


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


Deprecated Features
-------------------

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


New Callback Plugins
--------------------

- null

- unixy

- yaml


New Connection Plugins
----------------------

- kubectl

- oc

- netconf

- network\_cli
   - The existing network\_cli and netconf connection plugins can now be used directly with network modules. See
     `Network Best Practices for Ansible 2.5 <http://docs.ansible.com/ansible/devel/network_best_practices_2.5.html>`_ for more details.


New Filter Plugins
------------------

- parse\_xml


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


Bugfixes
--------

- azure_rm modules - updated with internal changes to use API profiles and kwargs for future Azure Stack support and better stability between SDK updates. (https://github.com/ansible/ansible/pull/35538)

- fixed memory bloat on nested includes by preventing blocks from self-parenting (https://github.com/ansible/ansible/pull/36075)

- updated to ensure displayed messages under peristent connections are returned to the controller (https://github.com/ansible/ansible/pull/36064)

- eos_vrf and eos_eapi - fixed vrf parsing (https://github.com/ansible/ansible/pull/35791)

- interface_file - now accepts interfaces without address family or method (https://github.com/ansible/ansible/pull/34200)

- lineinfile - fixed insertion if pattern already exists (https://github.com/ansible/ansible/pull/33393)

- nxos_evpn_vni - fixed a number of issues (https://github.com/ansible/ansible/pull/35930)

- nxos_igmp_interface - fixed response handling for different nxos versions (https://github.com/ansible/ansible/pull/35959)

- nxos_interface_ospf - added various bugfixes (https://github.com/ansible/ansible/pull/35988)

- openshift modules - updated to client version 0.4.0 (https://github.com/ansible/ansible/pull/35127)

- fixed templating issues in loop_control (https://github.com/ansible/ansible/pull/36124)

- ansible-config - fixed traceback when no config file is present (https://github.com/ansible/ansible/issues/35965)

- added various fixes to Linux virtualization facts (https://github.com/ansible/ansible/issues/36038)

- fixed failure when remote_tmp is a subdir of a system tempdir (https://github.com/ansible/ansible/pull/36143)

- ios_ping - updated to allow for count > 70 (https://github.com/ansible/ansible/pull/36142)

- vmware_guest_snapshot - updated to always check for root snapshot (https://github.com/ansible/ansible/pull/36001)

- vyos - added fixes to check mode support (https://github.com/ansible/ansible/pull/35977)

- vyos_l3_interface - added support for localhost (https://github.com/ansible/ansible/pull/36141)

- win_domain_controller - updated to only specify ReadOnlyReplica when necessary (https://github.com/ansible/ansible/pull/36017)

- win_updates - fixed regression with string category names (https://github.com/ansible/ansible/pull/36015)

- win_uri - fixed issues with the creates and removes options (https://github.com/ansible/ansible/pull/36016)

