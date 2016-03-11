Configuration file
++++++++++++++++++

.. contents:: Topics

.. highlight:: bash

Certain settings in Ansible are adjustable via a configuration file.  The stock configuration should be sufficient
for most users, but there may be reasons you would want to change them.

Changes can be made and used in a configuration file which will be processed in the following order::

    * ANSIBLE_CONFIG (an environment variable)
    * ansible.cfg (in the current directory)
    * .ansible.cfg (in the home directory)
    * /etc/ansible/ansible.cfg

Prior to 1.5 the order was::

    * ansible.cfg (in the current directory)
    * ANSIBLE_CONFIG (an environment variable)
    * .ansible.cfg (in the home directory)
    * /etc/ansible/ansible.cfg

Ansible will process the above list and use the first file found. Settings in files are not merged.

.. _getting_the_latest_configuration:

Getting the latest configuration
````````````````````````````````

If installing ansible from a package manager, the latest ansible.cfg should be present in /etc/ansible, possibly
as a ".rpmnew" file (or other) as appropriate in the case of updates.

If you have installed from pip or from source, however, you may want to create this file in order to override
default settings in Ansible.

You may wish to consult the `ansible.cfg in source control <https://raw.github.com/ansible/ansible/devel/examples/ansible.cfg>`_ for all of the possible latest values.

.. _environmental_configuration:

Environmental configuration
```````````````````````````

Ansible also allows configuration of settings via environment variables.  If these environment variables are set, they will
override any setting loaded from the configuration file.  These variables are for brevity not defined here, but look in `constants.py <https://github.com/ansible/ansible/blob/devel/lib/ansible/constants.py>`_ in the source tree if you want to use these.  They are mostly considered to be a legacy system as compared to the config file, but are equally valid.

.. _config_values_by_section:

Explanation of values by section
````````````````````````````````

The configuration file is broken up into sections.  Most options are in the "general" section but some sections of the file
are specific to certain connection types.

.. _general_defaults:

General defaults
----------------

In the [defaults] section of ansible.cfg, the following settings are tunable:

.. _action_plugins:

action_plugins
==============

Actions are pieces of code in ansible that enable things like module execution, templating, and so forth.

This is a developer-centric feature that allows low-level extensions around Ansible to be loaded from
different locations::

   action_plugins = ~/.ansible/plugins/action_plugins/:/usr/share/ansible_plugins/action_plugins

Most users will not need to use this feature.  See :doc:`developing_plugins` for more details.

.. _ansible_managed:

ansible_managed
===============

Ansible-managed is a string that can be inserted into files written by Ansible's config templating system, if you use
a string like::

   {{ ansible_managed }}

The default configuration shows who modified a file and when::

    ansible_managed = Ansible managed: {file} modified on %Y-%m-%d %H:%M:%S by {uid} on {host}

This is useful to tell users that a file has been placed by Ansible and manual changes are likely to be overwritten.

Note that if using this feature, and there is a date in the string, the template will be reported changed each time as the date is updated.

.. _ask_pass:

ask_pass
========

This controls whether an Ansible playbook should prompt for a password by default.  The default behavior is no::

    ask_pass=True

If using SSH keys for authentication, it's probably not needed to change this setting.

.. _ask_sudo_pass:

ask_sudo_pass
=============

Similar to ask_pass, this controls whether an Ansible playbook should prompt for a sudo password by default when
sudoing.  The default behavior is also no::

    ask_sudo_pass=True

Users on platforms where sudo passwords are enabled should consider changing this setting.

.. _ask_vault_pass:

ask_vault_pass
==============

This controls whether an Ansible playbook should prompt for the vault password by default.  The default behavior is no::

    ask_vault_pass=True

.. _bin_ansible_callbacks:

bin_ansible_callbacks
=====================

.. versionadded:: 1.8

Controls whether callback plugins are loaded when running /usr/bin/ansible.  This may be used to log activity from
the command line, send notifications, and so on.  Callback plugins are always loaded for /usr/bin/ansible-playbook
if present and cannot be disabled::

    bin_ansible_callbacks=False

