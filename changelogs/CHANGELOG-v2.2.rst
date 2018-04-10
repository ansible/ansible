==================================================
Ansible 2.2 "The Battle of Evermore" Release Notes
==================================================
2.2.4 "The Battle of Evermore" - TBD
------------------------------------

-  avoid vault view writing to logs
-  moved htpasswd module to use LooseVersion vs StrictVersion to make
   usable on Debian
-  fix for adhoc not obeying callback options

2.2.3 "The Battle of Evermore" - 05-09-2017
-------------------------------------------

Major Changes:
~~~~~~~~~~~~~~

-  [SECURITY] (HIGH): fix for CVE-2017-7466, which was caused by an
   incomplete cherry-picking of commits related to CVE-2016-9587. This
   can lead to some jinja2 syntax not being stripped out of templated
   results.
-  [SECURITY] (MODERATE): fix for CVE-2017-7481, in which data for
   lookup plugins used as variables was not being correctly marked as
   "unsafe".

Minor Changes:
~~~~~~~~~~~~~~

-  Fixes a bug when using YAML inventory where hosts were not put in the
   'all' group, and some other 'ungrouped' issues in inventory.
-  Fixes a bug when using ansible commands without a tty for stdin.
-  Split on newlines when searching for become prompt.
-  Fix crash upon pass prompt in py3 when using the paramiko connection
   type.

2.2.2 "The Battle of Evermore" - 03-27-2017
-------------------------------------------

Major Changes:
~~~~~~~~~~~~~~

-  [SECURITY] (HIGH): (continued fix for CVE-2016-9587) Handle some
   additional corner cases in the way conditionals are parsed and
   evaluated.
-  [SECURITY] (LOW): properly filter passwords out of URLs when
   displaying output from some modules.

Minor Changes:
~~~~~~~~~~~~~~

-  Fix azure\_rm version checks (#22270).
-  Fix for traceback when we encounter non-utf8 characters when using
   --diff.
-  Ensure ssh hostkey checks respect server port.
-  Use proper PyYAML classes for safe loading YAML files.
-  Fix for bug related to when statements for older jinja2 versions.
-  Fix a bug/traceback when using to\_yaml/to\_nice\_yaml.
-  Properly clean data of jinja2-like syntax, even if that data came
   from an unsafe source.
-  Fix bug regarding undefined entries in HostVars.
-  Skip fact gathering if the entire play was included via conditional
   which evaluates to False.
-  Fixed a performance regression when using a large number of items in
   a with loop.
-  Fixed a bug in the way the end of role was detected, which in some
   cases could cause a role to be run more than once.
-  Add jinja2 groupby filter override to cast namedtuple to tuple to
   handle a non-compatible change in jinja2 2.9.4-2.9.5.
-  Fixed several bugs related to temp directory creation on remote
   systems when using shell expansions and become privilege escalation.
-  Fixed a bug related to spliting/parsing the output of a become
   privilege escalation when looking for a password prompt.
-  Several unicode/bytes fixes.

2.2.1 "The Battle of Evermore" - 01-16-2017
-------------------------------------------

Major Changes:
~~~~~~~~~~~~~~

-  Security fix for CVE-2016-9587 - An attacker with control over a
   client system being managed by Ansible and the ability to send facts
   back to the Ansible server could use this flaw to execute arbitrary
   code on the Ansible server as the user and group Ansible is running
   as.

Minor Changes
~~~~~~~~~~~~~

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
-  Fix regression in jinja2 include search path.
-  Various minor fixes for Python 3
-  Inserted some checks for jinja2-2.9, which can cause some issues with
   Ansible currently.

2.2 "The Battle of Evermore" - 11-01-2016
-----------------------------------------

Major Changes:
~~~~~~~~~~~~~~

-  Security fix for CVE-2016-8628 - Command injection by compromised
   server via fact variables. In some situations, facts returned by
   modules could overwrite connection-based facts or some other special
   variables, leading to injected commands running on the Ansible
   controller as the user running Ansible (or via escalated
   permissions).
-  Security fix for CVE-2016-8614 - apt\_key module not properly
   validating keys in some situations.
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

New Modules
^^^^^^^^^^^

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

New Callbacks
^^^^^^^^^^^^^

-  foreman

Minor Changes
~~~~~~~~~~~~~

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
-  The subversion module from core now marks its password parameter as
   no\_log so the password is obscured when logging.
-  The postgresql\_lang and postgresql\_ext modules from extras now mark
   login\_password as no\_log so the password is obscured when logging.
-  Fix for yum module incorrectly thinking it succeeded in installing
   packages
-  Make the default ansible\_managed template string into a static
   string since all of the replacable values lead to non-idempotent
   behaviour.

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

Removed Deprecated
~~~~~~~~~~~~~~~~~~

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
