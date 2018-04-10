=====================================
Ansible 2.3 "Ramble On" Release Notes
=====================================
2.3.4 "Ramble On" - TBD
-----------------------

-  Flush stdin when passing the become password. Fixes some cases of
   timeout on Python3 with the ssh connection plugin:
   https://github.com/ansible/ansible/pull/35049

Bugfixes
~~~~~~~~

-  Fix setting of environment in a task that uses a loop:
   https://github.com/ansible/ansible/issues/32685
-  Fix https retrieval with TLSv1.2:
   https://github.com/ansible/ansible/pull/32053

2.3.3 "Ramble On" - TBD
-----------------------

Bugfixes
~~~~~~~~

-  Security fix for CVE-2017-7550 the jenkins\_plugin module was logging
   the jenkins server password if the url\_password was passed via the
   params field: https://github.com/ansible/ansible/pull/30875
-  Fix alternatives module handlling of non existing options
-  Fix synchronize traceback with the docker connection plugin
-  Do not escape backslashes in the template lookup plugin to mirror
   what the template module does
-  Fix the expires option of the postgresq\_user module
-  Fix for win\_acl when settings permissions on registry objects that
   use ``ALL APPLICATION PACKAGES`` and
   ``ALL RESTRICTED APPLICATION PACKAGES``
-  Python3 fixes
-  asorted azure modules
-  pause module
-  hacking/env-setup script
-  Fix traceback when checking for passwords in logged strings when
   logging executed commands.
-  docker\_login module
-  Workaround python-libselinux API change in the seboolean module
-  digital\_ocean\_tag module
-  Fix the zip filter
-  Fix user module combining bytes and text
-  Fix for security groups in the amazon efs module
-  Fix for the jail connection plugin not finding the named jail
-  Fix for blockinfile's parameters insertbefore and insertafter
-  ios\_config: Fix traceback when the efaults parameter is not set
-  iosxr\_config: Fixed unicode error when UTF-8 characters are in
   configs
-  Fix check mode in archive module
-  Fix UnboundLocalError in check mode in cs\_role module
-  Fix to always use lowercase hostnames for host keys in known\_hosts
   module
-  Added missing return results for win\_stat
-  Fix rabbitmq modules to give a helpful error if requests is not
   installed
-  Fix yum module not deleting rpms that it downloaded
-  Fix yum module failing with a URL to an rpm
-  Fix file module inappropriately expanding literal dollar signs in a
   path read from the filesystem as an environment variable.
-  Fix the ssh "smart" transport setting which automatically selects the
   best means of transferring files over ssh (sftp, ssh, piped).
-  Fix authentication by api\_key parameter in exoscale modules.
-  vmware module\_utils shared code ssl/validate\_certs fixes in
   connection logic
-  allow 'bridge' facts to work for certain containers that create
   conflicting ones with connection plugins
-  Fix for win\_get\_url to use TLS 1.2/1.1 if it is available on the
   host
-  Fix for the filetree lookup with non-ascii group names
-  Better message for invalid keywords/options in task due to undefined
   expressions
-  Fixed check mode for enable on Solaris for service module
-  Fix cloudtrail module to allow AWS profiles other than the default
-  Fix an encoding issue with secret (password) vars\_prompts
-  Fix for Windows become to show the stdout and stderr strings on a
   failure
-  Fix the issue SSL verification can not be disabled for Tower modules
-  Use safe\_load instead on load to read a yaml document
-  Fix for win\_file to respect check mode when deleting directories
-  Include\_role now complains about invalid arguments
-  Added socket conditions to ignore for wait\_for, no need to error for
   closing already closed connection
-  Updated hostname module to work on newer RHEL7 releases
-  Security fix to avoid provider password leaking in logs for network
   modules

 \* Python3 fixes for azure modules

2.3.2 "Ramble On" - 2017-08-04
------------------------------

Bugfixes
~~~~~~~~

