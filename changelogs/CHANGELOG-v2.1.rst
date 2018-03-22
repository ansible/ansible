=====================================================
Ansible 2.1 "The Song Remains the Same" Release Notes
=====================================================
2.1.6 "The Song Remains the Same" - 06-01-2017
----------------------------------------------

-  Security fix for CVE-2017-7481 - data for lookup plugins used as
   variables was not being correctly marked as "unsafe".

2.1.5 "The Song Remains the Same" - 03-27-2017
----------------------------------------------

-  Security continued fix for CVE-2016-9587 - Handle some additional
   corner cases in the way conditionals are parsed and evaluated.

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
   ``to_json*`` filters.
-  Fixed some bugs related to the use of non-ascii characters in become
   passwords.
-  Fixed a bug with Azure modules which may be using the latest rc6
   library.
-  Backported some docker\_common fixes.

2.1.2 "The Song Remains the Same" - 2016-09-29
----------------------------------------------

Minor Changes
~~~~~~~~~~~~~

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

Deprecations
~~~~~~~~~~~~

-  Deprecated the use of ``_fixup_perms``. Use ``_fixup_perms2``
   instead. This change only impacts custom action plugins using
   ``_fixup_perms``.

Incompatible Changes
~~~~~~~~~~~~~~~~~~~~

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

New Modules
^^^^^^^^^^^

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

New Strategies
^^^^^^^^^^^^^^

-  debug

New Filters
^^^^^^^^^^^

-  extract
-  ip4\_hex
-  regex\_search
-  regex\_findall

New Callbacks
^^^^^^^^^^^^^

-  actionable (only shows changed and failed)
-  slack
-  json

New Tests
^^^^^^^^^

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
