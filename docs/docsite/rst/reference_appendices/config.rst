==============================
Ansible Configuration Settings
==============================

Ansible supports a few ways of providing configuration variables, mainly through environment variables, command line switches and an ini file named ``ansible.cfg``.

Starting at Ansible 2.4 the ``ansible-config`` utility allows users to see all the configuration settings available, their defaults, how to set them and
where their current value comes from. See :doc:ansible-config for more information.


The configuration file
======================

Changes can be made and used in a configuration file which will be searched for in the following order:

 * ``ANSIBLE_CONFIG`` (environment variable if set)
 * ``ansible.cfg`` (in the current directory)
 * ``~/.ansible.cfg`` (in the home directory)
 * ``/etc/ansible/ansible.cfg``

Ansible will process the above list and use the first file found, all others are ignored.

.. note::

   The configuration file is one variant of an INI format.
   Both the hash sign (``#``) and semicolon (``;``) are allowed as
   comment markers when the comment starts the line.
   However, if the comment is inline with regular values,
   only the semicolon is allowed to introduce the comment.
   For instance::

        # some basic default values...
        inventory = /etc/ansible/hosts  ; This points to the file that lists your hosts


Common Options
==============

This is a copy of the options available from our release, your local install might have extra options due to additional plugins,
you can use the command line utility mentioned above (`ansible-config`) to browse through those.



.. _ACTION_WARNINGS:

ACTION_WARNINGS
---------------

:Description: By default Ansible will issue a warning when recieved from a task action (module or action plugin) These warnings can be silenced by adjusting this setting to False.
:Type: boolean
:Default: True
:Version Added: 2.5
:Ini Section: defaults
:Ini Key: action_warnings
:Environment: :envvar:`ANSIBLE_ACTION_WARNINGS`

.. _AGNOSTIC_BECOME_PROMPT:

AGNOSTIC_BECOME_PROMPT
----------------------

:Description: Display an agnostic become prompt instead of displaying a prompt containing the command line supplied become method
:Type: boolean
:Default: False
:Version Added: 2.5
:Ini Section: privilege_escalation
:Ini Key: agnostic_become_prompt
:Environment: :envvar:`ANSIBLE_AGNOSTIC_BECOME_PROMPT`

.. _ALLOW_WORLD_READABLE_TMPFILES:

ALLOW_WORLD_READABLE_TMPFILES
-----------------------------

:Description: This makes the temporary files created on the machine to be world readable and will issue a warning instead of failing the task. It is useful when becoming an unprivileged user.
:Type: boolean
:Default: False
:Version Added: 2.1
:Ini Section: defaults
:Ini Key: allow_world_readable_tmpfiles

.. _ANSIBLE_COW_PATH:

ANSIBLE_COW_PATH
----------------

:Description: Specify a custom cowsay path or swap in your cowsay implementation of choice
:Type: string
:Default: None
:Ini Section: defaults
:Ini Key: cowpath
:Environment: :envvar:`ANSIBLE_COW_PATH`

.. _ANSIBLE_COW_SELECTION:

ANSIBLE_COW_SELECTION
---------------------

:Description: This allows you to chose a specific cowsay stencil for the banners or use 'random' to cycle through them.
:Default: default
:Ini Section: defaults
:Ini Key: cow_selection
:Environment: :envvar:`ANSIBLE_COW_SELECTION`

.. _ANSIBLE_COW_WHITELIST:

ANSIBLE_COW_WHITELIST
---------------------

:Description: White list of cowsay templates that are 'safe' to use, set to empty list if you want to enable all installed templates.
:Type: list
:Default: ['bud-frogs', 'bunny', 'cheese', 'daemon', 'default', 'dragon', 'elephant-in-snake', 'elephant', 'eyes', 'hellokitty', 'kitty', 'luke-koala', 'meow', 'milk', 'moofasa', 'moose', 'ren', 'sheep', 'small', 'stegosaurus', 'stimpy', 'supermilker', 'three-eyes', 'turkey', 'turtle', 'tux', 'udder', 'vader-koala', 'vader', 'www']
:Ini Section: defaults
:Ini Key: cow_whitelist
:Environment: :envvar:`ANSIBLE_COW_WHITELIST`

.. _ANSIBLE_FORCE_COLOR:

ANSIBLE_FORCE_COLOR
-------------------

:Description: This options forces color mode even when running without a TTY or the "nocolor" setting is True.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: force_color
:Environment: :envvar:`ANSIBLE_FORCE_COLOR`

.. _ANSIBLE_NOCOLOR:

ANSIBLE_NOCOLOR
---------------

:Description: This setting allows suppressing colorizing output, which is used to give a better indication of failure and status information.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: nocolor
:Environment: :envvar:`ANSIBLE_NOCOLOR`

.. _ANSIBLE_NOCOWS:

ANSIBLE_NOCOWS
--------------

:Description: If you have cowsay installed but want to avoid the 'cows' (why????), use this.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: nocows
:Environment: :envvar:`ANSIBLE_NOCOWS`

.. _ANSIBLE_PIPELINING:

ANSIBLE_PIPELINING
------------------

:Description: Pipelining, if supported by the connection plugin, reduces the number of network operations required to execute a module on the remote server, by executing many Ansible modules without actual file transfer. This can result in a very significant performance improvement when enabled. However this conflicts with privilege escalation (become). For example, when using 'sudo:' operations you must first disable 'requiretty' in /etc/sudoers on all managed hosts, which is why it is disabled by default.
:Type: boolean
:Default: False
:Ini Section: connection
:Ini Key: pipelining
:Ini Section: ssh_connection
:Ini Key: pipelining
:Environment: :envvar:`ANSIBLE_PIPELINING`
:Environment: :envvar:`ANSIBLE_SSH_PIPELINING`

.. _ANSIBLE_SSH_ARGS:

ANSIBLE_SSH_ARGS
----------------

:Description: If set, this will override the Ansible default ssh arguments. In particular, users may wish to raise the ControlPersist time to encourage performance.  A value of 30 minutes may be appropriate. Be aware that if `-o ControlPath` is set in ssh_args, the control path setting is not used.
:Default: -C -o ControlMaster=auto -o ControlPersist=60s
:Ini Section: ssh_connection
:Ini Key: ssh_args
:Environment: :envvar:`ANSIBLE_SSH_ARGS`

.. _ANSIBLE_SSH_CONTROL_PATH:

ANSIBLE_SSH_CONTROL_PATH
------------------------

:Description: This is the location to save ssh's ControlPath sockets, it uses ssh's variable substitution. Since 2.3, if null, ansible will generate a unique hash. Use `%(directory)s` to indicate where to use the control dir path setting. Before 2.3 it defaulted to `control_path=%(directory)s/ansible-ssh-%%h-%%p-%%r`. Be aware that this setting is ignored if `-o ControlPath` is set in ssh args.
:Default: None
:Ini Section: ssh_connection
:Ini Key: control_path
:Environment: :envvar:`ANSIBLE_SSH_CONTROL_PATH`

.. _ANSIBLE_SSH_CONTROL_PATH_DIR:

ANSIBLE_SSH_CONTROL_PATH_DIR
----------------------------

:Description: This sets the directory to use for ssh control path if the control path setting is null. Also, provides the `%(directory)s` variable for the control path setting.
:Default: ~/.ansible/cp
:Ini Section: ssh_connection
:Ini Key: control_path_dir
:Environment: :envvar:`ANSIBLE_SSH_CONTROL_PATH_DIR`

.. _ANSIBLE_SSH_EXECUTABLE:

ANSIBLE_SSH_EXECUTABLE
----------------------

:Description: This defines the location of the ssh binary. It defaults to `ssh` which will use the first ssh binary available in $PATH. This option is usually not required, it might be useful when access to system ssh is restricted, or when using ssh wrappers to connect to remote hosts.
:Default: ssh
:Version Added: 2.2
:Ini Section: ssh_connection
:Ini Key: ssh_executable
:Environment: :envvar:`ANSIBLE_SSH_EXECUTABLE`

.. _ANSIBLE_SSH_RETRIES:

ANSIBLE_SSH_RETRIES
-------------------

:Description: Number of attempts to establish a connection before we give up and report the host as 'UNREACHABLE'
:Type: integer
:Default: 0
:Ini Section: ssh_connection
:Ini Key: retries
:Environment: :envvar:`ANSIBLE_SSH_RETRIES`

.. _ANY_ERRORS_FATAL:

ANY_ERRORS_FATAL
----------------

:Description: Sets the default value for the any_errors_fatal keyword, if True, Task failures will be considered fatal errors.
:Type: boolean
:Default: False
:Version Added: 2.4
:Ini Section: defaults
:Ini Key: any_errors_fatal
:Environment: :envvar:`ANSIBLE_ANY_ERRORS_FATAL`

.. _BECOME_ALLOW_SAME_USER:

BECOME_ALLOW_SAME_USER
----------------------

:Description: This setting controls if become is skipped when remote user and become user are the same. I.E root sudo to root.
:Type: boolean
:Default: False
:Ini Section: privilege_escalation
:Ini Key: become_allow_same_user
:Environment: :envvar:`ANSIBLE_BECOME_ALLOW_SAME_USER`

.. _CACHE_PLUGIN:

CACHE_PLUGIN
------------

:Description: Chooses which cache plugin to use, the default 'memory' is ephimeral.
:Default: memory
:Ini Section: defaults
:Ini Key: fact_caching
:Environment: :envvar:`ANSIBLE_CACHE_PLUGIN`

.. _CACHE_PLUGIN_CONNECTION:

CACHE_PLUGIN_CONNECTION
-----------------------

:Description: Defines connection or path information for the cache plugin
:Default: None
:Ini Section: defaults
:Ini Key: fact_caching_connection
:Environment: :envvar:`ANSIBLE_CACHE_PLUGIN_CONNECTION`

.. _CACHE_PLUGIN_PREFIX:

CACHE_PLUGIN_PREFIX
-------------------

:Description: Prefix to use for cache plugin files/tables
:Default: ansible_facts
:Ini Section: defaults
:Ini Key: fact_caching_prefix
:Environment: :envvar:`ANSIBLE_CACHE_PLUGIN_PREFIX`

.. _CACHE_PLUGIN_TIMEOUT:

CACHE_PLUGIN_TIMEOUT
--------------------

:Description: Expiration timeout for the cache plugin data
:Type: integer
:Default: 86400
:Ini Section: defaults
:Ini Key: fact_caching_timeout
:Environment: :envvar:`ANSIBLE_CACHE_PLUGIN_TIMEOUT`

.. _COLOR_CHANGED:

COLOR_CHANGED
-------------

:Description: Defines the color to use on 'Changed' task status
:Default: yellow
:Ini Section: colors
:Ini Key: changed
:Environment: :envvar:`ANSIBLE_COLOR_CHANGED`

.. _COLOR_DEBUG:

COLOR_DEBUG
-----------

:Description: Defines the color to use when emitting debug messages
:Default: dark gray
:Ini Section: colors
:Ini Key: debug
:Environment: :envvar:`ANSIBLE_COLOR_DEBUG`

.. _COLOR_DEPRECATE:

COLOR_DEPRECATE
---------------

:Description: Defines the color to use when emitting deprecation messages
:Default: purple
:Ini Section: colors
:Ini Key: deprecate
:Environment: :envvar:`ANSIBLE_COLOR_DEPRECATE`

.. _COLOR_DIFF_ADD:

COLOR_DIFF_ADD
--------------

:Description: Defines the color to use when showing added lines in diffs
:Default: green
:Ini Section: colors
:Ini Key: diff_add
:Environment: :envvar:`ANSIBLE_COLOR_DIFF_ADD`

.. _COLOR_DIFF_LINES:

COLOR_DIFF_LINES
----------------

:Description: Defines the color to use when showing diffs
:Default: cyan
:Ini Section: colors
:Ini Key: diff_lines
:Environment: :envvar:`ANSIBLE_COLOR_DIFF_LINES`

.. _COLOR_DIFF_REMOVE:

COLOR_DIFF_REMOVE
-----------------

:Description: Defines the color to use when showing removed lines in diffs
:Default: red
:Ini Section: colors
:Ini Key: diff_remove
:Environment: :envvar:`ANSIBLE_COLOR_DIFF_REMOVE`

.. _COLOR_ERROR:

COLOR_ERROR
-----------

:Description: Defines the color to use when emitting error messages
:Default: red
:Ini Section: colors
:Ini Key: error
:Environment: :envvar:`ANSIBLE_COLOR_ERROR`

.. _COLOR_HIGHLIGHT:

COLOR_HIGHLIGHT
---------------

:Description: Color used for highlights
:Default: white
:Ini Section: colors
:Ini Key: highlight
:Environment: :envvar:`ANSIBLE_COLOR_HIGHLIGHT`

.. _COLOR_OK:

COLOR_OK
--------

:Description: Defines the color to use when showing 'OK' task status
:Default: green
:Ini Section: colors
:Ini Key: ok
:Environment: :envvar:`ANSIBLE_COLOR_OK`

.. _COLOR_SKIP:

COLOR_SKIP
----------

:Description: Defines the color to use when showing 'Skipped' task status
:Default: cyan
:Ini Section: colors
:Ini Key: skip
:Environment: :envvar:`ANSIBLE_COLOR_SKIP`

.. _COLOR_UNREACHABLE:

COLOR_UNREACHABLE
-----------------

:Description: Defines the color to use on 'Unreachable' status
:Default: bright red
:Ini Section: colors
:Ini Key: unreachable
:Environment: :envvar:`ANSIBLE_COLOR_UNREACHABLE`

.. _COLOR_VERBOSE:

COLOR_VERBOSE
-------------

:Description: Defines the color to use when emitting verbose messages. i.e those that show with '-v's.
:Default: blue
:Ini Section: colors
:Ini Key: verbose
:Environment: :envvar:`ANSIBLE_COLOR_VERBOSE`

.. _COLOR_WARN:

COLOR_WARN
----------

:Description: Defines the color to use when emitting warning messages
:Default: bright purple
:Ini Section: colors
:Ini Key: warn
:Environment: :envvar:`ANSIBLE_COLOR_WARN`

.. _COMMAND_WARNINGS:

COMMAND_WARNINGS
----------------

:Description: By default Ansible will issue a warning when the shell or command module is used and the command appears to be similar to an existing Ansible module. These warnings can be silenced by adjusting this setting to False. You can also control this at the task level with the module optoin ``warn``.
:Type: boolean
:Default: True
:Version Added: 1.8
:Ini Section: defaults
:Ini Key: command_warnings
:Environment: :envvar:`ANSIBLE_COMMAND_WARNINGS`

.. _DEFAULT_ACTION_PLUGIN_PATH:

DEFAULT_ACTION_PLUGIN_PATH
--------------------------

:Description: Colon separated paths in which Ansible will search for Action Plugins.
:Type: pathspec
:Default: ~/.ansible/plugins/action:/usr/share/ansible/plugins/action
:Ini Section: defaults
:Ini Key: action_plugins
:Environment: :envvar:`ANSIBLE_ACTION_PLUGINS`

.. _DEFAULT_ALLOW_UNSAFE_LOOKUPS:

DEFAULT_ALLOW_UNSAFE_LOOKUPS
----------------------------

:Description: When enabled, this option allows lookup plugins (whether used in variables as ``{{lookup('foo')}}`` or as a loop as with_foo) to return data that is not marked 'unsafe'. By default, such data is marked as unsafe to prevent the templating engine from evaluating any jinja2 templating language, as this could represent a security risk.  This option is provided to allow for backwards-compatibility, however users should first consider adding allow_unsafe=True to any lookups which may be expected to contain data which may be run through the templating engine late
:Type: boolean
:Default: False
:Version Added: 2.2.3
:Ini Section: defaults
:Ini Key: allow_unsafe_lookups

.. _DEFAULT_ASK_PASS:

DEFAULT_ASK_PASS
----------------

:Description: This controls whether an Ansible playbook should prompt for a login password. If using SSH keys for authentication, you probably do not needed to change this setting.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: ask_pass
:Environment: :envvar:`ANSIBLE_ASK_PASS`

.. _DEFAULT_ASK_SU_PASS:

DEFAULT_ASK_SU_PASS
-------------------

:Description: This controls whether an Ansible playbook should prompt for a su password.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: ask_su_pass
:Environment: :envvar:`ANSIBLE_ASK_SU_PASS`
:Deprecated in: 2.8
:Deprecated detail: In favor of become which is a generic framework
:Deprecated alternatives: become

.. _DEFAULT_ASK_SUDO_PASS:

DEFAULT_ASK_SUDO_PASS
---------------------

:Description: This controls whether an Ansible playbook should prompt for a sudo password.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: ask_sudo_pass
:Environment: :envvar:`ANSIBLE_ASK_SUDO_PASS`
:Deprecated in: 2.8
:Deprecated detail: In favor of become which is a generic framework
:Deprecated alternatives: become

.. _DEFAULT_ASK_VAULT_PASS:

DEFAULT_ASK_VAULT_PASS
----------------------

:Description: This controls whether an Ansible playbook should prompt for a vault password.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: ask_vault_pass
:Environment: :envvar:`ANSIBLE_ASK_VAULT_PASS`

.. _DEFAULT_BECOME:

DEFAULT_BECOME
--------------

:Description: Toggles the use of privilege escalation, allowing you to 'become' another user after login.
:Type: boolean
:Default: False
:Ini Section: privilege_escalation
:Ini Key: become
:Environment: :envvar:`ANSIBLE_BECOME`

.. _DEFAULT_BECOME_ASK_PASS:

DEFAULT_BECOME_ASK_PASS
-----------------------

:Description: Toggle to prompt for privilege escalation password.
:Type: boolean
:Default: False
:Ini Section: privilege_escalation
:Ini Key: become_ask_pass
:Environment: :envvar:`ANSIBLE_BECOME_ASK_PASS`

.. _DEFAULT_BECOME_EXE:

DEFAULT_BECOME_EXE
------------------

:Description: executable to use for privilege escalation, otherwise Ansible will depend on PATH
:Default: None
:Ini Section: privilege_escalation
:Ini Key: become_exe
:Environment: :envvar:`ANSIBLE_BECOME_EXE`

.. _DEFAULT_BECOME_FLAGS:

DEFAULT_BECOME_FLAGS
--------------------

:Description: Flags to pass to the privilege escalation executable.
:Default: 
:Ini Section: privilege_escalation
:Ini Key: become_flags
:Environment: :envvar:`ANSIBLE_BECOME_FLAGS`

.. _DEFAULT_BECOME_METHOD:

DEFAULT_BECOME_METHOD
---------------------

:Description: Privilege escalation method to use when `become` is enabled.
:Default: sudo
:Ini Section: privilege_escalation
:Ini Key: become_method
:Environment: :envvar:`ANSIBLE_BECOME_METHOD`

.. _DEFAULT_BECOME_USER:

DEFAULT_BECOME_USER
-------------------

:Description: The user your login/remote user 'becomes' when using privilege escalation, most systems will use 'root' when no user is specified.
:Default: root
:Ini Section: privilege_escalation
:Ini Key: become_user
:Environment: :envvar:`ANSIBLE_BECOME_USER`

.. _DEFAULT_CACHE_PLUGIN_PATH:

DEFAULT_CACHE_PLUGIN_PATH
-------------------------

:Description: Colon separated paths in which Ansible will search for Cache Plugins.
:Type: pathspec
:Default: ~/.ansible/plugins/cache:/usr/share/ansible/plugins/cache
:Ini Section: defaults
:Ini Key: cache_plugins
:Environment: :envvar:`ANSIBLE_CACHE_PLUGINS`

.. _DEFAULT_CALLABLE_WHITELIST:

DEFAULT_CALLABLE_WHITELIST
--------------------------

:Description: Whitelist of callable methods to be made available to template evaluation
:Type: list
:Default: []
:Ini Section: defaults
:Ini Key: callable_whitelist
:Environment: :envvar:`ANSIBLE_CALLABLE_WHITELIST`

.. _DEFAULT_CALLBACK_PLUGIN_PATH:

DEFAULT_CALLBACK_PLUGIN_PATH
----------------------------

:Description: Colon separated paths in which Ansible will search for Callback Plugins.
:Type: pathspec
:Default: ~/.ansible/plugins/callback:/usr/share/ansible/plugins/callback
:Ini Section: defaults
:Ini Key: callback_plugins
:Environment: :envvar:`ANSIBLE_CALLBACK_PLUGINS`

.. _DEFAULT_CALLBACK_WHITELIST:

DEFAULT_CALLBACK_WHITELIST
--------------------------

:Description: List of whitelisted callbacks, not all callbacks need whitelisting, but many of those shipped with Ansible do as we don't want them activated by default.
:Type: list
:Default: []
:Ini Section: defaults
:Ini Key: callback_whitelist
:Environment: :envvar:`ANSIBLE_CALLBACK_WHITELIST`

.. _DEFAULT_CONNECTION_PLUGIN_PATH:

DEFAULT_CONNECTION_PLUGIN_PATH
------------------------------

:Description: Colon separated paths in which Ansible will search for Connection Plugins.
:Type: pathspec
:Default: ~/.ansible/plugins/connection:/usr/share/ansible/plugins/connection
:Ini Section: defaults
:Ini Key: connection_plugins
:Environment: :envvar:`ANSIBLE_CONNECTION_PLUGINS`

.. _DEFAULT_DEBUG:

DEFAULT_DEBUG
-------------

:Description: Toggles debug output in Ansible, VERY verbose and can hinder multiprocessing.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: debug
:Environment: :envvar:`ANSIBLE_DEBUG`

.. _DEFAULT_EXECUTABLE:

DEFAULT_EXECUTABLE
------------------

:Description: This indicates the command to use to spawn a shell under for Ansible's execution needs on a target. Users may need to change this in rare instances when shell usage is constrained, but in most cases it may be left as is.
:Default: /bin/sh
:Ini Section: defaults
:Ini Key: executable
:Environment: :envvar:`ANSIBLE_EXECUTABLE`

.. _DEFAULT_FACT_PATH:

DEFAULT_FACT_PATH
-----------------

:Description: This option allows you to globally configure a custom path for 'local_facts' for the implied M(setup) task when using fact gathering. If not set, it will fallback to the default from the M(setup) module: ``/etc/ansible/facts.d``. This does **not** affect  user defined tasks that use the M(setup) module.
:Type: path
:Default: None
:Ini Section: defaults
:Ini Key: fact_path
:Environment: :envvar:`ANSIBLE_FACT_PATH`

.. _DEFAULT_FILTER_PLUGIN_PATH:

DEFAULT_FILTER_PLUGIN_PATH
--------------------------

:Description: Colon separated paths in which Ansible will search for Jinja2 Filter Plugins.
:Type: pathspec
:Default: ~/.ansible/plugins/filter:/usr/share/ansible/plugins/filter
:Ini Section: defaults
:Ini Key: filter_plugins
:Environment: :envvar:`ANSIBLE_FILTER_PLUGINS`

.. _DEFAULT_FORCE_HANDLERS:

DEFAULT_FORCE_HANDLERS
----------------------

:Description: This option controls if notified handlers run on a host even if a failure occurs on that host. When false, the handlers will not run if a failure has occurred on a host. This can also be set per play or on the command line. See Handlers and Failure for more details.
:Type: boolean
:Default: False
:Version Added: 1.9.1
:Ini Section: defaults
:Ini Key: force_handlers
:Environment: :envvar:`ANSIBLE_FORCE_HANDLERS`

.. _DEFAULT_FORKS:

DEFAULT_FORKS
-------------

:Description: Maximum number of forks Ansible will use to execute tasks on target hosts.
:Type: integer
:Default: 5
:Ini Section: defaults
:Ini Key: forks
:Environment: :envvar:`ANSIBLE_FORKS`

.. _DEFAULT_GATHER_SUBSET:

DEFAULT_GATHER_SUBSET
---------------------

:Description: Set the `gather_subset` option for the M(setup) task in the implicit fact gathering. See the module documentation for specifics. It does **not** apply to user defined M(setup) tasks.
:Default: all
:Version Added: 2.1
:Ini Section: defaults
:Ini Key: gather_subset
:Environment: :envvar:`ANSIBLE_GATHER_SUBSET`

.. _DEFAULT_GATHER_TIMEOUT:

DEFAULT_GATHER_TIMEOUT
----------------------

:Description: Set the timeout in seconds for the implicit fact gathering. It does **not** apply to user defined M(setup) tasks.
:Type: integer
:Default: 10
:Ini Section: defaults
:Ini Key: gather_timeout
:Environment: :envvar:`ANSIBLE_GATHER_TIMEOUT`

.. _DEFAULT_GATHERING:

DEFAULT_GATHERING
-----------------

:Description: This setting controls the default policy of fact gathering (facts discovered about remote systems). When 'implicit' (the default), the cache plugin will be ignored and facts will be gathered per play unless 'gather_facts: False' is set. When 'explicit' the inverse is true, facts will not be gathered unless directly requested in the play. The 'smart' value means each new host that has no facts discovered will be scanned, but if the same host is addressed in multiple plays it will not be contacted again in the playbook run. This option can be useful for those wishing to save fact gathering time. Both 'smart' and 'explicit' will use the cache plugin.
:Default: implicit
:Version Added: 1.6
:Ini Section: defaults
:Ini Key: gathering
:Environment: :envvar:`ANSIBLE_GATHERING`

.. _DEFAULT_HANDLER_INCLUDES_STATIC:

DEFAULT_HANDLER_INCLUDES_STATIC
-------------------------------

:Description: Since 2.0 M(include) can be 'dynamic', this setting (if True) forces that if the include appears in a ``handlers`` section to be 'static'.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: handler_includes_static
:Environment: :envvar:`ANSIBLE_HANDLER_INCLUDES_STATIC`
:Deprecated in: 2.8
:Deprecated detail: include itself is deprecated and this setting will not matter in the future
:Deprecated alternatives: none as its already built into the decision between include_tasks and import_tasks

.. _DEFAULT_HASH_BEHAVIOUR:

DEFAULT_HASH_BEHAVIOUR
----------------------

:Description: This setting controls how variables merge in Ansible. By default Ansible will override variables in specific precedence orders, as described in Variables. When a variable of higher precedence wins, it will replace the other value. Some users prefer that variables that are hashes (aka 'dictionaries' in Python terms) are merged. This setting is called 'merge'. This is not the default behavior and it does not affect variables whose values are scalars (integers, strings) or arrays.  We generally recommend not using this setting unless you think you have an absolute need for it, and playbooks in the official examples repos do not use this setting In version 2.0 a ``combine`` filter was added to allow doing this for a particular variable (described in Filters).
:Type: string
:Default: replace
:Ini Section: defaults
:Ini Key: hash_behaviour
:Environment: :envvar:`ANSIBLE_HASH_BEHAVIOUR`

.. _DEFAULT_HOST_LIST:

DEFAULT_HOST_LIST
-----------------

:Description: Colon separated list of Ansible inventory sources
:Type: pathlist
:Default: /etc/ansible/hosts
:Ini Section: defaults
:Ini Key: hostfile
:Ini Section: defaults
:Ini Key: inventory
:Environment: :envvar:`ANSIBLE_HOSTS`
:Environment: :envvar:`ANSIBLE_INVENTORY`

.. _DEFAULT_INTERNAL_POLL_INTERVAL:

DEFAULT_INTERNAL_POLL_INTERVAL
------------------------------

:Description: This sets the interval (in seconds) of Ansible internal processes polling each other. Lower values improve performance with large playbooks at the expense of extra CPU load. Higher values are more suitable for Ansible usage in automation scenarios, when UI responsiveness is not required but CPU usage might be a concern. The default corresponds to the value hardcoded in Ansible <= 2.1
:Type: float
:Default: 0.001
:Version Added: 2.2
:Ini Section: defaults
:Ini Key: internal_poll_interval

.. _DEFAULT_INVENTORY_PLUGIN_PATH:

DEFAULT_INVENTORY_PLUGIN_PATH
-----------------------------

:Description: Colon separated paths in which Ansible will search for Inventory Plugins.
:Type: pathspec
:Default: ~/.ansible/plugins/inventory:/usr/share/ansible/plugins/inventory
:Ini Section: defaults
:Ini Key: inventory_plugins
:Environment: :envvar:`ANSIBLE_INVENTORY_PLUGINS`

.. _DEFAULT_JINJA2_EXTENSIONS:

DEFAULT_JINJA2_EXTENSIONS
-------------------------

:Description: This is a developer-specific feature that allows enabling additional Jinja2 extensions. See the Jinja2 documentation for details. If you do not know what these do, you probably don't need to change this setting :)
:Default: []
:Ini Section: defaults
:Ini Key: jinja2_extensions
:Environment: :envvar:`ANSIBLE_JINJA2_EXTENSIONS`

.. _DEFAULT_KEEP_REMOTE_FILES:

DEFAULT_KEEP_REMOTE_FILES
-------------------------

:Description: Enables/disables the cleaning up of the temporary files Ansible used to execute the tasks on the remote.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: keep_remote_files
:Environment: :envvar:`ANSIBLE_KEEP_REMOTE_FILES`

.. _DEFAULT_LIBVIRT_LXC_NOSECLABEL:

DEFAULT_LIBVIRT_LXC_NOSECLABEL
------------------------------

:Description: This setting causes libvirt to connect to lxc containers by passing --noseclabel to virsh. This is necessary when running on systems which do not have SELinux.
:Type: boolean
:Default: False
:Version Added: 2.1
:Ini Section: selinux
:Ini Key: libvirt_lxc_noseclabel
:Environment: :envvar:`LIBVIRT_LXC_NOSECLABEL`

.. _DEFAULT_LOAD_CALLBACK_PLUGINS:

DEFAULT_LOAD_CALLBACK_PLUGINS
-----------------------------

:Description: Controls whether callback plugins are loaded when running /usr/bin/ansible. This may be used to log activity from the command line, send notifications, and so on. Callback plugins are always loaded for ``ansible-playbook``.
:Type: boolean
:Default: False
:Version Added: 1.8
:Ini Section: defaults
:Ini Key: bin_ansible_callbacks
:Environment: :envvar:`ANSIBLE_LOAD_CALLBACK_PLUGINS`

.. _DEFAULT_LOCAL_TMP:

DEFAULT_LOCAL_TMP
-----------------

:Description: Temporary directory for Ansible to use on the controller.
:Type: tmppath
:Default: ~/.ansible/tmp
:Ini Section: defaults
:Ini Key: local_tmp
:Environment: :envvar:`ANSIBLE_LOCAL_TEMP`

.. _DEFAULT_LOG_PATH:

DEFAULT_LOG_PATH
----------------

:Description: File to which Ansible will log on the controller. When empty logging is disabled.
:Type: path
:Default: 
:Ini Section: defaults
:Ini Key: log_path
:Environment: :envvar:`ANSIBLE_LOG_PATH`

.. _DEFAULT_LOOKUP_PLUGIN_PATH:

DEFAULT_LOOKUP_PLUGIN_PATH
--------------------------

:Description: Colon separated paths in which Ansible will search for Lookup Plugins.
:Type: pathspec
:Default: ~/.ansible/plugins/lookup:/usr/share/ansible/plugins/lookup
:Ini Section: defaults
:Ini Key: lookup_plugins
:Environment: :envvar:`ANSIBLE_LOOKUP_PLUGINS`

.. _DEFAULT_MANAGED_STR:

DEFAULT_MANAGED_STR
-------------------

:Description: Sets the macro for the 'ansible_managed' variable available for M(template) tasks.
:Default: Ansible managed
:Ini Section: defaults
:Ini Key: ansible_managed

.. _DEFAULT_MODULE_ARGS:

DEFAULT_MODULE_ARGS
-------------------

:Description: This sets the default arguments to pass to the ``ansible`` adhoc binary if no ``-a`` is specified.
:Default: 
:Ini Section: defaults
:Ini Key: module_args
:Environment: :envvar:`ANSIBLE_MODULE_ARGS`

.. _DEFAULT_MODULE_COMPRESSION:

DEFAULT_MODULE_COMPRESSION
--------------------------

:Description: Compression scheme to use when transfering Python modules to the target.
:Default: ZIP_DEFLATED
:Ini Section: defaults
:Ini Key: module_compression

.. _DEFAULT_MODULE_LANG:

DEFAULT_MODULE_LANG
-------------------

:Description: Language locale setting to use for modules when they execute on the target. If empty it tries to set itself to the LANG environment variable on the controller. This is only used if DEFAULT_MODULE_SET_LOCALE is set to true
:Default: {{ CONTROLLER_LANG }}
:Ini Section: defaults
:Ini Key: module_lang
:Environment: :envvar:`ANSIBLE_MODULE_LANG`
:Deprecated in: 2.9
:Deprecated detail: Modules are coded to set their own locale if needed for screenscraping
:Deprecated alternatives: 

.. _DEFAULT_MODULE_NAME:

DEFAULT_MODULE_NAME
-------------------

:Description: Module to use with the ``ansible`` AdHoc command, if none is specified via ``-m``.
:Default: command
:Ini Section: defaults
:Ini Key: module_name

.. _DEFAULT_MODULE_PATH:

DEFAULT_MODULE_PATH
-------------------

:Description: Colon separated paths in which Ansible will search for Modules.
:Type: pathspec
:Default: ~/.ansible/plugins/modules:/usr/share/ansible/plugins/modules
:Ini Section: defaults
:Ini Key: library
:Environment: :envvar:`ANSIBLE_LIBRARY`

.. _DEFAULT_MODULE_SET_LOCALE:

DEFAULT_MODULE_SET_LOCALE
-------------------------

:Description: Controls if we set locale for modules when executing on the target.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: module_set_locale
:Environment: :envvar:`ANSIBLE_MODULE_SET_LOCALE`
:Deprecated in: 2.9
:Deprecated detail: Modules are coded to set their own locale if needed for screenscraping
:Deprecated alternatives: 

.. _DEFAULT_MODULE_UTILS_PATH:

DEFAULT_MODULE_UTILS_PATH
-------------------------

:Description: Colon separated paths in which Ansible will search for Module utils files, which are shared by modules.
:Type: pathspec
:Default: ~/.ansible/plugins/module_utils:/usr/share/ansible/plugins/module_utils
:Ini Section: defaults
:Ini Key: module_utils
:Environment: :envvar:`ANSIBLE_MODULE_UTILS`

.. _DEFAULT_NO_LOG:

DEFAULT_NO_LOG
--------------

:Description: Toggle Ansible's display and logging of task details, mainly used to avoid security disclosures.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: no_log
:Environment: :envvar:`ANSIBLE_NO_LOG`

.. _DEFAULT_NO_TARGET_SYSLOG:

DEFAULT_NO_TARGET_SYSLOG
------------------------

:Description: Toggle Ansible logging to syslog on the target when it executes tasks.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: no_target_syslog
:Environment: :envvar:`ANSIBLE_NO_TARGET_SYSLOG`

.. _DEFAULT_NULL_REPRESENTATION:

DEFAULT_NULL_REPRESENTATION
---------------------------

:Description: What templating should return as a 'null' value. When not set it will let Jinja2 decide.
:Type: none
:Default: None
:Ini Section: defaults
:Ini Key: null_representation
:Environment: :envvar:`ANSIBLE_NULL_REPRESENTATION`

.. _DEFAULT_POLL_INTERVAL:

DEFAULT_POLL_INTERVAL
---------------------

:Description: For asynchronous tasks in Ansible (covered in Asynchronous Actions and Polling), this is how often to check back on the status of those tasks when an explicit poll interval is not supplied. The default is a reasonably moderate 15 seconds which is a tradeoff between checking in frequently and providing a quick turnaround when something may have completed.
:Type: integer
:Default: 15
:Ini Section: defaults
:Ini Key: poll_interval
:Environment: :envvar:`ANSIBLE_POLL_INTERVAL`

.. _DEFAULT_PRIVATE_KEY_FILE:

DEFAULT_PRIVATE_KEY_FILE
------------------------

:Description: Option for connections using a certificate or key file to authenticate, rather than an agent or passwords, you can set the default value here to avoid re-specifying --private-key with every invocation.
:Type: path
:Default: None
:Ini Section: defaults
:Ini Key: private_key_file
:Environment: :envvar:`ANSIBLE_PRIVATE_KEY_FILE`

.. _DEFAULT_PRIVATE_ROLE_VARS:

DEFAULT_PRIVATE_ROLE_VARS
-------------------------

:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: private_role_vars
:Environment: :envvar:`ANSIBLE_PRIVATE_ROLE_VARS`

.. _DEFAULT_REMOTE_PORT:

DEFAULT_REMOTE_PORT
-------------------

:Description: Port to use in remote connections, when blank it will use the connection plugin default.
:Type: integer
:Default: None
:Ini Section: defaults
:Ini Key: remote_port
:Environment: :envvar:`ANSIBLE_REMOTE_PORT`

.. _DEFAULT_REMOTE_USER:

DEFAULT_REMOTE_USER
-------------------

:Description: Sets the login user for the target machines When blank it uses the connection plugin's default, normally the user currently executing Ansible.
:Default: None
:Ini Section: defaults
:Ini Key: remote_user
:Environment: :envvar:`ANSIBLE_REMOTE_USER`

.. _DEFAULT_ROLES_PATH:

DEFAULT_ROLES_PATH
------------------

:Description: Colon separated paths in which Ansible will search for Roles.
:Type: pathspec
:Default: ~/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles
:Ini Section: defaults
:Ini Key: roles_path
:Environment: :envvar:`ANSIBLE_ROLES_PATH`

.. _DEFAULT_SCP_IF_SSH:

DEFAULT_SCP_IF_SSH
------------------

:Description: Prefered method to use when transfering files over ssh When set to smart, Ansible will try them until one succeeds or they all fail If set to True, it will force 'scp', if False it will use 'sftp'
:Default: smart
:Ini Section: ssh_connection
:Ini Key: scp_if_ssh
:Environment: :envvar:`ANSIBLE_SCP_IF_SSH`

.. _DEFAULT_SELINUX_SPECIAL_FS:

DEFAULT_SELINUX_SPECIAL_FS
--------------------------

:Description: Some filesystems do not support safe operations and/or return inconsistent errors, this setting makes Ansible 'tolerate' those in the list w/o causing fatal errors. Data corruption may occur and writes are not always verified when a filesystem is in the list.
:Type: list
:Default: fuse, nfs, vboxsf, ramfs, 9p
:Ini Section: selinux
:Ini Key: special_context_filesystems

.. _DEFAULT_SFTP_BATCH_MODE:

DEFAULT_SFTP_BATCH_MODE
-----------------------

:Type: boolean
:Default: True
:Ini Section: ssh_connection
:Ini Key: sftp_batch_mode
:Environment: :envvar:`ANSIBLE_SFTP_BATCH_MODE`

.. _DEFAULT_SQUASH_ACTIONS:

DEFAULT_SQUASH_ACTIONS
----------------------

:Description: Ansible can optimise actions that call modules that support list parameters when using ``with_`` looping. Instead of calling the module once for each item, the module is called once with the full list. The default value for this setting is only for certain package managers, but it can be used for any module Currently, this is only supported for modules that have a name or pkg parameter, and only when the item is the only thing being passed to the parameter.
:Type: list
:Default: apk, apt, dnf, homebrew, openbsd_pkg, pacman, pkgng, yum, zypper
:Version Added: 2.0
:Ini Section: defaults
:Ini Key: squash_actions
:Environment: :envvar:`ANSIBLE_SQUASH_ACTIONS`

.. _DEFAULT_SSH_TRANSFER_METHOD:

DEFAULT_SSH_TRANSFER_METHOD
---------------------------

:Description: unused?
:Default: None
:Ini Section: ssh_connection
:Ini Key: transfer_method
:Environment: :envvar:`ANSIBLE_SSH_TRANSFER_METHOD`

.. _DEFAULT_STDOUT_CALLBACK:

DEFAULT_STDOUT_CALLBACK
-----------------------

:Description: Set the main callback used to display Ansible output, you can only have one at a time. You can have many other callbacks, but just one can be in charge of stdout.
:Default: default
:Ini Section: defaults
:Ini Key: stdout_callback
:Environment: :envvar:`ANSIBLE_STDOUT_CALLBACK`

.. _DEFAULT_STRATEGY:

DEFAULT_STRATEGY
----------------

:Description: Set the default strategy used for plays.
:Default: linear
:Version Added: 2.3
:Ini Section: defaults
:Ini Key: strategy
:Environment: :envvar:`ANSIBLE_STRATEGY`

.. _DEFAULT_STRATEGY_PLUGIN_PATH:

DEFAULT_STRATEGY_PLUGIN_PATH
----------------------------

:Description: Colon separated paths in which Ansible will search for Strategy Plugins.
:Type: pathspec
:Default: ~/.ansible/plugins/strategy:/usr/share/ansible/plugins/strategy
:Ini Section: defaults
:Ini Key: strategy_plugins
:Environment: :envvar:`ANSIBLE_STRATEGY_PLUGINS`

.. _DEFAULT_SU:

DEFAULT_SU
----------

:Description: Toggle the use of "su" for tasks.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: su
:Environment: :envvar:`ANSIBLE_SU`

.. _DEFAULT_SU_EXE:

DEFAULT_SU_EXE
--------------

:Description: specify an "su" executable, otherwise it relies on PATH.
:Default: su
:Ini Section: defaults
:Ini Key: su_exe
:Environment: :envvar:`ANSIBLE_SU_EXE`
:Deprecated in: 2.8
:Deprecated detail: In favor of become which is a generic framework
:Deprecated alternatives: become

.. _DEFAULT_SU_FLAGS:

DEFAULT_SU_FLAGS
----------------

:Description: Flags to pass to su
:Default: 
:Ini Section: defaults
:Ini Key: su_flags
:Environment: :envvar:`ANSIBLE_SU_FLAGS`
:Deprecated in: 2.8
:Deprecated detail: In favor of become which is a generic framework
:Deprecated alternatives: become

.. _DEFAULT_SU_USER:

DEFAULT_SU_USER
---------------

:Description: User you become when using "su", leaving it blank will use the default configured on the target (normally root)
:Default: None
:Ini Section: defaults
:Ini Key: su_user
:Environment: :envvar:`ANSIBLE_SU_USER`
:Deprecated in: 2.8
:Deprecated detail: In favor of become which is a generic framework
:Deprecated alternatives: become

.. _DEFAULT_SUDO:

DEFAULT_SUDO
------------

:Description: Toggle the use of "sudo" for tasks.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: sudo
:Environment: :envvar:`ANSIBLE_SUDO`
:Deprecated in: 2.8
:Deprecated detail: In favor of become which is a generic framework
:Deprecated alternatives: become

.. _DEFAULT_SUDO_EXE:

DEFAULT_SUDO_EXE
----------------

:Description: specify an "sudo" executable, otherwise it relies on PATH.
:Default: sudo
:Ini Section: defaults
:Ini Key: sudo_exe
:Environment: :envvar:`ANSIBLE_SUDO_EXE`
:Deprecated in: 2.8
:Deprecated detail: In favor of become which is a generic framework
:Deprecated alternatives: become

.. _DEFAULT_SUDO_FLAGS:

DEFAULT_SUDO_FLAGS
------------------

:Description: Flags to pass to "sudo"
:Default: -H -S -n
:Ini Section: defaults
:Ini Key: sudo_flags
:Environment: :envvar:`ANSIBLE_SUDO_FLAGS`
:Deprecated in: 2.8
:Deprecated detail: In favor of become which is a generic framework
:Deprecated alternatives: become

.. _DEFAULT_SUDO_USER:

DEFAULT_SUDO_USER
-----------------

:Description: User you become when using "sudo", leaving it blank will use the default configured on the target (normally root)
:Default: None
:Ini Section: defaults
:Ini Key: sudo_user
:Environment: :envvar:`ANSIBLE_SUDO_USER`
:Deprecated in: 2.8
:Deprecated detail: In favor of become which is a generic framework
:Deprecated alternatives: become

.. _DEFAULT_SYSLOG_FACILITY:

DEFAULT_SYSLOG_FACILITY
-----------------------

:Description: Syslog facility to use when Ansible logs to the remote target
:Default: LOG_USER
:Ini Section: defaults
:Ini Key: syslog_facility
:Environment: :envvar:`ANSIBLE_SYSLOG_FACILITY`

.. _DEFAULT_TASK_INCLUDES_STATIC:

DEFAULT_TASK_INCLUDES_STATIC
----------------------------

:Description: The `include` tasks can be static or dynamic, this toggles the default expected behaviour if autodetection fails and it is not explicitly set in task.
:Type: boolean
:Default: False
:Version Added: 2.1
:Ini Section: defaults
:Ini Key: task_includes_static
:Environment: :envvar:`ANSIBLE_TASK_INCLUDES_STATIC`
:Deprecated in: 2.8
:Deprecated detail: include itself is deprecated and this setting will not matter in the future
:Deprecated alternatives: None, as its already built into the decision between include_tasks and import_tasks

.. _DEFAULT_TEST_PLUGIN_PATH:

DEFAULT_TEST_PLUGIN_PATH
------------------------

:Description: Colon separated paths in which Ansible will search for Jinja2 Test Plugins.
:Type: pathspec
:Default: ~/.ansible/plugins/test:/usr/share/ansible/plugins/test
:Ini Section: defaults
:Ini Key: test_plugins
:Environment: :envvar:`ANSIBLE_TEST_PLUGINS`

.. _DEFAULT_TIMEOUT:

DEFAULT_TIMEOUT
---------------

:Description: This is the default timeout for connection plugins to use.
:Type: integer
:Default: 10
:Ini Section: defaults
:Ini Key: timeout
:Environment: :envvar:`ANSIBLE_TIMEOUT`

.. _DEFAULT_TRANSPORT:

DEFAULT_TRANSPORT
-----------------

:Description: Default connection plugin to use, the 'smart' option will toggle between 'ssh' and 'paramiko' depending on controller OS and ssh versions
:Default: smart
:Ini Section: defaults
:Ini Key: transport
:Environment: :envvar:`ANSIBLE_TRANSPORT`

.. _DEFAULT_UNDEFINED_VAR_BEHAVIOR:

DEFAULT_UNDEFINED_VAR_BEHAVIOR
------------------------------

:Description: When True, this causes ansible templating to fail steps that reference variable names that are likely typoed. Otherwise, any '{{ template_expression }}' that contains undefined variables will be rendered in a template or ansible action line exactly as written.
:Type: boolean
:Default: True
:Version Added: 1.3
:Ini Section: defaults
:Ini Key: error_on_undefined_vars
:Environment: :envvar:`ANSIBLE_ERROR_ON_UNDEFINED_VARS`

.. _DEFAULT_VARS_PLUGIN_PATH:

DEFAULT_VARS_PLUGIN_PATH
------------------------

:Description: Colon separated paths in which Ansible will search for Vars Plugins.
:Type: pathspec
:Default: ~/.ansible/plugins/vars:/usr/share/ansible/plugins/vars
:Ini Section: defaults
:Ini Key: vars_plugins
:Environment: :envvar:`ANSIBLE_VARS_PLUGINS`

.. _DEFAULT_VAULT_ENCRYPT_IDENTITY:

DEFAULT_VAULT_ENCRYPT_IDENTITY
------------------------------

:Description: The vault_id to use for encrypting by default. If multiple vault_ids are provided, this specifies which to use for encryption. The --encrypt-vault-id cli option overrides the configured value.
:Default: None
:Ini Section: defaults
:Ini Key: vault_encrypt_identity
:Environment: :envvar:`ANSIBLE_VAULT_ENCRYPT_IDENTITY`

.. _DEFAULT_VAULT_ID_MATCH:

DEFAULT_VAULT_ID_MATCH
----------------------

:Description: If true, decrypting vaults with a vault id will only try the password from the matching vault-id
:Default: False
:Ini Section: defaults
:Ini Key: vault_id_match
:Environment: :envvar:`ANSIBLE_VAULT_ID_MATCH`

.. _DEFAULT_VAULT_IDENTITY:

DEFAULT_VAULT_IDENTITY
----------------------

:Description: The label to use for the default vault id label in cases where a vault id label is not provided
:Default: default
:Ini Section: defaults
:Ini Key: vault_identity
:Environment: :envvar:`ANSIBLE_VAULT_IDENTITY`

.. _DEFAULT_VAULT_IDENTITY_LIST:

DEFAULT_VAULT_IDENTITY_LIST
---------------------------

:Description: A list of vault-ids to use by default. Equivalent to multiple --vault-id args. Vault-ids are tried in order.
:Type: list
:Default: []
:Ini Section: defaults
:Ini Key: vault_identity_list
:Environment: :envvar:`ANSIBLE_VAULT_IDENTITY_LIST`

.. _DEFAULT_VAULT_PASSWORD_FILE:

DEFAULT_VAULT_PASSWORD_FILE
---------------------------

:Description: The vault password file to use. Equivalent to --vault-password-file or --vault-id
:Type: path
:Default: None
:Ini Section: defaults
:Ini Key: vault_password_file
:Environment: :envvar:`ANSIBLE_VAULT_PASSWORD_FILE`

.. _DEFAULT_VERBOSITY:

DEFAULT_VERBOSITY
-----------------

:Description: Sets the default verbosity, equivalent to the number of ``-v`` passed in the command line.
:Type: integer
:Default: 0
:Ini Section: defaults
:Ini Key: verbosity
:Environment: :envvar:`ANSIBLE_VERBOSITY`

.. _DEPRECATION_WARNINGS:

DEPRECATION_WARNINGS
--------------------

:Description: Toggle to control the showing of deprecation warnings
:Type: boolean
:Default: True
:Ini Section: defaults
:Ini Key: deprecation_warnings
:Environment: :envvar:`ANSIBLE_DEPRECATION_WARNINGS`

.. _DIFF_ALWAYS:

DIFF_ALWAYS
-----------

:Description: Configuration toggle to tell modules to show differences when in 'changed' status, equivalent to ``--diff``.
:Type: bool
:Default: False
:Ini Section: diff
:Ini Key: always
:Environment: :envvar:`ANSIBLE_DIFF_ALWAYS`

.. _DIFF_CONTEXT:

DIFF_CONTEXT
------------

:Description: How many lines of context to show when displaying the differences between files.
:Type: integer
:Default: 3
:Ini Section: diff
:Ini Key: context
:Environment: :envvar:`ANSIBLE_DIFF_CONTEXT`

.. _DISPLAY_ARGS_TO_STDOUT:

DISPLAY_ARGS_TO_STDOUT
----------------------

:Description: Normally ``ansible-playbook`` will print a header for each task that is run. These headers will contain the name: field from the task if you specified one. If you didn't then ``ansible-playbook`` uses the task's action to help you tell which task is presently running. Sometimes you run many of the same action and so you want more information about the task to differentiate it from others of the same action. If you set this variable to True in the config then ``ansible-playbook`` will also include the task's arguments in the header. This setting defaults to False because there is a chance that you have sensitive values in your parameters and you do not want those to be printed. If you set this to True you should be sure that you have secured your environment's stdout (no one can shoulder surf your screen and you aren't saving stdout to an insecure file) or made sure that all of your playbooks explicitly added the ``no_log: True`` parameter to tasks which have sensistive values See How do I keep secret data in my playbook? for more information.
:Type: boolean
:Default: False
:Version Added: 2.1
:Ini Section: defaults
:Ini Key: display_args_to_stdout
:Environment: :envvar:`ANSIBLE_DISPLAY_ARGS_TO_STDOUT`

.. _DISPLAY_SKIPPED_HOSTS:

DISPLAY_SKIPPED_HOSTS
---------------------

:Description: Toggle to control displaying skipped task/host entries in a task in the default callback
:Type: boolean
:Default: True
:Ini Section: defaults
:Ini Key: display_skipped_hosts
:Environment: :envvar:`DISPLAY_SKIPPED_HOSTS`

.. _ENABLE_TASK_DEBUGGER:

ENABLE_TASK_DEBUGGER
--------------------

:Description: Whether or not to enable the task debugger, this previously was done as a strategy plugin. Now all strategy plugins can inherit this behavior. The debugger defaults to activating when a task is failed on unreachable. Use the debugger keyword for more flexibility.
:Type: boolean
:Default: False
:Version Added: 2.5
:Ini Section: defaults
:Ini Key: enable_task_debugger
:Environment: :envvar:`ANSIBLE_ENABLE_TASK_DEBUGGER`

.. _ERROR_ON_MISSING_HANDLER:

ERROR_ON_MISSING_HANDLER
------------------------

:Description: Toggle to allow missing handlers to become a warning instead of an error when notifying.
:Type: boolean
:Default: True
:Ini Section: defaults
:Ini Key: error_on_missing_handler
:Environment: :envvar:`ANSIBLE_ERROR_ON_MISSING_HANDLER`

.. _GALAXY_IGNORE_CERTS:

GALAXY_IGNORE_CERTS
-------------------

:Description: If set to yes, ansible-galaxy will not validate TLS certificates. This can be useful for testing against a server with a self-signed certificate.
:Type: boolean
:Default: False
:Ini Section: galaxy
:Ini Key: ignore_certs
:Environment: :envvar:`ANSIBLE_GALAXY_IGNORE`

.. _GALAXY_ROLE_SKELETON:

GALAXY_ROLE_SKELETON
--------------------

:Description: Role skeleton directory to use as a template for the ``init`` action in ``ansible-galaxy``, same as ``--role-skeleton``.
:Type: path
:Default: None
:Ini Section: galaxy
:Ini Key: role_skeleton
:Environment: :envvar:`ANSIBLE_GALAXY_ROLE_SKELETON`

.. _GALAXY_ROLE_SKELETON_IGNORE:

GALAXY_ROLE_SKELETON_IGNORE
---------------------------

:Description: patterns of files to ignore inside a galaxy role skeleton directory
:Type: list
:Default: ['^.git$', '^.*/.git_keep$']
:Ini Section: galaxy
:Ini Key: role_skeleton_ignore
:Environment: :envvar:`ANSIBLE_GALAXY_ROLE_SKELETON_IGNORE`

.. _GALAXY_SERVER:

GALAXY_SERVER
-------------

:Description: URL to prepend when roles don't specify the full URI, assume they are referencing this server as the source.
:Default: https://galaxy.ansible.com
:Ini Section: galaxy
:Ini Key: server
:Environment: :envvar:`ANSIBLE_GALAXY_SERVER`

.. _GALAXY_TOKEN:

GALAXY_TOKEN
------------

:Description: GitHub personal access token
:Default: None
:Ini Section: galaxy
:Ini Key: token
:Environment: :envvar:`ANSIBLE_GALAXY_TOKEN`

.. _HOST_KEY_CHECKING:

HOST_KEY_CHECKING
-----------------

:Description: Set this to "False" if you want to avoid host key checking by the underlying tools Ansible uses to connect to the host
:Type: boolean
:Default: True
:Ini Section: defaults
:Ini Key: host_key_checking
:Environment: :envvar:`ANSIBLE_HOST_KEY_CHECKING`

.. _INJECT_FACTS_AS_VARS:

INJECT_FACTS_AS_VARS
--------------------

:Description: Facts are available inside the `ansible_facts` variable, this setting also pushes them as their own vars in the main namespace. Unlike inside the `ansible_facts` dictionary, these will have an `ansible_` prefix.
:Type: boolean
:Default: True
:Version Added: 2.5
:Ini Section: defaults
:Ini Key: inject_facts_as_vars
:Environment: :envvar:`ANSIBLE_INJECT_FACT_VARS`

.. _INVENTORY_ENABLED:

INVENTORY_ENABLED
-----------------

:Description: List of enabled inventory plugins, it also determines the order in which they are used.
:Type: list
:Default: ['host_list', 'script', 'yaml', 'ini', 'auto']
:Ini Section: inventory
:Ini Key: enable_plugins
:Environment: :envvar:`ANSIBLE_INVENTORY_ENABLED`

.. _INVENTORY_IGNORE_EXTS:

INVENTORY_IGNORE_EXTS
---------------------

:Description: List of extensions to ignore when using a directory as an inventory source
:Type: list
:Default: {{(BLACKLIST_EXTS + ( '~', '.orig', '.ini', '.cfg', '.retry'))}}
:Ini Section: defaults
:Ini Key: inventory_ignore_extensions
:Ini Section: inventory
:Ini Key: ignore_extensions
:Environment: :envvar:`ANSIBLE_INVENTORY_IGNORE`

.. _INVENTORY_IGNORE_PATTERNS:

INVENTORY_IGNORE_PATTERNS
-------------------------

:Description: List of patterns to ignore when using a directory as an inventory source
:Type: list
:Default: []
:Ini Section: defaults
:Ini Key: inventory_ignore_patterns
:Ini Section: inventory
:Ini Key: ignore_patterns
:Environment: :envvar:`ANSIBLE_INVENTORY_IGNORE_REGEX`

.. _INVENTORY_UNPARSED_IS_FAILED:

INVENTORY_UNPARSED_IS_FAILED
----------------------------

:Description: If 'true' unparsed inventory sources become fatal errors, they are warnings otherwise.
:Type: bool
:Default: False
:Ini Section: inventory
:Ini Key: unparsed_is_failed
:Environment: :envvar:`ANSIBLE_INVENTORY_UNPARSED_FAILED`

.. _MAX_FILE_SIZE_FOR_DIFF:

MAX_FILE_SIZE_FOR_DIFF
----------------------

:Description: Maximum size of files to be considered for diff display
:Type: int
:Default: 104448
:Ini Section: defaults
:Ini Key: max_diff_size
:Environment: :envvar:`ANSIBLE_MAX_DIFF_SIZE`

.. _MERGE_MULTIPLE_CLI_TAGS:

MERGE_MULTIPLE_CLI_TAGS
-----------------------

:Description: This allows changing how multiple --tags and --skip-tags arguments are handled on the command line. In Ansible up to and including 2.3, specifying --tags more than once will only take the last value of --tags. Setting this config value to True will mean that all of the --tags options will be merged together. The same holds true for --skip-tags.
:Type: bool
:Default: True
:Version Added: 2.3
:Ini Section: defaults
:Ini Key: merge_multiple_cli_tags
:Environment: :envvar:`ANSIBLE_MERGE_MULTIPLE_CLI_TAGS`

.. _NETWORK_GROUP_MODULES:

NETWORK_GROUP_MODULES
---------------------

:Type: list
:Default: ['eos', 'nxos', 'ios', 'iosxr', 'junos', 'enos', 'ce', 'vyos', 'sros', 'dellos9', 'dellos10', 'dellos6', 'asa', 'aruba', 'aireos', 'bigip', 'ironware', 'onyx']
:Ini Section: defaults
:Ini Key: network_group_modules
:Environment: :envvar:`NETWORK_GROUP_MODULES`

.. _PARAMIKO_HOST_KEY_AUTO_ADD:

PARAMIKO_HOST_KEY_AUTO_ADD
--------------------------

:Type: boolean
:Default: False
:Ini Section: paramiko_connection
:Ini Key: host_key_auto_add
:Environment: :envvar:`ANSIBLE_PARAMIKO_HOST_KEY_AUTO_ADD`

.. _PARAMIKO_LOOK_FOR_KEYS:

PARAMIKO_LOOK_FOR_KEYS
----------------------

:Type: boolean
:Default: True
:Ini Section: paramiko_connection
:Ini Key: look_for_keys
:Environment: :envvar:`ANSIBLE_PARAMIKO_LOOK_FOR_KEYS`

.. _PERSISTENT_COMMAND_TIMEOUT:

PERSISTENT_COMMAND_TIMEOUT
--------------------------

:Description: This controls the amount of time to wait for response from remote device before timing out presistent connection.
:Type: int
:Default: 10
:Ini Section: persistent_connection
:Ini Key: command_timeout
:Environment: :envvar:`ANSIBLE_PERSISTENT_COMMAND_TIMEOUT`

.. _PERSISTENT_CONNECT_RETRY_TIMEOUT:

PERSISTENT_CONNECT_RETRY_TIMEOUT
--------------------------------

:Description: This contorls the retry timeout for presistent connection to connect to the local domain socket.
:Type: integer
:Default: 15
:Ini Section: persistent_connection
:Ini Key: connect_retry_timeout
:Environment: :envvar:`ANSIBLE_PERSISTENT_CONNECT_RETRY_TIMEOUT`

.. _PERSISTENT_CONNECT_TIMEOUT:

PERSISTENT_CONNECT_TIMEOUT
--------------------------

:Description: This controls how long the persistent connection will remain idle before it is destroyed.
:Type: integer
:Default: 30
:Ini Section: persistent_connection
:Ini Key: connect_timeout
:Environment: :envvar:`ANSIBLE_PERSISTENT_CONNECT_TIMEOUT`

.. _PERSISTENT_CONTROL_PATH_DIR:

PERSISTENT_CONTROL_PATH_DIR
---------------------------

:Description: Path to socket to be used by the connection persistence system.
:Type: path
:Default: ~/.ansible/pc
:Ini Section: persistent_connection
:Ini Key: control_path_dir
:Environment: :envvar:`ANSIBLE_PERSISTENT_CONTROL_PATH_DIR`

.. _PLAYBOOK_VARS_ROOT:

PLAYBOOK_VARS_ROOT
------------------

:Description: This sets which playbook dirs will be used as a root to process vars plugins, which includes finding host_vars/group_vars The ``top`` option follows the traditional behaviour of using the top playbook in the chain to find the root directory. The ``bottom`` option follows the 2.4.0 behaviour of using the current playbook to find the root directory. The ``all`` option examines from the first parent to the current playbook.
:Default: top
:Version Added: 2.4.1
:Ini Section: defaults
:Ini Key: playbook_vars_root
:Environment: :envvar:`ANSIBLE_PLAYBOOK_VARS_ROOT`

.. _PLUGIN_FILTERS_CFG:

PLUGIN_FILTERS_CFG
------------------

:Description: A path to configuration for filtering which plugins installed on the system are allowed to be used. See :doc:`plugin_filtering_config` for details of the filter file's format.  The default is /etc/ansible/plugin_filters.yml
:Default: None
:Version Added: 2.5.0
:Ini Section: default
:Ini Key: plugin_filters_cfg

.. _RETRY_FILES_ENABLED:

RETRY_FILES_ENABLED
-------------------

:Description: This controls whether a failed Ansible playbook should create a .retry file.
:Type: bool
:Default: True
:Ini Section: defaults
:Ini Key: retry_files_enabled
:Environment: :envvar:`ANSIBLE_RETRY_FILES_ENABLED`

.. _RETRY_FILES_SAVE_PATH:

RETRY_FILES_SAVE_PATH
---------------------

:Description: This sets the path in which Ansible will save .retry files when a playbook fails and retry files are enabled.
:Type: path
:Default: None
:Ini Section: defaults
:Ini Key: retry_files_save_path
:Environment: :envvar:`ANSIBLE_RETRY_FILES_SAVE_PATH`

.. _SHOW_CUSTOM_STATS:

SHOW_CUSTOM_STATS
-----------------

:Description: This adds the custom stats set via the set_stats plugin to the default output
:Type: bool
:Default: False
:Ini Section: defaults
:Ini Key: show_custom_stats
:Environment: :envvar:`ANSIBLE_SHOW_CUSTOM_STATS`

.. _STRING_TYPE_FILTERS:

STRING_TYPE_FILTERS
-------------------

:Description: This list of filters avoids 'type conversion' when templating variables Useful when you want to avoid conversion into lists or dictionaries for JSON strings, for example.
:Type: list
:Default: ['string', 'to_json', 'to_nice_json', 'to_yaml', 'ppretty', 'json']
:Ini Section: jinja2
:Ini Key: dont_type_filters
:Environment: :envvar:`ANSIBLE_STRING_TYPE_FILTERS`

.. _SYSTEM_WARNINGS:

SYSTEM_WARNINGS
---------------

:Description: Allows disabling of warnings related to potential issues on the system running ansible itself (not on the managed hosts) These may include warnings about 3rd party packages or other conditions that should be resolved if possible.
:Type: boolean
:Default: True
:Ini Section: defaults
:Ini Key: system_warnings
:Environment: :envvar:`ANSIBLE_SYSTEM_WARNINGS`

.. _TAGS_RUN:

TAGS_RUN
--------

:Description: default list of tags to run in your plays, Skip Tags has precedence.
:Type: list
:Default: []
:Ini Section: tags
:Ini Key: run
:Environment: :envvar:`ANSIBLE_RUN_TAGS`

.. _TAGS_SKIP:

TAGS_SKIP
---------

:Description: default list of tags to skip in your plays, has precedence over Run Tags
:Type: list
:Default: []
:Ini Section: tags
:Ini Key: skip
:Environment: :envvar:`ANSIBLE_SKIP_TAGS`

.. _USE_PERSISTENT_CONNECTIONS:

USE_PERSISTENT_CONNECTIONS
--------------------------

:Description: Toggles the use of persistence for connections.
:Type: boolean
:Default: False
:Ini Section: defaults
:Ini Key: use_persistent_connections
:Environment: :envvar:`ANSIBLE_USE_PERSISTENT_CONNECTIONS`

.. _VARIABLE_PRECEDENCE:

VARIABLE_PRECEDENCE
-------------------

:Description: Allows to change the group variable precedence merge order.
:Type: list
:Default: ['all_inventory', 'groups_inventory', 'all_plugins_inventory', 'all_plugins_play', 'groups_plugins_inventory', 'groups_plugins_play']
:Version Added: 2.4
:Ini Section: defaults
:Ini Key: precedence
:Environment: :envvar:`ANSIBLE_PRECEDENCE`

.. _YAML_FILENAME_EXTENSIONS:

YAML_FILENAME_EXTENSIONS
------------------------

:Description: Check all of these extensions when looking for 'variable' files which should be YAML or JSON or vaulted versions of these. This affects vars_files, include_vars, inventory and vars plugins among others.
:Type: list
:Default: ['.yml', '.yaml', '.json']
:Ini Section: defaults
:Ini Key: yaml_valid_extensions
:Environment: :envvar:`ANSIBLE_YAML_FILENAME_EXT`


Environment Variables
=====================

.. envvar:: ANSIBLE_CONFIG


    Override the default ansible config file


.. envvar:: ANSIBLE_MERGE_MULTIPLE_CLI_TAGS

    This allows changing how multiple --tags and --skip-tags arguments are handled on the command line. In Ansible up to and including 2.3, specifying --tags more than once will only take the last value of --tags.Setting this config value to True will mean that all of the --tags options will be merged together. The same holds true for --skip-tags.

    See also :ref:`MERGE_MULTIPLE_CLI_TAGS <MERGE_MULTIPLE_CLI_TAGS>`


.. envvar:: DISPLAY_SKIPPED_HOSTS

    Toggle to control displaying skipped task/host entries in a task in the default callback

    See also :ref:`DISPLAY_SKIPPED_HOSTS <DISPLAY_SKIPPED_HOSTS>`


.. envvar:: ANSIBLE_SUDO_FLAGS

    Flags to pass to "sudo"

    See also :ref:`DEFAULT_SUDO_FLAGS <DEFAULT_SUDO_FLAGS>`


.. envvar:: ANSIBLE_PERSISTENT_CONNECT_RETRY_TIMEOUT

    This contorls the retry timeout for presistent connection to connect to the local domain socket.

    See also :ref:`PERSISTENT_CONNECT_RETRY_TIMEOUT <PERSISTENT_CONNECT_RETRY_TIMEOUT>`


.. envvar:: ANSIBLE_DIFF_CONTEXT

    How many lines of context to show when displaying the differences between files.

    See also :ref:`DIFF_CONTEXT <DIFF_CONTEXT>`


.. envvar:: ANSIBLE_COW_PATH

    Specify a custom cowsay path or swap in your cowsay implementation of choice

    See also :ref:`ANSIBLE_COW_PATH <ANSIBLE_COW_PATH>`


.. envvar:: ANSIBLE_TEST_PLUGINS

    Colon separated paths in which Ansible will search for Jinja2 Test Plugins.

    See also :ref:`DEFAULT_TEST_PLUGIN_PATH <DEFAULT_TEST_PLUGIN_PATH>`


.. envvar:: ANSIBLE_INVENTORY_ENABLED

    List of enabled inventory plugins, it also determines the order in which they are used.

    See also :ref:`INVENTORY_ENABLED <INVENTORY_ENABLED>`


.. envvar:: ANSIBLE_GALAXY_ROLE_SKELETON_IGNORE

    patterns of files to ignore inside a galaxy role skeleton directory

    See also :ref:`GALAXY_ROLE_SKELETON_IGNORE <GALAXY_ROLE_SKELETON_IGNORE>`


.. envvar:: ANSIBLE_PIPELINING

    Pipelining, if supported by the connection plugin, reduces the number of network operations required to execute a module on the remote server, by executing many Ansible modules without actual file transfer.This can result in a very significant performance improvement when enabled.However this conflicts with privilege escalation (become). For example, when using 'sudo:' operations you must first disable 'requiretty' in /etc/sudoers on all managed hosts, which is why it is disabled by default.

    See also :ref:`ANSIBLE_PIPELINING <ANSIBLE_PIPELINING>`

.. envvar:: ANSIBLE_SSH_PIPELINING

    Pipelining, if supported by the connection plugin, reduces the number of network operations required to execute a module on the remote server, by executing many Ansible modules without actual file transfer.This can result in a very significant performance improvement when enabled.However this conflicts with privilege escalation (become). For example, when using 'sudo:' operations you must first disable 'requiretty' in /etc/sudoers on all managed hosts, which is why it is disabled by default.

    See also :ref:`ANSIBLE_PIPELINING <ANSIBLE_PIPELINING>`


.. envvar:: ANSIBLE_BECOME_METHOD

    Privilege escalation method to use when `become` is enabled.

    See also :ref:`DEFAULT_BECOME_METHOD <DEFAULT_BECOME_METHOD>`


.. envvar:: ANSIBLE_HOST_KEY_CHECKING

    Set this to "False" if you want to avoid host key checking by the underlying tools Ansible uses to connect to the host

    See also :ref:`HOST_KEY_CHECKING <HOST_KEY_CHECKING>`


.. envvar:: ANSIBLE_ASK_SU_PASS

    This controls whether an Ansible playbook should prompt for a su password.

    See also :ref:`DEFAULT_ASK_SU_PASS <DEFAULT_ASK_SU_PASS>`


.. envvar:: ANSIBLE_SU_USER

    User you become when using "su", leaving it blank will use the default configured on the target (normally root)

    See also :ref:`DEFAULT_SU_USER <DEFAULT_SU_USER>`


.. envvar:: ANSIBLE_CALLABLE_WHITELIST

    Whitelist of callable methods to be made available to template evaluation

    See also :ref:`DEFAULT_CALLABLE_WHITELIST <DEFAULT_CALLABLE_WHITELIST>`


.. envvar:: ANSIBLE_COLOR_VERBOSE

    Defines the color to use when emitting verbose messages. i.e those that show with '-v's.

    See also :ref:`COLOR_VERBOSE <COLOR_VERBOSE>`


.. envvar:: ANSIBLE_GATHERING

    This setting controls the default policy of fact gathering (facts discovered about remote systems).When 'implicit' (the default), the cache plugin will be ignored and facts will be gathered per play unless 'gather_facts: False' is set.When 'explicit' the inverse is true, facts will not be gathered unless directly requested in the play.The 'smart' value means each new host that has no facts discovered will be scanned, but if the same host is addressed in multiple plays it will not be contacted again in the playbook run.This option can be useful for those wishing to save fact gathering time. Both 'smart' and 'explicit' will use the cache plugin.

    See also :ref:`DEFAULT_GATHERING <DEFAULT_GATHERING>`


.. envvar:: ANSIBLE_TIMEOUT

    This is the default timeout for connection plugins to use.

    See also :ref:`DEFAULT_TIMEOUT <DEFAULT_TIMEOUT>`


.. envvar:: ANSIBLE_SCP_IF_SSH

    Prefered method to use when transfering files over sshWhen set to smart, Ansible will try them until one succeeds or they all failIf set to True, it will force 'scp', if False it will use 'sftp'

    See also :ref:`DEFAULT_SCP_IF_SSH <DEFAULT_SCP_IF_SSH>`


.. envvar:: ANSIBLE_NOCOWS

    If you have cowsay installed but want to avoid the 'cows' (why????), use this.

    See also :ref:`ANSIBLE_NOCOWS <ANSIBLE_NOCOWS>`


.. envvar:: ANSIBLE_INVENTORY_IGNORE_REGEX

    List of patterns to ignore when using a directory as an inventory source

    See also :ref:`INVENTORY_IGNORE_PATTERNS <INVENTORY_IGNORE_PATTERNS>`


.. envvar:: ANSIBLE_NO_LOG

    Toggle Ansible's display and logging of task details, mainly used to avoid security disclosures.

    See also :ref:`DEFAULT_NO_LOG <DEFAULT_NO_LOG>`


.. envvar:: ANSIBLE_MAX_DIFF_SIZE

    Maximum size of files to be considered for diff display

    See also :ref:`MAX_FILE_SIZE_FOR_DIFF <MAX_FILE_SIZE_FOR_DIFF>`



.. envvar:: ANSIBLE_HANDLER_INCLUDES_STATIC

    Since 2.0 M(include) can be 'dynamic', this setting (if True) forces that if the include appears in a ``handlers`` section to be 'static'.

    See also :ref:`DEFAULT_HANDLER_INCLUDES_STATIC <DEFAULT_HANDLER_INCLUDES_STATIC>`


.. envvar:: ANSIBLE_KEEP_REMOTE_FILES

    Enables/disables the cleaning up of the temporary files Ansible used to execute the tasks on the remote.

    See also :ref:`DEFAULT_KEEP_REMOTE_FILES <DEFAULT_KEEP_REMOTE_FILES>`


.. envvar:: ANSIBLE_POLL_INTERVAL

    For asynchronous tasks in Ansible (covered in Asynchronous Actions and Polling), this is how often to check back on the status of those tasks when an explicit poll interval is not supplied. The default is a reasonably moderate 15 seconds which is a tradeoff between checking in frequently and providing a quick turnaround when something may have completed.

    See also :ref:`DEFAULT_POLL_INTERVAL <DEFAULT_POLL_INTERVAL>`


.. envvar:: ANSIBLE_BECOME_ALLOW_SAME_USER

    This setting controls if become is skipped when remote user and become user are the same. I.E root sudo to root.

    See also :ref:`BECOME_ALLOW_SAME_USER <BECOME_ALLOW_SAME_USER>`


.. envvar:: ANSIBLE_SSH_ARGS

    If set, this will override the Ansible default ssh arguments.In particular, users may wish to raise the ControlPersist time to encourage performance.  A value of 30 minutes may be appropriate.Be aware that if `-o ControlPath` is set in ssh_args, the control path setting is not used.

    See also :ref:`ANSIBLE_SSH_ARGS <ANSIBLE_SSH_ARGS>`


.. envvar:: ANSIBLE_ACTION_PLUGINS

    Colon separated paths in which Ansible will search for Action Plugins.

    See also :ref:`DEFAULT_ACTION_PLUGIN_PATH <DEFAULT_ACTION_PLUGIN_PATH>`


.. envvar:: ANSIBLE_REMOTE_USER

    Sets the login user for the target machinesWhen blank it uses the connection plugin's default, normally the user currently executing Ansible.

    See also :ref:`DEFAULT_REMOTE_USER <DEFAULT_REMOTE_USER>`


.. envvar:: ANSIBLE_INVENTORY_PLUGINS

    Colon separated paths in which Ansible will search for Inventory Plugins.

    See also :ref:`DEFAULT_INVENTORY_PLUGIN_PATH <DEFAULT_INVENTORY_PLUGIN_PATH>`


.. envvar:: ANSIBLE_VAULT_PASSWORD_FILE

    The vault password file to use. Equivalent to --vault-password-file or --vault-id

    See also :ref:`DEFAULT_VAULT_PASSWORD_FILE <DEFAULT_VAULT_PASSWORD_FILE>`


.. envvar:: ANSIBLE_CACHE_PLUGINS

    Colon separated paths in which Ansible will search for Cache Plugins.

    See also :ref:`DEFAULT_CACHE_PLUGIN_PATH <DEFAULT_CACHE_PLUGIN_PATH>`


.. envvar:: ANSIBLE_CALLBACK_PLUGINS

    Colon separated paths in which Ansible will search for Callback Plugins.

    See also :ref:`DEFAULT_CALLBACK_PLUGIN_PATH <DEFAULT_CALLBACK_PLUGIN_PATH>`


.. envvar:: ANSIBLE_CONNECTION_PLUGINS

    Colon separated paths in which Ansible will search for Connection Plugins.

    See also :ref:`DEFAULT_CONNECTION_PLUGIN_PATH <DEFAULT_CONNECTION_PLUGIN_PATH>`


.. envvar:: ANSIBLE_JINJA2_EXTENSIONS

    This is a developer-specific feature that allows enabling additional Jinja2 extensions.See the Jinja2 documentation for details. If you do not know what these do, you probably don't need to change this setting :)

    See also :ref:`DEFAULT_JINJA2_EXTENSIONS <DEFAULT_JINJA2_EXTENSIONS>`


.. envvar:: ANSIBLE_COMMAND_WARNINGS

    By default Ansible will issue a warning when the shell or command module is used and the command appears to be similar to an existing Ansible module.These warnings can be silenced by adjusting this setting to False. You can also control this at the task level with the module optoin ``warn``.

    See also :ref:`COMMAND_WARNINGS <COMMAND_WARNINGS>`


.. envvar:: ANSIBLE_COLOR_OK

    Defines the color to use when showing 'OK' task status

    See also :ref:`COLOR_OK <COLOR_OK>`


.. envvar:: ANSIBLE_INJECT_FACT_VARS

    Facts are available inside the `ansible_facts` variable, this setting also pushes them as their own vars in the main namespace.Unlike inside the `ansible_facts` dictionary, these will have an `ansible_` prefix.

    See also :ref:`INJECT_FACTS_AS_VARS <INJECT_FACTS_AS_VARS>`


.. envvar:: ANSIBLE_COLOR_CHANGED

    Defines the color to use on 'Changed' task status

    See also :ref:`COLOR_CHANGED <COLOR_CHANGED>`


.. envvar:: ANSIBLE_DISPLAY_ARGS_TO_STDOUT

    Normally ``ansible-playbook`` will print a header for each task that is run. These headers will contain the name: field from the task if you specified one. If you didn't then ``ansible-playbook`` uses the task's action to help you tell which task is presently running. Sometimes you run many of the same action and so you want more information about the task to differentiate it from others of the same action. If you set this variable to True in the config then ``ansible-playbook`` will also include the task's arguments in the header.This setting defaults to False because there is a chance that you have sensitive values in your parameters and you do not want those to be printed.If you set this to True you should be sure that you have secured your environment's stdout (no one can shoulder surf your screen and you aren't saving stdout to an insecure file) or made sure that all of your playbooks explicitly added the ``no_log: True`` parameter to tasks which have sensistive values See How do I keep secret data in my playbook? for more information.

    See also :ref:`DISPLAY_ARGS_TO_STDOUT <DISPLAY_ARGS_TO_STDOUT>`


.. envvar:: ANSIBLE_LOCAL_TEMP

    Temporary directory for Ansible to use on the controller.

    See also :ref:`DEFAULT_LOCAL_TMP <DEFAULT_LOCAL_TMP>`


.. envvar:: ANSIBLE_COLOR_ERROR

    Defines the color to use when emitting error messages

    See also :ref:`COLOR_ERROR <COLOR_ERROR>`


.. envvar:: ANSIBLE_VAULT_ID_MATCH

    If true, decrypting vaults with a vault id will only try the password from the matching vault-id

    See also :ref:`DEFAULT_VAULT_ID_MATCH <DEFAULT_VAULT_ID_MATCH>`


.. envvar:: ANSIBLE_ERROR_ON_MISSING_HANDLER

    Toggle to allow missing handlers to become a warning instead of an error when notifying.

    See also :ref:`ERROR_ON_MISSING_HANDLER <ERROR_ON_MISSING_HANDLER>`


.. envvar:: ANSIBLE_CACHE_PLUGIN

    Chooses which cache plugin to use, the default 'memory' is ephimeral.

    See also :ref:`CACHE_PLUGIN <CACHE_PLUGIN>`


.. envvar:: ANSIBLE_BECOME

    Toggles the use of privilege escalation, allowing you to 'become' another user after login.

    See also :ref:`DEFAULT_BECOME <DEFAULT_BECOME>`


.. envvar:: ANSIBLE_VERBOSITY

    Sets the default verbosity, equivalent to the number of ``-v`` passed in the command line.

    See also :ref:`DEFAULT_VERBOSITY <DEFAULT_VERBOSITY>`


.. envvar:: ANSIBLE_SQUASH_ACTIONS

    Ansible can optimise actions that call modules that support list parameters when using ``with_`` looping. Instead of calling the module once for each item, the module is called once with the full list.The default value for this setting is only for certain package managers, but it can be used for any moduleCurrently, this is only supported for modules that have a name or pkg parameter, and only when the item is the only thing being passed to the parameter.

    See also :ref:`DEFAULT_SQUASH_ACTIONS <DEFAULT_SQUASH_ACTIONS>`


.. envvar:: ANSIBLE_VARS_PLUGINS

    Colon separated paths in which Ansible will search for Vars Plugins.

    See also :ref:`DEFAULT_VARS_PLUGIN_PATH <DEFAULT_VARS_PLUGIN_PATH>`


.. envvar:: ANSIBLE_FILTER_PLUGINS

    Colon separated paths in which Ansible will search for Jinja2 Filter Plugins.

    See also :ref:`DEFAULT_FILTER_PLUGIN_PATH <DEFAULT_FILTER_PLUGIN_PATH>`


.. envvar:: ANSIBLE_GALAXY_ROLE_SKELETON

    Role skeleton directory to use as a template for the ``init`` action in ``ansible-galaxy``, same as ``--role-skeleton``.

    See also :ref:`GALAXY_ROLE_SKELETON <GALAXY_ROLE_SKELETON>`


.. envvar:: ANSIBLE_PERSISTENT_CONNECT_TIMEOUT

    This controls how long the persistent connection will remain idle before it is destroyed.

    See also :ref:`PERSISTENT_CONNECT_TIMEOUT <PERSISTENT_CONNECT_TIMEOUT>`


.. envvar:: ANSIBLE_BECOME_ASK_PASS

    Toggle to prompt for privilege escalation password.

    See also :ref:`DEFAULT_BECOME_ASK_PASS <DEFAULT_BECOME_ASK_PASS>`


.. envvar:: ANSIBLE_PERSISTENT_COMMAND_TIMEOUT

    This controls the amount of time to wait for response from remote device before timing out presistent connection.

    See also :ref:`PERSISTENT_COMMAND_TIMEOUT <PERSISTENT_COMMAND_TIMEOUT>`


.. envvar:: ANSIBLE_HOSTS

    Colon separated list of Ansible inventory sources

    See also :ref:`DEFAULT_HOST_LIST <DEFAULT_HOST_LIST>`

.. envvar:: ANSIBLE_INVENTORY

    Colon separated list of Ansible inventory sources

    See also :ref:`DEFAULT_HOST_LIST <DEFAULT_HOST_LIST>`


.. envvar:: ANSIBLE_GATHER_TIMEOUT

    Set the timeout in seconds for the implicit fact gathering.It does **not** apply to user defined M(setup) tasks.

    See also :ref:`DEFAULT_GATHER_TIMEOUT <DEFAULT_GATHER_TIMEOUT>`


.. envvar:: ANSIBLE_LIBRARY

    Colon separated paths in which Ansible will search for Modules.

    See also :ref:`DEFAULT_MODULE_PATH <DEFAULT_MODULE_PATH>`


.. envvar:: ANSIBLE_MODULE_ARGS

    This sets the default arguments to pass to the ``ansible`` adhoc binary if no ``-a`` is specified.

    See also :ref:`DEFAULT_MODULE_ARGS <DEFAULT_MODULE_ARGS>`



.. envvar:: ANSIBLE_VAULT_IDENTITY_LIST

    A list of vault-ids to use by default. Equivalent to multiple --vault-id args. Vault-ids are tried in order.

    See also :ref:`DEFAULT_VAULT_IDENTITY_LIST <DEFAULT_VAULT_IDENTITY_LIST>`


.. envvar:: ANSIBLE_COLOR_DIFF_ADD

    Defines the color to use when showing added lines in diffs

    See also :ref:`COLOR_DIFF_ADD <COLOR_DIFF_ADD>`


.. envvar:: ANSIBLE_COW_WHITELIST

    White list of cowsay templates that are 'safe' to use, set to empty list if you want to enable all installed templates.

    See also :ref:`ANSIBLE_COW_WHITELIST <ANSIBLE_COW_WHITELIST>`


.. envvar:: ANSIBLE_SFTP_BATCH_MODE


    See also :ref:`DEFAULT_SFTP_BATCH_MODE <DEFAULT_SFTP_BATCH_MODE>`


.. envvar:: ANSIBLE_TRANSPORT

    Default connection plugin to use, the 'smart' option will toggle between 'ssh' and 'paramiko' depending on controller OS and ssh versions

    See also :ref:`DEFAULT_TRANSPORT <DEFAULT_TRANSPORT>`


.. envvar:: ANSIBLE_GALAXY_SERVER

    URL to prepend when roles don't specify the full URI, assume they are referencing this server as the source.

    See also :ref:`GALAXY_SERVER <GALAXY_SERVER>`



.. envvar:: ANSIBLE_FORCE_HANDLERS

    This option controls if notified handlers run on a host even if a failure occurs on that host.When false, the handlers will not run if a failure has occurred on a host.This can also be set per play or on the command line. See Handlers and Failure for more details.

    See also :ref:`DEFAULT_FORCE_HANDLERS <DEFAULT_FORCE_HANDLERS>`


.. envvar:: ANSIBLE_SUDO_EXE

    specify an "sudo" executable, otherwise it relies on PATH.

    See also :ref:`DEFAULT_SUDO_EXE <DEFAULT_SUDO_EXE>`


.. envvar:: ANSIBLE_DEBUG

    Toggles debug output in Ansible, VERY verbose and can hinder multiprocessing.

    See also :ref:`DEFAULT_DEBUG <DEFAULT_DEBUG>`


.. envvar:: ANSIBLE_STDOUT_CALLBACK

    Set the main callback used to display Ansible output, you can only have one at a time.You can have many other callbacks, but just one can be in charge of stdout.

    See also :ref:`DEFAULT_STDOUT_CALLBACK <DEFAULT_STDOUT_CALLBACK>`


.. envvar:: ANSIBLE_COLOR_DIFF_LINES

    Defines the color to use when showing diffs

    See also :ref:`COLOR_DIFF_LINES <COLOR_DIFF_LINES>`


.. envvar:: ANSIBLE_FACT_PATH

    This option allows you to globally configure a custom path for 'local_facts' for the implied M(setup) task when using fact gathering.If not set, it will fallback to the default from the M(setup) module: ``/etc/ansible/facts.d``.This does **not** affect  user defined tasks that use the M(setup) module.

    See also :ref:`DEFAULT_FACT_PATH <DEFAULT_FACT_PATH>`


.. envvar:: ANSIBLE_TASK_INCLUDES_STATIC

    The `include` tasks can be static or dynamic, this toggles the default expected behaviour if autodetection fails and it is not explicitly set in task.

    See also :ref:`DEFAULT_TASK_INCLUDES_STATIC <DEFAULT_TASK_INCLUDES_STATIC>`


.. envvar:: ANSIBLE_BECOME_FLAGS

    Flags to pass to the privilege escalation executable.

    See also :ref:`DEFAULT_BECOME_FLAGS <DEFAULT_BECOME_FLAGS>`


.. envvar:: ANSIBLE_SU_FLAGS

    Flags to pass to su

    See also :ref:`DEFAULT_SU_FLAGS <DEFAULT_SU_FLAGS>`


.. envvar:: ANSIBLE_COLOR_WARN

    Defines the color to use when emitting warning messages

    See also :ref:`COLOR_WARN <COLOR_WARN>`


.. envvar:: ANSIBLE_COLOR_UNREACHABLE

    Defines the color to use on 'Unreachable' status

    See also :ref:`COLOR_UNREACHABLE <COLOR_UNREACHABLE>`


.. envvar:: ANSIBLE_ASK_SUDO_PASS

    This controls whether an Ansible playbook should prompt for a sudo password.

    See also :ref:`DEFAULT_ASK_SUDO_PASS <DEFAULT_ASK_SUDO_PASS>`


.. envvar:: ANSIBLE_SUDO

    Toggle the use of "sudo" for tasks.

    See also :ref:`DEFAULT_SUDO <DEFAULT_SUDO>`


.. envvar:: ANSIBLE_MODULE_LANG

    Language locale setting to use for modules when they execute on the target.If empty it tries to set itself to the LANG environment variable on the controller.This is only used if DEFAULT_MODULE_SET_LOCALE is set to true

    See also :ref:`DEFAULT_MODULE_LANG <DEFAULT_MODULE_LANG>`


.. envvar:: LIBVIRT_LXC_NOSECLABEL

    This setting causes libvirt to connect to lxc containers by passing --noseclabel to virsh. This is necessary when running on systems which do not have SELinux.

    See also :ref:`DEFAULT_LIBVIRT_LXC_NOSECLABEL <DEFAULT_LIBVIRT_LXC_NOSECLABEL>`


.. envvar:: ANSIBLE_NULL_REPRESENTATION

    What templating should return as a 'null' value. When not set it will let Jinja2 decide.

    See also :ref:`DEFAULT_NULL_REPRESENTATION <DEFAULT_NULL_REPRESENTATION>`


.. envvar:: ANSIBLE_COLOR_DIFF_REMOVE

    Defines the color to use when showing removed lines in diffs

    See also :ref:`COLOR_DIFF_REMOVE <COLOR_DIFF_REMOVE>`


.. envvar:: ANSIBLE_PRIVATE_ROLE_VARS


    See also :ref:`DEFAULT_PRIVATE_ROLE_VARS <DEFAULT_PRIVATE_ROLE_VARS>`


.. envvar:: ANSIBLE_ENABLE_TASK_DEBUGGER

    Whether or not to enable the task debugger, this previously was done as a strategy plugin.Now all strategy plugins can inherit this behavior. The debugger defaults to activating whena task is failed on unreachable. Use the debugger keyword for more flexibility.

    See also :ref:`ENABLE_TASK_DEBUGGER <ENABLE_TASK_DEBUGGER>`


.. envvar:: ANSIBLE_COLOR_DEBUG

    Defines the color to use when emitting debug messages

    See also :ref:`COLOR_DEBUG <COLOR_DEBUG>`


.. envvar:: ANSIBLE_LOAD_CALLBACK_PLUGINS

    Controls whether callback plugins are loaded when running /usr/bin/ansible. This may be used to log activity from the command line, send notifications, and so on. Callback plugins are always loaded for ``ansible-playbook``.

    See also :ref:`DEFAULT_LOAD_CALLBACK_PLUGINS <DEFAULT_LOAD_CALLBACK_PLUGINS>`


.. envvar:: ANSIBLE_SYSLOG_FACILITY

    Syslog facility to use when Ansible logs to the remote target

    See also :ref:`DEFAULT_SYSLOG_FACILITY <DEFAULT_SYSLOG_FACILITY>`


.. envvar:: ANSIBLE_PARAMIKO_HOST_KEY_AUTO_ADD


    See also :ref:`PARAMIKO_HOST_KEY_AUTO_ADD <PARAMIKO_HOST_KEY_AUTO_ADD>`


.. envvar:: ANSIBLE_USE_PERSISTENT_CONNECTIONS

    Toggles the use of persistence for connections.

    See also :ref:`USE_PERSISTENT_CONNECTIONS <USE_PERSISTENT_CONNECTIONS>`



.. envvar:: ANSIBLE_VAULT_IDENTITY

    The label to use for the default vault id label in cases where a vault id label is not provided

    See also :ref:`DEFAULT_VAULT_IDENTITY <DEFAULT_VAULT_IDENTITY>`


.. envvar:: ANSIBLE_YAML_FILENAME_EXT

    Check all of these extensions when looking for 'variable' files which should be YAML or JSON or vaulted versions of these.This affects vars_files, include_vars, inventory and vars plugins among others.

    See also :ref:`YAML_FILENAME_EXTENSIONS <YAML_FILENAME_EXTENSIONS>`


.. envvar:: ANSIBLE_COLOR_SKIP

    Defines the color to use when showing 'Skipped' task status

    See also :ref:`COLOR_SKIP <COLOR_SKIP>`


.. envvar:: ANSIBLE_STRING_TYPE_FILTERS

    This list of filters avoids 'type conversion' when templating variablesUseful when you want to avoid conversion into lists or dictionaries for JSON strings, for example.

    See also :ref:`STRING_TYPE_FILTERS <STRING_TYPE_FILTERS>`



.. envvar:: ANSIBLE_REMOTE_PORT

    Port to use in remote connections, when blank it will use the connection plugin default.

    See also :ref:`DEFAULT_REMOTE_PORT <DEFAULT_REMOTE_PORT>`


.. envvar:: ANSIBLE_PLAYBOOK_VARS_ROOT

    This sets which playbook dirs will be used as a root to process vars plugins, which includes finding host_vars/group_varsThe ``top`` option follows the traditional behaviour of using the top playbook in the chain to find the root directory.The ``bottom`` option follows the 2.4.0 behaviour of using the current playbook to find the root directory.The ``all`` option examines from the first parent to the current playbook.

    See also :ref:`PLAYBOOK_VARS_ROOT <PLAYBOOK_VARS_ROOT>`


.. envvar:: ANSIBLE_ASK_VAULT_PASS

    This controls whether an Ansible playbook should prompt for a vault password.

    See also :ref:`DEFAULT_ASK_VAULT_PASS <DEFAULT_ASK_VAULT_PASS>`



.. envvar:: ANSIBLE_PRECEDENCE

    Allows to change the group variable precedence merge order.

    See also :ref:`VARIABLE_PRECEDENCE <VARIABLE_PRECEDENCE>`


.. envvar:: ANSIBLE_HASH_BEHAVIOUR

    This setting controls how variables merge in Ansible. By default Ansible will override variables in specific precedence orders, as described in Variables. When a variable of higher precedence wins, it will replace the other value.Some users prefer that variables that are hashes (aka 'dictionaries' in Python terms) are merged. This setting is called 'merge'. This is not the default behavior and it does not affect variables whose values are scalars (integers, strings) or arrays.  We generally recommend not using this setting unless you think you have an absolute need for it, and playbooks in the official examples repos do not use this settingIn version 2.0 a ``combine`` filter was added to allow doing this for a particular variable (described in Filters).

    See also :ref:`DEFAULT_HASH_BEHAVIOUR <DEFAULT_HASH_BEHAVIOUR>`


.. envvar:: ANSIBLE_BECOME_USER

    The user your login/remote user 'becomes' when using privilege escalation, most systems will use 'root' when no user is specified.

    See also :ref:`DEFAULT_BECOME_USER <DEFAULT_BECOME_USER>`


.. envvar:: ANSIBLE_ERROR_ON_UNDEFINED_VARS

    When True, this causes ansible templating to fail steps that reference variable names that are likely typoed.Otherwise, any '{{ template_expression }}' that contains undefined variables will be rendered in a template or ansible action line exactly as written.

    See also :ref:`DEFAULT_UNDEFINED_VAR_BEHAVIOR <DEFAULT_UNDEFINED_VAR_BEHAVIOR>`


.. envvar:: ANSIBLE_CACHE_PLUGIN_TIMEOUT

    Expiration timeout for the cache plugin data

    See also :ref:`CACHE_PLUGIN_TIMEOUT <CACHE_PLUGIN_TIMEOUT>`


.. envvar:: ANSIBLE_SSH_CONTROL_PATH

    This is the location to save ssh's ControlPath sockets, it uses ssh's variable substitution.Since 2.3, if null, ansible will generate a unique hash. Use `%(directory)s` to indicate where to use the control dir path setting.Before 2.3 it defaulted to `control_path=%(directory)s/ansible-ssh-%%h-%%p-%%r`.Be aware that this setting is ignored if `-o ControlPath` is set in ssh args.

    See also :ref:`ANSIBLE_SSH_CONTROL_PATH <ANSIBLE_SSH_CONTROL_PATH>`


.. envvar:: ANSIBLE_CACHE_PLUGIN_PREFIX

    Prefix to use for cache plugin files/tables

    See also :ref:`CACHE_PLUGIN_PREFIX <CACHE_PLUGIN_PREFIX>`


.. envvar:: NETWORK_GROUP_MODULES


    See also :ref:`NETWORK_GROUP_MODULES <NETWORK_GROUP_MODULES>`


.. envvar:: ANSIBLE_LOG_PATH

    File to which Ansible will log on the controller. When empty logging is disabled.

    See also :ref:`DEFAULT_LOG_PATH <DEFAULT_LOG_PATH>`


.. envvar:: ANSIBLE_RUN_TAGS

    default list of tags to run in your plays, Skip Tags has precedence.

    See also :ref:`TAGS_RUN <TAGS_RUN>`


.. envvar:: ANSIBLE_SKIP_TAGS

    default list of tags to skip in your plays, has precedence over Run Tags

    See also :ref:`TAGS_SKIP <TAGS_SKIP>`


.. envvar:: ANSIBLE_STRATEGY

    Set the default strategy used for plays.

    See also :ref:`DEFAULT_STRATEGY <DEFAULT_STRATEGY>`


.. envvar:: ANSIBLE_DIFF_ALWAYS

    Configuration toggle to tell modules to show differences when in 'changed' status, equivalent to ``--diff``.

    See also :ref:`DIFF_ALWAYS <DIFF_ALWAYS>`


.. envvar:: ANSIBLE_NO_TARGET_SYSLOG

    Toggle Ansible logging to syslog on the target when it executes tasks.

    See also :ref:`DEFAULT_NO_TARGET_SYSLOG <DEFAULT_NO_TARGET_SYSLOG>`


.. envvar:: ANSIBLE_MODULE_SET_LOCALE

    Controls if we set locale for modules when executing on the target.

    See also :ref:`DEFAULT_MODULE_SET_LOCALE <DEFAULT_MODULE_SET_LOCALE>`


.. envvar:: ANSIBLE_LOOKUP_PLUGINS

    Colon separated paths in which Ansible will search for Lookup Plugins.

    See also :ref:`DEFAULT_LOOKUP_PLUGIN_PATH <DEFAULT_LOOKUP_PLUGIN_PATH>`


.. envvar:: ANSIBLE_ASK_PASS

    This controls whether an Ansible playbook should prompt for a login password. If using SSH keys for authentication, you probably do not needed to change this setting.

    See also :ref:`DEFAULT_ASK_PASS <DEFAULT_ASK_PASS>`


.. envvar:: ANSIBLE_INVENTORY_UNPARSED_FAILED

    If 'true' unparsed inventory sources become fatal errors, they are warnings otherwise.

    See also :ref:`INVENTORY_UNPARSED_IS_FAILED <INVENTORY_UNPARSED_IS_FAILED>`


.. envvar:: ANSIBLE_CALLBACK_WHITELIST

    List of whitelisted callbacks, not all callbacks need whitelisting, but many of those shipped with Ansible do as we don't want them activated by default.

    See also :ref:`DEFAULT_CALLBACK_WHITELIST <DEFAULT_CALLBACK_WHITELIST>`


.. envvar:: ANSIBLE_PRIVATE_KEY_FILE

    Option for connections using a certificate or key file to authenticate, rather than an agent or passwords, you can set the default value here to avoid re-specifying --private-key with every invocation.

    See also :ref:`DEFAULT_PRIVATE_KEY_FILE <DEFAULT_PRIVATE_KEY_FILE>`


.. envvar:: ANSIBLE_PERSISTENT_CONTROL_PATH_DIR

    Path to socket to be used by the connection persistence system.

    See also :ref:`PERSISTENT_CONTROL_PATH_DIR <PERSISTENT_CONTROL_PATH_DIR>`


.. envvar:: ANSIBLE_MODULE_UTILS

    Colon separated paths in which Ansible will search for Module utils files, which are shared by modules.

    See also :ref:`DEFAULT_MODULE_UTILS_PATH <DEFAULT_MODULE_UTILS_PATH>`


.. envvar:: ANSIBLE_ROLES_PATH

    Colon separated paths in which Ansible will search for Roles.

    See also :ref:`DEFAULT_ROLES_PATH <DEFAULT_ROLES_PATH>`


.. envvar:: ANSIBLE_CACHE_PLUGIN_CONNECTION

    Defines connection or path information for the cache plugin

    See also :ref:`CACHE_PLUGIN_CONNECTION <CACHE_PLUGIN_CONNECTION>`


.. envvar:: ANSIBLE_BECOME_EXE

    executable to use for privilege escalation, otherwise Ansible will depend on PATH

    See also :ref:`DEFAULT_BECOME_EXE <DEFAULT_BECOME_EXE>`


.. envvar:: ANSIBLE_SSH_RETRIES

    Number of attempts to establish a connection before we give up and report the host as 'UNREACHABLE'

    See also :ref:`ANSIBLE_SSH_RETRIES <ANSIBLE_SSH_RETRIES>`


.. envvar:: ANSIBLE_COLOR_DEPRECATE

    Defines the color to use when emitting deprecation messages

    See also :ref:`COLOR_DEPRECATE <COLOR_DEPRECATE>`


.. envvar:: ANSIBLE_EXECUTABLE

    This indicates the command to use to spawn a shell under for Ansible's execution needs on a target. Users may need to change this in rare instances when shell usage is constrained, but in most cases it may be left as is.

    See also :ref:`DEFAULT_EXECUTABLE <DEFAULT_EXECUTABLE>`


.. envvar:: ANSIBLE_DEPRECATION_WARNINGS

    Toggle to control the showing of deprecation warnings

    See also :ref:`DEPRECATION_WARNINGS <DEPRECATION_WARNINGS>`


.. envvar:: ANSIBLE_NOCOLOR

    This setting allows suppressing colorizing output, which is used to give a better indication of failure and status information.

    See also :ref:`ANSIBLE_NOCOLOR <ANSIBLE_NOCOLOR>`


.. envvar:: ANSIBLE_PARAMIKO_LOOK_FOR_KEYS


    See also :ref:`PARAMIKO_LOOK_FOR_KEYS <PARAMIKO_LOOK_FOR_KEYS>`


.. envvar:: ANSIBLE_RETRY_FILES_ENABLED

    This controls whether a failed Ansible playbook should create a .retry file.

    See also :ref:`RETRY_FILES_ENABLED <RETRY_FILES_ENABLED>`


.. envvar:: ANSIBLE_SUDO_USER

    User you become when using "sudo", leaving it blank will use the default configured on the target (normally root)

    See also :ref:`DEFAULT_SUDO_USER <DEFAULT_SUDO_USER>`


.. envvar:: ANSIBLE_STRATEGY_PLUGINS

    Colon separated paths in which Ansible will search for Strategy Plugins.

    See also :ref:`DEFAULT_STRATEGY_PLUGIN_PATH <DEFAULT_STRATEGY_PLUGIN_PATH>`


.. envvar:: ANSIBLE_SSH_CONTROL_PATH_DIR

    This sets the directory to use for ssh control path if the control path setting is null.Also, provides the `%(directory)s` variable for the control path setting.

    See also :ref:`ANSIBLE_SSH_CONTROL_PATH_DIR <ANSIBLE_SSH_CONTROL_PATH_DIR>`


.. envvar:: ANSIBLE_INVENTORY_IGNORE

    List of extensions to ignore when using a directory as an inventory source

    See also :ref:`INVENTORY_IGNORE_EXTS <INVENTORY_IGNORE_EXTS>`


.. envvar:: ANSIBLE_GALAXY_IGNORE

    If set to yes, ansible-galaxy will not validate TLS certificates. This can be useful for testing against a server with a self-signed certificate.

    See also :ref:`GALAXY_IGNORE_CERTS <GALAXY_IGNORE_CERTS>`


.. envvar:: ANSIBLE_RETRY_FILES_SAVE_PATH

    This sets the path in which Ansible will save .retry files when a playbook fails and retry files are enabled.

    See also :ref:`RETRY_FILES_SAVE_PATH <RETRY_FILES_SAVE_PATH>`


.. envvar:: ANSIBLE_SHOW_CUSTOM_STATS

    This adds the custom stats set via the set_stats plugin to the default output

    See also :ref:`SHOW_CUSTOM_STATS <SHOW_CUSTOM_STATS>`


.. envvar:: ANSIBLE_VAULT_ENCRYPT_IDENTITY

    The vault_id to use for encrypting by default. If multiple vault_ids are provided, this specifies which to use for encryption. The --encrypt-vault-id cli option overrides the configured value.

    See also :ref:`DEFAULT_VAULT_ENCRYPT_IDENTITY <DEFAULT_VAULT_ENCRYPT_IDENTITY>`



.. envvar:: ANSIBLE_COW_SELECTION

    This allows you to chose a specific cowsay stencil for the banners or use 'random' to cycle through them.

    See also :ref:`ANSIBLE_COW_SELECTION <ANSIBLE_COW_SELECTION>`


.. envvar:: ANSIBLE_GALAXY_TOKEN

    GitHub personal access token

    See also :ref:`GALAXY_TOKEN <GALAXY_TOKEN>`


.. envvar:: ANSIBLE_FORKS

    Maximum number of forks Ansible will use to execute tasks on target hosts.

    See also :ref:`DEFAULT_FORKS <DEFAULT_FORKS>`


.. envvar:: ANSIBLE_SU

    Toggle the use of "su" for tasks.

    See also :ref:`DEFAULT_SU <DEFAULT_SU>`


.. envvar:: ANSIBLE_GATHER_SUBSET

    Set the `gather_subset` option for the M(setup) task in the implicit fact gathering. See the module documentation for specifics.It does **not** apply to user defined M(setup) tasks.

    See also :ref:`DEFAULT_GATHER_SUBSET <DEFAULT_GATHER_SUBSET>`


.. envvar:: ANSIBLE_COLOR_HIGHLIGHT

    Color used for highlights

    See also :ref:`COLOR_HIGHLIGHT <COLOR_HIGHLIGHT>`


.. envvar:: ANSIBLE_FORCE_COLOR

    This options forces color mode even when running without a TTY or the "nocolor" setting is True.

    See also :ref:`ANSIBLE_FORCE_COLOR <ANSIBLE_FORCE_COLOR>`


.. envvar:: ANSIBLE_SU_EXE

    specify an "su" executable, otherwise it relies on PATH.

    See also :ref:`DEFAULT_SU_EXE <DEFAULT_SU_EXE>`


.. envvar:: ANSIBLE_ANY_ERRORS_FATAL

    Sets the default value for the any_errors_fatal keyword, if True, Task failures will be considered fatal errors.

    See also :ref:`ANY_ERRORS_FATAL <ANY_ERRORS_FATAL>`


.. envvar:: ANSIBLE_SYSTEM_WARNINGS

    Allows disabling of warnings related to potential issues on the system running ansible itself (not on the managed hosts)These may include warnings about 3rd party packages or other conditions that should be resolved if possible.

    See also :ref:`SYSTEM_WARNINGS <SYSTEM_WARNINGS>`


.. envvar:: ANSIBLE_SSH_TRANSFER_METHOD

    unused?

    See also :ref:`DEFAULT_SSH_TRANSFER_METHOD <DEFAULT_SSH_TRANSFER_METHOD>`


.. envvar:: ANSIBLE_SSH_EXECUTABLE

    This defines the location of the ssh binary. It defaults to `ssh` which will use the first ssh binary available in $PATH.This option is usually not required, it might be useful when access to system ssh is restricted, or when using ssh wrappers to connect to remote hosts.

    See also :ref:`ANSIBLE_SSH_EXECUTABLE <ANSIBLE_SSH_EXECUTABLE>`


.. envvar:: ANSIBLE_ACTION_WARNINGS

    By default Ansible will issue a warning when recieved from a task action (module or action plugin)These warnings can be silenced by adjusting this setting to False.

    See also :ref:`ACTION_WARNINGS <ACTION_WARNINGS>`



.. envvar:: ANSIBLE_AGNOSTIC_BECOME_PROMPT

    Display an agnostic become prompt instead of displaying a prompt containing the command line supplied become method

    See also :ref:`AGNOSTIC_BECOME_PROMPT <AGNOSTIC_BECOME_PROMPT>`