-  Fix partend i18n issues
-  fixed handling of extra vars for tower\_job\_template (#25272)
-  Python3 bugfixes
-  Fix sorting of ec2 policies
-  Fix digital\_ocean dynamic inventory script
-  Fix for the docker connection plugin
-  Fix pip module when using python3's pyvenv and python3 -m venv to
   create virtualenvs
-  Fix for the AnsiBallZ wrapper so that it gives a better error message
   when there's not enough disk space to create its tempdir.
-  Fix so ansilbe-galaxy install --force with unversioned roles will
   once again overwrite old versions.
-  Fix for RabbitMQ 3.6.7 endpoint return code changing.
-  Fix for Foreman organization creation
-  fixed incorrect fail\_json ref in rpm\_key
-  Corrected requried on hash\_name for dynamodb\_table
-  Fix for fetch action plugin not validating correctly
-  Avoid vault view writing display to logs
-  htpasswd: fix passlib module version comparison
-  Fix for flowdock error message when external\_user\_name is missing
-  fixed corner case for delegate\_to, loops and delegate\_facts
-  fixed wait\_for python2.4/2.5 compatibility (this is last version
   this is needed)
-  fix for adhoc not obeying callback options
-  fix for win\_find where it fails to recursively scan empty nested
   directories
-  fix non-pipelined code paths for Windows (eg,
   ANSIBLE\_KEEP\_REMOTE\_FILES, non-pipelined connection plugins)
-  fix for win\_updates where args and check mode were ignored due to
   common code change
-  fix for unprivileged users to Windows runas become method
-  fix starttls code path for mail module
-  fix missing LC\_TYPE in parted module
-  fix CN parsing with OpenSSL 1.1 in letsencrypt module
-  fix params assignment in jabber module
-  fix TXT record type handling in exo\_dns\_record module
-  fix message queue message ttl can't be 0 in rabbitmq\_queue module
-  CloudStack bugfixes:
-  fix template upload for users in cs\_template module, change default
   to is\_routing=None
-  several fixes in cs\_host module fixes hypervisor handling
-  fix network param ignored due typo in cs\_nic module
-  fix missing type bool in module cs\_zone
-  fix KeyError: 'sshkeypair' in cs\_instance module for CloudStack v4.5
   and before
-  fix for win\_chocolatey where trying to upgrade all the packages as
   per the example docs fails
-  fix for win\_chocolatey where it did not fail if the version set did
   not exist
-  fix for win\_regedit always changing a reg key if the dword values
   set is a hex
-  fix for wait\_for on non-Linux systems with newer versions of psutil
-  fix eos\_banner code and test issues
-  run tearup and teardown of EAPI service only on EAPI tests
-  fix eos\_config tests so only Eth1 and Eth2 are used
-  Fix for potential bug when using legacy inventory vars for
   configuring the su password.
-  Fix crash in file module when directories contain non-utf8 filenames
-  Fix for dnf groupinstall with dnf-2.x
-  Fix seboolean module for incompatibility in newer Python3 selinux
   bindings
-  Optimization for inventory, no need to dedup at every stage, its
   redundant and slow
-  Fix fact gathering for package and service action plugins
-  make random\_choice more error resilient (#27380)
-  ensure prefix in plugin loading to avoid conflicts
-  fix for a small number of modules (tempfile, possibly copy) which
   could fail if the tempdir on the remote box was a symlink
-  fix non-pipelined code paths for Windows (eg,
   ANSIBLE\_KEEP\_REMOTE\_FILES, non-pipelined connection plugins)
-  fix for win\_updates where args and check mode were ignored due to
   common code change

2.3.1 "Ramble On" - 2017-06-01
------------------------------

Bugfixes
~~~~~~~~

-  Security fix for CVE-2017-7481 - data for lookup plugins used as
   variables was not being correctly marked as "unsafe".
-  Fix default value of fetch module's validate\_checksum to be True
-  Added fix for "meta: refresh\_connection" not working with default
   'smart' connection.
-  Fix template so that the --diff command line option works when the
   destination is a directory
-  Fix python3 bugs in pam\_limits
-  Fix unbound error when using module deprecation as a single string
-  Several places in which error handling was broken due to bad
   conversions or just typos
-  Fix to user module for appending/setting groups on OpenBSD (flags
   were reversed)
-  assemble fix to use safer os.join.path, avoids charset issues
-  fixed issue with solaris facts and i18n
-  added python2.4 compatiblity fix to sysctl module
-  Fix comparison of exisiting container security opts in the
   docker\_container module
-  fixed service module invocation of insserv on certain platforms
-  Fix traceback in os\_user in an error case.
-  Fix docker container to restart a container when changing to fewer
   exposed ports
-  Fix tracebacks in docker\_network
-  Fixes to detection of updated docker images
-  Handle detection of docker image changes when published ports is
   changed
-  Fix for docker\_container restarting images when links list is empty.

2.3 "Ramble On" - 2017-04-12
----------------------------

Moving to Ansible 2.3 guide
http://docs.ansible.com/ansible/porting\_guide\_2.3.html

Major Changes
~~~~~~~~~~~~~

-  Documented and renamed the previously released 'single var vaulting'
   feature, allowing user to use vault encryption for single variables
   in a normal YAML vars file.
-  Allow module\_utils for custom modules to be placed in site-specific
   directories and shipped in roles
-  On platforms that support it, use more modern system polling API
   instead of select in the ssh connection plugin. This removes one
   limitation on how many parallel forks are feasible on these systems.
-  Windows/WinRM supports (experimental) become method "runas" to run
   modules and scripts as a different user, and to transparently access
   network resources.
-  The WinRM connection plugin now uses pipelining when executing
   modules, resulting in significantly faster execution for small tasks.
-  The WinRM connection plugin can now manage Kerberos tickets
   automatically when ``ansible_winrm_transport=kerberos`` and
   ``ansible_user``/``ansible_password`` are specified.
-  Refactored/standardized most Windows modules, adding check-mode and
   diff support where possible.
-  Extended Windows module API with parameter-type support, helper
   functions. (i.e. Expand-Environment, Add-Warning,
   Add-DeprecatationWarning)
-  restructured how async works to allow it to apply to action plugins
   that choose to support it.

Minor Changes
~~~~~~~~~~~~~

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
-  Added 'metadata' to modules to enable classification
-  ansible-doc now displays path to module and existing 'metadata'
-  added optional 'piped' transfer method to ssh plugin for when scp and
   sftp are missing, ssh plugin is also now 'smarter' when using these
   options
-  default controlpersist path is now a custom hash of host-port-user to
   avoid the socket path length errors for long hostnames
-  Various fixes for Python3 compatibility
-  Fixed issues with inventory formats not handling 'all' and
   'ungrouped' in an uniform way.
-  'service' tasks can now use async again, we had lost this capability
   when changed into an action plugin.
-  made any\_errors\_fatal inheritable from play to task and all other
   objects in between.
-  many small performance improvements in inventory and variable
   handling and in task execution.
-  Added a retry class to the ec2\_asg module since customers were
   running into throttling errors (AWSRetry is a solution for modules
   using boto3 which isn't applicable here).

Deprecations
~~~~~~~~~~~~

-  Specifying --tags (or --skip-tags) multiple times on the command line
   currently leads to the last one overriding all the previous ones.
   This behaviour is deprecated. In the future, if you specify --tags
   multiple times the tags will be merged together. From now on, using
   --tags multiple times on one command line will emit a deprecation
   warning. Setting the merge\_multiple\_cli\_tags option to True in the
   ansible.cfg file will enable the new behaviour. In 2.4, the default
   will be to merge and you can enable the old overwriting behaviour via
   the config option. In 2.5, multiple --tags options will be merged
   with no way to go back to the old behaviour.

-  Modules (scheduled for removal in 2.5)
-  ec2\_vpc
-  cl\_bond
-  cl\_bridge
-  cl\_img\_install
-  cl\_interface
-  cl\_interface\_policy
-  cl\_license
-  cl\_ports
-  nxos\_mtu, use nxos\_system instead

New: Callbacks
^^^^^^^^^^^^^^

-  dense: minimal stdout output with fallback to default when verbose

New: lookups
^^^^^^^^^^^^

-  keyring: allows getting password from the 'controller' system's
   keyrings

New: cache
^^^^^^^^^^

-  pickle (uses python's own serializer)
-  yaml

New: inventory scripts
^^^^^^^^^^^^^^^^^^^^^^

-  oVirt/RHV

New: filters
^^^^^^^^^^^^

-  combinations
-  permutations
-  zip
-  zip\_longest

Module Notes
~~~~~~~~~~~~

-  AWS lambda: previously ignored changes that only affected one
   parameter. Existing deployments may have outstanding changes that
   this bugfix will apply.
-  oVirt/RHV: Added support for 4.1 features and the following:
-  data centers, clusters, hosts, storage domains and networks
   management.
-  hosts and virtual machines affinity groups and labels.
-  users, groups and permissions management.
-  Improved virtual machines and disks management.
-  Mount: Some fixes so bind mounts are not mounted each time the
   playbook runs.

New Modules
~~~~~~~~~~~

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
-  ios\_banner
-  ios\_system
-  ios\_vrf
-  iosxr\_system
-  iso\_extract
-  java\_cert
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
-  proxysql:
-  proxysql\_backend\_servers
-  proxysql\_global\_variables
-  proxysql\_manage\_config
-  proxysql\_mysql\_users
-  proxysql\_query\_rules
-  proxysql\_replication\_hostgroups
-  proxysql\_scheduler
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
