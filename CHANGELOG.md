Ansible Changes By Release
==========================

0.4 "Unchained" ------- in progress, ETA May 2012

* custom facts provided by the setup module mean no dependency on Ruby, facter, or ohai
* sudo improvements, now works much more smoothly
* OS X support in progress for ansible on the host and clients (modules still TBA)
* list of hosts in playbooks can be expressed as a YAML list in addition to ; delimited
* tweaks to SELinux implementation for file module
* first_available_file feature, see selective_file_sources.yml in examples/playbooks for info
* fixes for yum module corner cases on EL5
* --extra-vars="a=2 b=3" etc, now available to inject parameters into playbooks from CLI
* file module now correctly returns the mode in octal
* modules can no longer include stderr output (paramiko limitation from sudo)
* 'group_names' is now a variable made available to templates
* variables in the 'all' section can be used to define other variables based on those values
* fix for symlink handling in the file module
* groups and users module takes an optional system=yes|no on creation (default no)
* async handling improvements
* service takes an enable=yes|no which works with chkconfig or updates-rc.d as appropriate

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
* command task supports creates=foo for idempotent semantics, won't
run if file foo already exists 

0.0.2 and 0.0.1

* Initial stages of project