Prior to 1.8, callbacks were never loaded for /usr/bin/ansible.

.. _callback_plugins:

callback_plugins
================

Callbacks are pieces of code in ansible that get called on specific events, permitting to trigger notifications.

This is a developer-centric feature that allows low-level extensions around Ansible to be loaded from
different locations::

   callback_plugins = ~/.ansible/plugins/callback_plugins/:/usr/share/ansible_plugins/callback_plugins

Most users will not need to use this feature.  See :doc:`developing_plugins` for more details

.. _stdout_callback:

stdout_callback
===============

.. versionadded:: 2.0

This setting allows you to override the default stdout callback for ansible-playbook::

    stdout_callback = skippy

.. _callback_whitelist:

callback_whitelist
==================

.. versionadded:: 2.0

Now ansible ships with all included callback plugins ready to use but they are disabled by default.
This setting lets you enable a list of additional callbacks. This cannot change or override the
default stdout callback, use :ref:`stdout_callback` for that::

    callback_whitelist = timer,mail

.. _command_warnings:

command_warnings
================

.. versionadded:: 1.8

By default since Ansible 1.8, Ansible will warn when usage of the shell and
command module appear to be simplified by using a default Ansible module
instead.  This can include reminders to use the 'git' module instead of
shell commands to execute 'git'.  Using modules when possible over arbitrary
shell commands can lead to more reliable and consistent playbook runs, and
also easier to maintain playbooks::

    command_warnings = False

These warnings can be silenced by adjusting the following
setting or adding warn=yes or warn=no to the end of the command line
parameter string, like so::


    - name: usage of git that could be replaced with the git module
      shell: git update foo warn=yes

.. _connection_plugins:

connection_plugins
==================

Connections plugin permit to extend the channel used by ansible to transport commands and files.

This is a developer-centric feature that allows low-level extensions around Ansible to be loaded from
different locations::

    connection_plugins = ~/.ansible/plugins/connection_plugins/:/usr/share/ansible_plugins/connection_plugins

Most users will not need to use this feature.  See :doc:`developing_plugins` for more details

.. _deprecation_warnings:

deprecation_warnings
====================

.. versionadded:: 1.3

Allows disabling of deprecating warnings in ansible-playbook output::

    deprecation_warnings = True

Deprecation warnings indicate usage of legacy features that are slated for removal in a future release of Ansible.

.. _display_args_to_stdout:

display_args_to_stdout
======================

.. versionadded:: 2.1.0

By default, ansible-playbook will print a header for each task that is run to
stdout.  These headers will contain the ``name:`` field from the task if you
specified one.  If you didn't then ansible-playbook uses the task's action to
help you tell which task is presently running.  Sometimes you run many of the
same action and so you want more information about the task to differentiate
it from others of the same action.  If you set this variable to ``True`` in
the config then ansible-playbook will also include the task's arguments in the
header.

This setting defaults to ``False`` because there is a chance that you have
sensitive values in your parameters and do not want those to be printed to
stdout::

    display_args_to_stdout=False

If you set this to ``True`` you should be sure that you have secured your
environment's stdout (no one can shoulder surf your screen and you aren't
saving stdout to an insecure file) or made sure that all of your playbooks
explicitly added the ``no_log: True`` parameter to tasks which have sensistive
values   See :ref:`keep_secret_data` for more information.

.. _display_skipped_hosts:

display_skipped_hosts
=====================

If set to `False`, ansible will not display any status for a task that is skipped. The default behavior is to display skipped tasks::

    display_skipped_hosts=True

Note that Ansible will always show the task header for any task, regardless of whether or not the task is skipped.

.. _error_on_undefined_vars:

error_on_undefined_vars
=======================

On by default since Ansible 1.3, this causes ansible to fail steps that reference variable names that are likely
typoed::

    error_on_undefined_vars=True

