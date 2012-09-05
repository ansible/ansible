Ansible Changes By Release
==========================

0.7 "Panama" -- release pending -- I can barely see the roadmap from the heat coming off of it.

Module changes:

* login_unix_socket option for mysql user and database modules (see PR #781 for doc notes)
* new modules -- pip, easy_install, apt_repository, supervisorctl
* error handling for setup module when SELinux is in a weird state
* misc yum module fixes
* better changed=True/False detection in user module on older Linux distros
* nicer errors from modules when arguments are not key=value
* backup option on copy (backup=yes), as well as template, assemble, and lineinfile
* file module will not recurse on directory properties
* yum module now workable without having repoquery installed, but doesn't support comparisons or list= if so
* setup module now detects interfaces with aliases
* better handling of VM guest type detection in setup module
* new module boilerplate code to check for mutually required arguments, arguments required together, exclusive args
* add pattern= as a paramter to the service module (for init scripts that don't do status, or do poor status)
* various fixes to mysql & postresql modules
* added a thirsty= option (boolean, default no) to the get_url module to decide to download the file every time or not
* added a wait_for module to poll for ports being open
* added a nagios module for controlling outage windows and alert statuses
* added a seboolean module for getsebool/setsebool type operations
* added a selinux module for controlling overall SELinux policy
* added a subversion module
* added lineinfile for adding and removing lines from basic files
* added facts for ARM-based CPUs
* support for systemd in the service module
* git moduleforce reset behavior is now controllable
* file module can now operate on special files (block devices, etc)

Core changes:

* ansible --version will now give branch/SHA information if running from git
* better sudo permissions when encountering different umasks
* when using paramiko and SFTP is not accessible, do not traceback, but return a nice human readable msg
* use -vvv for extreme debug levels. -v gives more playbook output as before
* -vv shows module arguments to all module calls (and maybe some other things later)
* don not pass "--" to sudo to work on older EL5
* make remote_md5 internal function work with non-bash shells
* allow user to be passed in via --extra-vars (regression)
* add --limit option, which can be used to further confine the pattern given in ansible-playbooks
* adds ranged patterns like dbservers[0-49] for usage with patterns or --limit
* -u and user: defaults to current user, rather than root, override as before
* /etc/ansible/ansible.cfg and ~/ansible.cfg now available to set default values and other things
* (developers) ANSIBLE_KEEP_REMOTE_FILES=1 can be used in debugging (envrionment variable)
* (developers) connection types are now plugins
* (developers) callbacks can now be extended via plugins
* added FreeBSD ports packaging scripts
* check for terminal properties prior to engaging color modes
* explicitly disable password auth with -c ssh, as it is not used anyway

Playbooks:

* YAML syntax errors detected and show where the problem is
* if you ctrl+c a playbook it will not traceback (usually)
* vars_prompt now has encryption options (see examples/playbooks/prompts.yml)
* allow variables in parameterized task include parameters (regression)
* add ability to store the result of any command in a register (see examples/playbooks/register_logic.yml)
* --list-hosts to show what hosts are included in each play of a playbook
* fix a variable ordering issue that could affect vars_files with selective file source lists
* adds 'delegate_to' for a task, which can be used to signal outage windows and load balancers on behalf of hosts
* adds 'serial' to playbook, allowing you to specify how many hosts can be processing a playbook at one time (default 0=all)
* adds 'local_action: <action parameters>' as an alias to 'delegate_to: 127.0.0.1'

0.6 "Cabo" -- August 6, 2012

playbooks:

* support to tag tasks and includes and use --tags in playbook CLI
* playbooks can now include other playbooks (example/playbooks/nested_playbooks.yml)
* vars_files now usable with with_items, provided file paths don't contain host specific facts
* error reporting if with_items value is unbound
* with_items no longer creates lots of tasks, creates one task that makes multiple calls
* can use host_specific facts inside with_items (see above)
* at the top level of a playbook, set 'gather_facts: False' to skip fact gathering
* first_available_file and with_items used together will now raise an error
* to catch typos, like 'var' for 'vars', playbooks and tasks now yell on invalid parameters
* automatically load (directory_of_inventory_file)/group_vars/groupname and /host_vars/hostname in vars_files
* playbook is now colorized, set ANSIBLE_NOCOLOR=1 if you do not like this, does not colorize if not a TTY
* hostvars now preserved between plays (regression in 0.5 from 0.4), useful for sharing vars in multinode configs
* ignore_errors: True on a task can be used to allow a task to fail and not stop the play
* with_items with the apt/yum module will install/remove/update everything in a single command

inventory:

* groups variable available as a hash to return the hosts in each group name
* in YAML inventory, hosts can list their groups in inverted order now also (see tests/yaml_hosts)
* YAML inventory is deprecated and will be removed in 0.7
* ec2 inventory script
* support ranges of hosts in the host file, like www[001-100].example.com (supports leading zeros and also not)

modules:

* fetch module now does not fail a system when requesting file paths (ex: logs) that don't exist
* apt module now takes an optional install-recommends=yes|no (default yes)
* fixes to the return codes of the copy module
* copy module takes a remote md5sum to avoid large file transfer
* various user and group module fixes (error handling, etc)
* apt module now takes an optional force parameter
* slightly better psychic service status handling for the service module
* fetch module fixes for SSH connection type
* modules now consistently all take yes/no for boolean parameters (and DWIM on true/false/1/0/y/n/etc)
* setup module no longer saves to disk, template module now only used in playbooks
* setup module no longer needs to run twice per playbook
* apt module now passes DEBIAN_FRONTEND=noninteractive
* mount module (manages active mounts + fstab)
* setup module fixes if no ipv6 support
* internals: template in common module boilerplate, also causes less SSH operations when used
* git module fixes
* setup module overhaul, more modular
* minor caching logic added to inventory to reduce hammering of inventory scripts.
* MySQL and PostgreSQL modules for user and db management
* vars_prompt now supports private password entry (see examples/playbooks/prompts.yml)
* yum module modified to be more tolerant of plugins spewing random console messages (ex: RHN)

internals:

* when sudoing to root, still use /etc/ansible/setup as the metadata path, as if root
* paramiko is now only imported if needed when running from source checkout
* cowsay support on Ubuntu
* various ssh connection fixes for old Ubuntu clients
* ./hacking/test-module now supports options like ansible takes and has a debugger mode
* sudoing to a user other than root now works more seamlessly (uses /tmp, avoids umask issues)

0.5 "Amsterdam" ------- July 04, 2012

* Service module gets more accurate service states when running with upstart
* Jinja2 usage in playbooks (not templates), reinstated, supports %include directive
* support for --connection ssh (supports Kerberos, bastion hosts, etc), requires ControlMaster
* misc tracebacks replaced with error messages
* various API/internals refactoring
* vars can be built from other variables
* support for exclusion of hosts/groups with "!groupname"
* various changes to support md5 tool differences for FreeBSD nodes & OS X clients
* "unparseable" command output shows in command output for easier debugging
* mktemp is no longer required on remotes (not available on BSD)
* support for older versions of python-apt in the apt module
* a new "assemble" module, for constructing files from pieces of files (inspired by Puppet "fragments" idiom)
* ability to override most default values with ANSIBLE_FOO environment variables
* --module-path parameter can support multiple directories seperated with the OS path seperator
* with_items can take a variable of type list
* ansible_python_interpreter variable available for systems with more than one Python
* BIOS and VMware "fact" upgrades
* cowsay is used by ansible-playbook if installed to improve output legibility (try installing it)
* authorized_key module
* SELinux facts now sourced from the python selinux library
* removed module debug option -D
* added --verbose, which shows output from successful playbook operations
* print the output of the raw command inside /usr/bin/ansible as with command/shell
* basic setup module support for Solaris
* ./library relative to the playbook is always in path so modules can be included in tarballs with playbooks

0.4 "Unchained" ------- May 23, 2012

Internals/Core
* internal inventory API now more object oriented, parsers decoupled
* async handling improvements
* misc fixes for running ansible on OS X (overlord only)
* sudo improvements, now works much more smoothly
* sudo to a particular user with -U/--sudo-user, or using 'sudo_user: foo' in a playbook
* --private-key CLI option to work with pem files

Inventory
* can use -i host1,host2,host3:port to specify hosts not in inventory (replaces --override-hosts)
* ansible INI style format can do groups of groups [groupname:children] and group vars [groupname:vars]
* groups and users module takes an optional system=yes|no on creation (default no)
* list of hosts in playbooks can be expressed as a YAML list in addition to ; delimited

Playbooks
* variables can be replaced like ${foo.nested_hash_key.nested_subkey[array_index]}
* unicode now ok in templates (assumes utf8)
* able to pass host specifier or group name in to "hosts:" with --extra-vars
* ansible-pull script and example playbook (extreme scaling, remediation)
* inventory_hostname variable available that contains the value of the host as ansible knows it
* variables in the 'all' section can be used to define other variables based on those values
* 'group_names' is now a variable made available to templates
* first_available_file feature, see selective_file_sources.yml in examples/playbooks for info
* --extra-vars="a=2 b=3" etc, now available to inject parameters into playbooks from CLI

Incompatible Changes
* jinja2 is only usable in templates, not playbooks, use $foo instead
* --override-hosts removed, can use -i with comma notation (-i "ahost,bhost")
* modules can no longer include stderr output (paramiko limitation from sudo)

Module Changes
* tweaks to SELinux implementation for file module
* fixes for yum module corner cases on EL5
* file module now correctly returns the mode in octal
* fix for symlink handling in the file module
* service takes an enable=yes|no which works with chkconfig or updates-rc.d as appropriate
* service module works better on Ubuntu
* git module now does resets and such to work more smoothly on updates
* modules all now log to syslog
* enabled=yes|no on a service can be used to toggle chkconfig & updates-rc.d states
* git module supports branch=
* service fixes to better detect status using return codes of the service script
* custom facts provided by the setup module mean no dependency on Ruby, facter, or ohai
* service now has a state=reloaded
* raw module for bootstrapping and talking to routers w/o Python, etc

Misc Bugfixes
* fixes for variable parsing in only_if lines
* misc fixes to key=value parsing
* variables with mixed case now legal
* fix to internals of hacking/test-module development script


0.3 "Baluchitherium" -- April 23, 2012

* Packaging for Debian, Gentoo, and Arch
* Improvements to the apt and yum modules
* A virt module
* SELinux support for the file module
* Ability to use facts from other systems in templates (aka exported
resources like support)
* Built in Ansible facts so you don't need ohai, facter, or Ruby
* tempdir selections that work with noexec mounted /tmp
* templates happen locally, not remotely, so no dependency on
python-jinja2 for remote computers
* advanced inventory format in YAML allows more control over variables
per host and per group
* variables in playbooks can be structured/nested versus just a flat namespace
* manpage upgrades (docs)
* various bugfixes
* can specify a default --user for playbooks rather than specifying it
in the playbook file
* able to specify ansible port in ansible host file (see docs)
* refactored Inventory API to make it easier to write scripts using Ansible
* looping capability for playbooks (with_items)
* support for using sudo with a password
* module arguments can be unicode
* A local connection type, --connection=local,  for use with cron or
in kickstarts
* better module debugging with -D
* fetch module for pulling in files from remote hosts
* command task supports creates=foo for idempotent semantics, won't run if file foo already exists

0.0.2 and 0.0.1

* Initial stages of project

