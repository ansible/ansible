Ansible Changes By Release
==========================

2.3 TBD - ACTIVE DEVELOPMENT
----------------------------

Major Changes:
~~~~~~~~~~~~~~

-  Documented and renamed the previously released 'single var vaulting'
   feature, allowing user to use vault encryption for single variables
   in a normal YAML vars file.
-  Allow module\_utils for custom modules to be placed in site-specific
   directories and shipped in roles
-  On platforms that support it, use more modern system polling API
   instead of select in the ssh connection plugin. This removes one
   limitation on how many parallel forks are feasible on these systems.
-  Windows supports become method "runas" to run modules as a different
   user, and to transparently access network resources.
-  Windows now uses pipelining when executing modules, resulting in
   significantly faster execution for small tasks.
-  Refactored/standardized most Windows modules, adding check-mode and
   diff support where possible.
-  Extended Windows module API with parameter-type support, helper
   functions. (i.e. Expand-Environment, Add-Warning,
   Add-DeprecatationWarning)

Minor Changes:
~~~~~~~~~~~~~~

-  The version and release facts for OpenBSD hosts were reversed. This
   has been changed so that version has the numeric portion and release
   has the name of the release.
-  removed 'package' from default squash actions as not all package
   managers support it and it creates errors when using loops, any user
   can add back via config options if they don't use those package
   managers or otherwise avoid the errors.
-  Blocks can now have a ``name`` field, to aid in playbook readability.
-  default strategy is now configurable via ansible.cfg or environment
   variable.
-  Added 'ansible\_playbook\_python' which contains 'current python
   executable', it can be blank in some cases in which Ansible is not
   invoked via the standard CLI (sys.executable limitation).
-  ansible-doc now displays path to module
-  added optional 'piped' transfer method to ssh plugin for when scp and
   sftp are missing
-  default controlpersist path is now a custom hash of host-port-user to
   avoid the socket path length errors for long hostnames
-  Various fixes for Python3 compatibility
-  The AWS Lambda module previously ignored changes that only affected
   one parameter. Existing deployments may have outstanding changes that
   this bugfix will apply.

Deprecations:
~~~~~~~~~~~~~

-  Specifying --tags (or --skip-tags) multiple times on the command line
   currently leads to the last one overridding all the previous ones.
   This behaviour is deprecated. In the future, if you specify --tags
   multiple times the tags will be merged together. In 2.3, using --tags
   multiple times on one command line will emit a deprecation warning.
   Setting the merge\_multiple\_cli\_tags option to True in the
   ansible.cfg file will enable the new behaviour. In 2.4, the default
   will be to merge and you can enable the old overwriting behaviour via
   the config option. In 2.5, multiple --tags options will be merged
   with no way to go back to the old behaviour.
-  Modules
-  ec2\_vpc will be deprecated in 2.3 and removed in 2.5
-  cl\_bond will be deprecated in 2.3 and removed in 2.5
-  cl\_bridge will be deprecated in 2.3 and removed in 2.5
-  cl\_img\_install will be deprecated in 2.3 and removed in 2.5
-  cl\_interface will be deprecated in 2.3 and removed in 2.5
-  cl\_interface\_policy will be deprecated in 2.3 and removed in 2.5
-  cl\_license will be deprecated in 2.3 and removed in 2.5
-  cl\_ports will be deprecated in 2.3 and removed in 2.5

Modules Notes:
~~~~~~~~~~~~~~

-  oVirt/RHV
-  Add dynamic inventory.
-  Add support for 4.1 features.
-  Add support for data centers, clusters, hosts, storage domains and
   networks management.
-  Add support for hosts and virtual machines affinity groups and
   labels.
-  Add support for users, groups and permissions management.
-  Improved virtual machines and disks management.
-  Mount: Some fixes so bind mounts are not mounted each time the
   playbook runs.

New Modules:
~~~~~~~~~~~~

-  a10\_server\_axapi3
-  amazon:
-  aws\_kms
-  cloudfront\_facts
-  ec2\_group\_facts
-  ec2\_lc\_facts
-  ec2\_vpc\_igw\_facts
-  ec2\_vpc\_nat\_gateway\_facts
-  ec2\_vpc\_vgw\_facts
-  ecs\_ecr
-  elasticache\_parameter\_group
-  elasticache\_snapshot
-  iam\_role
-  s3\_sync
-  archive
-  beadm
-  bigswitch:
-  bigmon\_chain
-  bigmon\_policy
-  cloudengine:
-  ce\_command
-  cloudscale\_server
-  cloudstack:
-  cs\_host
-  cs\_nic
-  cs\_region
-  cs\_role
-  cs\_vpc
-  dimensiondata\_network
-  eos:
-  eos\_banner
-  eos\_system
-  eos\_user
-  f5:
-  bigip\_gtm\_facts
-  bigip\_hostname
-  bigip\_snat\_pool
-  bigip\_sys\_global
-  foreman:
-  foreman
-  katello
-  fortios
-  fortios\_config
-  gconftool2
-  google:
-  gce\_eip
-  gce\_snapshot
-  gcpubsub
-  gcpubsub\_facts
-  hpilo:
-  hpilo\_boot
-  hpilo\_facts
-  hponcfg
-  icinga2\_feature
-  illumos:
-  dladm\_iptun
-  dladm\_linkprop
-  dladm\_vlan
-  ipadm\_addr
-  ipadm\_addrprop
-  ipadm\_ifprop
-  infinidat:
-  infini\_export
-  infini\_export\_client
-  infini\_fs
-  infini\_host
-  infini\_pool
-  infini\_vol
-  ipa:
-  ipa\_group
-  ipa\_hbacrule
-  ipa\_host
-  ipa\_hostgroup
-  ipa\_role
-  ipa\_sudocmd
-  ipa\_sudocmdgroup
-  ipa\_sudorule
-  ipa\_user
-  ipinfoio\_facts
-  ios:
-  ios\_system
-  ios\_vrf
-  iosxr\_system
-  iso\_extract
-  jenkins\_script
-  ldap:
-  ldap\_attr
-  ldap\_entry
-  logstash\_plugin
-  mattermost
-  net\_command
-  netapp:
-  sf\_account\_manager
-  sf\_snapshot\_schedule\_manager
-  sf\_volume\_manager
-  sf\_volume\_access\_group\_manager
-  nginx\_status\_facts
-  nsupdate
-  omapi\_host
-  openssl:
-  openssl\_privatekey
-  openssl\_publickey
-  openstack:
-  os\_nova\_host\_aggregate
-  os\_quota
-  openwrt\_init
-  ordnance:
-  ordnance\_config
-  ordnance\_facts
-  ovirt:
-  ovirt\_affinity\_groups
-  ovirt\_affinity\_labels
-  ovirt\_affinity\_labels\_facts
-  ovirt\_clusters
-  ovirt\_clusters\_facts
-  ovirt\_datacenters
-  ovirt\_datacenters\_facts
-  ovirt\_external\_providers
-  ovirt\_external\_providers\_facts
-  ovirt\_groups
-  ovirt\_groups\_facts
-  ovirt\_host\_networks
-  ovirt\_host\_pm
-  ovirt\_hosts
-  ovirt\_hosts\_facts
-  ovirt\_mac\_pools
-  ovirt\_networks
-  ovirt\_networks\_facts
-  ovirt\_nics
-  ovirt\_nics\_facts
-  ovirt\_permissions
-  ovirt\_permissions\_facts
-  ovirt\_quotas
-  ovirt\_quotas\_facts
-  ovirt\_snapshots
-  ovirt\_snapshots\_facts
-  ovirt\_storage\_domains
-  ovirt\_storage\_domains\_facts
-  ovirt\_tags
-  ovirt\_tags\_facts
-  ovirt\_templates
-  ovirt\_templates\_facts
-  ovirt\_users
-  ovirt\_users\_facts
-  ovirt\_vmpools
-  ovirt\_vmpools\_facts
-  ovirt\_vms\_facts
-  pacemaker\_cluster
-  packet:
-  packet\_device
-  packet\_sshkey
-  pamd
-  panos:
-  panos\_address
-  panos\_admin
-  panos\_admpwd
-  panos\_cert\_gen\_ssh
-  panos\_check
-  panos\_commit
-  panos\_dag
-  panos\_import
-  panos\_interface
-  panos\_lic
-  panos\_loadcfg
-  panos\_mgtconfig
-  panos\_nat\_policy
-  panos\_pg
-  panos\_restart
-  panos\_security\_policy
-  panos\_service
-  postgresql\_schema
-  proxmox\_kvm
-  pubnub\_blocks
-  pulp\_repo
-  runit
-  serverless
-  set\_stats
-  panos:
-  panos\_security\_policy
-  smartos:
-  imgadm
-  vmadm
-  sorcery
-  stacki\_host
-  swupd
-  tempfile
-  tower:
-  tower\_credential
-  tower\_group
-  tower\_host
-  tower\_inventory
-  tower\_job\_template
-  tower\_label
-  tower\_organization
-  tower\_project
-  tower\_role
-  tower\_team
-  tower\_user
-  vmware:
-  vmware\_guest\_facts
-  vmware\_guest\_snapshot
-  web\_infrastructure:
-  jenkins\_script
-  system
-  parted
-  windows:
-  win\_disk\_image
-  win\_dns\_client
-  win\_domain
-  win\_domain\_controller
-  win\_domain\_membership
-  win\_find
-  win\_msg
-  win\_path
-  win\_psexec
-  win\_reg\_stat
-  win\_region
-  win\_say
-  win\_shortcut
-  win\_tempfile
-  xbps
-  zfs:
-  zfs\_facts
-  zpool\_facts

New Callbacks:
^^^^^^^^^^^^^^

-  dense: minimal stdout output with fallback to default when verbose

New: lookups
^^^^^^^^^^^^

-  keyring: allows getting password from system keyrings

New: cache
^^^^^^^^^^