If set to False, any '{{ template_expression }}' that contains undefined variables will be rendered in a template
or ansible action line exactly as written.

.. _executable:

executable
==========

This indicates the command to use to spawn a shell under a sudo environment.  Users may need to change this to /bin/bash in rare instances when sudo is constrained, but in most cases it may be left as is::

    executable = /bin/bash

.. _filter_plugins:

filter_plugins
==============

Filters are specific functions that can be used to extend the template system.

This is a developer-centric feature that allows low-level extensions around Ansible to be loaded from
different locations::

    filter_plugins = ~/.ansible/plugins/filter_plugins/:/usr/share/ansible_plugins/filter_plugins

Most users will not need to use this feature.  See :doc:`developing_plugins` for more details

.. _force_color:

force_color
===========

This options forces color mode even when running without a TTY::

    force_color = 1

.. _force_handlers:

force_handlers
==============

.. versionadded:: 1.9.1

This option causes notified handlers to run on a host even if a failure occurs on that host::

		force_handlers = True

The default is False, meaning that handlers will not run if a failure has occurred on a host.
This can also be set per play or on the command line. See :ref:`handlers_and_failure` for more details.

.. _forks:

forks
=====

This is the default number of parallel processes to spawn when communicating with remote hosts.  Since Ansible 1.3,
the fork number is automatically limited to the number of possible hosts, so this is really a limit of how much
network and CPU load you think you can handle.  Many users may set this to 50, some set it to 500 or more.  If you
have a large number of hosts, higher values will make actions across all of those hosts complete faster.  The default
is very very conservative::

    forks=5

.. _gathering:

gathering
=========

New in 1.6, the 'gathering' setting controls the default policy of facts gathering (variables discovered about remote systems).

The value 'implicit' is the default, which means that the fact cache will be ignored and facts will be gathered per play unless 'gather_facts: False' is set.
The value 'explicit' is the inverse, facts will not be gathered unless directly requested in the play.
The value 'smart' means each new host that has no facts discovered will be scanned, but if the same host is addressed in multiple plays it will not be contacted again in the playbook run.
This option can be useful for those wishing to save fact gathering time. Both 'smart' and 'explicit' will use the fact cache::

    gathering = smart

hash_behaviour
==============

Ansible by default will override variables in specific precedence orders, as described in :doc:`playbooks_variables`.  When a variable
of higher precedence wins, it will replace the other value.

Some users prefer that variables that are hashes (aka 'dictionaries' in Python terms) are merged.  This setting is called 'merge'. This is not the default behavior and it does not affect variables whose values are scalars (integers, strings) or
arrays.  We generally recommend not using this setting unless you think you have an absolute need for it, and playbooks in the
official examples repos do not use this setting::

    hash_behaviour=replace

The valid values are either 'replace' (the default) or 'merge'.

.. versionadded: '2.0'

If you want to merge hashes without changing the global settings, use
the `combine` filter described in :doc:`playbooks_filters`.

.. _hostfile:

hostfile
========

This is a deprecated setting since 1.9, please look at :ref:`inventory_file` for the new setting.

.. _host_key_checking:

host_key_checking
=================

As described in :doc:`intro_getting_started`, host key checking is on by default in Ansible 1.3 and later.  If you understand the
implications and wish to disable it, you may do so here by setting the value to False::

    host_key_checking=True

.. _inventory_file:

inventory
=========

This is the default location of the inventory file, script, or directory that Ansible will use to determine what hosts it has available
to talk to::

    inventory = /etc/ansible/hosts

It used to be called hostfile in Ansible before 1.9

.. _jinja2_extensions:

jinja2_extensions
=================

This is a developer-specific feature that allows enabling additional Jinja2 extensions::

    jinja2_extensions = jinja2.ext.do,jinja2.ext.i18n

If you do not know what these do, you probably don't need to change this setting :)

.. _library:

library
=======

This is the default location Ansible looks to find modules::

     library = /usr/share/ansible

