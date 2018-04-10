=======================================================
Ansible 2.0 "Over the Hills and Far Away" Release Notes
=======================================================
2.0.3 "Over the Hills and Far Away"
-----------------------------------

-  Backport fix to uri module to return the body of an error response
-  Backport fix to uri module to handle file:/// uris.
-  Backport fix to uri module to fix traceback when handling certain
   server error types.

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
   that start with ``HEADER_`` were causing a traceback.
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
   depending on 'ansible\_env' which was previously ignored

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
-  Ansible 2.0 has deprecated the "ssh" from ansible\_ssh\_user,
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

   .. code:: yaml

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

   .. code:: yaml

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

-  In 1.9.x, newlines in templates were converted to Unix EOL
   conventions. If someone wanted a templated file to end up with
   Windows or Mac EOL conventions, this could cause problems for them.
   In 2.x newlines now remain as specified in the template file.

-  When specifying complex args as a variable, the variable must use the
   full jinja2 variable syntax ('{{var\_name}}') - bare variable names
   there are no longer accepted. In fact, even specifying args with
   variables has been deprecated, and will not be allowed in future
   versions:

   .. code:: yaml

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

-  The bigip\* networking modules have a new parameter, validate\_certs.
   When True (the default) the module will validate any hosts it
   connects to against the TLS certificates it presents when run on new
   enough python versions. If the python version is too old to validate
   certificates or you used certificates that cannot be validated
   against available CAs you will need to add validate\_certs=no to your
   playbook for those tasks.

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

