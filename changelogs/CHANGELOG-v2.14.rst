=================================================
ansible-core 2.14 "C'mon Everybody" Release Notes
=================================================

.. contents:: Topics


v2.14.0rc2
==========

Release Summary
---------------

| Release Date: 2022-10-31
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- ansible-test - Update ``base`` and ``default`` containers to include Python 3.11.0.
- ansible-test - Update ``default`` containers to include new ``docs-build`` sanity test requirements.

Bugfixes
--------

- ansible-test - Add ``wheel < 0.38.0`` constraint for Python 3.6 and earlier.
- ansible-test - Update the ``pylint`` sanity test requirements to resolve crashes on Python 3.11. (https://github.com/ansible/ansible/issues/78882)
- ansible-test - Update the ``pylint`` sanity test to use version 2.15.5.

v2.14.0rc1
==========

Release Summary
---------------

| Release Date: 2022-10-17
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Bugfixes
--------

- BSD network facts - Do not assume column indexes, look for ``netmask`` and ``broadcast`` for determining the correct columns when parsing ``inet`` line (https://github.com/ansible/ansible/issues/79117)
- ansible-config limit shorthand format to assigned values
- ansible-test - Update the ``pylint`` sanity test to use version 2.15.4.

v2.14.0b3
=========

Release Summary
---------------

| Release Date: 2022-10-10
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Bugfixes
--------

- Do not crash when templating an expression with a test or filter that is not a valid Ansible filter name (https://github.com/ansible/ansible/issues/78912, https://github.com/ansible/ansible/pull/78913).
- handlers - fix an issue where the ``flush_handlers`` meta task could not be used with FQCN: ``ansible.builtin.meta`` (https://github.com/ansible/ansible/issues/79023)
- keyword inheritance - Ensure that we do not squash keywords in validate (https://github.com/ansible/ansible/issues/79021)
- omit on keywords was resetting to default value, ignoring inheritance.
- service_facts - Use python re to parse service output instead of grep (https://github.com/ansible/ansible/issues/78541)

New Plugins
-----------

Test
~~~~

- uri - is the string a valid URI
- url - is the string a valid URL
- urn - is the string a valid URN

v2.14.0b2
=========

Release Summary
---------------

| Release Date: 2022-10-03
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- ansible-test validate-modules - Added support for validating module documentation stored in a sidecar file alongside the module (``{module}.yml`` or ``{module}.yaml``). Previously these files were ignored and documentation had to be placed in ``{module}.py``.
- apt_repository will use the trust repo directories in order of preference (more appropriate to less) as they exist on the target.

Breaking Changes / Porting Guide
--------------------------------

- ansible-test validate-modules - Removed the ``missing-python-doc`` error code in validate modules, ``missing-documentation`` is used instead for missing PowerShell module documentation.

Bugfixes
--------

- Fix reusing a connection in a task loop that uses a redirected or aliased name - https://github.com/ansible/ansible/issues/78425
- Fix setting become activation in a task loop - https://github.com/ansible/ansible/issues/78425
- apt module should not traceback on invalid type given as package. issue 78663.
- known_hosts - do not return changed status when a non-existing key is removed (https://github.com/ansible/ansible/issues/78598)
- plugin loader, fix detection for existing configuration before initializing for a plugin

v2.14.0b1
=========

Release Summary
---------------

| Release Date: 2022-09-26
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Major Changes
-------------

- Move handler processing into new ``PlayIterator`` phase to use the configured strategy (https://github.com/ansible/ansible/issues/65067)
- ansible - At startup the filesystem encoding and locale are checked to verify they are UTF-8. If not, the process exits with an error reporting the errant encoding.
- ansible - Increase minimum Python requirement to Python 3.9 for CLI utilities and controller code
- ansible-test - At startup the filesystem encoding is checked to verify it is UTF-8. If not, the process exits with an error reporting the errant encoding.
- ansible-test - At startup the locale is configured as ``en_US.UTF-8``, with a fallback to ``C.UTF-8``. If neither encoding is available the process exits with an error. If the fallback is used, a warning is displayed. In previous versions the ``en_US.UTF-8`` locale was always requested. However, no startup checking was performed to verify the locale was successfully configured.

Minor Changes
-------------

- Add a new "INVENTORY_UNPARSED_WARNING" flag add to hide the "No inventory was parsed, only implicit localhost is available" warning
- Add an 'action_plugin' field for modules in runtime.yml plugin_routing.

  This fixes module_defaults by supporting modules-as-redirected-actions
  without redirecting module_defaults entries to the common action.

  .. code: yaml

     plugin_routing:
       action:
         facts:
           redirect: ns.coll.eos
         command:
           redirect: ns.coll.eos
       modules:
         facts:
           redirect: ns.coll.eos_facts
         command:
           redirect: ns.coll.eos_command

  With the runtime.yml above for ns.coll, a task such as

  .. code: yaml

     - hosts: all
       module_defaults:
         ns.coll.eos_facts: {'valid_for_eos_facts': 'value'}
         ns.coll.eos_command: {'not_valid_for_eos_facts': 'value'}
       tasks:
         - ns.coll.facts:

  will end up with defaults for eos_facts and eos_command
  since both modules redirect to the same action.

  To select an action plugin for a module without merging
  module_defaults, define an action_plugin field for the resolved
  module in the runtime.yml.

  .. code: yaml

     plugin_routing:
       modules:
         facts:
           redirect: ns.coll.eos_facts
           action_plugin: ns.coll.eos
         command:
           redirect: ns.coll.eos_command
           action_plugin: ns.coll.eos

  The action_plugin field can be a redirected action plugin, as
  it is resolved normally.

  Using the modified runtime.yml, the example task will only use
  the ns.coll.eos_facts defaults.
- Add support for parsing ``-a`` module options as JSON and not just key=value arguments - https://github.com/ansible/ansible/issues/78112
- Added Kylin Linux Advanced Server OS in RedHat OS Family.
- Allow ``when`` conditionals to be used on ``flush_handlers`` (https://github.com/ansible/ansible/issues/77616)
- Allow meta tasks to be used as handlers.
- Display - The display class will now proxy calls to Display.display via the queue from forks/workers to be handled by the parent process for actual display. This reduces some reliance on the fork start method and improves reliability of displaying messages.
- Jinja version test - Add pep440 version_type for version test. (https://github.com/ansible/ansible/issues/78288)
- Loops - Add new ``loop_control.extended_allitems`` to allow users to disable tracking all loop items for each loop (https://github.com/ansible/ansible/issues/75216)
- NetBSD - Add uptime_seconds fact
- Provide a `utc` option for strftime to show time in UTC rather than local time
- Raise a proper error when ``include_role`` or ``import_role`` is used as a handler.
- Remove the ``AnsibleContext.resolve`` method as its override is not necessary. Furthermore the ability to override the ``resolve`` method was deprecated in Jinja 3.0.0 and removed in Jinja 3.1.0.
- Utilize @classmethod and @property together to form classproperty (Python 3.9) to access field attributes of a class
- ``LoopControl`` is now templated through standard ``post_validate`` method (https://github.com/ansible/ansible/pull/75715)
- ``ansible-galaxy collection install`` - add an ``--offline`` option to prevent querying distribution servers (https://github.com/ansible/ansible/issues/77443).
- ansible - Add support for Python 3.11 to Python interpreter discovery.
- ansible - At startup the stdin/stdout/stderr file handles are checked to verify they are using blocking IO. If not, the process exits with an error reporting which file handle(s) are using non-blocking IO.
- ansible-config adds JSON and YAML output formats for list and dump actions.
- ansible-connection now supports verbosity directly on cli
- ansible-console added 'collections' command to match playbook keyword.
- ansible-doc - remove some of the manual formatting, and use YAML more uniformly. This in particular means that ``true`` and ``false`` are used for boolean values, instead of ``True`` and ``False`` (https://github.com/ansible/ansible/pull/78668).
- ansible-galaxy - Support resolvelib versions 0.6.x, 0.7.x, and 0.8.x. The full range of supported versions is now >= 0.5.3, < 0.9.0.
- ansible-galaxy now supports a user defined timeout,  instead of existing hardcoded 60s (now the default).
- ansible-test - Add FreeBSD 13.1 remote support.
- ansible-test - Add RHEL 9.0 remote support.
- ansible-test - Add support for Python 3.11.
- ansible-test - Add support for RHEL 8.6 remotes.
- ansible-test - Add support for Ubuntu VMs using the ``--remote`` option.
- ansible-test - Add support for exporting inventory with ``ansible-test shell --export {path}``.
- ansible-test - Add support for multi-arch remotes.
- ansible-test - Add support for provisioning Alpine 3.16 remote instances.
- ansible-test - Add support for provisioning Fedora 36 remote instances.
- ansible-test - Add support for provisioning Ubuntu 20.04 remote instances.
- ansible-test - Add support for provisioning remotes which require ``doas`` for become.
- ansible-test - Add support for running non-interactive commands with ``ansible-test shell``.
- ansible-test - Alpine remotes now use ``sudo`` for tests, using ``doas`` only for bootstrapping.
- ansible-test - An improved error message is shown when the download of a pip bootstrap script fails. The download now uses ``urllib2`` instead of ``urllib`` on Python 2.
- ansible-test - Avoid using the ``mock_use_standalone_module`` setting for unit tests running on Python 3.8 or later.
- ansible-test - Become support for remote instance provisioning is no longer tied to a fixed list of platforms.
- ansible-test - Blocking mode is now enforced for stdin, stdout and stderr. If any of these are non-blocking then ansible-test will exit during startup with an error.
- ansible-test - Distribution specific test containers are now multi-arch, supporting both x86_64 and aarch64.
- ansible-test - Distribution specific test containers no longer contain a ``/etc/ansible/hosts`` file.
- ansible-test - Enable loading of ``coverage`` data files created by older supported ansible-test releases.
- ansible-test - Fedora 36 has been added as a test container.
- ansible-test - FreeBSD remotes now use ``sudo`` for tests, using ``su`` only for bootstrapping.
- ansible-test - Improve consistency of output messages by using stdout or stderr for most output, but not both.
- ansible-test - Remote Alpine instances now have the ``acl`` package installed.
- ansible-test - Remote Fedora instances now have the ``acl`` package installed.
- ansible-test - Remote FreeBSD instances now have ACLs enabled on the root filesystem.
- ansible-test - Remote Ubuntu instances now have the ``acl`` package installed.
- ansible-test - Remove Fedora 34 test container.
- ansible-test - Remove Fedora 35 test container.
- ansible-test - Remove FreeBSD 13.0 remote support.
- ansible-test - Remove RHEL 8.5 remote support.
- ansible-test - Remove Ubuntu 18.04 test container.
- ansible-test - Remove support for Python 2.7 on provisioned FreeBSD instances.
- ansible-test - Remove support for Python 3.8 on the controller.
- ansible-test - Remove the ``opensuse15py2`` container.
- ansible-test - Support multiple pinned versions of the ``coverage`` module. The version used now depends on the Python version in use.
- ansible-test - Test containers have been updated to remove the ``VOLUME`` instruction.
- ansible-test - The Alpine 3 test container has been updated to Alpine 3.16.0.
- ansible-test - The ``http-test-container`` container is now multi-arch, supporting both x86_64 and aarch64.
- ansible-test - The ``pypi-test-container`` container is now multi-arch, supporting both x86_64 and aarch64.
- ansible-test - The ``shell`` command can be used outside a collection if no controller delegation is required.
- ansible-test - The openSUSE test container has been updated to openSUSE Leap 15.4.
- ansible-test - Ubuntu 22.04 has been added as a test container.
- ansible-test - Update pinned sanity test requirements for all tests.
- ansible-test - Update the ``base`` container to 3.4.0.
- ansible-test - Update the ``default`` containers to 6.6.0.
- apt_repository remove dependency on apt-key and use gpg + /usr/share/keyrings directly instead
- blockinfile - The presence of the multiline flag (?m) in the regular expression for insertafter opr insertbefore controls whether the match is done line by line or with multiple lines (https://github.com/ansible/ansible/pull/75090).
- calls to listify_lookup_plugin_terms in core do not pass in loader/dataloader anymore.
- collections - ``ansible-galaxy collection build`` can now utilize ``MANIFEST.in`` style directives from ``galaxy.yml`` instead of ``build_ignore`` effectively inverting the logic from include by default, to exclude by default. (https://github.com/ansible/ansible/pull/78422)
- config manager, move templating into main query function in config instead of constants
- config manager, remove updates to configdata as it is mostly unused
- configuration entry INTERPRETER_PYTHON_DISTRO_MAP is now 'private' and won't show up in normal configuration queries and docs, since it is not 'settable' this avoids user confusion.
- distribution - add distribution_minor_version for Debian Distro (https://github.com/ansible/ansible/issues/74481).
- documentation construction now gives more information on error.
- facts - add OSMC to Debian os_family mapping
- get_url - permit to pass to parameter ``checksum`` an URL pointing to a file containing only a checksum (https://github.com/ansible/ansible/issues/54390).
- new tests url, uri and urn will verify string as such, but they don't check existance of the resource
- plugin loader - add ansible_name and ansible_aliases attributes to plugin objects/classes.
- systemd is now systemd_service to better reflect the scope of the module, systemd is kept as an alias for backwards compatibility.
- templating - removed internal template cache
- uri - cleanup write_file method, remove overkill safety checks and report any exception, change shutilcopyfile to use module.atomic_move
- urls - Add support to specify SSL/TLS ciphers to use during a request (https://github.com/ansible/ansible/issues/78633)
- validate-modules - Allow ``type: raw`` on a module return type definition for values that have a dynamic type
- version output now includes the path to the python executable that Ansible is running under
- yum_repository - do not give the ``async`` parameter a default value anymore, since this option is deprecated in RHEL 8. This means that ``async = 1`` won't be added to repository files if omitted, but it can still be set explicitly if needed.

Breaking Changes / Porting Guide
--------------------------------

- Allow for lazy evaluation of Jinja2 expressions (https://github.com/ansible/ansible/issues/56017)
- The default ansible-galaxy role skeletons no longer contain .travis.yml files. You can configure ansible-galaxy to use a custom role skeleton that contains a .travis.yml file to continue using Galaxy's integration with Travis CI.
- ansible - At startup the filesystem encoding and locale are checked to verify they are UTF-8. If not, the process exits with an error reporting the errant encoding.
- ansible - Increase minimum Python requirement to Python 3.9 for CLI utilities and controller code
- ansible-test - At startup the filesystem encoding is checked to verify it is UTF-8. If not, the process exits with an error reporting the errant encoding.
- ansible-test - At startup the locale is configured as ``en_US.UTF-8``, with a fallback to ``C.UTF-8``. If neither encoding is available the process exits with an error. If the fallback is used, a warning is displayed. In previous versions the ``en_US.UTF-8`` locale was always requested. However, no startup checking was performed to verify the locale was successfully configured.
- strategy plugins - Make ``ignore_unreachable`` to increase ``ignored`` and ``ok`` and  counter, not ``skipped`` and ``unreachable``. (https://github.com/ansible/ansible/issues/77690)

Deprecated Features
-------------------

- Deprecate ability of lookup plugins to return arbitrary data. Lookup plugins must return lists, failing to do so will be an error in 2.18. (https://github.com/ansible/ansible/issues/77788)
- Encryption - Deprecate use of the Python crypt module due to it's impending removal from Python 3.13
- PlayContext.verbosity is deprecated and will be removed in 2.18. Use ansible.utils.display.Display().verbosity as the single source of truth.
- ``DEFAULT_FACT_PATH``, ``DEFAULT_GATHER_SUBSET`` and ``DEFAULT_GATHER_TIMEOUT`` are deprecated and will be removed in 2.18. Use ``module_defaults`` keyword instead.
- ``PlayIterator`` - deprecate ``cache_block_tasks`` and ``get_original_task`` which are noop and unused.
- ``Templar`` - deprecate ``shared_loader_obj`` option which is unused. ``ansible.plugins.loader`` is used directly instead.
- listify_lookup_plugin_terms, deprecate 'loader/dataloader' parameter as it not used.
- vars plugins - determining whether or not to run ansible.legacy vars plugins with the class attribute REQUIRES_WHITELIST is deprecated, set REQUIRES_ENABLED instead.

Removed Features (previously deprecated)
----------------------------------------

- PlayIterator - remove deprecated ``PlayIterator.ITERATING_*`` and ``PlayIterator.FAILED_*``
- Remove deprecated ``ALLOW_WORLD_READABLE_TMPFILES`` configuration option (https://github.com/ansible/ansible/issues/77393)
- Remove deprecated ``COMMAND_WARNINGS`` configuration option (https://github.com/ansible/ansible/issues/77394)
- Remove deprecated ``DISPLAY_SKIPPED_HOSTS`` environment variable (https://github.com/ansible/ansible/issues/77396)
- Remove deprecated ``LIBVIRT_LXC_NOSECLABEL`` environment variable (https://github.com/ansible/ansible/issues/77395)
- Remove deprecated ``NETWORK_GROUP_MODULES`` environment variable (https://github.com/ansible/ansible/issues/77397)
- Remove deprecated ``UnsafeProxy``
- Remove deprecated ``plugin_filters_cfg`` config option from ``default`` section (https://github.com/ansible/ansible/issues/77398)
- Remove deprecated functionality that allows loading cache plugins directly without using ``cache_loader``.
- Remove deprecated functionality that allows subclassing ``DefaultCallback`` without the corresponding ``doc_fragment``.
- Remove deprecated powershell functions ``Load-CommandUtils`` and ``Import-PrivilegeUtil``
- apt_key - remove deprecated ``key`` module param
- command/shell - remove deprecated ``warn`` module param
- get_url - remove deprecated ``sha256sum`` module param
- import_playbook - remove deprecated functionality that allows providing additional parameters in free form

Bugfixes
--------

- "meta: refresh_inventory" does not clobber entries added by add_host/group_by anymore.
- Add PyYAML >= 5.1 as a dependency of ansible-core to be compatible with Python 3.8+.
- Avoid 'unreachable' error when chmod on AIX has 255 as return code.
- Bug fix for when handlers were ran on failed hosts after an ``always`` section was executed (https://github.com/ansible/ansible/issues/52561)
- Do not allow handlers from dynamic includes to be notified (https://github.com/ansible/ansible/pull/78399)
- Ensure handlers observe ``any_errors_fatal`` (https://github.com/ansible/ansible/issues/46447)
- Ensure syntax check errors include playbook filenames
- Ensure the correct ``environment_class`` is set on ``AnsibleJ2Template``
- Error for collection redirects that do not use fully qualified collection names, as the redirect would be determined by the ``collections`` keyword.
- Fix PluginLoader to mimic Python import machinery by adding module to sys.modules before exec
- Fix ``-vv`` output for meta tasks to not have an empty message when skipped, print the skip reason instead. (https://github.com/ansible/ansible/issues/77315)
- Fix an issue where ``ansible_play_hosts`` and ``ansible_play_batch`` were not properly updated when a failure occured in an explicit block inside the rescue section (https://github.com/ansible/ansible/issues/78612)
- Fix dnf module documentation to indicate that comparison operators for package version require spaces around them (https://github.com/ansible/ansible/issues/78295)
- Fix for linear strategy when tasks were executed in incorrect order or even removed from execution. (https://github.com/ansible/ansible/issues/64611, https://github.com/ansible/ansible/issues/64999, https://github.com/ansible/ansible/issues/72725, https://github.com/ansible/ansible/issues/72781)
- Fix for network_cli not getting all relevant connection options
- Fix handlers execution with ``serial`` in the ``linear`` strategy (https://github.com/ansible/ansible/issues/54991)
- Fix potential, but unlikely, cases of variable use before definition.
- Fix traceback when installing a collection from a git repository and git is not installed (https://github.com/ansible/ansible/issues/77479).
- GALAXY_IGNORE_CERTS reworked to allow each server entry to override
- More gracefully handle separator errors in jinja2 template overrides (https://github.com/ansible/ansible/pull/77495).
- Move undefined check from concat to finalize (https://github.com/ansible/ansible/issues/78156)
- Prevent losing unsafe on results returned from lookups (https://github.com/ansible/ansible/issues/77535)
- Propagate ``ansible_failed_task`` and ``ansible_failed_result`` to an outer rescue (https://github.com/ansible/ansible/issues/43191)
- Properly execute rescue section when an include task fails in all loop iterations (https://github.com/ansible/ansible/issues/23161)
- Properly send a skipped message when a list in a ``loop`` is empty and comes from a template (https://github.com/ansible/ansible/issues/77934)
- Support colons in jinja2 template override values (https://github.com/ansible/ansible/pull/77495).
- ``ansible-galaxy`` - remove extra server api call during dependency resolution for requirements and dependencies that are already satisfied (https://github.com/ansible/ansible/issues/77443).
- `ansible-config init -f vars` will now use shorthand format
- action plugins now pass cannonical info to modules instead of 'temporary' info from play_context
- ansible - Exclude Python 2.6 from Python interpreter discovery.
- ansible-config dump - Only display plugin type headers when plugin options are changed if --only-changed is specified.
- ansible-configi init should now skip internal reserved config entries
- ansible-connection - decrypt vaulted parameters before sending over the socket, as vault secrets are not available on the other side.
- ansible-console - Renamed the first argument of ``ConsoleCLI.default`` from ``arg`` to ``line`` to match the first argument of the same method on the base class ``Cmd``.
- ansible-console commands now all have a help entry.
- ansible-console fixed to load modules via fqcn, short names and handle redirects.
- ansible-console now shows installed collection modules.
- ansible-doc - fix listing plugins.
- ansible-doc will not add 'website for' in ":ref:" substitutions as it made them confusing.
- ansible-doc will not again warn and skip when missing docs, always show the doc file (for edit on github) and match legacy plugins.
- ansible-doc will not traceback when legacy plugins don't have docs nor adjacent file with docs
- ansible-doc will now also display until as an 'implicit' templating keyword.
- ansible-doc will now not display version_added_collection under same conditions it does not display version_added.
- ansible-galaxy - Fix detection of ``--role-file`` in arguments for implicit role invocation (https://github.com/ansible/ansible/issues/78204)
- ansible-galaxy - Fix exit codes for role search and delete (https://github.com/ansible/ansible/issues/78516)
- ansible-galaxy - Fix loading boolean server options so False doesn't become a truthy string (https://github.com/ansible/ansible/issues/77416).
- ansible-galaxy - Fix reinitializing the whole collection directory with ``ansible-galaxy collection init ns.coll --force``. Now directories and files that are not included in the collection skeleton will be removed.
- ansible-galaxy - Fix unhandled traceback if a role's dependencies in meta/main.yml or meta/requirements.yml are not lists.
- ansible-galaxy - do not require mandatory keys in the ``galaxy.yml`` of source collections when listing them (https://github.com/ansible/ansible/issues/70180).
- ansible-galaxy - fix installing collections that have dependencies in the metadata set to null instead of an empty dictionary (https://github.com/ansible/ansible/issues/77560).
- ansible-galaxy - fix listing collections that contains metadata but the namespace or name are not strings.
- ansible-galaxy - fix missing meta/runtime.yml in default galaxy skeleton used for ansible-galaxy collection init
- ansible-galaxy - fix setting the cache for paginated responses from Galaxy NG/AH (https://github.com/ansible/ansible/issues/77911).
- ansible-galaxy - handle unsupported versions of resolvelib gracefully.
- ansible-galaxy --ignore-certs now has proper precedence over configuration
- ansible-test - Allow disabled, unsupported, unstable and destructive integration test targets to be selected using their respective prefixes.
- ansible-test - Allow unstable tests to run when targeted changes are made and the ``--allow-unstable-changed`` option is specified (resolves https://github.com/ansible/ansible/issues/74213).
- ansible-test - Always remove containers after failing to create/run them. This avoids leaving behind created containers when using podman.
- ansible-test - Correctly detect when running as the ``root`` user (UID 0) on the origin host. The result of the detection was incorrectly being inverted.
- ansible-test - Delegation for commands which generate output for programmatic consumption no longer redirect all output to stdout. The affected commands and options are ``shell``, ``sanity --lint``, ``sanity --list-tests``, ``integration --list-targets``, ``coverage analyze``
- ansible-test - Delegation now properly handles arguments given after ``--`` on the command line.
- ansible-test - Don't fail if network cannot be disconnected (https://github.com/ansible/ansible/pull/77472)
- ansible-test - Fix bootstrapping of Python 3.9 on Ubuntu 20.04 remotes.
- ansible-test - Fix change detection for ansible-test's own integration tests.
- ansible-test - Fix internal validation of remote completion configuration.
- ansible-test - Fix skipping of tests marked ``needs/python`` on the origin host.
- ansible-test - Fix skipping of tests marked ``needs/root`` on the origin host.
- ansible-test - Prevent ``--target-`` prefixed options for the ``shell`` command from being combined with legacy environment options.
- ansible-test - Sanity test output with the ``--lint`` option is no longer mixed in with bootstrapping output.
- ansible-test - Subprocesses are now isolated from the stdin, stdout and stderr of ansible-test. This avoids issues with subprocesses tampering with the file descriptors, such as SSH making them non-blocking. As a result of this change, subprocess output from unit and integration tests on stderr now go to stdout.
- ansible-test - Subprocesses no longer have access to the TTY ansible-test is connected to, if any. This maintains consistent behavior between local testing and CI systems, which typically do not provide a TTY. Tests which require a TTY should use pexpect or another mechanism to create a PTY.
- ansible-test - Temporary executables are now verified as executable after creation. Without this check, path injected scripts may not be found, typically on systems with ``/tmp`` mounted using the "noexec" option. This can manifest as a missing Python interpreter, or use of the wrong Python interpreter, as well as other error conditions.
- ansible-test - Test configuration for collections is now parsed only once, prior to delegation. Fixes issue: https://github.com/ansible/ansible/issues/78334
- ansible-test - Test containers are now run with the ``--tmpfs`` option for ``/tmp``, ``/run`` and ``/run/lock``. This allows use of containers built without the ``VOLUME`` instruction. Additionally, containers with those volumes defined no longer create anonymous volumes for them. This avoids leaving behind volumes on the container host after the container is stopped and deleted.
- ansible-test - The ``shell`` command no longer redirects all output to stdout when running a provided command. Any command output written to stderr will be mixed with the stderr output from ansible-test.
- ansible-test - The ``shell`` command no longer requests a TTY when using delegation unless an interactive shell is being used. An interactive shell is the default behavior when no command is given to pass to the shell.
- ansible-test - ansible-doc sanity test - Correctly determine the fully-qualified collection name for plugins in subdirectories, resolving https://github.com/ansible/ansible/issues/78490.
- ansible-test - validate-modules - Documentation-only modules, used for documenting actions, are now allowed to have docstrings (https://github.com/ansible/ansible/issues/77972).
- ansible-test compile sanity test - do not crash if a column could not be determined for an error (https://github.com/ansible/ansible/pull/77465).
- apt - Fix module failure when a package is not installed and only_upgrade=True. Skip that package and check the remaining requested packages for upgrades. (https://github.com/ansible/ansible/issues/78762)
- apt - don't actually update the cache in check mode with update_cache=true.
- apt - don't mark existing packages as manually installed in check mode (https://github.com/ansible/ansible/issues/66413).
- apt - fix package selection to include /etc/apt/preferences(.d) (https://github.com/ansible/ansible/issues/77969)
- apt module now correctly handles virtual packages.
- arg_spec - Fix incorrect ``no_log`` warning when a parameter alias is used (https://github.com/ansible/ansible/pull/77576)
- callback plugins - do not crash when ``exception`` passed from a module is not a string (https://github.com/ansible/ansible/issues/75726, https://github.com/ansible/ansible/pull/77781).
- cli now emits clearer error on no hosts selected
- config, ensure that pulling values from configmanager are templated if possible.
- display itself should be single source of 'verbosity' level to the engine.
- dnf - Condense a few internal boolean returns.
- dnf - The ``nobest`` option now also works for ``state=latest``.
- dnf - The ``skip_broken`` option is now used in installs (https://github.com/ansible/ansible/issues/73072).
- dnf - fix output parsing on systems with ``LANGUAGE`` set to a language other than English (https://github.com/ansible/ansible/issues/78193)
- facts - fix IP address discovery for specific interface names (https://github.com/ansible/ansible/issues/77792).
- facts - fix processor facts on AIX: correctly detect number of cores and threads, turn ``processor`` into a list (https://github.com/ansible/ansible/pull/78223).
- fetch_file - Ensure we only use the filename when calculating a tempfile, and do not incude the query string (https://github.com/ansible/ansible/issues/29680)
- fetch_file - properly split files with multiple file extensions (https://github.com/ansible/ansible/pull/75257)
- file - setting attributes of symbolic links or files that are hard linked no longer fails when the link target is unspecified (https://github.com/ansible/ansible/issues/76142).
- file backed cache plugins now handle concurrent access by making atomic updates to the files.
- git module fix docs and proper use of ssh wrapper script and GIT_SSH_COMMAND depending on version.
- if a config setting prevents running ansible it should at least show it's "origin".
- include module - add docs url to include deprecation message (https://github.com/ansible/ansible/issues/76684).
- items2dict - Handle error if an item is not a dictionary or is missing the required keys (https://github.com/ansible/ansible/issues/70337).
- local facts - if a local fact in the facts directory cannot be stated, store an error message as the fact value and emit a warning just as if just as if the facts execution has failed. The stat can fail e.g. on dangling symlinks.
- lookup plugin - catch KeyError when lookup returns dictionary (https://github.com/ansible/ansible/pull/77789).
- module_utils - Make distro.id() report newer versions of OpenSuSE (at least >=15) also report as ``opensuse``. They report themselves as ``opensuse-leap``.
- module_utils.service - daemonize - Avoid modifying the list of file descriptors while iterating over it.
- null_representation config entry changed to 'raw' as it must allow 'none/null' and empty string.
- paramiko - Add a new option to allow paramiko >= 2.9 to easily work with all devices now that rsa-sha2 support was added to paramiko, which prevented communication with numerous platforms. (https://github.com/ansible/ansible/issues/76737)
- paramiko - Add back support for ``ssh_args``, ``ssh_common_args``, and ``ssh_extra_args`` for parsing the ``ProxyCommand`` (https://github.com/ansible/ansible/issues/78750)
- password lookup does not ignore k=v arguments anymore.
- pause module will now report proper 'echo' vs always being true.
- pip - fix cases where resolution of pip Python module fails when importlib.util has not already been imported
- plugin loader - Sort results when fuzzy matching plugin names (https://github.com/ansible/ansible/issues/77966).
- plugin loader will now load config data for plugin by name instead of by file to avoid issues with the same file being loaded under different names (fqcn + short name).
- plugin loader, now when skipping a plugin due to an abstract method error we provide that in 'verbose' mode instead of totally obscuring the error. The current implementation assumed only the base classes would trigger this and failed to consider 'in development' plugins.
- prevent lusermod from using group name instead of group id (https://github.com/ansible/ansible/pull/77914)
- prevent type annotation shim failures from causing runtime failures (https://github.com/ansible/ansible/pull/77860)
- psrp connection now handles default to inventory_hostname correctly.
- roles, fixed issue with roles loading paths not contained in the role itself when using the `_from` options.
- setup - Adds a default value to ``lvm_facts`` when lvm or lvm2 is not installed on linux (https://github.com/ansible/ansible/issues/17393)
- shell plugins now give a more user friendly error when fed the wrong type of data.
- template module/lookup - fix ``convert_data`` option that was effectively always set to True for Jinja macros (https://github.com/ansible/ansible/issues/78141)
- unarchive - if unzip is available but zipinfo is not, use unzip -Z instead of zipinfo (https://github.com/ansible/ansible/issues/76959).
- uri - properly use uri parameter use_proxy (https://github.com/ansible/ansible/issues/58632)
- uri module - failed status when Authentication Bearer used with netrc, because Basic authentication was by default. Fix now allows to ignore netrc by changing use_netrc=False (https://github.com/ansible/ansible/issues/74397).
- urls - Guard imports of ``urllib3`` by catching ``Exception`` instead of ``ImportError`` to prevent exceptions in the import process of optional dependencies from preventing use of ``urls.py`` (https://github.com/ansible/ansible/issues/78648)
- user - Fix error "Permission denied" in user module while generating SSH keys (https://github.com/ansible/ansible/issues/78017).
- user - fix creating a local user if the user group already exists (https://github.com/ansible/ansible/pull/75042)
- user module - Replace uses of the deprecated ``spwd`` python module with ctypes (https://github.com/ansible/ansible/pull/78050)
- validate-modules - fix validating version_added for new options.
- variablemanager, more efficient read of vars files
- vault secrets file now executes in the correct context when it is a symlink (not resolved to canonical file).
- wait_for - Read file and perform comparisons using bytes to avoid decode errors (https://github.com/ansible/ansible/issues/78214)
- winrm - Ensure ``kinit`` is run with the same ``PATH`` env var as the Ansible process
- winrm connection now handles default to inventory_hostname correctly.
- yaml inventory plugin - fix the error message for non-string hostnames (https://github.com/ansible/ansible/issues/77519).
- yum - fix traceback when ``releasever`` is specified with ``latest`` (https://github.com/ansible/ansible/issues/78058)