Ansible knows how to look in multiple locations if you feed it a colon separated path, and it also will look for modules in the
"./library" directory alongside a playbook.

.. _log_path:

log_path
========

If present and configured in ansible.cfg, Ansible will log information about executions at the designated location.  Be sure
the user running Ansible has permissions on the logfile::

    log_path=/var/log/ansible.log

This behavior is not on by default.  Note that ansible will, without this setting, record module arguments called to the
syslog of managed machines.  Password arguments are excluded.

For Enterprise users seeking more detailed logging history, you may be interested in :doc:`tower`.

.. _lookup_plugins:

lookup_plugins
==============

This is a developer-centric feature that allows low-level extensions around Ansible to be loaded from
different locations::

    lookup_plugins = ~/.ansible/plugins/lookup_plugins/:/usr/share/ansible_plugins/lookup_plugins

Most users will not need to use this feature.  See :doc:`developing_plugins` for more details

.. _module_lang:

module_lang
===========

This is to set the default language to communicate between the module and the system. By default, the value is 'C'::

    module_lang = en_US.UTF-8

.. _module_name:

module_name
===========

This is the default module name (-m) value for /usr/bin/ansible.  The default is the 'command' module.
Remember the command module doesn't support shell variables, pipes, or quotes, so you might wish to change
it to 'shell'::

    module_name = command

.. _nocolor:

nocolor
=======

By default ansible will try to colorize output to give a better indication of failure and status information.
If you dislike this behavior you can turn it off by setting 'nocolor' to 1::

    nocolor=0

.. _nocows:

nocows
======

By default ansible will take advantage of cowsay if installed to make /usr/bin/ansible-playbook runs more exciting.
Why?  We believe systems management should be a happy experience.  If you do not like the cows, you can disable them
by setting 'nocows' to 1::

    nocows=0

.. _pattern:

pattern
=======

This is the default group of hosts to talk to in a playbook if no "hosts:" stanza is supplied.  The default is to talk
to all hosts.  You may wish to change this to protect yourself from surprises::

    hosts=*

Note that /usr/bin/ansible always requires a host pattern and does not use this setting, only /usr/bin/ansible-playbook.

.. _poll_interval:

poll_interval
=============

For asynchronous tasks in Ansible (covered in :doc:`playbooks_async`), this is how often to check back on the status of those
tasks when an explicit poll interval is not supplied.  The default is a reasonably moderate 15 seconds which is a tradeoff
between checking in frequently and providing a quick turnaround when something may have completed::

    poll_interval=15

.. _private_key_file:

private_key_file
================

If you are using a pem file to authenticate with machines rather than SSH agent or passwords, you can set the default
value here to avoid re-specifying ``--private-key`` with every invocation::

    private_key_file=/path/to/file.pem

.. _remote_port:

remote_port
===========

This sets the default SSH port on all of your systems, for systems that didn't specify an alternative value in inventory.
The default is the standard 22::

    remote_port = 22

.. _remote_tmp:

remote_tmp
==========

Ansible works by transferring modules to your remote machines, running them, and then cleaning up after itself.  In some
cases, you may not wish to use the default location and would like to change the path.  You can do so by altering this
setting::

    remote_tmp = $HOME/.ansible/tmp

The default is to use a subdirectory of the user's home directory.  Ansible will then choose a random directory name
inside this location.

.. _remote_user:

remote_user
===========

This is the default username ansible will connect as for /usr/bin/ansible-playbook.  Note that /usr/bin/ansible will
always default to the current user if this is not defined::

    remote_user = root

.. _retry_files_enabled:

retry_files_enabled
===================

This controls whether a failed Ansible playbook should create a .retry file. The default setting is True::

    retry_files_enabled = False

.. _retry_files_save_path:

retry_files_save_path
=====================

The retry files save path is where Ansible will save .retry files when a playbook fails and retry_files_enabled is True (the default).
The default location is ~/ and can be changed to any writeable path::

    retry_files_save_path = ~/.ansible-retry

The directory will be created if it does not already exist.