-  amazon: ec2\_ami\_copy
-  amazon: ec2\_ami\_find
-  amazon: ec2\_elb\_facts
-  amazon: ec2\_eni
-  amazon: ec2\_eni\_facts
-  amazon: ec2\_remote\_facts
-  amazon: ec2\_vpc\_igw
-  amazon: ec2\_vpc\_net
-  amazon: ec2\_vpc\_net\_facts
-  amazon: ec2\_vpc\_route\_table
-  amazon: ec2\_vpc\_route\_table\_facts
-  amazon: ec2\_vpc\_subnet
-  amazon: ec2\_vpc\_subnet\_facts
-  amazon: ec2\_win\_password
-  amazon: ecs\_cluster
-  amazon: ecs\_task
-  amazon: ecs\_taskdefinition
-  amazon: elasticache\_subnet\_group\_facts
-  amazon: iam
-  amazon: iam\_cert
-  amazon: iam\_policy
-  amazon: route53\_facts
-  amazon: route53\_health\_check
-  amazon: route53\_zone
-  amazon: sts\_assume\_role
-  amazon: s3\_bucket
-  amazon: s3\_lifecycle
-  amazon: s3\_logging
-  amazon: sqs\_queue
-  amazon: sns\_topic
-  amazon: sts\_assume\_role
-  apk
-  bigip\_gtm\_wide\_ip
-  bundler
-  centurylink: clc\_aa\_policy
-  centurylink: clc\_alert\_policy
-  centurylink: clc\_blueprint\_package
-  centurylink: clc\_firewall\_policy
-  centurylink: clc\_group
-  centurylink: clc\_loadbalancer
-  centurylink: clc\_modify\_server
-  centurylink: clc\_publicip
-  centurylink: clc\_server
-  centurylink: clc\_server\_snapshot
-  circonus\_annotation
-  consul
-  consul\_acl
-  consul\_kv
-  consul\_session
-  cloudtrail
-  cloudstack: cs\_account
-  cloudstack: cs\_affinitygroup
-  cloudstack: cs\_domain
-  cloudstack: cs\_facts
-  cloudstack: cs\_firewall
-  cloudstack: cs\_iso
-  cloudstack: cs\_instance
-  cloudstack: cs\_instancegroup
-  cloudstack: cs\_ip\_address
-  cloudstack: cs\_loadbalancer\_rule
-  cloudstack: cs\_loadbalancer\_rule\_member
-  cloudstack: cs\_network
-  cloudstack: cs\_portforward
-  cloudstack: cs\_project
-  cloudstack: cs\_sshkeypair
-  cloudstack: cs\_securitygroup
-  cloudstack: cs\_securitygroup\_rule
-  cloudstack: cs\_staticnat
-  cloudstack: cs\_template
-  cloudstack: cs\_user
-  cloudstack: cs\_vmsnapshot
-  cronvar
-  datadog\_monitor
-  deploy\_helper
-  docker: docker\_login
-  dpkg\_selections
-  elasticsearch\_plugin
-  expect
-  find
-  google: gce\_tag
-  hall
-  ipify\_facts
-  iptables
-  libvirt: virt\_net
-  libvirt: virt\_pool
-  maven\_artifact
-  openstack: os\_auth
-  openstack: os\_client\_config
-  openstack: os\_image
-  openstack: os\_image\_facts
-  openstack: os\_floating\_ip
-  openstack: os\_ironic
-  openstack: os\_ironic\_node
-  openstack: os\_keypair
-  openstack: os\_network
-  openstack: os\_network\_facts
-  openstack: os\_nova\_flavor
-  openstack: os\_object
-  openstack: os\_port
-  openstack: os\_project
-  openstack: os\_router
-  openstack: os\_security\_group
-  openstack: os\_security\_group\_rule
-  openstack: os\_server
-  openstack: os\_server\_actions
-  openstack: os\_server\_facts
-  openstack: os\_server\_volume
-  openstack: os\_subnet
-  openstack: os\_subnet\_facts
-  openstack: os\_user
-  openstack: os\_user\_group
-  openstack: os\_volume
-  openvswitch\_db.
-  osx\_defaults
-  pagerduty\_alert
-  pam\_limits
-  pear
-  profitbricks: profitbricks
-  profitbricks: profitbricks\_datacenter
-  profitbricks: profitbricks\_nic
-  profitbricks: profitbricks\_volume
-  profitbricks: profitbricks\_volume\_attachments
-  profitbricks: profitbricks\_snapshot
-  proxmox: proxmox
-  proxmox: proxmox\_template
-  puppet
-  pushover
-  pushbullet
-  rax: rax\_clb\_ssl
-  rax: rax\_mon\_alarm
-  rax: rax\_mon\_check
-  rax: rax\_mon\_entity
-  rax: rax\_mon\_notification
-  rax: rax\_mon\_notification\_plan
-  rabbitmq\_binding
-  rabbitmq\_exchange
-  rabbitmq\_queue
-  selinux\_permissive
-  sendgrid
-  sensu\_check
-  sensu\_subscription
-  seport
-  slackpkg
-  solaris\_zone
-  taiga\_issue
-  vertica\_configuration
-  vertica\_facts
-  vertica\_role
-  vertica\_schema
-  vertica\_user
-  vmware: vca\_fw
-  vmware: vca\_nat
-  vmware: vmware\_cluster
-  vmware: vmware\_datacenter
-  vmware: vmware\_dns\_config
-  vmware: vmware\_dvs\_host
-  vmware: vmware\_dvs\_portgroup
-  vmware: vmware\_dvswitch
-  vmware: vmware\_host
-  vmware: vmware\_migrate\_vmk
-  vmware: vmware\_portgroup
-  vmware: vmware\_target\_canonical\_facts
-  vmware: vmware\_vm\_facts
-  vmware: vmware\_vm\_vss\_dvs\_migrate
-  vmware: vmware\_vmkernel
-  vmware: vmware\_vmkernel\_ip\_config
-  vmware: vmware\_vsan\_cluster
-  vmware: vmware\_vswitch
-  vmware: vsphere\_copy
-  webfaction\_app
-  webfaction\_db
-  webfaction\_domain
-  webfaction\_mailbox
-  webfaction\_site
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

-  The yum module's detection of installed packages has been made more
   robust by using /usr/bin/rpm in cases where it woud have used
   repoquery before.
-  The pip module now properly reports changes when packages are coming
   from a VCS.
-  Fixes for retrieving files over https when a CONNECT-only proxy is in
   the middle.