-  pickle (uses python's own serializer)
-  yaml

2.2.1 "The Battle of Evermore" - 2017-01-16
-------------------------------------------

Major Changes:
~~~~~~~~~~~~~~

-  Security fix for CVE-2016-9587 - An attacker with control over a
   client system being managed by Ansible and the ability to send facts
   back to the Ansible server could use this flaw to execute arbitrary
   code on the Ansible server as the user and group Ansible is running
   as.

Minor Changes:
~~~~~~~~~~~~~~

-  Fixes a bug where undefined variables in with\_\* loops would cause a
   task failure even if the when condition would cause the task to be
   skipped.
-  Fixed a bug related to roles where in certain situations a role may
   be run more than once despite not allowing duplicates.
-  Fixed some additional bugs related to atomic\_move for modules.
-  Fixes multiple bugs related to field/attribute inheritance in nested
   blocks and includes, as well as task iteration logic during failures.
-  Fixed pip installing packages into virtualenvs using the system pip
   instead of the virtualenv pip.
-  Fixed dnf on systems with dnf-2.0.x (some changes in the API).
-  Fixed traceback with dnf install of groups.
-  Fixes a bug in which include\_vars was not working with failed\_when.
-  Fix for include\_vars only loading files with .yml, .yaml, and .json
   extensions. This was only supposed to apply to loading a directory of
   vars files.
-  Fixes several bugs related to properly incrementing the failed count
   in the host statistics.
-  Fixes a bug with listening handlers which did not specify a ``name``
   field.
-  Fixes a bug with the ``play_hosts`` internal variable, so that it
   properly reflects the current list of hosts.
-  Fixes a bug related to the v2\_playbook\_on\_start callback method
   and legacy (v1) plugins.
-  Fixes an openssh related process exit race condition, related to the
   fact that connections using ControlPersist do not close stderr.
-  Improvements and fixes to OpenBSD fact gathering.
-  Updated ``make deb`` to use pbuilder. Use ``make local_deb`` for the
   previous non-pbuilder build.
-  Fixed Windows async to avoid blocking due to handle inheritance.
-  Fixed bugs in the mount module on older Linux kernels and \*BSDs
-  Various minor fixes for Python 3
-  Inserted some checks for jinja2-2.9, which can cause some issues with
   Ansible currently.

2.2 "The Battle of Evermore" - 2016-11-01
-----------------------------------------

Major Changes:
~~~~~~~~~~~~~~

-  Added the ``listen`` feature for modules. This feature allows tasks
   to more easily notify multiple handlers, as well as making it easier
   for handlers from decoupled roles to be notified.
-  Major performance improvements.
-  Added support for binary modules
-  Added the ability to specify serial batches as a list
   (``serial: [1, 5, 10]``), which allows for so-called "canary" actions
   in one play.
-  Fixed 'local type' plugins and actions to have a more predictable
   relative path. Fixes a regression of 1.9 (PR #16805). Existing users
   of 2.x will need to adjust related tasks.
-  ``meta`` tasks can now use conditionals.
-  ``raw`` now returns ``changed: true`` to be consistent with
   shell/command/script modules. Add ``changed_when: false`` to ``raw``
   tasks to restore the pre-2.2 behavior if necessary.
-  New privilege escalation become method ``ksu``
-  Windows ``async:`` support for long-running or background tasks.
-  Windows ``environment:`` support for setting module environment vars
   in play/task.
-  Added a new ``meta`` option: ``end_play``, which can be used to skip
   to the end of a play.
-  roles can now be included in the middle of a task list via the new
   ``include_role`` module, this also allows for making the role import
   'loopable' and/or conditional.
-  The service module has been changed to use system specific modules if
   they exist and fall back to the old service module if they cannot be
   found or detected.
-  Add ability to specify what ssh client binary to use on the
   controller. This can be configured via ssh\_executable in the ansible
   config file or by setting ansible\_ssh\_executable as an inventory
   variable if different ones are needed for different hosts.
-  Windows:
-  several facts were modified or renamed for consistency with their
   Unix counterparts, and many new facts were added. If your playbooks
   rely on any of the following keys, please ensure they are using the
   correct key names and/or values:

   -  ansible\_date\_time.date (changed to use yyyy-mm-dd format instead
      of default system-locale format)
   -  ansible\_date\_time.iso8601 (changed to UTC instead of local time)
   -  ansible\_distribution (now uses OS caption string, e.g.:
      "Microsoft Windows Server 2012 R2 Standard", version is still
      available on ansible\_distribution\_version)
   -  ansible\_totalmem (renamed to ansible\_memtotal\_mb, units changed
      to MB instead of bytes)

-  ``async:`` support for long-running or background tasks.
-  ``environment:`` support for setting module environment vars in
   play/task.
-  Tech Preview: Work has been done to get Ansible running under
   Python3. This work is not complete enough to depend upon in
   production environments but it is enough to begin testing it.
-  Most of the controller side should now work. Users should be able to
   run python3 /usr/bin/ansible and python3 /usr/bin/ansible-playbook
   and have core features of ansible work.
-  A few of the most essential modules have been audited and are known
   to work. Others work out of the box.
-  We are using unit and integration tests to help us port code and not
   regress later. Even if you are not familiar with python you can still
   help by contributing integration tests (just ansible roles) that
   exercise more of the code to make sure it continues to run on both
   Python2 and Python3.
-  scp\_if\_ssh now supports True, False and "smart". "smart" is the
   default and will retry failed sftp transfers with scp.
-  Network:
-  Refactored all network modules to remove duplicate code and take
   advantage of Ansiballz implementation
-  All functionality from \*\_template network modules have been
   combined into \*\_config module
-  Network \*\_command modules not longer allow configuration mode
   statements

New Modules:
^^^^^^^^^^^^

-  apache2\_mod\_proxy
-  asa
-  asa\_acl
-  asa\_command
-  asa\_config
-  atomic
-  atomic\_host
-  atomic\_image
-  aws
-  cloudformation\_facts
-  ec2\_asg\_facts
-  ec2\_customer\_gateway
-  ec2\_lc\_find
-  ec2\_vpc\_dhcp\_options\_facts
-  ec2\_vpc\_nacl
-  ec2\_vpc\_nacl\_facts
-  ec2\_vpc\_nat\_gateway
-  ec2\_vpc\_peer
-  ec2\_vpc\_vgw
-  efs
-  efs\_facts
-  execute\_lambda
-  iam\_mfa\_device\_facts
-  iam\_server\_certificate\_facts
-  kinesis\_stream
-  lambda
-  lambda\_alias
-  lambda\_event
-  lambda\_facts
-  redshift
-  redshift\_subnet\_group
-  s3\_website
-  sts\_session\_token
-  cloudstack
-  cs\_router
-  cs\_snapshot\_policy
-  dellos6
-  dellos6\_command
-  dellos6\_config
-  dellos6\_facts
-  dellos9
-  dellos9\_command
-  dellos9\_config
-  dellos9\_facts
-  dellos10
-  dellos10\_command
-  dellos10\_config
-  dellos10\_facts
-  digital\_ocean\_block\_storage
-  docker
-  docker\_network
-  eos
-  eos\_facts
-  exoscale:
-  exo\_dns\_domain
-  exo\_dns\_record
-  f5:
-  bigip\_device\_dns
-  bigip\_device\_ntp
-  bigip\_device\_sshd
-  bigip\_gtm\_datacenter
-  bigip\_gtm\_virtual\_server
-  bigip\_irule
-  bigip\_routedomain
-  bigip\_selfip
-  bigip\_ssl\_certificate
-  bigip\_sys\_db
-  bigip\_vlan
-  github
-  github\_key
-  github\_release
-  google
-  gcdns\_record
-  gcdns\_zone
-  gce\_mig
-  honeybadger\_deployment
-  illumos
-  dladm\_etherstub
-  dladm\_vnic
-  flowadm
-  ipadm\_if
-  ipadm\_prop
-  ipmi
-  ipmi\_boot
-  ipmi\_power
-  ios
-  ios\_facts
-  iosxr
-  iosxr\_facts
-  include\_role
-  jenkins
-  jenkins\_job
-  jenkins\_plugin
-  kibana\_plugin
-  letsencrypt
-  logicmonitor
-  logicmonitor\_facts
-  lxd
-  lxd\_profile
-  lxd\_container
-  netapp
-  netapp\_e\_amg
-  netapp\_e\_amg\_role
-  netapp\_e\_amg\_sync
-  netapp\_e\_auth
-  netapp\_e\_facts
-  netapp\_e\_flashcache
-  netapp\_e\_hostgroup
-  netapp\_e\_host
-  netapp\_e\_lun\_mapping
-  netapp\_e\_snapshot\_group
-  netapp\_e\_snapshot\_images
-  netapp\_e\_snapshot\_volume
-  netapp\_e\_storage\_system
-  netapp\_e\_storagepool
-  netapp\_e\_volume
-  netapp\_e\_volume\_copy
-  netconf\_config
-  netvisor
-  pn\_cluster
-  pn\_ospfarea
-  pn\_ospf
-  pn\_show
-  pn\_trunk
-  pn\_vlag
-  pn\_vlan
-  pn\_vrouterbgp
-  pn\_vrouterif
-  pn\_vrouterlbif
-  pn\_vrouter
-  nxos
-  nxos\_aaa\_server\_host
-  nxos\_aaa\_server
-  nxos\_acl\_interface
-  nxos\_acl
-  nxos\_bgp\_af
-  nxos\_bgp\_neighbor\_af
-  nxos\_bgp\_neighbor
-  nxos\_bgp
-  nxos\_evpn\_global
-  nxos\_evpn\_vni
-  nxos\_file\_copy
-  nxos\_gir\_profile\_management
-  nxos\_gir
-  nxos\_hsrp
-  nxos\_igmp\_interface
-  nxos\_igmp
-  nxos\_igmp\_snooping
-  nxos\_install\_os
-  nxos\_interface\_ospf
-  nxos\_mtu
-  nxos\_ntp\_auth
-  nxos\_ntp\_options
-  nxos\_ntp
-  nxos\_ospf
-  nxos\_ospf\_vrf
-  nxos\_overlay\_global
-  nxos\_pim\_interface
-  nxos\_pim
-  nxos\_pim\_rp\_address
-  nxos\_portchannel
-  nxos\_rollback
-  nxos\_smu
-  nxos\_snapshot
-  nxos\_snmp\_community
-  nxos\_snmp\_contact
-  nxos\_snmp\_host
-  nxos\_snmp\_location
-  nxos\_snmp\_traps
-  nxos\_snmp\_user
-  nxos\_static\_route
-  nxos\_udld\_interface
-  nxos\_udld
-  nxos\_vpc\_interface
-  nxos\_vpc
-  nxos\_vrf\_af
-  nxos\_vtp\_domain
-  nxos\_vtp\_password
-  nxos\_vtp\_version
-  nxos\_vxlan\_vtep
-  nxos\_vxlan\_vtep\_vni
-  mssql\_db
-  ovh\_ip\_loadbalancing\_backend
-  opendj\_backendprop
-  openstack
-  os\_keystone\_service
-  os\_recordset
-  os\_server\_group
-  os\_stack
-  os\_zone
-  ovirt
-  ovirt\_auth
-  ovirt\_disks
-  ovirt\_vms
-  rhevm
-  rocketchat
-  sefcontext
-  sensu\_subscription
-  smartos
-  smartos\_image\_facts
-  sros
-  sros\_command
-  sros\_config
-  sros\_rollback
-  statusio\_maintenance
-  systemd
-  telegram
-  univention
-  udm\_dns\_record
-  udm\_dns\_zone
-  udm\_group
-  udm\_share
-  udm\_user
-  vmware
-  vmware\_guest
-  vmware\_local\_user\_manager
-  vmware\_vmotion
-  vyos
-  vyos\_command
-  vyos\_config
-  vyos\_facts
-  wakeonlan
-  windows
-  win\_command
-  win\_robocopy
-  win\_shell

New Callbacks:
^^^^^^^^^^^^^^

-  foreman

Minor Changes:
~~~~~~~~~~~~~~

-  now -vvv shows exact path from which 'currently executing module' was
   picked up from.
-  loop\_control now has a label option to allow fine grained control
   what gets displayed per item
-  loop\_control now has a pause option to allow pausing for N seconds
   between loop iterations of a task.
-  New privilege escalation become method ``ksu``
-  ``raw`` now returns ``changed: true`` to be consistent with
   shell/command/script modules. Add ``changed_when: false`` to ``raw``
   tasks to restore the pre-2.2 behavior if necessary.
-  removed previously deprecated ';' as host list separator.
-  Only check if the default ssh client supports ControlPersist once
   instead of once for each host + task combination.
-  Fix a problem with the pip module updating the python pip package
   itself.
-  ansible\_play\_hosts is a new magic variable to provide a list of
   hosts in scope for the current play. Unlike play\_hosts it is not
   subject to the 'serial' keyword.
-  ansible\_play\_batch is a new magic variable meant to substitute the
   current play\_hosts.

For custom front ends using the API:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ansible.parsing.vault:
-  VaultLib.is\_encrypted() has been deprecated. It will be removed in
   2.4. Use ansible.parsing.vault.is\_encrypted() instead
-  VaultFile has been removed. This unfinished code was never used
   inside of Ansible. The feature it was intended to support has now
   been implemented without using this.
-  VaultAES, the older, insecure encrypted format that debuted in
   Ansible-1.5 and was replaced by VaultAES256 less than a week later,
   now has a deprecation warning. **It will be removed in 2.3**. In the
   unlikely event that you wrote a vault file in that 1 week window and
   have never modified the file since (ansible-vault automatically
   re-encrypts the file using VaultAES256 whenever it is written to but
   not read), run ``ansible-vault rekey [filename]`` to move to
   VaultAES256.

Removed Deprecated:
~~~~~~~~~~~~~~~~~~~

-  ';' as host list separator.
-  with\_ 'bare variable' handling, now loop items must always be
   templated ``{{ }}`` or they will be considered as plain strings.
-  skipping task on 'missing attribute' in loop variable, now in a loop
   an undefined attribute will return an error instead of skipping the
   task.
-  skipping on undefined variables in loop, now loops will have to
   define a variable or use ``|default`` to avoid errors.

Deprecations
~~~~~~~~~~~~

Notice given that the following will be removed in Ansible 2.4: \*
Modules \* eos\_template \* ios\_template \* iosxr\_template \*
junos\_template \* nxos\_template \* ops\_template

2.1.4 "The Song Remains the Same" - 2017-01-16
----------------------------------------------

-  Security fix for CVE-2016-9587 - An attacker with control over a
   client system being managed by Ansible and the ability to send facts
   back to the Ansible server could use this flaw to execute arbitrary
   code on the Ansible server as the user and group Ansible is running
   as.
-  Fixed a bug with conditionals in loops, where undefined variables and
   other errors will defer raising the error until the conditional has
   been evaluated.
-  Added a version check for jinja2-2.9, which does not fully work with
   Ansible currently.

2.1.3 "The Song Remains the Same" - 2016-11-04
----------------------------------------------

-  Security fix for CVE-2016-8628 - Command injection by compromised
   server via fact variables. In some situations, facts returned by
   modules could overwrite connection-based facts or some other special
   variables, leading to injected commands running on the Ansible
   controller as the user running Ansible (or via escalated
   permissions).
-  Security fix for CVE-2016-8614 - apt\_key module not properly
   validating keys in some situations.

Minor Changes:
~~~~~~~~~~~~~~

-  The subversion module from core now marks its password parameter as
   no\_log so the password is obscured when logging.
-  The postgresql\_lang and postgresql\_ext modules from extras now mark
   login\_password as no\_log so the password is obscured when logging.
-  Fixed several bugs related to locating files relative to
   role/playbook directories.
-  Fixed a bug in the way hosts were tested for failed states, resulting
   in incorrectly skipped block sessions.
-  Fixed a bug in the way our custom JSON encoder is used for the
   to\_json\* filters.
-  Fixed some bugs related to the use of non-ascii characters in become
   passwords.
-  Fixed a bug with Azure modules which may be using the latest rc6
   library.
-  Backported some docker\_common fixes.

2.1.2 "The Song Remains the Same" - 2016-09-29
----------------------------------------------

Minor Changes:
~~~~~~~~~~~~~~

-  Fixed a bug related to creation of retry files (#17456)
-  Fixed a bug in the way include params are used when an include task
   is dynamic (#17064)
-  Fixed a bug related to including blocks in an include task (#15963)
-  Fixed a bug related to the use of hostvars internally when creating
   the connection plugin. This prevents things like variables using
   lookups from being evaluated unnecessarily (#17024)
-  Fixed a bug where using a variable containing a list for the
   ``hosts`` of a play resulted in an list of lists (#16583)
-  Fixed a bug where integer values would cause an error if a module
   param was of type ``float`` (no issue)
-  Fixed a bug with net\_template failing if src was not specified
   (#17726)
-  Fixed a bug in "ansible-galaxy import" (#17417)
-  Fixed a bug in which INI files incorrectly treated a hosts range as a
   section header (#15331)
-  Fixed a bug in which the max\_fail\_percentage calculation
   erroneously caused a series of plays to stop executing (#15954)
-  Fixed a bug in which the task names were not properly templated
   (#16295)
-  Fixed a bug causing "squashed" loops (ie. yum, apt) to incorrectly
   report results (ansible-modules-core#4214)
-  Fixed several bugs related to includes:
-  when including statically, make sure that all parents were also
   included statically (issue #16990)
-  properly resolve nested static include paths
-  print a message when a file is statically included
-  Fixed a bug in which module params expected to be float types were
   not converted from integers (only strings) (#17325)
-  Fixed a bug introduced by static includes in 2.1, which prevented
   notifications from going to the "top level" handler name.
-  Fixed a bug where a group\_vars or host\_vars directory in the
   current working directory would be used (and would take precedence)
   over those in the inventory and/or playbook directory.
-  Fixed a bug which could occur when the result of an async task did
   not parse as valid JSON.
-  (re)-allowed the use of ansible\_python\_interpreter lines with more
   than one argument.
-  Fixed several bugs related to the creation of the implicit localhost
   in inventory.
-  Fixed a bug related to an unspecified number of retries when using
   until.
-  Fixed a race-condition bug when creating temp directories before the
   worker process is forked.
-  Fix a bug with async's poll keyword not making use of
   ansible\_python\_interpreter to run (and thus breaking when
   /usr/bin/python is not present on the remote machine.)
-  Fix a bug where hosts that started with a range in inventory were
   being treated as an invalid section header.

Module fixes: \* Fixed a bug where the temporary CA files created by the
module helper code were not being deleted properly in some situations
(#17073) \* Fixed many bugs in the unarchive module \* Fixes for module
ec2: - Fixed a bug related to source\_dest\_check when used with non-vpc
instances (core#3243) - Fixed a bug in ec2 where instances were not
powering of when referenced via tags only (core#4765) - Fixed a bug
where instances with multiple interfaces were not powering up/down
correctly (core#3234) \* Fixes for module get\_url: - Fixed a bug in
get\_url module to force a download if there is a checksum mismatch
regardless of the last modified time (core#4262) - Fixed a bug in
get\_url module to properly process FTP results (core#3661 and
core#4601) \* Fixed a bug in win\_user related to users with disabled
accounts/expired passwords (core#4369) \* ini\_file: - Fixed a bug where
option lines are now inserted before blank lines. - Fixed a bug where
leading whitespace prevented matches on options. \* Fixed a bug in
iam\_cert when dup\_ok is used as a string. \* Fixed a bug in
postgresql\_db related to the changed logic when state=absent. \* Fixed
a bug where single\_transaction and quick were not passed into db\_dump
for the mysql\_db module. \* Fixed a bug where the fetch module was not
idempotent when retrieving the target of a symlink. \* Many minor fixes
for bugs in extras modules.

Deprecations:
~~~~~~~~~~~~~

-  Deprecated the use of ``_fixup_perms``. Use ``_fixup_perms2``
   instead. This change only impacts custom action plugins using
   ``_fixup_perms``.

Incompatible Changes:
~~~~~~~~~~~~~~~~~~~~~

-  Use of ``_fixup_perms`` with ``recursive=True`` (the default) is no
   longer supported. Custom action plugins using ``_fixup_perms`` will
   require changes unless they already use ``recursive=False``. Use
   ``_fixup_perms2`` if support for previous releases is not required.
   Otherwise use ``_fixup_perms`` with ``recursive=False``.

2.1 "The Song Remains the Same"
-------------------------------

Major Changes:
~~~~~~~~~~~~~~

-  Official support for the networking modules, originally available in
   2.0 as a tech preview.
-  Refactored and expanded support for Docker with new modules and many
   improvements to existing modules, as well as a new Kubernetes module.
-  Added new modules for Azure (see below for the full list)
-  Added the ability to specify includes as "static" (either through a
   configuration option or on a per-include basis). When includes are
   static, they are loaded at compile time and cannot contain dynamic
   features like loops.
-  Added a new strategy ``debug``, which allows per-task debugging of
   playbooks, for more details see
   https://docs.ansible.com/ansible/playbooks\_debugger.html
-  Added a new option for tasks: ``loop_control``. This currently only
   supports one option - ``loop_var``, which allows a different loop
   variable from ``item`` to be used.
-  Added the ability to filter facts returned by the fact gathering
   setup step using the ``gather_subset`` option on the play or in the
   ansible.cfg configuration file. See
   http://docs.ansible.com/ansible/intro\_configuration.html#gathering
   for details on the format of the option.
-  Added the ability to send per-item callbacks, rather than a batch
   update (this more closely resembles the behavior of Ansible 1.x).
-  Added facility for modules to send back 'diff' for display when
   ansible is called with --diff, updated several modules to return this
   info
-  Added ansible-console tool, a REPL shell that allows running adhoc
   tasks against a chosen inventory (based on
   https://github.com/dominis/ansible-shell)
-  Added two new variables, which are set when the ``rescue`` portion of
   a ``block`` is started:
-  ``ansible_failed_task``, which contains the serialized version of the
   failed task.
-  ``ansible_failed_result``, which contains the result of the failed
   task.
-  New meta action, ``meta: clear_host_errors`` which will clear any
   hosts which were marked as failed (but not unreachable hosts).
-  New meta action, ``meta: clear_facts`` which will remove existing
   facts for the current host from current memory and facts cache.
-  copy module can now transparently use a vaulted file as source, if
   vault passwords were provided it will decrypt and copy on the fly.
-  The way new-style python modules (which include all of the
   non-windows modules shipped with Ansible) are assembled before
   execution on the remote machine has been changed. The new way stays
   closer to how python imports modules which will make it easier to
   write modules which rely heavily on shared code.
-  Reduce the situations in which a module can end up as world readable.
   For details, see:
   https://docs.ansible.com/ansible/become.html#becoming-an-unprivileged-user
-  Re-implemented the retry file feature, which had been left out of 2.0
   (fix was backported to 2.0.1 originally).
-  Improved winrm argument validation and feature sniffing (for upcoming
   pywinrm NTLM support).
-  Improved winrm error handling: basic parsing of stderr from CLIXML
   stream.

New Modules:
^^^^^^^^^^^^

-  aws
-  ec2\_vol\_facts
-  ec2\_vpc\_dhcp\_options
-  ec2\_vpc\_net\_facts
-  ec2\_snapshot\_facts
-  azure:
-  azure\_rm\_deployment
-  azure\_rm\_networkinterface
-  azure\_rm\_networkinterface\_facts (TECH PREVIEW)
-  azure\_rm\_publicipaddress
-  azure\_rm\_publicipaddress\_facts (TECH PREVIEW)
-  azure\_rm\_resourcegroup
-  azure\_rm\_resourcegroup\_facts (TECH PREVIEW)
-  azure\_rm\_securitygroup
-  azure\_rm\_securitygroup\_facts (TECH PREVIEW)
-  azure\_rm\_storageaccount
-  azure\_rm\_storageaccount\_facts (TECH PREVIEW)
-  azure\_rm\_storageblob
-  azure\_rm\_subnet
-  azure\_rm\_virtualmachine
-  azure\_rm\_virtualmachineimage\_facts (TECH PREVIEW)
-  azure\_rm\_virtualnetwork
-  azure\_rm\_virtualnetwork\_facts (TECH PREVIEW)
-  cloudflare\_dns
-  cloudstack
-  cs\_cluster
-  cs\_configuration
-  cs\_instance\_facts
-  cs\_pod
-  cs\_resourcelimit
-  cs\_volume
-  cs\_zone
-  cs\_zone\_facts
-  clustering
-  kubernetes
-  cumulus
-  cl\_bond
-  cl\_bridge
-  cl\_img\_install
-  cl\_interface
-  cl\_interface\_policy
-  cl\_license
-  cl\_ports
-  eos
-  eos\_command
-  eos\_config
-  eos\_eapi
-  eos\_template
-  gitlab
-  gitlab\_group
-  gitlab\_project
-  gitlab\_user
-  ios
-  ios\_command
-  ios\_config
-  ios\_template
-  iosxr
-  iosxr\_command
-  iosxr\_config
-  iosxr\_template
-  junos
-  junos\_command
-  junos\_config
-  junos\_facts
-  junos\_netconf
-  junos\_package
-  junos\_template
-  make
-  mongodb\_parameter
-  nxos
-  nxos\_command
-  nxos\_config
-  nxos\_facts
-  nxos\_feature
-  nxos\_interface
-  nxos\_ip\_interface
-  nxos\_nxapi
-  nxos\_ping
-  nxos\_switchport
-  nxos\_template
-  nxos\_vlan
-  nxos\_vrf
-  nxos\_vrf\_interface
-  nxos\_vrrp
-  openstack
-  os\_flavor\_facts
-  os\_group
-  os\_ironic\_inspect
-  os\_keystone\_domain\_facts
-  os\_keystone\_role
-  os\_port\_facts
-  os\_project\_facts
-  os\_user\_facts
-  os\_user\_role
-  openswitch
-  ops\_command
-  ops\_config
-  ops\_facts
-  ops\_template
-  softlayer
-  sl\_vm
-  vmware
-  vmware\_maintenancemode
-  vmware\_vm\_shell
-  windows
-  win\_acl\_inheritance
-  win\_owner
-  win\_reboot
-  win\_regmerge
-  win\_timezone
-  yum\_repository

New Strategies:
^^^^^^^^^^^^^^^

-  debug

New Filters:
^^^^^^^^^^^^

-  extract
-  ip4\_hex
-  regex\_search
-  regex\_findall

New Callbacks:
^^^^^^^^^^^^^^

-  actionable (only shows changed and failed)
-  slack
-  json

New Tests:
^^^^^^^^^^

-  issubset
-  issuperset

New Inventory scripts:
^^^^^^^^^^^^^^^^^^^^^^

-  brook
-  rackhd
-  azure\_rm

Minor Changes:
~~~~~~~~~~~~~~

-  Added support for pipelining mode to more connection plugins, which
   helps prevent module data from being written to disk.
-  Added a new '!unsafe' YAML decorator, which can be used in playbooks
   to ensure a string is not templated. For example:
   ``foo: !unsafe "Don't template {{me}}"``.
-  Callbacks now have access to the options with which the CLI was
   called
-  Debug now has verbosity option to control when to display by matching
   number of -v in command line
-  Modules now get verbosity, diff and other flags as passed to ansible
-  Mount facts now also show 'network mounts' that use the pattern
   ``<host>:/<mount>``
-  Plugins are now sorted before loading. This means, for instance, if
   you want two custom callback plugins to run in a certain order you
   can name them 10-first-callback.py and 20-second-callback.py.
-  Added (alpha) Centirfy's dzdo as another become meethod (privilege
   escalation)

Deprecations:
~~~~~~~~~~~~~

-  Deprecated the use of "bare" variables in loops (ie.
   ``with_items: foo``, where ``foo`` is a variable). The full jinja2
   variable syntax of ``{{foo}}`` should always be used instead. This
   warning will be removed completely in 2.3, after which time it will
   be an error.
-  play\_hosts magic variable, use ansible\_play\_batch or
   ansible\_play\_hosts instead.

2.0.2 "Over the Hills and Far Away"
-----------------------------------

-  Backport of the 2.1 feature to ensure per-item callbacks are sent as
   they occur, rather than all at once at the end of the task.
-  Fixed bugs related to the iteration of tasks when certain
   combinations of roles, blocks, and includes were used, especially
   when handling errors in rescue/always portions of blocks.
-  Fixed handling of redirects in our helper code, and ported the uri
   module to use this helper code. This removes the httplib dependency
   for this module while fixing some bugs related to redirects and SSL
   certs.
-  Fixed some bugs related to the incorrect creation of extra temp
   directories for uploading files, which were not cleaned up properly.
-  Improved error reporting in certain situations, to provide more
   information such as the playbook file/line.
-  Fixed a bug related to the variable precedence of role parameters,
   especially when a role may be used both as a dependency of a role and
   directly by itself within the same play.
-  Fixed some bugs in the 2.0 implementation of do/until.
-  Fixed some bugs related to run\_once:
-  Ensure that all hosts are marked as failed if a task marked as
   run\_once fails.
-  Show a warning when using the free strategy when a run\_once task is
   encountered, as there is no way for the free strategy to guarantee
   the task is not run more than once.
-  Fixed a bug where the assemble module was not honoring check mode in
   some situations.
-  Fixed a bug related to delegate\_to, where we were incorrectly using
   variables from the inventory host rather than the delegated-to host.
-  The 'package' meta-module now properly squashes items down to a
   single execution (as the apt/yum/other package modules do).
-  Fixed a bug related to the ansible-galaxy CLI command dealing with
   paged results from the Galaxy server.
-  Pipelining support is now available for the local and jail connection
   plugins, which is useful for users who do not wish to have temp
   files/directories created when running tasks with these connection
   types.
-  Improvements in support for additional shell types.
-  Improvements in the code which is used to calculate checksums for
   remote files.
-  Some speed ups and bug fixes related to the variable merging code.
-  Workaround bug in python subprocess on El Capitan that was making
   vault fail when attempting to encrypt a file
-  Fix lxc\_container module having predictable temp file names and
   setting file permissions on the temporary file too leniently on a
   temporary file that was executed as a script. Addresses CVE-2016-3096
-  Fix a bug in the uri module where setting headers via module params
   that start with HEADER\_ were causing a traceback.
-  Fix bug in the free strategy that was causing it to synchronize its
   workers after every task (making it a lot more like linear than it
   should have been).

2.0.1 "Over the Hills and Far Away"
-----------------------------------

-  Fixes a major compatibility break in the synchronize module shipped
   with 2.0.0.x. That version of synchronize ran sudo on the controller
   prior to running rsync. In 1.9.x and previous, sudo was run on the
   host that rsync connected to. 2.0.1 restores the 1.9.x behaviour.
-  Additionally, several other problems with where synchronize chose to
   run when combined with delegate\_to were fixed. In particular, if a
   playbook targetted localhost and then delegated\_to a remote host the
   prior behavior (in 1.9.x and 2.0.0.x) was to copy files between the
   src and destination directories on the delegated host. This has now
   been fixed to copy between localhost and the delegated host.
-  Fix a regression where synchronize was unable to deal with unicode
   paths.
-  Fix a regression where synchronize deals with inventory hosts that
   use localhost but with an alternate port.
-  Fixes a regression where the retry files feature was not implemented.
-  Fixes a regression where the any\_errors\_fatal option was
   implemented in 2.0 incorrectly, and also adds a feature where
   any\_errors\_fatal can be set at the block level.
-  Fix tracebacks when playbooks or ansible itself were located in
   directories with unicode characters.
-  Fix bug when sending unicode characters to an external pager for
   display.
-  Fix a bug with squashing loops for special modules (mostly package
   managers). The optimization was squashing when the loop did not apply
   to the selection of packages. This has now been fixed.
-  Temp files created when using vault are now "shredded" using the unix
   shred program which overwrites the file with random data.
-  Some fixes to cloudstack modules for case sensitivity
-  Fix non-newstyle modules (non-python modules and old-style modules)
   to disabled pipelining.
-  Fix fetch module failing even if fail\_on\_missing is set to False
-  Fix for cornercase when local connections, sudo, and raw were used
   together.
-  Fix dnf module to remove dependent packages when state=absent is
   specified. This was a feature of the 1.9.x version that was left out
   by mistake when the module was rewritten for 2.0.
-  Fix bugs with non-english locales in yum, git, and apt modules
-  Fix a bug with the dnf module where state=latest could only upgrade,
   not install.
-  Fix to make implicit fact gathering task correctly inherit settings
   from play, this might cause an error if settings environment on play
   depending on 'ansible\_env' which was previouslly ignored

2.0 "Over the Hills and Far Away" - Jan 12, 2016
------------------------------------------------

Major Changes:
~~~~~~~~~~~~~~

-  Releases are now named after Led Zeppelin songs, 1.9 will be the last
   Van Halen named release.
-  The new block/rescue/always directives allow for making task blocks
   and exception-like semantics
-  New strategy plugins (e.g. ``free``) allow control over the flow of
   task execution per play. The default (``linear``) will be the same as
   before.
-  Improved error handling, with more detailed parser messages. General
   exception handling and display has been revamped.
-  Task includes are now evaluated during execution, allowing more
   dynamic includes and options. Play includes are unchanged both still
   use the ``include`` directive.
-  "with\_" loops can now be used with task includes since they are
   dynamic.
-  Callback, connection, cache and lookup plugin APIs have changed.
   Existing plugins might require modification to work with the new
   versions.
-  Callbacks are now shipped in the active directory and don't need to
   be copied, just whitelisted in ansible.cfg.
-  Many API changes. Those integrating directly with Ansible's API will
   encounter breaking changes, but the new API is much easier to use and
   test.
-  Settings are now more inheritable; what you set at play, block or
   role will be automatically inherited by the contained tasks. This
   allows for new features to automatically be settable at all levels,
   previously we had to manually code this.
-  Vars are now settable at play, block, role and task level with the
   ``vars`` directive and scoped to the tasks contained.
-  Template code now retains types for bools and numbers instead of
   turning them into strings. If you need the old behaviour, quote the
   value and it will get passed around as a string
-  Empty variables and variables set to null in yaml will no longer be
   converted to empty strings. They will retain the value of ``None``.
   To go back to the old behaviour, you can override the
   ``null_representation`` setting to an empty string in your config
   file or by setting the ``ANSIBLE_NULL_REPRESENTATION`` environment
   variable.
-  Added ``meta: refresh_inventory`` to force rereading the inventory in
   a play. This re-executes inventory scripts, but does not force them
   to ignore any cache they might use.
-  New delegate\_facts directive, a boolean that allows you to apply
   facts to the delegated host (true/yes) instead of the
   inventory\_hostname (no/false) which is the default and previous
   behaviour.
-  local connections now work with 'su' as a privilege escalation method
-  Ansible 2.0 has deprecated the “ssh” from ansible\_ssh\_user,
   ansible\_ssh\_host, and ansible\_ssh\_port to become ansible\_user,
   ansible\_host, and ansible\_port.
-  New ssh configuration variables (``ansible_ssh_common_args``,
   ``ansible_ssh_extra_args``) can be used to configure a per-group or
   per-host ssh ProxyCommand or set any other ssh options.
   ``ansible_ssh_extra_args`` is used to set options that are accepted
   only by ssh (not sftp or scp, which have their own analogous
   settings).
-  ansible-pull can now verify the code it runs when using git as a
   source repository, using git's code signing and verification
   features.
-  Backslashes used when specifying parameters in jinja2 expressions in
   YAML dicts sometimes needed to be escaped twice. This has been fixed
   so that escaping once works. Here's an example of how playbooks need
   to be modified:

   ::

       # Syntax in 1.9.x
       - debug:
           msg: "{{ 'test1_junk 1\\\\3' | regex_replace('(.*)_junk (.*)', '\\\\1 \\\\2') }}"
       # Syntax in 2.0.x
       - debug:
           msg: "{{ 'test1_junk 1\\3' | regex_replace('(.*)_junk (.*)', '\\1 \\2') }}"

       # Output:
       "msg": "test1 1\\3"

-  When a string with a trailing newline was specified in the playbook
   via yaml dict format, the trailing newline was stripped. When
   specified in key=value format the trailing newlines were kept. In v2,
   both methods of specifying the string will keep the trailing
   newlines. If you relied on the trailing newline being stripped you
   can change your playbook like this:

   ::

       # Syntax in 1.9.2
       vars:
         message: >
           Testing
           some things
       tasks:
       - debug:
           msg: "{{ message }}"

       # Syntax in 2.0.x
       vars:
         old_message: >
           Testing
           some things
         message: "{{ old_messsage[:-1] }}"
       - debug:
           msg: "{{ message }}"
       # Output
       "msg": "Testing some things"

-  When specifying complex args as a variable, the variable must use the
   full jinja2 variable syntax ('{{var\_name}}') - bare variable names
   there are no longer accepted. In fact, even specifying args with
   variables has been deprecated, and will not be allowed in future
   versions:

   ::

       ---
       - hosts: localhost
         connection: local
         gather_facts: false
         vars:
           my_dirs:
             - { path: /tmp/3a, state: directory, mode: 0755 }
             - { path: /tmp/3b, state: directory, mode: 0700 }
         tasks:
           - file:
             args: "{{item}}"
             with_items: my_dirs

Plugins
~~~~~~~

-  Rewritten dnf module that should be faster and less prone to
   encountering bugs in cornercases
-  WinRM connection plugin passes all vars named ``ansible_winrm_*`` to
   the underlying pywinrm client. This allows, for instance,
   ``ansible_winrm_server_cert_validation=ignore`` to be used with newer
   versions of pywinrm to disable certificate validation on Python
   2.7.9+.
-  WinRM connection plugin put\_file is significantly faster and no
   longer has file size limitations.

Deprecated Modules (new ones in parens):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  ec2\_ami\_search (ec2\_ami\_find)
-  quantum\_network (os\_network)
-  glance\_image
-  nova\_compute (os\_server)
-  quantum\_floating\_ip (os\_floating\_ip)
-  quantum\_router (os\_router)
-  quantum\_router\_gateway (os\_router)
-  quantum\_router\_interface (os\_router)

New Modules:
^^^^^^^^^^^^

-  amazon
-  ec2\_ami\_copy
-  ec2\_ami\_find
-  ec2\_elb\_facts
-  ec2\_eni
-  ec2\_eni\_facts
-  ec2\_remote\_facts
-  ec2\_vpc\_igw
-  ec2\_vpc\_net
-  ec2\_vpc\_net\_facts
-  ec2\_vpc\_route\_table
-  ec2\_vpc\_route\_table\_facts
-  ec2\_vpc\_subnet
-  ec2\_vpc\_subnet\_facts
-  ec2\_win\_password
-  ecs\_cluster
-  ecs\_task
-  ecs\_taskdefinition
-  elasticache\_subnet\_group\_facts
-  iam
-  iam\_cert
-  iam\_policy
-  route53\_facts
-  route53\_health\_check
-  route53\_zone
-  s3\_bucket
-  s3\_lifecycle
-  s3\_logging
-  sns\_topic
-  sqs\_queue
-  sts\_assume\_role
-  apk
-  bigip\_gtm\_wide\_ip
-  bundler
-  centurylink
-  clc\_aa\_policy
-  clc\_alert\_policy
-  clc\_blueprint\_package
-  clc\_firewall\_policy
-  clc\_group
-  clc\_loadbalancer
-  clc\_modify\_server
-  clc\_publicip
-  clc\_server
-  clc\_server\_snapshot
-  circonus\_annotation
-  consul
-  consul
-  consul\_acl
-  consul\_kv
-  consul\_session
-  cloudtrail
-  cloudstack
-  cs\_account
-  cs\_affinitygroup
-  cs\_domain
-  cs\_facts
-  cs\_firewall
-  cs\_iso
-  cs\_instance
-  cs\_instancegroup
-  cs\_ip\_address
-  cs\_loadbalancer\_rule
-  cs\_loadbalancer\_rule\_member
-  cs\_network
-  cs\_portforward
-  cs\_project
-  cs\_securitygroup
-  cs\_securitygroup\_rule
-  cs\_sshkeypair
-  cs\_staticnat
-  cs\_template
-  cs\_user
-  cs\_vmsnapshot
-  cronvar
-  datadog\_monitor
-  deploy\_helper
-  docker
-  docker\_login
-  dpkg\_selections
-  elasticsearch\_plugin
-  expect
-  find
-  google
-  gce\_tag
-  hall
-  ipify\_facts
-  iptables
-  libvirt
-  virt\_net
-  virt\_pool
-  maven\_artifact
-  openstack
-  os\_auth
-  os\_client\_config
-  os\_image
-  os\_image\_facts
-  os\_floating\_ip
-  os\_ironic
-  os\_ironic\_node
-  os\_keypair
-  os\_network
-  os\_network\_facts
-  os\_nova\_flavor
-  os\_object
-  os\_port
-  os\_project
-  os\_router
-  os\_security\_group
-  os\_security\_group\_rule
-  os\_server
-  os\_server\_actions
-  os\_server\_facts
-  os\_server\_volume
-  os\_subnet
-  os\_subnet\_facts
-  os\_user
-  os\_user\_group
-  os\_volume
-  openvswitch\_db
-  osx\_defaults
-  pagerduty\_alert
-  pam\_limits
-  pear
-  profitbricks
-  profitbricks
-  profitbricks\_datacenter
-  profitbricks\_nic
-  profitbricks\_snapshot
-  profitbricks\_volume
-  profitbricks\_volume\_attachments
-  proxmox
-  proxmox
-  proxmox\_template
-  puppet
-  pushover
-  pushbullet
-  rax
-  rax\_clb\_ssl
-  rax\_mon\_alarm
-  rax\_mon\_check
-  rax\_mon\_entity
-  rax\_mon\_notification
-  rax\_mon\_notification\_plan
-  rabbitmq
-  rabbitmq\_binding
-  rabbitmq\_exchange
-  rabbitmq\_queue
-  selinux\_permissive
-  sendgrid
-  sensu
-  sensu\_check
-  sensu\_subscription
-  seport
-  slackpkg
-  solaris\_zone
-  taiga\_issue
-  vertica
-  vertica\_configuration
-  vertica\_facts
-  vertica\_role
-  vertica\_schema
-  vertica\_user
-  vmware
-  vca\_fw
-  vca\_nat
-  vmware\_cluster
-  vmware\_datacenter
-  vmware\_dns\_config
-  vmware\_dvs\_host
-  vmware\_dvs\_portgroup
-  vmware\_dvswitch
-  vmware\_host
-  vmware\_migrate\_vmk
-  vmware\_portgroup
-  vmware\_target\_canonical\_facts
-  vmware\_vm\_facts
-  vmware\_vm\_vss\_dvs\_migrate
-  vmware\_vmkernel
-  vmware\_vmkernel\_ip\_config
-  vmware\_vsan\_cluster
-  vmware\_vswitch
-  vsphere\_copy
-  webfaction
-  webfaction\_app
-  webfaction\_db
-  webfaction\_domain
-  webfaction\_mailbox
-  webfaction\_site
-  windows
-  win\_acl
-  win\_dotnet\_ngen
-  win\_environment
-  win\_firewall\_rule
-  win\_iis\_virtualdirectory
-  win\_iis\_webapplication
-  win\_iis\_webapppool
-  win\_iis\_webbinding
-  win\_iis\_website
-  win\_lineinfile
-  win\_nssm
-  win\_package
-  win\_regedit
-  win\_scheduled\_task
-  win\_unzip
-  win\_updates
-  win\_webpicmd
-  xenserver\_facts
-  zabbbix
-  zabbix\_host
-  zabbix\_hostmacro
-  zabbix\_screen
-  znode

New Inventory scripts:
^^^^^^^^^^^^^^^^^^^^^^

-  cloudstack
-  fleetctl
-  openvz
-  nagios\_ndo
-  nsot
-  proxmox
-  rudder
-  serf

New Lookups:
^^^^^^^^^^^^

-  credstash
-  hashi\_vault
-  ini
-  shelvefile

New Filters:
^^^^^^^^^^^^

-  combine

New Connection:
^^^^^^^^^^^^^^^

-  docker: for talking to docker containers on the ansible controller
   machine without using ssh.

New Callbacks:
^^^^^^^^^^^^^^

-  logentries: plugin to send play data to logentries service
-  skippy: same as default but does not display skip messages

Minor changes:
~~~~~~~~~~~~~~

-  Many more tests. The new API makes things more testable and we took
   advantage of it.
-  big\_ip modules now support turning off ssl certificate validation
   (use only for self-signed certificates).
-  Consolidated code from modules using urllib2 to normalize features,
   TLS and SNI support.
-  synchronize module's dest\_port parameter now takes precedence over
   the ansible\_ssh\_port inventory setting.
-  Play output is now dynamically sized to terminal with a minimum of 80
   coluumns (old default).
-  vars\_prompt and pause are now skipped with a warning if the play is
   called noninteractively (i.e. pull from cron).
-  Support for OpenBSD's 'doas' privilege escalation method.
-  Most vault operations can now be done over multilple files.
-  ansible-vault encrypt/decrypt read from stdin if no other input file
   is given, and can write to a given ``--output file`` (including
   stdout, '-'). This lets you avoid ever writing sensitive plaintext to
   disk.
-  ansible-vault rekey accepts the --new-vault-password-file option.
-  ansible-vault now preserves file permissions on edit and rekey and
   defaults to restrictive permissions for other options.
-  Configuration items defined as paths (local only) now all support
   shell style interpolations.
-  Many fixes and new options added to modules, too many to list here.
-  Now you can see task file and line number when using verbosity of 3
   or above.
-  The ``[x-y]`` host range syntax is no longer supported. Note that
   ``[0:1]`` matches two hosts, i.e. the range is inclusive of its
   endpoints.
-  We now recommend the use of ``pattern1,pattern2`` to combine host
   matching patterns.
-  The use of ':' as a separator conflicts with IPv6 addresses and host
   ranges. It will be deprecated in the future.
-  The undocumented use of ';' as a separator is now deprecated.
-  modules and callbacks have been extended to support no\_log to avoid
   data disclosure.
-  new managed\_syslog option has been added to control output to syslog
   on managed machines, no\_log supersedes this settings.
-  Lookup, vars and action plugin pathing has been normalized, all now
   follow the same sequence to find relative files.
-  We do not ignore the explicitly set login user for ssh when it
   matches the 'current user' anymore, this allows overriding
   .ssh/config when it is set explicitly. Leaving it unset will still
   use the same user and respect .ssh/config. This also means
   ansible\_ssh\_user can now return a None value.
-  environment variables passed to remote shells now default to
   'controller' settings, with fallback to en\_US.UTF8 which was the
   previous default.
-  add\_hosts is much stricter about host name and will prevent invalid
   names from being added.
-  ansible-pull now defaults to doing shallow checkouts with git, use
   ``--full`` to return to previous behaviour.
-  random cows are more random
-  when: now gets the registered var after the first iteration, making
   it possible to break out of item loops
-  Handling of undefined variables has changed. In most places they will
   now raise an error instead of silently injecting an empty string. Use
   the default filter if you want to approximate the old behaviour:

   ::

       - debug: msg="The error message was: {{error_code |default('') }}"

1.9.7 "Dancing in the Street" - TBD
-----------------------------------

-  Fix for lxc\_container backport which was broken because it tried to
   use a feature from ansible-2.x

1.9.6 "Dancing in the Street" - Apr 15, 2016
--------------------------------------------

-  Fix a regression in the loading of inventory variables where they
   were not found when placed inside of an inventory directory.
-  Fix lxc\_container having predictable temp file names. Addresses
   CVE-2016-3096

1.9.5 "Dancing In the Street" - Mar 21, 2016
--------------------------------------------

-  Compatibility fix with docker 1.8.
-  Fix a bug with the crypttab module omitting certain characters from
   the name of the device
-  Fix bug with uri module not handling all binary files
-  Fix bug with ini\_file not removing options set to an empty string
-  Fix bug with script and raw modules not honoring parameters passed
   via yaml dict syntax
-  Fix bug with plugin loading finding the wrong modules because the
   suffix checking was not ordered
-  Fix bug in the literal\_eval module code used when we need python-2.4
   compat
-  Added --ignore-certs, -c option to ansible-galaxy. Allows
   ansible-galaxy to work behind a proxy when the proxy fails to forward
   server certificates.
-  Fixed bug where tasks marked no\_log were showing hidden values in
   output if ansible's --diff option was used.
-  Fix bug with non-english locales in git and apt modules
-  Compatibility fix for using state=absent with the pip ansible module
   and pip-6.1.0+
-  Backported support for ansible\_winrm\_server\_cert\_validation flag
   to disable cert validation on Python 2.7.9+ (and support for other
   passthru args to pywinrm transport).
-  Backported various updates to user module (prevent accidental OS X
   group membership removals, various checkmode fixes).

1.9.4 "Dancing In the Street" - Oct 9, 2015
-------------------------------------------

-  Fixes a bug where yum state=latest would error if there were no
   updates to install.
-  Fixes a bug where yum state=latest did not work with wildcard package
   names.
-  Fixes a bug in lineinfile relating to escape sequences.
-  Fixes a bug where vars\_prompt was not keeping passwords private by
   default.
-  Fix ansible-galaxy and the hipchat callback plugin to check that the
   host it is contacting matches its TLS Certificate.

1.9.3 "Dancing In the Street" - Sep 3, 2015
-------------------------------------------

-  Fixes a bug related to keyczar messing up encodings internally,
   resulting in decrypted messages coming out as empty strings.
-  AES Keys generated for use in accelerated mode are now 256-bit by
   default instead of 128.
-  Fix url fetching for SNI with python-2.7.9 or greater. SNI does not
   work with python < 2.7.9. The best workaround is probably to use the
   command module with curl or wget.
-  Fix url fetching to allow tls-1.1 and tls-1.2 if the system's openssl
   library supports those protocols
-  Fix ec2\_ami\_search module to check TLS Certificates
-  Fix the following extras modules to check TLS Certificates:
-  campfire
-  layman
-  librarto\_annotate
-  twilio
-  typetalk
-  Fix docker module's parsing of docker-py version for dev checkouts
-  Fix docker module to work with docker server api 1.19
-  Change yum module's state=latest feature to update all packages
   specified in a single transaction. This is the same type of fix as
   was made for yum's state=installed in 1.9.2 and both solves the same
   problems and with the same caveats.
-  Fixed a bug where stdout from a module might be blank when there were
   were non-printable ASCII characters contained within it

1.9.2 "Dancing In the Street" - Jun 26, 2015
--------------------------------------------

-  Security fixes to check that hostnames match certificates with https
   urls (CVE-2015-3908)
-  get\_url and uri modules
-  url and etcd lookup plugins
-  Security fixes to the zone (Solaris containers), jail (bsd
   containers), and chroot connection plugins. These plugins can be used
   to connect to their respective container types in leiu of the
   standard ssh connection. Prior to this fix being applied these
   connection plugins didn't properly handle symlinks within the
   containers which could lead to files intended to be written to or
   read from the container being written to or read from the host system
   instead. (CVE pending)
-  Fixed a bug in the service module where init scripts were being
   incorrectly used instead of upstart/systemd.
-  Fixed a bug where sudo/su settings were not inherited from
   ansible.cfg correctly.
-  Fixed a bug in the rds module where a traceback may occur due to an
   unbound variable.
-  Fixed a bug where certain remote file systems where the SELinux
   context was not being properly set.
-  Re-enabled several windows modules which had been partially merged
   (via action plugins):
-  win\_copy.ps1
-  win\_copy.py
-  win\_file.ps1
-  win\_file.py
-  win\_template.py
-  Fix bug using with\_sequence and a count that is zero. Also allows
   counting backwards isntead of forwards
-  Fix get\_url module bug preventing use of custom ports with https
   urls
-  Fix bug disabling repositories in the yum module.
-  Fix giving yum module a url to install a package from on RHEL/CENTOS5
-  Fix bug in dnf module preventing it from working when yum-utils was
   not already installed

1.9.1 "Dancing In the Street" - Apr 27, 2015
--------------------------------------------

-  Fixed a bug related to Kerberos auth when using winrm with a domain
   account.
-  Fixing several bugs in the s3 module.
-  Fixed a bug with upstart service detection in the service module.
-  Fixed several bugs with the user module when used on OSX.
-  Fixed unicode handling in some module situations (assert and
   shell/command execution).
-  Fixed a bug in redhat\_subscription when using the activationkey
   parameter.
-  Fixed a traceback in the gce module on EL6 distros when multiple
   pycrypto installations are available.
-  Added support for PostgreSQL 9.4 in rds\_param\_group
-  Several other minor fixes.

1.9 "Dancing In the Street" - Mar 25, 2015
------------------------------------------

Major changes:

-  Added kerberos support to winrm connection plugin.
-  Tags rehaul: added 'all', 'always', 'untagged' and 'tagged' special
   tags and normalized tag resolution. Added tag information to
   --list-tasks and new --list-tags option.
-  Privilege Escalation generalization, new 'Become' system and
   variables now will handle existing and new methods. Sudo and su have
   been kept for backwards compatibility. New methods pbrun and pfexec
   in 'alpha' state, planned adding 'runas' for winrm connection plugin.
-  Improved ssh connection error reporting, now you get back the
   specific message from ssh.
-  Added facility to document task module return values for registered
   vars, both for ansible-doc and the docsite. Documented copy, stats
   and acl modules, the rest must be updated individually (we will start
   doing so incrementally).
-  Optimize the plugin loader to cache available plugins much more
   efficiently. For some use cases this can lead to dramatic
   improvements in startup time.
-  Overhaul of the checksum system, now supports more systems and more
   cases more reliably and uniformly.
-  Fix skipped tasks to not display their parameters if no\_log is
   specified.
-  Many fixes to unicode support, standarized functions to make it
   easier to add to input/output boundaries.
-  Added travis integration to github for basic tests, this should speed
   up ticket triage and merging.
-  environment: directive now can also be applied to play and is
   inhertited by tasks, which can still override it.
-  expanded facts and OS/distribution support for existing facts and
   improved performance with pypy.
-  new 'wantlist' option to lookups allows for selecting a list typed
   variable vs a comma delimited string as the return.
-  the shared module code for file backups now uses a timestamp
   resolution of seconds (previouslly minutes).
-  allow for empty inventories, this is now a warning and not an error
   (for those using localhost and cloud modules).
-  sped up YAML parsing in ansible by up to 25% by switching to CParser
   loader.

New Modules:

-  cryptab *-- manages linux encrypted block devices*
-  gce\_img *-- for utilizing GCE image resources*
-  gluster\_volume *-- manage glusterfs volumes*
-  haproxy *-- for the load balancer of same name*
-  known\_hosts *-- manages the ssh known\_hosts file*
-  lxc\_container *-- manage lxc containers*
-  patch *-- allows for patching files on target systems*
-  pkg5 *-- installing and uninstalling packages on Solaris*
-  pkg5\_publisher *-- manages Solaris pkg5 repository configuration*
-  postgresql\_ext *-- manage postgresql extensions*
-  snmp\_facts *-- gather facts via snmp*
-  svc *-- manages daemontools based services*
-  uptimerobot *-- manage monitoring with this service*

New Filters:

-  ternary: allows for trueval/falseval assignment dependent on
   conditional
-  cartesian: returns the Cartesian product of 2 lists
-  to\_uuid: given a string it will return an ansible domain specific
   UUID
-  checksum: uses the ansible internal checksum to return a hash from a
   string
-  hash: get a hash from a string (md5, sha1, etc)
-  password\_hash: get a hash form as string that can be used as a
   password in the user module (and others)
-  A whole set of ip/network manipulation filters:
   ipaddr,ipwrap,ipv4,ipv6ipsubnet,nthhost,hwaddr,macaddr

Other Notable Changes:

-  New lookup plugins:
-  dig: does dns resolution and returns IPs.
-  url: allows pulling data from a url.

-  New callback plugins:
-  syslog\_json: allows logging play output to a syslog network server
   using json format

-  Many new enhancements to the amazon web service modules:
-  ec2 now applies all specified security groups when creating a new
   instance. Previously it was only applying one
-  ec2\_vol gained the ability to specify the EBS volume type
-  ec2\_vol can now detach volumes by specifying instance=None
-  Fix ec2\_group to purge specific grants rather than whole rules
-  Added tenancy support for the ec2 module
-  rds module has gained the ability to manage tags and set charset and
   public accessibility
-  ec2\_snapshot module gained the capability to remove snapshots
-  Add alias support for route53
-  Add private\_zones support to route53
-  ec2\_asg: Add wait\_for\_instances parameter that waits until an
   instance is ready before ending the ansible task
-  Many new docker improvements:
-  restart\_policy parameters to configure when the container
   automatically restarts
-  If the docker client or server doesn't support an option, the task
   will now fail instead of silently ignoring the option
-  Add insecure\_registry parameter for connecting to registries via
   http
-  New parameter to set a container's domain name
-  Undeprecated docker\_image module until there's replacement
   functionality
-  Allow setting the container's pid namespace
-  Add a pull parameter that chooses when ansible will look for more
   recent images in the registry
-  docker module states have been greatly enhanced. The reworked and new
   states are:

   -  present now creates but does not start containers
   -  restarted always restarts a container
   -  reloaded restarts a container if ansible detects that the
      configuration is different than what is specified
   -  reloaded accounts for exposed ports, env vars, and volumes

-  Can now connect to the docker server using TLS
-  Several source control modules had force parameters that defaulted to
   true. These have been changed to default to false so as not to
   accidentally lose work. Playbooks that depended on the former
   behaviour simply need to add force=True to the task that needs it.
   Affected modules:
-  bzr: When local modifications exist in a checkout, the bzr module
   used to default to removing the modifications on any operation. Now
   the module will not remove the modifications unless force=yes is
   specified. Operations that depend on a clean working tree may fail
   unless force=yes is added.
-  git: When local modifications exist in a checkout, the git module
   will now fail unless force is explicitly specified. Specifying
   force=yes will allow the module to revert and overwrite local
   modifications to make git actions succeed.
-  hg: When local modifications exist in a checkout, the hg module used
   to default to removing the modifications on any operation. Now the
   module will not remove the modifications unless force=yes is
   specified.
-  subversion: When updating a checkout with local modifications, you
   now need to add force=yes so the module will revert the modifications
   before updating.
-  New inventory scripts:
-  vbox: virtualbox
-  consul: use consul as an inventory source
-  gce gained the ip\_forward parameter to forward ip packets
-  disk\_auto\_delete parameter to gce that will remove the boot disk
   after an instance is destroyed
-  gce can now spawn instances with no external ip
-  gce\_pd gained the ability to choose a disk type
-  gce\_net gained target\_tags parameter for creating firewall rules
-  rax module has new parameters for making use of a boot volume
-  Add scheduler\_hints to the nova\_compute module for optional
   parameters
-  vsphere\_guest now supports deploying guests from a template
-  Many fixes for hardlink and softlink handling in file-related modules
-  Implement user, group, mode, and selinux parameters for the unarchive
   module
-  authorized\_keys can now use url as a key source
-  authorized\_keys has a new exclusive parameter that determines if
   keys that weren't specified in the task
-  The selinux module now sets the current running state to permissive
   if state='disabled'
-  Can now set accounts to expire via the user module
-  Overhaul of the service module to make code simpler and behave better
   for systems running several popular init systems
-  yum module now has a parameter to refresh its cache of package
   metadata
-  apt module gained a build\_dep parameter to install a package's build
   dependencies
-  Add parameters to the postgres modules to specify a unix socket to
   connect to the db
-  The mount module now supports bind mounts
-  Add a clone parameter to git module that allows you to get
   information about a remote repo even if it doesn't exist locally.
-  Add a refspec argument to the git module that allows pulling commits
   that aren't part of a branch
-  Many documentation additions and fixes.

1.8.4 "You Really Got Me" - Feb 19, 2015
----------------------------------------

-  Fixed regressions in ec2 and mount modules, introduced in 1.8.3

1.8.3 "You Really Got Me" - Feb 17, 2015
----------------------------------------

-  Fixing a security bug related to the default permissions set on a
   temporary file created when using "ansible-vault view ".
-  Many bug fixes, for both core code and core modules.

1.8.2 "You Really Got Me" - Dec 04, 2014
----------------------------------------

-  Various bug fixes for packaging issues related to modules.
-  Various bug fixes for lookup plugins.
-  Various bug fixes for some modules (continued cleanup of postgresql
   issues, etc.).

-  Add a clone parameter to git module that allows you to get
   information about a remote repo even if it doesn't exist locally.

1.8.1 "You Really Got Me" - Nov 26, 2014
----------------------------------------

-  Various bug fixes in postgresql and mysql modules.
-  Fixed a bug related to lookup plugins used within roles not finding
   files based on the relative paths to the roles files/ directory.
-  Fixed a bug related to vars specified in plays being templated too
   early, resulting in incorrect variable interpolation.
-  Fixed a bug related to git submodules in bare repos.

1.8 "You Really Got Me" - Nov 25, 2014
--------------------------------------

Major changes:

-  fact caching support, pluggable, initially supports Redis (DOCS
   pending)
-  'serial' size in a rolling update can be specified as a percentage
-  added new Jinja2 filters, 'min' and 'max' that take lists
-  new 'ansible\_version' variable available contains a dictionary of
   version info
-  For ec2 dynamic inventory, ec2.ini can has various new configuration
   options
-  'ansible vault view filename.yml' opens filename.yml decrypted in a
   pager.
-  no\_log parameter now surpressess data from callbacks/output as well
   as syslog
-  ansible-galaxy install -f requirements.yml allows advanced options
   and installs from non-galaxy SCM sources and tarballs.
-  command\_warnings feature will warn about when usage of the
   shell/command module can be simplified to use core modules - this can
   be enabled in ansible.cfg
-  new omit value can be used to leave off a parameter when not set,
   like so module\_name: a=1 b={{ c \| default(omit) }}, would not pass
   value for b (not even an empty value) if c was not set.
-  developers: 'baby JSON' in module responses, originally intended for
   writing modules in bash, is removed as a feature to simplify logic,
   script module remains available for running bash scripts.
-  async jobs started in "fire & forget" mode can now be checked on at a
   later time.
-  added ability to subcategorize modules for docs.ansible.com
-  added ability for shipped modules to have aliases with symlinks
-  added ability to deprecate older modules by starting with "\_" and
   including "deprecated: message why" in module docs

New Modules:

-  cloud
-  rax\_cdb *-- manages Rackspace Cloud Database instances*
-  rax\_cdb\_database *-- manages Rackspace Cloud Databases*
-  rax\_cdb\_user *-- manages Rackspace Cloud Database users*
-  monitoring
-  bigpanda *-- support for bigpanda*
-  zabbix\_maintaince *-- handles outage windows with Zabbix*
-  net\_infrastructure
-  a10\_server *-- manages server objects on A10 devices*
-  a10\_service\_group *-- manages service group objects on A10 devices*
-  a10\_virtual\_server *-- manages virtual server objects on A10
   devices*
-  system
-  getent *-- read getent databases*

Some other notable changes:

-  added the ability to set "instance filters" in the ec2.ini to limit
   results from the inventory plugin.
-  upgrades for various variable precedence items and parsing related
   items
-  added a new "follow" parameter to the file and copy modules, which
   allows actions to be taken on the target of a symlink rather than the
   symlink itself.
-  if a module should ever traceback, it will return a standard error,
   catchable by ignore\_errors, versus an 'unreachable'
-  ec2\_lc: added support for multiple new parameters like kernel\_id,
   ramdisk\_id and ebs\_optimized.
-  ec2\_elb\_lb: added support for the connection\_draining\_timeout and
   cross\_az\_load\_balancing options.
-  support for symbolic representations (ie. u+rw) for file permission
   modes (file/copy/template modules etc.).
-  docker: Added support for specifying the net type of the container.
-  docker: support for specifying read-only volumes.
-  docker: support for specifying the API version to use for the remote
   connection.
-  openstack modules: various improvements
-  irc: ssl support for the notification module
-  npm: fix flags passed to package installation
-  windows: improved error handling
-  setup: additional facts on System Z
-  apt\_repository: certificate validation can be disabled if requested
-  pagerduty module: misc improvements
-  ec2\_lc: public\_ip boolean configurable in launch configurations
-  ec2\_asg: fixes related to proper termination of an autoscaling group
-  win\_setup: total memory fact correction
-  ec2\_vol: ability to list existing volumes
-  ec2: can set optimized flag
-  various parser improvements
-  produce a friendly error message if the SSH key is too permissive
-  ec2\_ami\_search: support for SSD and IOPS provisioned EBS images
-  can set ansible\_sudo\_exe as an inventory variable which allows
   specifying a different sudo (or equivalent) command
-  git module: Submodule handling has changed. Previously if you used
   the ``recursive`` parameter to handle submodules, ansible would track
   the submodule upstream's head revision. This has been changed to
   checkout the version of the submodule specified in the superproject's
   git repository. This is inline with what git submodule update does.
   If you want the old behaviour use the new module parameter
   track\_submodules=yes
-  Checksumming of transferred files has been made more portable and now
   uses the sha1 algorithm instead of md5 to be compatible with
   FIPS-140.
-  As a small side effect, the fetch module no longer returns a useful
   value in remote\_md5. If you need a replacement, switch to using
   remote\_checksum which returns the sha1sum of the remote file.
-  ansible-doc CLI tool contains various improvements for working with
   different terminals

And various other bug fixes and improvements ...

1.7.2 "Summer Nights" - Sep 24, 2014
------------------------------------

-  Fixes a bug in accelerate mode which caused a traceback when trying
   to use that connection method.
-  Fixes a bug in vault where the password file option was not being
   used correctly internally.
-  Improved multi-line parsing when using YAML literal blocks (using >
   or \|).
-  Fixed a bug with the file module and the creation of relative
   symlinks.
-  Fixed a bug where checkmode was not being honoured during the
   templating of files.
-  Other various bug fixes.

1.7.1 "Summer Nights" - Aug 14, 2014
------------------------------------

-  Security fix to disallow specifying 'args:' as a string, which could
   allow the insertion of extra module parameters through variables.
-  Performance enhancements related to previous security fixes, which
   could cause slowness when modules returned very large JSON results.
   This specifically impacted the unarchive module frequently, which
   returns the details of all unarchived files in the result.
-  Docker module bug fixes:
-  Fixed support for specifying rw/ro bind modes for volumes
-  Fixed support for allowing the tag in the image parameter
-  Various other bug fixes

1.7 "Summer Nights" - Aug 06, 2014
----------------------------------

Major new features:

-  Windows support (alpha) using native PowerShell remoting
-  Tasks can now specify ``run_once: true``, meaning they will be
   executed exactly once. This can be combined with delegate\_to to
   trigger actions you want done just the one time versus for every host
   in inventory.

New inventory scripts:

-  SoftLayer
-  Windows Azure

New Modules:

-  cloud
-  azure
-  rax\_meta
-  rax\_scaling\_group
-  rax\_scaling\_policy
-  windows
-  *version of setup module*
-  *version of slurp module*
-  win\_feature
-  win\_get\_url
-  win\_group
-  win\_msi
-  win\_ping
-  win\_service
-  win\_user

Other notable changes:

-  Security fixes
-  Prevent the use of lookups when using legacy "{{ }}" syntax around
   variables and with\_\* loops.
-  Remove relative paths in TAR-archived file names used by
   ansible-galaxy.
-  Inventory speed improvements for very large inventories.
-  Vault password files can now be executable, to support scripts that
   fetch the vault password.

1.6.10 "And the Cradle Will Rock" - Jul 25, 2014
------------------------------------------------

-  Fixes an issue with the copy module when copying a directory that
   fails when changing file attributes and the target file already
   exists
-  Improved unicode handling when splitting args

1.6.9 "And the Cradle Will Rock" - Jul 24, 2014
-----------------------------------------------

-  Further improvements to module parameter parsing to address
   additional regressions caused by security fixes

1.6.8 "And the Cradle Will Rock" - Jul 22, 2014
-----------------------------------------------

-  Corrects a regression in the way shell and command parameters were
   being parsed

1.6.7 "And the Cradle Will Rock" - Jul 21, 2014
-----------------------------------------------

-  Security fixes:
-  Strip lookup calls out of inventory variables and clean unsafe data
   returned from lookup plugins (CVE-2014-4966)
-  Make sure vars don't insert extra parameters into module args and
   prevent duplicate params from superseding previous params
   (CVE-2014-4967)

1.6.6 "And the Cradle Will Rock" - Jul 01, 2014
-----------------------------------------------

-  Security updates to further protect against the incorrect execution
   of untrusted data

1.6.4, 1.6.5 "And the Cradle Will Rock" - Jun 25, 2014
------------------------------------------------------

-  Security updates related to evaluation of untrusted remote inputs

1.6.3 "And the Cradle Will Rock" - Jun 09, 2014
-----------------------------------------------

-  Corrects a regression where handlers were run across all hosts, not
   just those that triggered the handler.
-  Fixed a bug in which modules did not support properly moving a file
   atomically when su was in use.
-  Fixed two bugs related to symlinks with directories when using the
   file module.
-  Fixed a bug related to MySQL master replication syntax.
-  Corrects a regression in the order of variable merging done by the
   internal runner code.
-  Various other minor bug fixes.

1.6.2 "And the Cradle Will Rock" - May 23, 2014
-----------------------------------------------

-  If an improper locale is specified, core modules will now
   automatically revert to using the 'C' locale.
-  Modules using the fetch\_url utility will now obey proxy environment
   variables.
-  The SSL validation step in fetch\_url will likewise obey proxy
   settings, however only proxies using the http protocol are supported.
-  Fixed multiple bugs in docker module related to version changes
   upstream.
-  Fixed a bug in the ec2\_group module where egress rules were lost
   when a VPC was specified.
-  Fixed two bugs in the synchronize module:
-  a trailing slash might be lost when calculating relative paths,
   resulting in an incorrect destination.
-  the sync might use the inventory directory incorrectly instead of the
   playbook or role directory.
-  Files will now only be chown'd on an atomic move if the src/dest
   uid/gid do not match.

1.6.1 "And the Cradle Will Rock" - May 7, 2014
----------------------------------------------

-  Fixed a bug in group\_by, where systems were being grouped
   incorrectly.
-  Fixed a bug where file descriptors may leak to a child process when
   using accelerate.
-  Fixed a bug in apt\_repository triggered when python-apt not being
   installed/available.
-  Fixed a bug in the apache2\_module module, where modules were not
   being disabled correctly.

1.6 "And the Cradle Will Rock" - May 5, 2014
--------------------------------------------

Major features/changes:

-  The deprecated legacy variable templating system has been finally
   removed. Use {{ foo }} always not $foo or ${foo}.
-  Any data file can also be JSON. Use sparingly -- with great power
   comes great responsibility. Starting file with "{" or "[" denotes
   JSON.
-  Added 'gathering' param for ansible.cfg to change the default
   gather\_facts policy.
-  Accelerate improvements:
-  multiple users can connect with different keys, when
   ``accelerate_multi_key = yes`` is specified in the ansible.cfg.
-  daemon lifetime is now based on the time from the last activity, not
   the time from the daemon's launch.
-  ansible-playbook now accepts --force-handlers to run handlers even if
   tasks result in failures.
-  Added VMWare support with the vsphere\_guest module.

New Modules:

-  files
-  replace
-  packaging
-  apt\_rpm
-  composer *(PHP)*
-  cpanm *(Perl)*
-  homebrew\_cask *(OS X)*
-  homebrew\_tap *(OS X)*
-  layman
-  portage
-  monitoring
-  librato\_annotation
-  logentries
-  rollbar\_deployment
-  notification
-  nexmo *(SMS)*
-  slack *(Slack.com)*
-  sns *(Amazon)*
-  twilio *(SMS)*
-  typetalk *(Typetalk.in)*
-  system
-  alternatives
-  capabilities
-  debconf
-  locale\_gen
-  ufw
-  net\_infrastructure
-  bigip\_facts
-  dnssimple
-  lldp
-  web\_infrastructure
-  apache2\_module
-  cloud
-  digital\_ocean\_domain
-  digital\_ocean\_sshkey
-  ec2\_asg *(configure autoscaling groups)*
-  ec2\_metric\_alarm
-  ec2\_scaling\_policy
-  rax\_identity
-  rax\_cbs *(cloud block storage)*
-  rax\_cbs\_attachments
-  vsphere\_guest

Other notable changes:

-  example callback plugin added for hipchat
-  added example inventory plugin for vcenter/vsphere
-  added example inventory plugin for doing really trivial inventory
   from SSH config files
-  libvirt module now supports destroyed and paused as states
-  s3 module can specify metadata
-  security token additions to ec2 modules
-  setup module code moved into module\_utils/, facts now accessible by
   other modules
-  synchronize module sets relative dirs based on inventory or role path
-  misc bugfixes and other parameters
-  the ec2\_key module now has wait/wait\_timeout parameters
-  added version\_compare filter (see docs)
-  added ability for module documentation YAML to utilize shared module
   snippets for common args
-  apt module now accepts "deb" parameter to install local dpkg files
-  regex\_replace filter plugin added
-  added an inventory script for Docker
-  added an inventory script for Abiquo
-  the get\_url module now accepts url\_username and url\_password as
   parameters, so sites which require authentication no longer need to
   have them embedded in the url
-  ... to be filled in from changelogs ...

1.5.5 "Love Walks In" - April 18, 2014
--------------------------------------

-  Security fix for vault, to ensure the umask is set to a restrictive
   mode before creating/editing vault files.
-  Backported apt\_repository security fixes relating to filename/mode
   upon sources list file creation.

1.5.4 "Love Walks In" - April 1, 2014
-------------------------------------

-  Security fix for safe\_eval, which further hardens the checking of
   the evaluation function.
-  Changing order of variable precedence for system facts, to ensure
   that inventory variables take precedence over any facts that may be
   set on a host.

1.5.3 "Love Walks In" - March 13, 2014
--------------------------------------

-  Fix validate\_certs and run\_command errors from previous release
-  Fixes to the git module related to host key checking

1.5.2 "Love Walks In" - March 11, 2014
--------------------------------------

-  Fix module errors in airbrake and apt from previous release

1.5.1 "Love Walks In" - March 10, 2014
--------------------------------------

-  Force command action to not be executed by the shell unless
   specifically enabled.
-  Validate SSL certs accessed through urllib\*.
-  Implement new default cipher class AES256 in ansible-vault.
-  Misc bug fixes.

1.5 "Love Walks In" - February 28, 2014
---------------------------------------

Major features/changes:

-  when\_foo which was previously deprecated is now removed, use "when:"
   instead. Code generates appropriate error suggestion.
-  include + with\_items which was previously deprecated is now removed,
   ditto. Use with\_nested / with\_together, etc.
-  only\_if, which is much older than when\_foo and was deprecated, is
   similarly removed.
-  ssh connection plugin is now more efficient if you add
   'pipelining=True' in ansible.cfg under [ssh\_connection], see
   example.cfg
-  localhost/127.0.0.1 is not required to be in inventory if referenced,
   if not in inventory, it does not implicitly appear in the 'all'
   group.
-  git module has new parameters (accept\_hostkey, key\_file, ssh\_opts)
   to ease the usage of git and ssh protocols.
-  when using accelerate mode, the daemon will now be restarted when
   specifying a different remote\_user between plays.
-  added no\_log: option for tasks. When used, no logging information
   will be sent to syslog during the module execution.
-  acl module now handles 'default' and allows for either shorthand
   entry or specific fields per entry section
-  play\_hosts is a new magic variable to provide a list of hosts in
   scope for the current play.
-  ec2 module now accepts 'exact\_count' and 'count\_tag' as a way to
   enforce a running number of nodes by tags.
-  all ec2 modules that work with Eucalyptus also now support a
   'validate\_certs' option, which can be set to 'off' for installations
   using self-signed certs.
-  Start of new integration test infrastructure (WIP, more details TBD)
-  if repoquery is unavailable, the yum module will automatically
   attempt to install yum-utils
-  ansible-vault: a framework for encrypting your playbooks and variable
   files
-  added support for privilege escalation via 'su' into bin/ansible and
   bin/ansible-playbook and associated keywords 'su', 'su\_user',
   'su\_pass' for tasks/plays

New modules:

-  cloud
-  docker\_image
-  ec2\_elb\_lb
-  ec2\_key
-  ec2\_snapshot
-  rax\_dns
-  rax\_dns\_record
-  rax\_files
-  rax\_files\_objects
-  rax\_keypair
-  rax\_queue
-  messaging
-  rabbitmq\_policy
-  system
-  at
-  utilities
-  assert

Other notable changes (many new module params & bugfixes may not be
listed):

-  no\_reboot is now defaulted to "no" in the ec2\_ami module to ensure
   filesystem consistency in the resulting AMI.
-  sysctl module overhauled
-  authorized\_key module overhauled
-  synchronized module now handles local transport better
-  apt\_key module now ignores case on keys
-  zypper\_repository now skips on check mode
-  file module now responds to force behavior when dealing with
   hardlinks
-  new lookup plugin 'csvfile'
-  fixes to allow hash\_merge behavior to work with dynamic inventory
-  mysql module will use port argument on dump/import
-  subversion module now ignores locale to better intercept status
   messages
-  rax api\_key argument is no longer logged
-  backwards/forwards compatibility for OpenStack modules, 'quantum'
   modules grok neutron renaming
-  hosts properly uniqueified if appearing in redundant groups
-  hostname module support added for ScientificLinux
-  ansible-pull can now show live stdout and pass verbosity levels to
   ansible-playbook
-  ec2 instances can now be stopped or started
-  additional volumes can be created when creating new ec2 instances
-  user module can move a home directory
-  significant enhancement and cleanup of rackspace modules
-  ansible\_ssh\_private\_key\_file can be templated
-  docker module updated to support docker-py 0.3.0
-  various other bug fixes
-  md5 logic improved during sudo operation
-  support for ed25519 keys in authorized\_key module
-  ability to set directory permissions during a recursive copy
   (directory\_mode parameter)

1.4.5 "Could This Be Magic" - February 12, 2014
-----------------------------------------------

-  fixed issue with permissions being incorrect on fireball/accelerate
   keys when the umask setting was too loose.

1.4.4 "Could This Be Magic" - January 6, 2014
---------------------------------------------

-  fixed a minor issue with newer versions of pip dropping the
   "use-mirrors" parameter.

1.4.3 "Could This Be Magic" - December 20, 2013
-----------------------------------------------

-  Fixed role\_path parsing from ansible.cfg
-  Fixed default role templates

1.4.2 "Could This Be Magic" - December 18, 2013
-----------------------------------------------

-  Fixed a few bugs related to unicode
-  Fixed errors in the ssh connection method with large data returns
-  Miscellaneous fixes for a few modules
-  Add the ansible-galaxy command

1.4.1 "Could This Be Magic" - November 27, 2013
-----------------------------------------------

-  Misc fixes to accelerate mode and various modules.

1.4 "Could This Be Magic" - November 21, 2013
---------------------------------------------

Highlighted new features:

-  Added do-until feature, which can be used to retry a failed task a
   specified number of times with a delay in-between the retries.
-  Added failed\_when option for tasks, which can be used to specify
   logical statements that make it easier to determine when a task has
   failed, or to make it easier to ignore certain non-zero return codes
   for some commands.
-  Added the "subelement" lookup plugin, which allows iteration of the
   keys of a dictionary or items in a list.
-  Added the capability to use either paramiko or ssh for the initial
   setup connection of an accelerated playbook.
-  Automatically provide advice on common parser errors users encounter.
-  Deprecation warnings are now shown for legacy features:
   when\_integer/etc, only\_if, include+with\_items, etc. Can be
   disabled in ansible.cfg
-  The system will now provide helpful tips around possible YAML syntax
   errors increasing ease of use for new users.
-  warnings are now shown for using {{ foo }} in loops and conditionals,
   and suggest leaving the variable expressions bare as per docs.
-  The roles search path is now configurable in ansible.cfg.
   'roles\_path' in the config setting.
-  Includes with parameters can now be done like roles for consistency:
   - { include: song.yml, year:1984, song:'jump' }
-  The name of each role is now shown before each task if roles are
   being used
-  Adds a "var=" option to the debug module for debugging variable data.
   "debug: var=hostvars['hostname']" and "debug: var=foo" are all valid
   syntax.
-  Variables in {{ format }} can be used as references even if they are
   structured data
-  Can force binding of accelerate to ipv6 ports.
-  the apt module will auto-install python-apt if not present rather
   than requiring a manual installation
-  the copy module is now recursive if the local 'src' parameter is a
   directory.
-  syntax checks now scan included task and variable files as well as
   main files

New modules and plugins.

-  cloud
-  docker *- instantiates/removes/manages docker containers*
-  ec2\_eip *-- manage AWS elastic IPs*
-  ec2\_vpc *-- manage ec2 virtual private clouds*
-  elasticcache *-- Manages clusters in Amazon Elasticache*
-  ovirt *-- VM lifecycle controls for ovirt*
-  rax\_network *-- sets up Rackspace networks*
-  rax\_facts *-- retrieve facts about a Rackspace Cloud Server*
-  rax\_clb\_nodes *-- manage Rackspace cloud load balanced nodes*
-  rax\_clb *-- manages Rackspace cloud load balancers*
-  files
-  acl *-- set or get acls on a file*
-  synchronize *-- a useful wrapper around rsyncing trees of files*
-  unarchive *-- pushes and extracts tarballs*
-  system
-  blacklist *-- add or remove modules from the kernel blacklist*
-  firewalld *-- manage the firewalld configuration*
-  hostname *-- sets the systems hostname*
-  modprobe *-- manage kernel modules on systems that support
   modprobe/rmmod*
-  open\_iscsi *-- manage targets on an initiator using open-iscsi*
-  utilities
-  include\_vars *-- dynamically load variables based on conditions.*
-  packaging
-  swdepot *-- a module for working with swdepot*
-  urpmi *-- work with urpmi packages*
-  zypper\_repository *-- adds or removes Zypper repositories*
-  notification
-  grove *-- notifies to Grove hosted IRC channels*
-  web\_infrastructure
-  ejabberd\_user *-- add and remove users to ejabberd*
-  jboss *-- deploys or undeploys apps to jboss*
-  source\_control
-  github\_hooks *-- manages GitHub service hooks*
-  net\_infrastructure
-  bigip\_monitor\_http *-- manages F5 BIG-IP LTM http monitors*
-  bigip\_monitor\_tcp *-- manages F5 BIG-IP LTM TCP monitors*
-  bigip\_node *-- manages F5 BIG-IP LTM nodes*
-  bigip\_pool\_member *-- manages F5 BIG-IP LTM pool members*
-  openvswitch\_port
-  openvswitch\_bridge

Plugins:

-  jail connection module (FreeBSD)
-  lxc connection module
-  added inventory script for listing FreeBSD jails
-  added md5 as a Jinja2 filter: {{ path \| md5 }}
-  added a fileglob filter that will return files matching a glob
   pattern. with\_items: "/foo/pattern/\*.txt \| fileglob"
-  'changed' filter returns whether a previous step was changed easier.
   when: registered\_result \| changed
-  DOCS NEEDED: 'unique' and 'intersect' filters are added for dealing
   with lists.
-  DOCS NEEDED: new lookup plugin added for etcd
-  a 'func' connection type to help people migrating from
   func/certmaster.

Misc changes (all module additions/fixes may not listed):

-  (docs pending) New features for accelerate mode: configurable
   timeouts and a keepalives for long running tasks.
-  Added a ``delimiter`` field to the assemble module.
-  Added ``ansible_env`` to the list of facts returned by the setup
   module.
-  Added ``state=touch`` to the file module, which functions similarly
   to the command-line version of ``touch``.
-  Added a -vvvv level, which will show SSH client debugging information
   in the event of a failure.
-  Includes now support the more standard syntax, similar to that of
   role includes and dependencies.
-  Changed the ``user:`` parameter on plays to ``remote_user:`` to
   prevent confusion with the module of the same name. Still backwards
   compatible on play parameters.
-  Added parameter to allow the fetch module to skip the md5 validation
   step ('validate\_md5=false'). This is useful when fetching files that
   are actively being written to, such as live log files.
-  Inventory hosts are used in the order they appear in the inventory.
-  in hosts: foo[2-5] type syntax, the iterators now are zero indexed
   and the last index is non-inclusive, to match Python standards.
-  There is now a way for a callback plugin to disable itself. See
   osx\_say example code for an example.
-  Many bugfixes to modules of all types.
-  Complex arguments now can be used with async tasks
-  SSH ControlPath is now configurable in ansible.cfg. There is a limit
   to the lengths of these paths, see how to shorten them in
   ansible.cfg.
-  md5sum support on AIX with csum.
-  Extremely large documentation refactor into subchapters
-  Added 'append\_privs' option to the mysql\_user module
-  Can now update (temporarily change) host variables using the
   "add\_host" module for existing hosts.
-  Fixes for IPv6 addresses in inventory text files
-  name of executable can be passed to pip/gem etc, for installing under
   *different* interpreters
-  copy of ./hacking/env-setup added for fish users,
   ./hacking/env-setup.fish
-  file module more tolerant of non-absolute paths in softlinks.
-  miscellaneous fixes/upgrades to async polling logic.
-  conditions on roles now pass to dependent roles
-  ansible\_sudo\_pass can be set in a host variable if desired
-  misc fixes for the pip an easy\_install modules
-  support for running handlers that have parameterized names based on
   role parameters
-  added support for compressing MySQL dumps and extracting during
   import
-  Boto version compatibility fixes for the EC2 inventory script
-  in the EC2 inventory script, a group 'EC2' and 'RDS' contains EC2 and
   RDS hosts.
-  umask is enforced by the cron module
-  apt packages that are not-removed and not-upgraded do not count as
   changes
-  the assemble module can now use src files from the local server and
   copy them over dynamically
-  authorization code has been standardized between Amazon cloud modules
-  the wait\_for module can now also wait for files to exist or a regex
   string to exist in a file
-  leading ranges are now allowed in ranged hostname patterns, ex:
   [000-250].example.com
-  pager support added to ansible-doc (so it will auto-invoke less, etc)
-  misc fixes to the cron module
-  get\_url module now understands content-disposition headers for
   deciding filenames
-  it is possible to have subdirectories in between group\_vars/ and
   host\_vars/ and the final filename, like host\_vars/rack42/asdf for
   the variables for host 'asdf'. The intermediate directories are
   ignored, and do not put a file in there twice.

1.3.4 "Top of the World" (reprise) - October 29, 2013
-----------------------------------------------------

-  Fixed a bug in the copy module, where a filename containing the
   string "raw" was handled incorrectly
-  Fixed a bug in accelerate mode, where copying a zero-length file out
   would fail

1.3.3 "Top of the World" (reprise) - October 9, 2013
----------------------------------------------------

Additional fixes for accelerate mode.

1.3.2 "Top of the World" (reprise) - September 19th, 2013
---------------------------------------------------------

Multiple accelerate mode fixes:

-  Make packet reception less greedy, so multiple frames of data are not
   consumed by one call.
-  Adding two timeout values (one for connection and one for data
   reception timeout).
-  Added keepalive packets, so async mode is no longer required for
   long-running tasks.
-  Modified accelerate daemon to use the verbose logging level of the
   ansible command that started it.
-  Fixed bug where accelerate would not work in check-mode.
-  Added a -vvvv level, which will show SSH client debugging information
   in the event of a failure.
-  Fixed bug in apt\_repository module where the repository cache was
   not being updated.
-  Fixed bug where "too many open files" errors would be encountered due
   to pseudo TTY's not being closed properly.

1.3.1 "Top of the World" (reprise) - September 16th, 2013
---------------------------------------------------------

Fixing a bug in accelerate mode whereby the gather\_facts step would
always be run via sudo regardless of the play settings.

1.3 "Top of the World" - September 13th, 2013
---------------------------------------------

Highlighted new features:

-  accelerated mode: An enhanced fireball mode that requires zero
   bootstrapping and fewer requirements plus adds capabilities like sudo
   commands.
-  role defaults: Allows roles to define a set of variables at the
   lowest priority. These variables can be overridden by any other
   variable.
-  new /etc/ansible/facts.d allows JSON or INI-style facts to be
   provided from the remote node, and supports executable fact programs
   in this dir. Files must end in \*.fact.
-  added the ability to make undefined template variables raise errors
   (see ansible.cfg)
-  (DOCS PENDING) sudo: True/False and sudo\_user: True/False can be set
   at include and role level
-  added changed\_when: (expression) which allows overriding whether a
   result is changed or not and can work with registered expressions
-  --extra-vars can now take a file as input, e.g., "-e @filename" and
   can also be formatted as YAML
-  external inventory scripts may now return host variables in one pass,
   which allows them to be much more efficient for large numbers of
   hosts
-  if --forks exceeds the numbers of hosts, it will be automatically
   reduced. Set forks to 0 and you get "as many forks as I have hosts"
   out of the box.
-  enabled error\_on\_undefined\_vars by default, which will make errors
   in playbooks more obvious
-  role dependencies -- one role can now pull in another, with
   parameters of its own.
-  added the ability to have tasks execute even during a check run
   (always\_run).
-  added the ability to set the maximum failure percentage for a group
   of hosts.

New modules:

-  notifications
-  datadog\_event *-- send data to datadog*
-  cloud
-  digital\_ocean *-- module for DigitalOcean provisioning that also
   includes inventory support*
-  rds *-- Amazon Relational Database Service*
-  linode *-- modules for Linode provisioning that also includes
   inventory support*
-  route53 *-- manage Amazon DNS entries*
-  ec2\_ami *-- manages (and creates!) ec2 AMIs*
-  database
-  mysql\_replication *-- manages mysql replication settings for
   masters/slaves*
-  mysql\_variables *-- manages mysql runtime variables*
-  redis *-- manages redis databases (slave mode and flushing data)*
-  net\_infrastructure
-  arista\_interface
-  arista\_l2interface
-  arista\_lag
-  arista\_vlan
-  dnsmadeeasy *-- manipulate DNS Made Easy records*
-  system
-  stat *-- reports on stat(istics) of remote files, for use with
   'register'*
-  web\_infrastructure
-  htpasswd *-- manipulate htpasswd files*
-  packaging
-  apt\_repository *-- rewritten to remove dependencies*
-  rpm\_key *-- adds or removes RPM signing keys*
-  monitoring
-  boundary\_meter *-- adds or removes boundary.com meters*
-  files
-  xattr *-- manages extended attributes on files*

Misc changes:

-  return 3 when there are hosts that were unreachable during a run
-  the yum module now supports wildcard values for the enablerepo
   argument
-  added an inventory script to pull host information from Zabbix
-  async mode no longer allows with\_\* lookup plugins due to
   incompatibilities
-  Added OpenRC support (Gentoo) to the service module
-  ansible\_ssh\_user value is available to templates
-  added placement\_group parameter to ec2 module
-  new sha256sum parameter added to get\_url module for checksum
   validation
-  search for mount binaries in system path and sbin vs assuming path
-  allowed inventory file to be read from a pipe
-  added Solaris distribution facts
-  fixed bug along error path in quantum\_network module
-  user password update mode is controllable in user module now (at
   creation vs. every time)
-  added check mode support to the OpenBSD package module
-  Fix for MySQL 5.6 compatibility
-  HP UX virtualization facts
-  fixed some executable bits in git
-  made rhn\_register module compatible with EL5
-  fix for setup module epoch time on Solaris
-  sudo\_user is now expanded later, allowing it to be set at inventory
   scope
-  mongodb\_user module changed to also support MongoDB 2.2
-  new state=hard option added to the file module for hardlinks vs
   softlinks
-  fixes to apt module purging option behavior
-  fixes for device facts with multiple PCI domains
-  added "with\_inventory\_hostnames" lookup plugin, which can take a
   pattern and loop over hostnames matching the pattern and is great for
   use with delegate\_to and so on
-  ec2 module supports adding to multiple security groups
-  cloudformation module includes fixes for the error path, and the
   'wait\_for' parameter was removed
-  added --only-if-changed to ansible-pull, which runs only if the repo
   has changes (not default)
-  added 'mandatory', a Jinja2 filter that checks if a variable is
   defined: {{ foo\|mandatory }}
-  added support for multiple size formats to the lvol module
-  timing reporting on wait\_for module now includes the delay time
-  IRC module can now send a server password
-  "~" now expanded on each component of configured plugin paths
-  fix for easy\_install module when dealing with virtualenv
-  rackspace module now explicitly indicates rackspace vs vanilla
   openstack
-  add\_host module does not report changed=True any longer
-  explanatory error message when using fireball with sudo has been
   improved
-  git module now automatically pulls down git submodules
-  negated patterns do not require "all:!foo", you can just say "!foo"
   now to select all not foos
-  fix for Debian services always reporting changed when toggling
   enablement bit
-  roles files now tolerate files named 'main.yaml' and 'main' in
   addition to main.yml
-  some help cleanup to command line flags on scripts
-  force option reinstated for file module so it can create symlinks to
   non-existent files, etc.
-  added termination support to ec2 module
-  --ask-sudo-pass or --sudo-user does not enable all options to use
   sudo in ansible-playbook
-  include/role conditionals are added ahead of task conditionals so
   they can short circuit properly
-  added pipes.quote in various places so paths with spaces are better
   tolerated
-  error handling while executing Jinja2 filters has been improved
-  upgrades to atomic replacement logic when copying files across
   partitions/etc
-  mysql user module can try to login before requiring explicit password
-  various additional options added to supervisorctl module
-  only add non unique parameter on group creation when required
-  allow rabbitmq\_plugin to specify a non-standard RabbitMQ path
-  authentication fixes to keystone\_user module
-  added IAM role support to EC2 module
-  fixes for OpenBSD package module to avoid shell expansion
-  git module upgrades to allow --depth and --version to be used
   together
-  new lookup plugin, "with\_flattened"
-  extra vars (-e) variables can be used in playbook include paths
-  improved reporting for invalid sudo passwords
-  improved reporting for inability to find a suitable tmp location
-  require libselinux-python to perform file operations if SELinux is
   operational
-  ZFS module fixes for byte display constants and handling paths with
   spaces
-  setup module more tolerant of gathering facts against things it does
   not have permission to read
-  can specify name=\* state=latest to update all yum modules
-  major speedups to the yum module for default cases
-  ec2\_facts module will now run in check mode
-  sleep option on service module for sleeping between stop/restart
-  fix for IPv6 facts on BSD
-  added Jinja2 filters: skipped, whether a result was skipped
-  added Jinja2 filters: quote, quotes a string if it needs to be quoted
-  allow force=yes to affect apt upgrades
-  fix for saving conditionals in variable names
-  support for multiple host ranges in INI inventory, e.g.,
   db[01:10:3]node-[01:10]
-  fixes/improvements to cron module
-  add user\_install=no option to gem module to install gems system wide
-  added raw=yes to allow copying without python on remote machines
-  added with\_indexed\_items lookup plugin
-  Linode inventory plugin now significantly faster
-  added recurse=yes parameter to pacman module for package removal
-  apt\_key module can now target specific keyrings (keyring=filename)
-  ec2 module change reporting improved
-  hg module now expands user paths (~)
-  SSH connection type known host checking now can process hashed
   known\_host files
-  lvg module now checks for executables in more correct locations
-  copy module now works correctly with sudo\_user
-  region parameter added to ec2\_elb module
-  better default XMPP module message types
-  fixed conditional tests against raw booleans
-  mysql module grant removal is now smarter
-  apt-remove is now forced to be non-interactive
-  support ; comments in INI file module
-  fixes to callbacks WRT async output (fire and forget tasks now
   trigger callbacks!)
-  folder support for s3 module
-  added new example inventory plugin for Red Hat OpenShift
-  and other misc. bugfixes

1.2.3 "Hear About It Later" (reprise) -- Aug 21, 2013
-----------------------------------------------------

-  Local security fixes for predictable file locations for
   ControlPersist and retry file paths on shared machines on operating
   systems without kernel symlink/hardlink protections.

1.2.2 "Hear About It Later" (reprise) -- July 4, 2013
-----------------------------------------------------

-  Added a configuration file option [paramiko\_connection]
   record\_host\_keys which allows the code that paramiko uses to update
   known\_hosts to be disabled. This is done because paramiko can be
   very slow at doing this if you have a large number of hosts and some
   folks may not want this behavior. This can be toggled independently
   of host key checking and does not affect the ssh transport plugin.
   Use of the ssh transport plugin is preferred if you have
   ControlPersist capability, and Ansible by default in 1.2.1 and later
   will autodetect.

1.2.1 "Hear About It Later" -- July 4, 2013
-------------------------------------------

-  Connection default is now "smart", which discovers if the system
   openssh can support ControlPersist, and uses it if so, if not falls
   back to paramiko.
-  Host key checking is on by default. Disable it if you like by adding
   host\_key\_checking=False in the [default] section of
   /etc/ansible/ansible.cfg or ~/ansible.cfg or by exporting
   ANSIBLE\_HOST\_KEY\_CHECKING=False
-  Paramiko now records host keys it was in contact with host key
   checking is on. It is somewhat sluggish when doing this, so switch to
   the 'ssh' transport if this concerns you.

1.2 "Right Now" -- June 10, 2013
--------------------------------

Core Features:

-  capability to set 'all\_errors\_fatal: True' in a playbook to force
   any error to stop execution versus a whole group or serial block
   needing to fail usable, without breaking the ability to override in
   ansible
-  ability to use variables from {{ }} syntax in mainline playbooks, new
   'when' conditional, as detailed in documentation. Can disable old
   style replacements in ansible.cfg if so desired, but are still active
   by default.
-  can set ansible\_ssh\_private\_key\_file as an inventory variable
   (similar to ansible\_ssh\_host, etc)
-  'when' statement can be affixed to task includes to auto-affix the
   conditional to each task therein
-  cosmetic: "\*\*\*\*\*" banners in ansible-playbook output are now
   constant width
-  --limit can now be given a filename (--limit @filename) to constrain
   a run to a host list on disk
-  failed playbook runs will create a retry file in /var/tmp/ansible
   usable with --limit
-  roles allow easy arrangement of reusable
   tasks/handlers/files/templates
-  pre\_tasks and post\_tasks allow for separating tasks into blocks
   where handlers will fire around them automatically
-  "meta: flush\_handler" task capability added for when you really need
   to force handlers to run
-  new --start-at-task option to ansible playbook allows starting at a
   specific task name in a long playbook
-  added a log file for ansible/ansible-playbook, set 'log\_path' in the
   configuration file or ANSIBLE\_LOG\_PATH in environment
-  debug mode always outputs debug in playbooks, without needing to
   specify -v
-  external inventory script added for Spacewalk / Red Hat Satellite
   servers
-  It is now possible to feed JSON structures to --extra-vars. Pass in a
   JSON dictionary/hash to feed in complex data.
-  group\_vars/ and host\_vars/ directories can now be kept alongside
   the playbook as well as inventory (or both!)
-  more filters: ability to say {{ foo\|success }} and {{ foo\|failed }}
   and when: foo\|success and when: foo\|failed
-  more filters: {{ path\|basename }} and {{ path\|dirname }}
-  lookup plugins now use the basedir of the file they have included
   from, avoiding needs of ../../../ in places and increasing the ease
   at which things can be reorganized.

Modules added:

-  cloud
-  rax *-- module for creating instances in the rackspace cloud (uses
   pyrax)*
-  packages
-  npm *-- node.js package management*
-  pkgng *-- next-gen package manager for FreeBSD*
-  redhat\_subscription *-- manage Red Hat subscription usage*
-  rhn\_register *-- basic RHN registration*
-  zypper *(SuSE)*
-  database
-  postgresql\_priv *-- manages postgresql privileges*
-  networking
-  bigip\_pool *-- load balancing with F5s*
-  ec2\_elb *-- add and remove machines from ec2 elastic load balancers*
-  notification
-  hipchat *-- send notification events to hipchat*
-  flowdock *-- send messages to flowdock during playbook runs*
-  campfire *-- send messages to campfire during playbook runs*
-  mqtt *-- send messages to the Mosquitto message bus*
-  irc *-- send messages to IRC channels*
-  filesystem *-- a wrapper around mkfs*
-  jabber *-- send jabber chat messages*
-  osx\_say *-- make OS X say things out loud*
-  openstack
-  glance\_image
-  nova\_compute
-  nova\_keypair
-  keystone\_user
-  quantum\_floating\_ip
-  quantum\_floating\_ip\_associate
-  quantum\_network
-  quantum\_router
-  quantum\_router\_gateway
-  quantum\_router\_interface
-  quantum\_subnet
-  monitoring
-  airbrake\_deployment *-- notify airbrake of new deployments*
-  monit
-  newrelic\_deployment *-- notifies newrelic of new deployments*
-  pagerduty
-  pingdom
-  utility
-  set\_fact *-- sets a variable, which can be the result of a template
   evaluation*

Modules removed

-  vagrant -- can't be compatible with both versions at once, just run
   things though the vagrant provisioner in vagrant core

Bugfixes and Misc Changes:

-  service module happier if only enabled=yes\|no specified and no state
-  mysql\_db: use --password= instead of -p in dump/import so it doesn't
   go interactive if no pass set
-  when using -c ssh and the ansible user is the current user, don't
   pass a -o to allow SSH config to be
-  overwrite parameter added to the s3 module
-  private\_ip parameter added to the ec2 module
-  $FILE and $PIPE now tolerate unicode
-  various plugin loading operations have been made more efficient
-  hostname now uses platform.node versus socket.gethostname to be more
   consistent with Unix 'hostname'
-  fix for SELinux operations on Unicode path names
-  inventory directory locations now ignore files with .ini extensions,
   making hybrid inventory easier
-  copy module in check-mode now reports back correct changed status
   when used with force=no
-  added avail. zone to ec2 module
-  fixes to the hash variable merging logic if so enabled in the main
   settings file (default is to replace, not merge hashes)
-  group\_vars and host\_vars files can now end in a .yaml or .yml
   extension, (previously required no extension, still favored)
-  ec2vol module improvements
-  if the user module is told to generate the ssh key, the key generated
   is now returned in the results
-  misc fixes to the Riak module
-  make template module slightly more efficient
-  base64encode / decode filters are now available to templates
-  libvirt module can now work with multiple different libvirt
   connection URIs
-  fix for postgresql password escaping
-  unicode fix for shlex.split in some cases
-  apt module upgrade logic improved
-  URI module now can follow redirects
-  yum module can now install off http URLs
-  sudo password now defaults to ssh password if you ask for both and
   just hit enter on the second prompt
-  validate feature on copy and template module, for example, running
   visudo prior to copying the file over
-  network facts upgraded to return advanced configs (bonding, etc)
-  region support added to ec2 module
-  riak module gets a wait for ring option
-  improved check mode support in the file module
-  exception handling added to handle scenario when attempt to log to
   systemd journal fails
-  fix for upstart handling when toggling the enablement and running
   bits at the same time
-  when registering a task with a conditional attached, and the task is
   skipped by the conditional, the variable is still registered for the
   host, with the attribute skipped: True.
-  delegate\_to tasks can look up ansible\_ssh\_private\_key\_file
   variable from inventory correctly now
-  s3 module takes a 'dest' parameter to change the destination for
   uploads
-  apt module gets a cache\_valid\_time option to avoid redundant cache
   updates
-  ec2 module better understands security groups
-  fix for postgresql codec usage
-  setup module now tolerant of OpenVZ interfaces
-  check mode reporting improved for files and directories
-  doc system now reports on module requirements
-  group\_by module can now also make use of globally scoped variables
-  localhost and 127.0.0.1 are now fuzzy matched in inventory (are now
   more or less interchangeable)
-  AIX improvements/fixes for users, groups, facts
-  lineinfile now does atomic file replacements
-  fix to not pass PasswordAuthentication=no in the config file
   unnecessarily for SSH connection type
-  for authorized\_key on Debian Squeeze
-  fixes for apt\_repository module reporting changed incorrectly on
   certain repository types
-  allow the virtualenv argument to the pip module to be a pathname
-  service pattern argument now correctly read for BSD services
-  fetch location can now be controlled more directly via the 'flat'
   parameter.
-  added basename and dirname as Jinja2 filters available to all
   templates
-  pip works better when sudoing from unprivileged users
-  fix for user creation with groups specification reporting 'changed'
   incorrectly in some cases
-  fix for some unicode encoding errors in outputing some data in
   verbose mode
-  improved FreeBSD, NetBSD and Solaris facts
-  debug module always outputs data without having to specify -v
-  fix for sysctl module creating new keys (must specify checks=none)
-  NetBSD and OpenBSD support for the user and groups modules
-  Add encrypted password support to password lookup

1.1 "Mean Street" -- 4/2/2013
-----------------------------

Core Features

-  added --check option for "dry run" mode
-  added --diff option to show how templates or copied files change, or
   might change
-  --list-tasks for the playbook will list the tasks without running
   them
-  able to set the environment by setting "environment:" as a dictionary
   on any task (go proxy support!)
-  added ansible\_ssh\_user and ansible\_ssh\_pass for per-host/group
   username and password
-  jinja2 extensions can now be loaded from the config file
-  support for complex arguments to modules (within reason)
-  can specify ansible\_connection=X to define the connection type in
   inventory variables
-  a new chroot connection type
-  module common code now has basic type checking (and casting)
   capability
-  module common now supports a 'no\_log' attribute to mark a field as
   not to be syslogged
-  inventory can now point to a directory containing multiple
   scripts/hosts files, if using this, put group\_vars/host\_vars
   directories inside this directory
-  added configurable crypt scheme for 'vars\_prompt'
-  password generating lookup plugin -- $PASSWORD(path/to/save/data/in)
-  added --step option to ansible-playbook, works just like Linux
   interactive startup!

Modules Added:

-  bzr *(bazaar version control)*
-  cloudformation
-  django-manage
-  gem *(ruby gems)*
-  homebrew
-  lvg *(logical volume groups)*
-  lvol *(LVM logical volumes)*
-  macports
-  mongodb\_user
-  netscaler
-  okg
-  openbsd\_pkg
-  rabbit\_mq\_parameter
-  rabbit\_mq\_plugin
-  rabbit\_mq\_user
-  rabbit\_mq\_vhost
-  rhn\_channel
-  s3 *-- allows putting file contents in buckets for sharing over s3*
-  uri module *-- can get/put/post/etc*
-  vagrant *-- launching VMs with vagrant, this is different from
   existing vagrant plugin*
-  zfs

Bugfixes and Misc Changes:

-  stderr shown when commands fail to parse
-  uses yaml.safe\_dump in filter plugins
-  authentication Q&A no longer happens before --syntax-check, but after
-  ability to get hostvars data for nodes not in the setup cache yet
-  SSH timeout now correctly passed to native SSH connection plugin
-  raise an error when multiple when\_ statements are provided
-  --list-hosts applies host limit selections better
-  (internals) template engine specifications to use template\_ds
   everywhere
-  better error message when your host file can not be found
-  end of line comments now work in the inventory file
-  directory destinations now work better with remote md5 code
-  lookup plugin macros like $FILE and $ENV now work without returning
   arrays in variable definitions/playbooks
-  uses yaml.safe\_load everywhere
-  able to add EXAMPLES to documentation via EXAMPLES docstring, rather
   than just in main documentation YAML
-  can set ANSIBLE\_COW\_SELECTION to pick other cowsay types (including
   random)
-  to\_nice\_yaml and to\_nice\_json available as Jinja2 filters that
   indent and sort
-  cowsay able to run out of macports (very important!)
-  improved logging for fireball mode
-  nicer error message when talking to an older system that needs a JSON
   module installed
-  'magic' variable 'inventory\_dir' now gives path to inventory file
-  'magic' variable 'vars' works like 'hostvars' but gives global scope
   variables, useful for debugging in templates mostly
-  conditionals can be used on plugins like add\_host
-  developers: all callbacks now have access to a ".runner" and
   ".playbook", ".play", and ".task" object (use getattr, they may not
   always be set!)

Facts:

-  block device facts for the setup module
-  facts for AIX
-  fact detection for OS type on Amazon Linux
-  device fact gathering stability improvements
-  ansible\_os\_family fact added
-  user\_id (remote user name)
-  a whole series of current time information under the 'datetime' hash
-  more OS X facts
-  support for detecting Alpine Linux
-  added facts for OpenBSD

Module Changes/Fixes:

-  ansible module common code (and ONLY that) which is mixed in with
   modules, is now BSD licensed. App remains GPLv3.
-  service code works better on platforms that mix upstart, systemd, and
   system-v
-  service enablement idempotence fixes for systemd and upstart
-  service status 4 is also 'not running'
-  supervisorctl restart fix
-  increased error handling for ec2 module
-  can recursively set permissions on directories
-  ec2: change to the way AMI tags are handled
-  cron module can now also manipulate cron.d files
-  virtualenv module can now inherit system site packages (or not)
-  lineinfile module now has an insertbefore option
-  NetBSD service module support
-  fixes to sysctl module where item has multiple values
-  AIX support for the user and group modules
-  able to specify a different hg repo to pull from than the original
   set
-  add\_host module can set ports and other inventory variables
-  add\_host module can add modules to multiple groups (groups=a,b,c),
   groups now alias for groupname
-  subnet ID can be set on EC2 module
-  MySQL module password handling improvements
-  added new virtualenv flags to pip and easy\_install modules
-  various improvements to lineinfile module, now accepts common
   arguments from file
-  force= now replaces thirsty where used before, thirsty remains an
   alias
-  setup module can take a 'filter=' parameter to just return a few
   facts (not used by playbooks)
-  cron module works even if no crontab is present (for cron.d)
-  security group ID settable on EC2 module
-  misc fixes to sysctl module
-  fix to apt module so packages not in cache are still removable
-  charset fix to mail module
-  postresql db module now does not try to create the 'PUBLIC' user
-  SVN module now works correctly with self signed certs
-  apt module now has an upgrade parameter (values=yes, no, or 'dist')
-  nagios module gets new silence/unsilence commands
-  ability to disable proxy usage in get\_url (use\_proxy=no)
-  more OS X facts
-  added a 'fail\_on\_missing' (default no) option to fetch
-  added timeout to the uri module (default 30 seconds, adjustable)
-  ec2 now has a 'wait' parameter to wait for the instance to be active,
   eliminates need for separate wait\_for call.
-  allow regex backreferences in lineinfile
-  id attribute on ec2 module can be used to set
   idempotent-do-not-recreate launches
-  icinga support for nagios module
-  fix default logins when no my.conf for MySQL module
-  option to create users with non-unique UIDs (user module)
-  macports module can enable/disable packages
-  quotes in my.cnf are stripped by the MySQL modules
-  Solaris Service management added
-  service module will attempt to auto-add unmanaged chkconfig services
   when needed
-  service module supports systemd service unit files

Plugins:

-  added 'with\_random\_choice' filter plugin
-  fixed ~ expansion for fileglob
-  with\_nested allows for nested loops (see examples in
   examples/playbooks)

1.0 "Eruption" -- Feb 1 2013
----------------------------

New modules:

-  apt\_key
-  ec2\_facts
-  hg *(now in core)*
-  pacman *(Arch linux)*
-  pkgin *(Joyent SmartOS)*
-  sysctl

New config settings:

-  sudo\_exe parameter can be set in config to use sudo alternatives
-  sudo\_flags parameter can alter the flags used with sudo

New playbook/language features:

-  added when\_failed and when\_changed
-  task includes can now be of infinite depth
-  when\_set and when\_unset can take more than one var (when\_set: $a
   and $b and $c)
-  added the with\_sequence lookup plugin
-  can override "connection:" on an individual task
-  parameterized playbook includes can now define complex variables (not
   just all on one line)
-  making inventory variables available for use in vars\_files paths
-  messages when skipping plays are now more clear
-  --extra-vars now has maximum precedence (as intended)

Module fixes and new flags:

-  ability to use raw module without python on remote system
-  fix for service status checking on Ubuntu
-  service module now responds to additional exit code for
   SERVICE\_UNAVAILABLE
-  fix for raw module with '-c local'
-  various fixes to git module
-  ec2 module now reports the public DNS name
-  can pass executable= to the raw module to specify alternative shells
-  fix for postgres module when user contains a "-"
-  added additional template variables -- $template\_fullpath and
   $template\_run\_date
-  raise errors on invalid arguments used with a task include statement
-  shell/command module takes a executable= parameter to specify a
   different shell than /bin/sh
-  added return code and error output to the raw module
-  added support for @reboot to the cron module
-  misc fixes to the pip module
-  nagios module can schedule downtime for all services on the host
-  various subversion module improvements
-  various mail module improvements
-  SELinux fix for files created by authorized\_key module
-  "template override" ??
-  get\_url module can now send user/password authorization
-  ec2 module can now deploy multiple simultaneous instances
-  fix for apt\_key modules stalling in some situations
-  fix to enable Jinja2 {% include %} to work again in template
-  ec2 module is now powered by Boto
-  setup module can now detect if package manager is using pacman
-  fix for yum module with enablerepo in use on EL 6

Core fixes and new behaviors:

-  various fixes for variable resolution in playbooks
-  fixes for handling of "~" in some paths
-  various fixes to DWIM'ing of relative paths
-  /bin/ansible now takes a --list-hosts just like ansible-playbook did
-  various patterns can now take a regex vs a glob if they start with
   "~" (need docs on which!) - also /usr/bin/ansible
-  allow intersecting host patterns by using "&"
   ("webservers:!debian:&datacenter1")
-  handle tilde shell character for --private-key
-  hash merging policy is now selectable in the config file, can choose
   to override or merge
-  environment variables now available for setting all plugin paths
   (ANSIBLE\_CALLBACK\_PLUGINS, etc)
-  added packaging file for macports (not upstreamed yet)
-  hacking/test-module script now uses /usr/bin/env properly
-  fixed error formatting for certain classes of playbook syntax errors
-  fix for processing returns with large volumes of output

Inventory files/scripts:

-  hostname patterns in the inventory file can now use alphabetic ranges
-  whitespace is now allowed around group variables in the inventory
   file
-  inventory scripts can now define groups of groups and group vars
   (need example for docs?)

0.9 "Dreams" -- Nov 30 2012
---------------------------

Highlighted core changes:

-  various performance tweaks, ansible executes dramatically less SSH
   ops per unit of work
-  close paramiko SFTP connections less often on copy/template
   operations (speed increase)
-  change the way we use multiprocessing (speed/RAM usage improvements)
-  able to set default for asking password & sudo password in config
   file
-  ansible now installs nicely if running inside a virtualenv
-  flag to allow SSH connection to move files by scp vs sftp (in config
   file)
-  additional RPM subpackages for easily installing fireball mode deps
   (server and node)
-  group\_vars/host\_vars now available to ansible, not just playbooks
-  native ssh connection type (-c ssh) now supports passwords as well as
   keys
-  ansible-doc program to show details

Other core changes:

-  fix for template calls when last character is '$'
-  if ansible\_python\_interpreter is set on a delegated host, it now
   works as intended
-  --limit can now take "," as separator as well as ";" or ":"
-  msg is now displaced with newlines when a task fails
-  if any with\_ plugin has no results in a list (empty list for
   with\_items, etc), the task is now skipped
-  various output formatting fixes/improvements
-  fix for Xen dom0/domU detection in default facts
-  'ansible\_domain' fact now available (ex value: example.com)
-  configured remote temp file location is now always used even for root
-  'register'-ed variables are not recorded for skipped hosts (for
   example, using only\_if/when)
-  duplicate host records for the same host can no longer result when a
   host is listed in multiple groups
-  ansible-pull now passes --limit to prevent running on multiple hosts
   when used with generic playbooks
-  remote md5sum check fixes for Solaris 10
-  ability to configure syslog facility used by remote module calls
-  in templating, stray '$' characters are now handled more correctly

Playbook changes:

-  relative paths now work for 'first\_available\_file'
-  various templating engine fixes
-  'when' is an easier form of only if
-  --list-hosts on the playbook command now supports multiple playbooks
   on the same command line
-  playbook includes can now be parameterized

Module additions:

-  (addhost) new module for adding a temporary host record (used for
   creating new guests)
-  (group\_by) module allows partitioning hosts based on group data
-  (ec2) new module for creating ec2 hosts
-  (script) added 'script' module for pushing and running self-deleting
   remote scripts
-  (svr4pkg) solaris svr4pkg module

Module changes:

-  (authorized key) module uses temp file now to prevent failure on full
   disk
-  (fetch) now uses the 'slurp' internal code to work as you would
   expect under sudo'ed accounts
-  (fetch) internal usage of md5 sums fixed for BSD
-  (get\_url) thirsty is no longer required for directory destinations
-  (git) various git module improvements/tweaks
-  (group) now subclassed for various platforms, includes SunOS support
-  (lineinfile) create= option on lineinfile can create the file when it
   does not exist
-  (mysql\_db) module takes new grant options
-  (postgresql\_db) module now takes role\_attr\_flags
-  (service) further upgrades to service module service status reporting
-  (service) tweaks to get service module to play nice with BSD style
   service systems (rc.conf)
-  (service) possible to pass additional arguments to services
-  (shell) and command module now take an 'executable=' flag for
   specifying an alternate shell than /bin/sh
-  (user) ability to create SSH keys for users when using user module to
   create users
-  (user) atomic replacement of files preserves permissions of original
   file
-  (user) module can create SSH keys
-  (user) module now does Solaris and BSD
-  (yum) module takes enablerepo= and disablerepo=
-  (yum) misc yum module fixing for various corner cases

Plugin changes:

-  EC2 inventory script now produces nicer failure message if AWS is
   down (or similar)
-  plugin loading code now more streamlined
-  lookup plugins for DNS text records, environment variables, and redis
-  added a template lookup plugin $TEMPLATE('filename.j2')
-  various tweaks to the EC2 inventory plugin
-  jinja2 filters are now pluggable so it's easy to write your own
   (to\_json/etc, are now impl. as such)

0.8 "Cathedral" -- Oct 19, 2012
-------------------------------

Highlighted Core Changes:

-  fireball mode -- ansible can bootstrap a ephemeral 0mq (zeromq)
   daemon that runs as a given user and expires after X period of time.
   It is very fast.
-  playbooks with errors now return 2 on failure. 1 indicates a more
   fatal syntax error. Similar for /usr/bin/ansible
-  server side action code (template, etc) are now fully pluggable
-  ability to write lookup plugins, like the code powering
   "with\_fileglob" (see below)

Other Core Changes:

-  ansible config file can also go in 'ansible.cfg' in cwd in addition
   to ~/.ansible.cfg and /etc/ansible/ansible.cfg
-  fix for inventory hosts at API level when hosts spec is a list and
   not a colon delimited string
-  ansible-pull example now sets up logrotate for the ansible-pull cron
   job log
-  negative host matching (!hosts) fixed for external inventory script
   usage
-  internals: os.executable check replaced with utils function so it
   plays nice on AIX
-  Debian packaging now includes ansible-pull manpage
-  magic variable 'ansible\_ssh\_host' can override the hostname (great
   for usage with tunnels)
-  date command usage in build scripts fixed for OS X
-  don't use SSH agent with paramiko if a password is specified
-  make output be cleaner on multi-line command/shell errors
-  /usr/bin/ansible now prints things when tasks are skipped, like when
   creates= is used with -m command and /usr/bin/ansible
-  when trying to async a module that is not a 'normal' asyncable
   module, ansible will now let you know
-  ability to access inventory variables via 'hostvars' for hosts not
   yet included in any play, using on demand lookups
-  merged ansible-plugins, ansible-resources, and ansible-docs into the
   main project
-  you can set ANSIBLE\_NOCOWS=1 if you want to disable cowsay if it is
   installed. Though no one should ever want to do this! Cows are great!
-  you can set ANSIBLE\_FORCE\_COLOR=1 to force color mode even when
   running without a TTY
-  fatal errors are now properly colored red.
-  skipped messages are now cyan, to differentiate them from unchanged
   messages.
-  extensive documentation upgrades
-  delegate\_action to localhost (aka local\_action) will always use the
   local connection type

Highlighted playbook changes:

-  is\_set is available for use inside of an only\_if expression:
   is\_set('ansible\_eth0'). We intend to further upgrade this with a
   'when' keyword providing better options to 'only\_if' in the next
   release. Also is\_unset('ansible\_eth0')
-  playbooks can import playbooks in other directories and then be able
   to import tasks relative to them
-  FILE($path) now allows access of contents of file in a path, very
   good for use with SSH keys
-  similarly PIPE($command) will run a local command and return the
   results of executing this command
-  if all hosts in a play fail, stop the playbook, rather than letting
   the console log spool on by
-  only\_if using register variables that are booleans now works in a
   boolean way like you'd expect
-  task includes now work with with\_items (such as: include:
   path/to/wordpress.yml user=$item)
-  when using a $list variable with $var or ${var} syntax it will
   automatically join with commas
-  setup is not run more than once when we know it is has already been
   run in a play that included another play, etc
-  can set/override sudo and sudo\_user on individual tasks in a play,
   defaults to what is set in the play if not present
-  ability to use with\_fileglob to iterate over local file patterns
-  templates now use Jinja2's 'trim\_blocks=True' to avoid stray
   newlines, small changes to templates may be required in rare cases.

Other playbook changes:

-  to\_yaml and from\_yaml are available as Jinja2 filters
-  $group and $group\_names are now accessible in with\_items
-  where 'stdout' is provided a new 'stdout\_lines' variable (type ==
   list) is now generated and usable with with\_items
-  when local\_action is used the transport is automatically overridden
   to the local type
-  output on failed playbook commands is now nicely split for
   stderr/stdout and syntax errors
-  if local\_action is not used and delegate\_to was 127.0.0.1 or
   localhost, use local connection regardless
-  when running a playbook, and the statement has changed, prints
   'changed:' now versus 'ok:' so it is obvious without colored mode
-  variables now usable within vars\_prompt (just not host/group vars)
-  setup facts are now retained across plays (dictionary just gets
   updated as needed)
-  --sudo-user now works with --extra-vars
-  fix for multi\_line strings with only\_if

New Modules:

-  ini\_file module for manipulating INI files
-  new LSB facts (release, distro, etc)
-  pause module -- (pause seconds=10) (pause minutes=1) (pause
   prompt=foo) -- it's an action plugin
-  a module for adding entries to the main crontab (though you may still
   wish to just drop template files into cron.d)
-  debug module can be used for outputing messages without using 'shell
   echo'
-  a fail module is now available for causing errors, you might want to
   use it with only\_if to fail in certain conditions

Other module Changes, Upgrades, and Fixes:

-  removes= exists on command just like creates=
-  postgresql modules now take an optional port= parameter
-  /proc/cmdline info is now available in Linux facts
-  public host key detection for OS X
-  lineinfile module now uses 'search' not exact 'match' in regexes,
   making it much more intuitive and not needing regex syntax most of
   the time
-  added force=yes\|no (default no) option for file module, which allows
   transition between files to directories and so on
-  additional facts for SunOS virtualization
-  copy module is now atomic when used across volumes
-  url\_get module now returns 'dest' with the location of the file
   saved
-  fix for yum module when using local RPMs vs downloading
-  cleaner error messages with copy if destination directory does not
   exist
-  setup module now still works if PATH is not set
-  service module status now correct for services with 'subsys locked'
   status
-  misc fixes/upgrades to the wait\_for module
-  git module now expands any "~" in provided destination paths
-  ignore stop error code failure for service module with
   state=restarted, always try to start
-  inline documentation for modules allows documentation source to built
   without pull requests to the ansible-docs project, among other things
-  variable '$ansible\_managed' is now great to include at the top of
   your templates and includes useful information and a warning that it
   will be replaced
-  "~" now expanded in command module when using creates/removes
-  mysql module can do dumps and imports
-  selinux policy is only required if setting to not disabled
-  various fixes for yum module when working with packages not in any
   present repo

0.7 "Panama" -- Sept 6 2012
---------------------------

Module changes:

-  login\_unix\_socket option for mysql user and database modules (see
   PR #781 for doc notes)
-  new modules -- pip, easy\_install, apt\_repository, supervisorctl
-  error handling for setup module when SELinux is in a weird state
-  misc yum module fixes
-  better changed=True/False detection in user module on older Linux
   distros
-  nicer errors from modules when arguments are not key=value
-  backup option on copy (backup=yes), as well as template, assemble,
   and lineinfile
-  file module will not recurse on directory properties
-  yum module now workable without having repoquery installed, but
   doesn't support comparisons or list= if so
-  setup module now detects interfaces with aliases
-  better handling of VM guest type detection in setup module
-  new module boilerplate code to check for mutually required arguments,
   arguments required together, exclusive args
-  add pattern= as a parameter to the service module (for init scripts
   that don't do status, or do poor status)
-  various fixes to mysql & postresql modules
-  added a thirsty= option (boolean, default no) to the get\_url module
   to decide to download the file every time or not
-  added a wait\_for module to poll for ports being open
-  added a nagios module for controlling outage windows and alert
   statuses
-  added a seboolean module for getsebool/setsebool type operations
-  added a selinux module for controlling overall SELinux policy
-  added a subversion module
-  added lineinfile for adding and removing lines from basic files
-  added facts for ARM-based CPUs
-  support for systemd in the service module
-  git moduleforce reset behavior is now controllable
-  file module can now operate on special files (block devices, etc)

Core changes:

-  ansible --version will now give branch/SHA information if running
   from git
-  better sudo permissions when encountering different umasks
-  when using paramiko and SFTP is not accessible, do not traceback, but
   return a nice human readable msg
-  use -vvv for extreme debug levels. -v gives more playbook output as
   before
-  -vv shows module arguments to all module calls (and maybe some other
   things later)
-  don not pass "--" to sudo to work on older EL5
-  make remote\_md5 internal function work with non-bash shells
-  allow user to be passed in via --extra-vars (regression)
-  add --limit option, which can be used to further confine the pattern
   given in ansible-playbooks
-  adds ranged patterns like dbservers[0-49] for usage with patterns or
   --limit
-  -u and user: defaults to current user, rather than root, override as
   before
-  /etc/ansible/ansible.cfg and ~/ansible.cfg now available to set
   default values and other things
-  (developers) ANSIBLE\_KEEP\_REMOTE\_FILES=1 can be used in debugging
   (envrionment variable)
-  (developers) connection types are now plugins
-  (developers) callbacks can now be extended via plugins
-  added FreeBSD ports packaging scripts
-  check for terminal properties prior to engaging color modes
-  explicitly disable password auth with -c ssh, as it is not used
   anyway

Playbooks:

-  YAML syntax errors detected and show where the problem is
-  if you ctrl+c a playbook it will not traceback (usually)
-  vars\_prompt now has encryption options (see
   examples/playbooks/prompts.yml)
-  allow variables in parameterized task include parameters (regression)
-  add ability to store the result of any command in a register (see
   examples/playbooks/register\_logic.yml)
-  --list-hosts to show what hosts are included in each play of a
   playbook
-  fix a variable ordering issue that could affect vars\_files with
   selective file source lists
-  adds 'delegate\_to' for a task, which can be used to signal outage
   windows and load balancers on behalf of hosts
-  adds 'serial' to playbook, allowing you to specify how many hosts can
   be processing a playbook at one time (default 0=all)
-  adds 'local\_action: ' as an alias to 'delegate\_to: 127.0.0.1'

0.6 "Cabo" -- August 6, 2012
----------------------------

playbooks:

-  support to tag tasks and includes and use --tags in playbook CLI
-  playbooks can now include other playbooks
   (example/playbooks/nested\_playbooks.yml)
-  vars\_files now usable with with\_items, provided file paths don't
   contain host specific facts
-  error reporting if with\_items value is unbound
-  with\_items no longer creates lots of tasks, creates one task that
   makes multiple calls
-  can use host\_specific facts inside with\_items (see above)
-  at the top level of a playbook, set 'gather\_facts: no' to skip fact
   gathering
-  first\_available\_file and with\_items used together will now raise
   an error
-  to catch typos, like 'var' for 'vars', playbooks and tasks now yell
   on invalid parameters
-  automatically load
   (directory\_of\_inventory\_file)/group\_vars/groupname and
   /host\_vars/hostname in vars\_files
-  playbook is now colorized, set ANSIBLE\_NOCOLOR=1 if you do not like
   this, does not colorize if not a TTY
-  hostvars now preserved between plays (regression in 0.5 from 0.4),
   useful for sharing vars in multinode configs
-  ignore\_errors: yes on a task can be used to allow a task to fail and
   not stop the play
-  with\_items with the apt/yum module will install/remove/update
   everything in a single command

inventory:

-  groups variable available as a hash to return the hosts in each group
   name
-  in YAML inventory, hosts can list their groups in inverted order now
   also (see tests/yaml\_hosts)
-  YAML inventory is deprecated and will be removed in 0.7
-  ec2 inventory script
-  support ranges of hosts in the host file, like
   www[001-100].example.com (supports leading zeros and also not)

modules:

-  fetch module now does not fail a system when requesting file paths
   (ex: logs) that don't exist
-  apt module now takes an optional install-recommends=yes\|no (default
   yes)
-  fixes to the return codes of the copy module
-  copy module takes a remote md5sum to avoid large file transfer
-  various user and group module fixes (error handling, etc)
-  apt module now takes an optional force parameter
-  slightly better psychic service status handling for the service
   module
-  fetch module fixes for SSH connection type
-  modules now consistently all take yes/no for boolean parameters (and
   DWIM on true/false/1/0/y/n/etc)
-  setup module no longer saves to disk, template module now only used
   in playbooks
-  setup module no longer needs to run twice per playbook
-  apt module now passes DEBIAN\_FRONTEND=noninteractive
-  mount module (manages active mounts + fstab)
-  setup module fixes if no ipv6 support
-  internals: template in common module boilerplate, also causes less
   SSH operations when used
-  git module fixes
-  setup module overhaul, more modular
-  minor caching logic added to inventory to reduce hammering of
   inventory scripts.
-  MySQL and PostgreSQL modules for user and db management
-  vars\_prompt now supports private password entry (see
   examples/playbooks/prompts.yml)
-  yum module modified to be more tolerant of plugins spewing random
   console messages (ex: RHN)

internals:

-  when sudoing to root, still use /etc/ansible/setup as the metadata
   path, as if root
-  paramiko is now only imported if needed when running from source
   checkout
-  cowsay support on Ubuntu
-  various ssh connection fixes for old Ubuntu clients
-  ./hacking/test-module now supports options like ansible takes and has
   a debugger mode
-  sudoing to a user other than root now works more seamlessly (uses
   /tmp, avoids umask issues)

0.5 "Amsterdam" ------- July 04, 2012
-------------------------------------

-  Service module gets more accurate service states when running with
   upstart
-  Jinja2 usage in playbooks (not templates), reinstated, supports
   %include directive
-  support for --connection ssh (supports Kerberos, bastion hosts, etc),
   requires ControlMaster
-  misc tracebacks replaced with error messages
-  various API/internals refactoring
-  vars can be built from other variables
-  support for exclusion of hosts/groups with "!groupname"
-  various changes to support md5 tool differences for FreeBSD nodes &
   OS X clients
-  "unparseable" command output shows in command output for easier
   debugging
-  mktemp is no longer required on remotes (not available on BSD)
-  support for older versions of python-apt in the apt module
-  a new "assemble" module, for constructing files from pieces of files
   (inspired by Puppet "fragments" idiom)
-  ability to override most default values with ANSIBLE\_FOO environment
   variables
-  --module-path parameter can support multiple directories separated
   with the OS path separator
-  with\_items can take a variable of type list
-  ansible\_python\_interpreter variable available for systems with more
   than one Python
-  BIOS and VMware "fact" upgrades
-  cowsay is used by ansible-playbook if installed to improve output
   legibility (try installing it)
-  authorized\_key module
-  SELinux facts now sourced from the python selinux library
-  removed module debug option -D
-  added --verbose, which shows output from successful playbook
   operations
-  print the output of the raw command inside /usr/bin/ansible as with
   command/shell
-  basic setup module support for Solaris
-  ./library relative to the playbook is always in path so modules can
   be included in tarballs with playbooks

0.4 "Unchained" ------- May 23, 2012
------------------------------------

Internals/Core \* internal inventory API now more object oriented,
parsers decoupled \* async handling improvements \* misc fixes for
running ansible on OS X (overlord only) \* sudo improvements, now works
much more smoothly \* sudo to a particular user with -U/--sudo-user, or
using 'sudo\_user: foo' in a playbook \* --private-key CLI option to
work with pem files

Inventory \* can use -i host1,host2,host3:port to specify hosts not in
inventory (replaces --override-hosts) \* ansible INI style format can do
groups of groups [groupname:children] and group vars [groupname:vars] \*
groups and users module takes an optional system=yes\|no on creation
(default no) \* list of hosts in playbooks can be expressed as a YAML
list in addition to ; delimited

Playbooks \* variables can be replaced like
${foo.nested\_hash\_key.nested\_subkey[array\_index]} \* unicode now ok
in templates (assumes utf8) \* able to pass host specifier or group name
in to "hosts:" with --extra-vars \* ansible-pull script and example
playbook (extreme scaling, remediation) \* inventory\_hostname variable
available that contains the value of the host as ansible knows it \*
variables in the 'all' section can be used to define other variables
based on those values \* 'group\_names' is now a variable made available
to templates \* first\_available\_file feature, see
selective\_file\_sources.yml in examples/playbooks for info \*
--extra-vars="a=2 b=3" etc, now available to inject parameters into
playbooks from CLI

Incompatible Changes \* jinja2 is only usable in templates, not
playbooks, use $foo instead \* --override-hosts removed, can use -i with
comma notation (-i "ahost,bhost") \* modules can no longer include
stderr output (paramiko limitation from sudo)

Module Changes \* tweaks to SELinux implementation for file module \*
fixes for yum module corner cases on EL5 \* file module now correctly
returns the mode in octal \* fix for symlink handling in the file module
\* service takes an enable=yes\|no which works with chkconfig or
updates-rc.d as appropriate \* service module works better on Ubuntu \*
git module now does resets and such to work more smoothly on updates \*
modules all now log to syslog \* enabled=yes\|no on a service can be
used to toggle chkconfig & updates-rc.d states \* git module supports
branch= \* service fixes to better detect status using return codes of
the service script \* custom facts provided by the setup module mean no
dependency on Ruby, facter, or ohai \* service now has a state=reloaded
\* raw module for bootstrapping and talking to routers w/o Python, etc

Misc Bugfixes \* fixes for variable parsing in only\_if lines \* misc
fixes to key=value parsing \* variables with mixed case now legal \* fix
to internals of hacking/test-module development script

0.3 "Baluchitherium" -- April 23, 2012
--------------------------------------

-  Packaging for Debian, Gentoo, and Arch
-  Improvements to the apt and yum modules
-  A virt module
-  SELinux support for the file module
-  Ability to use facts from other systems in templates (aka exported
   resources like support)
-  Built in Ansible facts so you don't need ohai, facter, or Ruby
-  tempdir selections that work with noexec mounted /tmp
-  templates happen locally, not remotely, so no dependency on
   python-jinja2 for remote computers
-  advanced inventory format in YAML allows more control over variables
   per host and per group
-  variables in playbooks can be structured/nested versus just a flat
   namespace
-  manpage upgrades (docs)
-  various bugfixes
-  can specify a default --user for playbooks rather than specifying it
   in the playbook file
-  able to specify ansible port in ansible host file (see docs)
-  refactored Inventory API to make it easier to write scripts using
   Ansible
-  looping capability for playbooks (with\_items)
-  support for using sudo with a password
-  module arguments can be unicode
-  A local connection type, --connection=local, for use with cron or in
   kickstarts
-  better module debugging with -D
-  fetch module for pulling in files from remote hosts
-  command task supports creates=foo for idempotent semantics, won't run
   if file foo already exists

0.0.2 and 0.0.1
---------------

-  Initial stages of project