.. _cfg_roles_path:

roles_path
==========

.. versionadded: '1.4'

The roles path indicate additional directories beyond the 'roles/' subdirectory of a playbook project to search to find Ansible
roles.  For instance, if there was a source control repository of common roles and a different repository of playbooks, you might
choose to establish a convention to checkout roles in /opt/mysite/roles like so::

    roles_path = /opt/mysite/roles

Additional paths can be provided separated by colon characters, in the same way as other pathstrings::

    roles_path = /opt/mysite/roles:/opt/othersite/roles

Roles will be first searched for in the playbook directory.  Should a role not be found, it will indicate all the possible paths
that were searched.

.. _strategy_plugins:

strategy_plugins
==================

Strategy plugin allow users to change the way in which Ansible runs tasks on targeted hosts.

This is a developer-centric feature that allows low-level extensions around Ansible to be loaded from
different locations::

    strategy_plugins = ~/.ansible/plugins/strategy_plugins/:/usr/share/ansible_plugins/strategy_plugins

Most users will not need to use this feature.  See :doc:`developing_plugins` for more details

.. _sudo_exe:

sudo_exe
========

If using an alternative sudo implementation on remote machines, the path to sudo can be replaced here provided
the sudo implementation is matching CLI flags with the standard sudo::

   sudo_exe=sudo

.. _sudo_flags:

sudo_flags
==========

Additional flags to pass to sudo when engaging sudo support. The default is '-H -S -n' which sets the HOME environment
variable, prompts for passwords via STDIN, and avoids prompting the user for input of any kind. Note that '-n' will conflict
with using password-less sudo auth, such as pam_ssh_agent_auth. In some situations you may wish to add or remove flags, but
in general most users will not need to change this setting:::

   sudo_flags=-H -S -n

.. _sudo_user:

sudo_user
=========

This is the default user to sudo to if ``--sudo-user`` is not specified or 'sudo_user' is not specified in an Ansible
playbook.  The default is the most logical: 'root'::

   sudo_user=root

.. _system_warnings:

system_warnings
===============

.. versionadded:: 1.6

Allows disabling of warnings related to potential issues on the system running ansible itself (not on the managed hosts)::

   system_warnings = True

These may include warnings about 3rd party packages or other conditions that should be resolved if possible.

.. _timeout:

timeout
=======

This is the default SSH timeout to use on connection attempts::

    timeout = 10

.. _transport:

transport
=========

This is the default transport to use if "-c <transport_name>" is not specified to /usr/bin/ansible or /usr/bin/ansible-playbook.
The default is 'smart', which will use 'ssh' (OpenSSH based) if the local operating system is new enough to support ControlPersist
technology, and then will otherwise use 'paramiko'.  Other transport options include 'local', 'chroot', 'jail', and so on.

Users should usually leave this setting as 'smart' and let their playbooks choose an alternate setting when needed with the
'connection:' play parameter::

    transport = paramiko

.. _vars_plugins:

vars_plugins
============

This is a developer-centric feature that allows low-level extensions around Ansible to be loaded from
different locations::

    vars_plugins = ~/.ansible/plugins/vars_plugins/:/usr/share/ansible_plugins/vars_plugins

Most users will not need to use this feature.  See :doc:`developing_plugins` for more details


.. _vault_password_file:

vault_password_file
===================

.. versionadded:: 1.7

Configures the path to the Vault password file as an alternative to specifying ``--vault-password-file`` on the command line::

   vault_password_file = /path/to/vault_password_file

As of 1.7 this file can also be a script. If you are using a script instead of a flat file, ensure that it is marked as executable, and that the password is printed to standard output. If your script needs to prompt for data, prompts can be sent to standard error.

.. _privilege_escalation:

Privilege Escalation Settings
-----------------------------

Ansible can use existing privilege escalation systems to allow a user to execute tasks as another. As of 1.9 ‘become’ supersedes the old sudo/su, while still being backwards compatible.  Settings live under the [privilege_escalation] header.

.. _become:

become
======

The equivalent of adding sudo: or su: to a play or task, set to true/yes to activate privilege escalation. The default behavior is no::

    become=True

.. _become_method:

become_method
=============

Set the privilege escalation method. The default is ``sudo``, other options are ``su``, ``pbrun``, ``pfexec``, ``doas``::

    become_method=su

.. _become_user:

become_user
=============

The equivalent to ansible_sudo_user or ansible_su_user, allows to set the user you become through privilege escalation. The default is 'root'::

    become_user=root

.. _become_ask_pass:

become_ask_pass
===============

Ask for privilege escalation password, the default is False::

    become_ask_pass=True

.. _become_allow_same_user:

become_allow_same_user
======================

Most of the time, using *sudo* to run a command as the same user who is running
*sudo* itself is unnecessary overhead, so Ansible does not allow it. However,
depending on the *sudo* configuration, it may be necessary to run a command as
the same user through *sudo*, such as to switch SELinux contexts. For this
reason, you can set ``become_allow_same_user`` to ``True`` and disable this
optimization.

.. _paramiko_settings:

Paramiko Specific Settings
--------------------------

Paramiko is the default SSH connection implementation on Enterprise Linux 6 or earlier, and is not used by default on other
platforms.  Settings live under the [paramiko] header.

.. _record_host_keys:

record_host_keys
================

The default setting of yes will record newly discovered and approved (if host key checking is enabled) hosts in the user's hostfile.
This setting may be inefficient for large numbers of hosts, and in those situations, using the ssh transport is definitely recommended
instead.  Setting it to False will improve performance and is recommended when host key checking is disabled::

    record_host_keys=True

.. _paramiko_proxy_command:

proxy_command
=============

.. versionadded:: 2.1

Use an OpenSSH like ProxyCommand for proxying all Paramiko SSH connections through a bastion or jump host. Requires a minimum of Paramiko version 1.9.0. On Enterprise Linux 6 this is provided by ``python-paramiko1.10`` in the EPEL repository::

    proxy_command = ssh -W "%h:%p" bastion

.. _openssh_settings:

OpenSSH Specific Settings
-------------------------

Under the [ssh_connection] header, the following settings are tunable for SSH connections.  OpenSSH is the default connection type for Ansible
on OSes that are new enough to support ControlPersist.  (This means basically all operating systems except Enterprise Linux 6 or earlier).

.. _ssh_args:

ssh_args
========

If set, this will pass a specific set of options to Ansible rather than Ansible's usual defaults::

    ssh_args = -o ControlMaster=auto -o ControlPersist=60s

In particular, users may wish to raise the ControlPersist time to encourage performance.  A value of 30 minutes may
be appropriate. If `ssh_args` is set, the default ``control_path`` setting is not used.

.. _control_path:

control_path
============

This is the location to save ControlPath sockets. This defaults to::

    control_path=%(directory)s/ansible-ssh-%%h-%%p-%%r

On some systems with very long hostnames or very long path names (caused by long user names or
deeply nested home directories) this can exceed the character limit on
file socket names (108 characters for most platforms). In that case, you
may wish to shorten the string to something like the below::

    control_path = %(directory)s/%%h-%%r

Ansible 1.4 and later will instruct users to run with "-vvvv" in situations where it hits this problem
and if so it is easy to tell there is too long of a Control Path filename.  This may be frequently
encountered on EC2. This setting is ignored if ``ssh_args`` is set.

.. _scp_if_ssh:

scp_if_ssh
==========

Occasionally users may be managing a remote system that doesn't have SFTP enabled.  If set to True, we can
cause scp to be used to transfer remote files instead::

    scp_if_ssh=False

There's really no reason to change this unless problems are encountered, and then there's also no real drawback
to managing the switch.  Most environments support SFTP by default and this doesn't usually need to be changed.


.. _pipelining:

pipelining
==========

Enabling pipelining reduces the number of SSH operations required to
execute a module on the remote server, by executing many ansible modules without actual file transfer. 
This can result in a very significant performance improvement when enabled, however when using "sudo:" operations you must
first disable 'requiretty' in /etc/sudoers on all managed hosts.

By default, this option is disabled to preserve compatibility with
sudoers configurations that have requiretty (the default on many distros), but is highly
recommended if you can enable it, eliminating the need for :doc:`playbooks_acceleration`::

    pipelining=False

.. _accelerate_settings:

Accelerated Mode Settings
-------------------------

Under the [accelerate] header, the following settings are tunable for :doc:`playbooks_acceleration`.  Acceleration is 
a useful performance feature to use if you cannot enable :ref:`pipelining` in your environment, but is probably
not needed if you can.

.. _accelerate_port:

accelerate_port
===============

.. versionadded:: 1.3

This is the port to use for accelerated mode::

    accelerate_port = 5099

.. _accelerate_timeout:

accelerate_timeout
==================

.. versionadded:: 1.4

This setting controls the timeout for receiving data from a client. If no data is received during this time, the socket connection will be closed. A keepalive packet is sent back to the controller every 15 seconds, so this timeout should not be set lower than 15 (by default, the timeout is 30 seconds)::

    accelerate_timeout = 30

.. _accelerate_connect_timeout:

accelerate_connect_timeout
==========================

.. versionadded:: 1.4

This setting controls the timeout for the socket connect call, and should be kept relatively low. The connection to the `accelerate_port` will be attempted 3 times before Ansible will fall back to ssh or paramiko (depending on your default connection setting) to try and start the accelerate daemon remotely. The default setting is 1.0 seconds::

    accelerate_connect_timeout = 1.0

Note, this value can be set to less than one second, however it is probably not a good idea to do so unless you're on a very fast and reliable LAN. If you're connecting to systems over the internet, it may be necessary to increase this timeout.

.. _accelerate_daemon_timeout:

accelerate_daemon_timeout
=========================

.. versionadded:: 1.6

This setting controls the timeout for the accelerated daemon, as measured in minutes. The default daemon timeout is 30 minutes::

    accelerate_daemon_timeout = 30

Note, prior to 1.6, the timeout was hard-coded from the time of the daemon's launch. For version 1.6+, the timeout is now based on the last activity to the daemon and is configurable via this option.

.. _accelerate_multi_key:

accelerate_multi_key
====================

.. versionadded:: 1.6

If enabled, this setting allows multiple private keys to be uploaded to the daemon. Any clients connecting to the daemon must also enable this option::

    accelerate_multi_key = yes

New clients first connect to the target node over SSH to upload the key, which is done via a local socket file, so they must have the same access as the user that launched the daemon originally.

.. _selinux_settings:

Selinux Specific Settings
-------------------------

These are settings that control SELinux interactions.


special_context_filesystems
===========================

.. versionadded:: 1.9

This is a list of file systems that require special treatment when dealing with security context.
The normal behaviour is for operations to copy the existing context or use the user default, this changes it to use a file system dependent context.
The default list is: nfs,vboxsf,fuse,ramfs::

    special_context_filesystems = nfs,vboxsf,fuse,ramfs,myspecialfs

libvirt_lxc_noseclabel
======================

.. versionadded:: 2.1

This setting causes libvirt to connect to lxc containers by passing --noseclabel to virsh.
This is necessary when running on systems which do not have SELinux.
The default behavior is no::

    libvirt_lxc_noseclabel = True

Galaxy Settings
---------------

The following options can be set in the [galaxy] section of ansible.cfg:

server
======

Override the default Galaxy server value of https://galaxy.ansible.com. Useful if you have a hosted version of the Galaxy web app or want to point to the testing site https://galaxy-qa.ansible.com. It does not work against private, hosted repos, which Galaxy can use for fetching and installing roles.

ignore_certs
============

If set to *yes*, ansible-galaxy will not validate TLS certificates. Handy for testing against a server with a self-signed certificate
.
