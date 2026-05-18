===============================================
ansible-core 2.21 "The Rain Song" Release Notes
===============================================

.. contents:: Topics

v2.21.0
=======

Release Summary
---------------

| Release Date: 2026-05-18
| `Porting Guide <https://docs.ansible.com/ansible-core/2.21/porting_guides/porting_guide_core_2.21.html>`__

Major Changes
-------------

- ``ansible-galaxy install`` and ``ansible-galaxy collection install|download`` - collections that declare a ``requires_ansible`` version that is not compatible with the running ansible-core version are now excluded from installation and download by default. In previous versions, ansible-galaxy would install such collections even if doing so resulted in an error at load time. To restore the previous behavior, set ``COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH`` to ``ignore`` in your configuration. (https://github.com/ansible/ansible/issues/78539)
- action plugins - Actions can directly register variables at several precedence layers using the ``register_host_variables`` method on ``ActionBase``. Previously, variable registration could only be simulated by user action plugins by returning ``ansible_facts`` with insecure fact injection.
- register projections - The ``register`` task keyword allows mapping multiple variable names to Jinja expressions to transform task results and other variables. The mapping form can replace many usages of ``set_fact`` and allows order-independent chained access to other variable expressions within the same task.
- task implicit object - A new ``_task`` implicit object is available for use in ``register`` and task conditional expressions (e.g., ``failed_when``). The result of the current task can be accessed via the ``_task.result`` property, without the use of ``register``. Under a loop, ``_task.result`` is the most recently completed result and ``_task.loop_result`` provides access to accumulated loop results. The ``_task.polymorphic_result`` property provides compatibility with classic name-only ``register`` in loops. The value is the result of the most recent loop iteration, then becomes the final list loop result once the loop is complete.

Minor Changes
-------------

- DataLoader - Update ``DataLoader`` to deal exclusively in str
- PowerShell 7 - Add support for running PowerShell written modules on POSIX hosts. PowerShell modules run with the ``pwsh`` interpreter and can access the same module utils that Windows PowerShell modules can use. Some PowerShell based module utils may not be compatible due to their reliance on Windows APIs but ``Ansible.Basic.cs`` for module input and output handling works.
- PowerShell AddType Util - Will only include the debug information when ``DISPLAY_TRACEBACK`` contains ``error`` or ``always``. In the past the debug information would have been included if ``-vvv`` or higher was used but this new behavior aligns the logic with the new option added in Ansible 2.19.
- The minimum required ``setuptools`` version is now ``77.0.3``, as it is needed for the new PEP 639 license format
- ansiballz - Add tech preview to embed arbitrary files, not relying on python ``import``
- ansible-playbook - consolidated block and task loading code to remove duplicated logic (https://github.com/ansible/ansible/pull/86603).
- ansible-test - Add PowerShell support to managed containers and remotes.
- ansible-test - Add container/remote aliases for more loosely specifying managed test environments.
- ansible-test - Add limited RHEL8 integration test remote supporting Python 3.12 only
- ansible-test - Add support for using the Ansible Core CI service from GitHub Actions.
- ansible-test - Expand functions covered by the ``unwanted`` rule for the ``pylint`` sanity test. It now includes various ``os.*`` and ``subprocess.*`` subprocess functions in Ansible modules and module_utils.
- ansible-test - Generate ``dist_info`` when running tests.
- ansible-test - Optimize DNF configuration for managed remote RHEL instances.
- ansible-test - Remove ``use-run-command-not-popen`` and ``use-run-command-not-os-call`` error codes from the ``validate-modules`` sanity test. These scenarios are now covered by the ``pylint`` sanity test.
- ansible-test - Remove pylint check for ``urllib2`` usage.
- ansible-test - Remove support for an obsolete remote authentication method.
- ansible-test - Replace Alpine 3.22 container and remote with 3.23.
- ansible-test - Replace Fedora 42 with 43.
- ansible-test - Replace FreeBSD 13.5 remote with 15.0.
- ansible-test - Replace FreeBSD 14.3 remote with 14.4.
- ansible-test - Replace RHEL 10.0 remote with 10.1.
- ansible-test - Replace RHEL 9.6 remote with 9.7.
- ansible-test - Replace macOS 15.3 remote with macOS 26.3.
- ansible-test - Replace the ``parallels`` managed macOS provider with a new ``mac`` provider.
- ansible-test - Support automatic loading of test collections in core integration tests.
- ansible-test - Switch managed macOS remotes from x86_64 to aarch64.
- ansible-test - Update URL used to download FreeBSD wheels for managed remotes.
- ansible-test - Update ansible-test-utility-container.
- ansible-test - Update base and default containers.
- ansible-test - Update http-test-container.
- ansible-test - Update pypi-test-container.
- ansible-test - Update sanity test requirements.
- ansible-test - Update the pylint sanity test to pylint 4.0.2.
- ansible-test - Upgrade the distro-specific test containers.
- ansible-test - Use the new API endpoint for the Ansible Core CI service.
- ansible-test - add ``.winrm`` and ``.networking`` as valid JSON/YAML inventory file extensions. This should not affect any public facing code as it is used internally for inventories generated by ``ansible-test``.
- ansible-test - update galaxy_ng container to current version deployed to galaxy.ansible.com
- ansible-test acme cloud plugin - update to the 2.4.0 ACME test image, which upgrades Pebble to 2.10.0, Go to 1.26, and Python to 3.14, and generally updates all contained Python dependencies (https://github.com/ansible/ansible/pull/86740).
- ansible-test validate-modules sanity test - now reports bad return value keys that cannot be used with the dot notation in Jinja expressions (https://github.com/ansible/ansible/issues/86079).
- ansible-vault - improved error messages for better clarity and context when vault operations fail, helping users diagnose configuration or file access issues more easily (https://github.com/ansible/ansible/pull/86602).
- ansible-vault - keep the original contents when the EDITOR returns failure when using ``ansible-vault edit``.
- break_when - A ``break_when_result`` key is always present in results when a ``break_when`` expression is used.
- break_when - A ``break_when_suppressed_exception`` key is added to a result when a ``break_when`` expression fails and masks an existing exception in a result.
- break_when - A failed ``break_when`` expression now preserves the loop structure of a result and any loop item results.
- callback - filter key starting with _ansible_ from debug messages (https://github.com/ansible/ansible/issues/69731).
- callback plugins - support configuration using extra variables.
- changed_when - A ``changed_when_result`` key is always present in results when a ``changed_when`` expression is used.
- changed_when - A ``changed_when_suppressed_exception`` key is added to a result when a ``changed_when`` expression fails and masks an existing exception in a result.
- core - The ``ActionBase._low_level_execute_command`` method no longer adds ``&& sleep 0`` to commands. This was a work-around for a 10+ year old Linux kernel bug affecting OpenSSH. By August of 2016 the fix had been included in kernel versions 4.1.26, 4.4.12, 4.5.6, 4.6.1 and 4.7. Linux kernel bug report: https://lore.kernel.org/lkml/alpine.LNX.2.00.1512091358290.9574@fanir.tuyoix.net/ OpenSSH bug report: https://bugzilla.mindrot.org/show_bug.cgi?id=2492
- deb822_repository - add include and exclude parameter arguments (https://github.com/ansible/ansible/issues/86155)
- default callback - add ``display_included_hosts`` option to control the ``included:`` banner lines for ``include_tasks``/``include_role`` (https://github.com/ansible/ansible/issues/84499).
- default callback plugin - add option to configure line width for YAML output. This allows to disable line wrapping (https://github.com/ansible/ansible/issues/84657, https://github.com/ansible/ansible/pull/85498).
- default callback plugin - add variable configuration for ``display_skipped_hosts`` (https://github.com/ansible/ansible/issues/84469).
- display - replace few words with more inclusive word list such as denylist, FilterDenyList (https://github.com/ansible/ansible/pull/86304).
- dnf - Separate module into module and utility script
- executor - remove unused RETURN_VARS
- file - return disk_usage_bytes fact (https://github.com/ansible/ansible/issues/70834).
- filter - Use datetime.strftime instead of time.strftime in strftime (https://github.com/ansible/ansible/issues/86260).
- find - add locale encoding in err msg when none is given
- generator - add support for extra vars (https://github.com/ansible/ansible/issues/83270).
- group - Add warning message when invalid priority values are provided to Group.set_priority() method (https://github.com/ansible/ansible/pull/85468).
- ignore_errors - Invalid values for ``ignore_errors`` will always be treated as ``False``
- ignore_errors - Templated values for the ``ignore_errors`` keyword behave more consistently in looped tasks. If ``ignore_errors`` resolves ``True`` for any loop item, errors will be ignored for the entire task.
- ignore_unreachable - Templated values for the ``ignore_unreachable`` keyword behave more consistently in looped tasks. If ``ignore_unreachable`` resolves ``True`` for any loop item, unreachable hosts will be ignored for the entire task.
- include_role has new option `rescuable` to allow it to toggle between task failure and syntax errors.
- loops - The ``break_when`` keyword is now validated when the value is falsey.
- loops - The registered result of a loop task no longer contains the ``skipped`` key when it would be ``False``.
- module/action results - A ``results`` key returned from an action or module is always preserved. Previously the ``results`` key was sometimes removed, depending on the type of its value.
- package_facts - Switch from rpm python to rpm CLI to list packages
- package_facts - use apk query instead of apk info for gathering package facts in Alpine (https://github.com/ansible/ansible/issues/86579).
- password hashing - Add support back for using the ``crypt`` implementation from the C library used to build Python, or with expanded functionality using ``libxcrypt``
- psrp - Added the ``certificate_key_password`` option through the variable ``ansible_psrp_certificate_key_password`` that can be used to decrypt the key specified by ``certificate_key_pem``. This option requires ``pypsrp>=0.9.0`` to be installed in the Ansible environment.
- psrp - Added the ``no_profile`` option through the variable ``ansible_psrp_no_profile`` that can stop the remote Windows host from loading the user profile on the Ansible tasks. This option requires ``pypsrp>=0.9.0`` to be installed in the Ansible environment.
- script - remove the currently unsupported ``decrypt`` argument from the module documentation (https://github.com/ansible/ansible/issues/86067).
- service - add support for GNU Hurd systems, which use SysV init scripts (https://github.com/ansible/ansible/pull/86622).
- slurp module gets new C(armor) option to allow user to disable base64 encoding.
- stat - return disk_usage_bytes fact (https://github.com/ansible/ansible/issues/70834).
- task results - Python and Powershell modules do not include the ``invocation`` task result key by default. Injection of the ``invocation`` task result key for Python and Powershell modules may be enabled with the var-settable ``INJECT_INVOCATION`` config item. Most callbacks mask ``invocation`` when displaying a task or loop item result.
- to_yaml / to_nice_yaml filters - Add optional ``vault_behavior`` argument to configure how vaulted values are rendered.
- worker process - When controller and forked child workers must share a TTY, the ``WORKER_SESSION_ISOLATION`` config item can be set to ``false`` (via variable/config/envvar) to disable forked worker session isolation.

Breaking Changes / Porting Guide
--------------------------------

- psrp - Changed the default of ``negotiate_service`` used to build the Kerberos Service Principal Name from ``WSMAN`` to ``host``. This aligns the defaults to how the native PowerShell PSRemoting client works on Windows and ensures that Kerberos can be used by more Windows targets by default. No deprecation period is used for this change as ``host`` is a builtin SPN to Windows and should improve compatibility out of the box. To go back to the old behaviour for any reason, set ``ansible_psrp_negotiate_service=WSMAN`` in the host vars.

Deprecated Features
-------------------

- The ``get_all_subclasses()`` function from ``ansible.module_utils.basic`` is deprecated and will be removed in ansible-core 2.24. Use ``get_all_subclasses()`` from ``ansible.module_utils.common._utils`` instead.
- The ``get_platfrom()`` function from ``ansible.module_utils.basic`` is deprecated and will be removed in ansible-core 2.24. Use ``platform.system()`` from the Python standard library instead.
- The ``load_platform_subclass()`` function from ``ansible.module_utils.basic`` is deprecated and will be removed in ansible-core 2.24. Use ``get_platform_subclass()`` from ``ansible.module_utils.common.sys_info`` instead.
- ``PluginLoader`` - Deprecate unused ``aliases`` attribute. Plugins in a collection should define aliases in the ``meta/runtime.yml`` file using the ``redirect`` field instead.
- ``ansible.module_utils.six`` - The ``six`` compatibility library provided at ``ansible.module_utils.six`` is deprecated, and planned for removal in ansible-core 2.24
- apt_key - deprecate in favor of deb822_repository.
- apt_repository - deprecate in favor of deb822_repository.
- connection plugins - Added a soft deprecation on the connection attributes ``has_native_async`` and ``always_pipeline_modules``. Connection plugins that wish to apply custom behaviour around pipelining should instead override the method ``is_pipelining_enabled(self, wrap_async=False)`` added in Ansible 2.19. For backwards compatibility no runtime deprecation warning is emitted but will be in the future.
- task result - Inferred task failure from a non-zero ``rc`` key and absence of a ``failed`` key will be deprecated in Ansible Core 2.22. Actions and modules must explicitly communicate failure by setting the ``failed`` key, using APIs that do so, or raising an unhandled exception. In future releases, the ``rc`` key will receive no special handling during task result processing.

Removed Features (previously deprecated)
----------------------------------------

- Removed 'required' option from get_bin_path API (https://github.com/ansible/ansible/issues/85998).
- Removed deprecated ``ansible.builtin.paramiko`` connection plugin (https://github.com/ansible/ansible/issues/86002). Setting the ``connection`` keyword to ``persistent`` or ``smart`` no longer attempts to use ``paramiko``.
- Removed deprecated ``ansible.module_utils.compat.paramiko`` (https://github.com/ansible/ansible/issues/86001).
- Removed deprecated ``handle_stats_and_callbacks`` parameter of the ``StrategyBase._load_included_file`` method. (https://github.com/ansible/ansible/issues/86003)
- Removed deprecated ability to import ``datetime``, ``signal``, ``types``, ``chain``, ``repeat``, ``map`` and ``shlex_quote`` from ``ansible.module_utils.basic``.
- compat.datetime - removed deprecated datetime compat APIs (https://github.com/ansible/ansible/issues/86000).
- git - removed deprecated alias gpg_whitelist (https://github.com/ansible/ansible/issues/86004).
- interpreter_discovery - removed auto_legacy and auto_legacy_slient options (https://github.com/ansible/ansible/issues/85995).
- module_utils - Remove previously deprecated ``safe_eval`` function (#85996) (#85999)

Bugfixes
--------

- Fix Windows LIB env var corruption (https://github.com/ansible-collections/ansible.windows/issues/297).
- Fix ``AnsibleModule.human_to_bytes()``, which was never adjusted after the standalone ``human_to_bytes()`` got a new parameter ``default_unit`` (https://github.com/ansible/ansible/pull/85259).
- Fix ``validate_argspec`` when tags are defined on the play. The ``always`` tag is only added if the play has no tags.
- Fix interpreter discovery on delegated ``async`` tasks (https://github.com/ansible/ansible/issues/86491)
- Fix source metadata validation (https://github.com/ansible/ansible/pull/86320).
- Fix up ``powershell`` shell commands when using a connection plugin that does not support stdin/pipeline input - https://github.com/ansible/ansible/issues/86397
- Fix up the Action plugin ``_make_tmp_path`` error to only include the command run rather than the shell's dataclass repr from ``mkdtemp``.
- Variable loading now uses file source instead of variables when invalidly formmated vars file is loaded.
- Windows - ignore temporary file cleanup warning when using AnsibleModule to compile C# utils. This should reduce the number of warnings that can safely be ignored when running PowerShell modules - https://github.com/ansible/ansible/issues/85976
- ``--start-at-task`` - fix starting at the requested task instead of starting at the next block or play. Play level tasks run first. (https://github.com/ansible/ansible/issues/86268)
- ``ansible-galaxy collection list`` - issue a warning when a collection's namespace and name do not match its filepath. (https://github.com/ansible/ansible/issues/69813)
- ``ansible-galaxy collection list|install`` - list collections based on reference (the fqcn used to refer to them in a playbook), not based on their documented name. (https://github.com/ansible/ansible/issues/69813)
- ``ansible-galaxy collection verify`` - fail collection verification when a collection's namespace and name  do not match its filepath. (https://github.com/ansible/ansible/issues/69813)
- ``ansible-galaxy install``/``ansible-galaxy collection download`` - collections from git repositories with a tag or sha version no longer emit detached head warning messages (https://github.com/ansible/ansible/issues/86169).
- ``ansible.builtin.pip`` - Running the built-in pip module with ``check_mode`` and packages coming from VCS URLs, archives, or local filepaths now correctly outputs the ``changed`` status of the task. Previously, it was always reported as changed due to improper package name resolution.  (https://github.com/ansible/ansible/pull/85623)
- ``ansible``, ``ansible-console`` - fix executing ``- meta: end_play`` tasks.
- ansible-connection - Prevent unpickling failures in module contexts by ensuring that AnsibleTaggedObjects in pickled responses are converted to plain types in ``JsonRpcServer``.
- ansible-galaxy - raise an error when wrong regex value specified in collection_skeleton_ignore.
- ansible-galaxy - warn instead of raising an error when no valid role or collections paths exist (https://github.com/ansible/ansible/pull/86341)
- ansible-galaxy collection - Fix using the server configuration for ``validate_certs`` when downloading collections. (https://github.com/ansible/ansible/issues/86694)
- ansible-test - Add missing bootstrapping for a target Python version in a controller container.
- ansible-test - Fix docker hostname parsing
- ansible-test - Fix traceback when requesting windows integration tests for multiple managed hosts.
- ansible-test - Missing git submodules in the source tree now result in a warning instead of an error.
- ansible-test - Restore code coverage reporting for Python code residing in integration tests.
- ansible-test - The runtime-metadata sanity test now ignores pre-release and build identifiers in collection versions. This prevents errors if a tombstone version is ``X.0.0``, while the collection's version is ``X.0.0-prerelease`` (https://github.com/ansible/ansible/issues/85193)."
- ansible-test - Upgrade ``expat`` during provisioning of Fedora 42 remote instances.
- ansible-test - When using the ``env --list-files`` option, non-filename output is now sent to stderr.
- ansible-test remote alias - Alias values for ``--controller`` and ``--target`` are properly resolved for ``remote``. Previously, remote alias values (e.g. ``fedora/latest``) resolved to the correct name only for the legacy ``--remote`` arg, failing with an unknown image error for the newer args.
- ansible_facts[os_*] - Contained wrong information, if ClearLinux parsing was tried before falling back to general os-release parsing
- ansible_local will no longer trigger variable injection default value deprecation.
- ansible_virtualization_role and ansible_virtualization_type facts - fix the detection of vms running inside FreeBSD Bhyve hypervisor and detection of jails  (https://github.com/ansible/ansible/pull/85767)
- apt - Stop the >= operator from being ignored for packages that are not already installed (https://github.com/ansible/ansible/pull/85254)
- apt - handle comma separated packages from recommends while installing local deb package (https://github.com/ansible/ansible/issues/86609).
- apt - recreate the APT lists directory (/var/lib/apt/lists by default) if missing (https://github.com/ansible/ansible/issues/61176).
- basic - fail in controlled manner when ``run_command()`` attempts to parse a command with broken syntax passed in as a string (https://github.com/ansible/ansible/issues/85719).
- cache plugins based on the BaseFileCache class will now sanitize keys to avoid names that could cause issues with the storage path
- callbacks - The value of ``TaskResult.task.connection`` properly reflects the loaded connection name used. Previously, incorrect values were reported in some cases.
- config lookup now properly factors in variables and show_origin when checking entries from the global configuration.
- config lookup now uses preexisting constants for templating when needed.
- copy - honor directory_mode when copying directories with remote_src=True (https://github.com/ansible/ansible/issues/81292).
- copy - when a single-file local directory was specified as the source, ``changed`` used to be ``false`` even when the source was actually copied. It now makes sure ``changed`` is ``true`` in this case. (https://github.com/ansible/ansible/issues/85833)
- deb822_repository - Remove ``Install-Python-Debian`` from files outputted by the ``deb822_repository`` module (https://github.com/ansible/ansible/issues/86395)
- deb822_repository no longer over-normalizes repository names when generating sources list filenames, preventing collisions for names that differ by case, underscores, or dots (https://github.com/ansible/ansible/issues/86243)
- display - Fix ``getuser`` fallback error handling on Python 3.13 and later. (https://github.com/ansible/ansible/issues/86142)
- dnf - When installing a dnf module, install and enable when missing, upgrade when present (https://github.com/ansible/ansible/issues/73457)
- dnf - fix package installation when specifying architecture without version (e.g., ``libgcc.i686``) where a different architecture of the same package is already installed (https://github.com/ansible/ansible/issues/86156).
- dnf5 - return failure message which occurred while running RPM scriptlet (https://github.com/ansible/ansible/issues/86117).
- file module - issue warning when attempting to access files/directories the user lacks permissions on instead of silently treating them as absent (https://github.com/ansible/ansible/issues/57573)
- first_found - Correct the "Include tasks only if one of the files exists, otherwise skip" example.
- first_found - ensure file lookup under ``files`` directory when the task action cannot be resolved (https://github.com/ansible/ansible/issues/85655).
- first_found - use the task action to determine the directory (templates/vars/files) containing the file when the lookup is not used as task loop.
- galaxy - previously, some corrupted cache files could cause Ansible Galaxy to fail with a traceback. This has been corrected to display a clear error message explaining how to resolve the problem. (https://github.com/ansible/ansible/issues/85918)
- get_url - fix regex for GNU Digest line which is used in comparing checksums (https://github.com/ansible/ansible/issues/86132).
- getent - handle non-empty string for split parameter value (https://github.com/ansible/ansible/issues/85720).
- git - Correct the output of git checkmode to a failure when the ``version`` supplied is an invalid ref (https://github.com/ansible/ansible/issues/51580)
- git - use the branch configured in ``.gitmodules`` or the remote HEAD instead of hardcoding ``master`` when ``track_submodules=yes`` (https://github.com/ansible/ansible/issues/77691).
- include_role would emit a syntax error on X_from options errors, but a task failure when missing a role to make it consistent now it also emits a task failure on missing tasks_from, which makes it subject to error handling in the play.
- include_role, would ignore missing X_from files if the subdir (tasks/vars/handlers/defaults) did not exist, now it is a proper error.
- iptables - The module can now detect when a extensions added with the module ``match`` argument have  been automatically imported by other module arguments such as ``uid_owner`` and prevents duplicate extension imports which previously caused an error (https://github.com/ansible/ansible/issues/84387). 
- local connection - Fix ``getuser`` fallback error handling on Python 3.13 and later.
- local connection - Pass correct type to become plugins when checking password (https://github.com/ansible/ansible/issues/86458)
- modules - fix AnsiballZ wrapper code escaping of sitecustomize
- option argument deprecations now have a proper alternative help text.
- package, service, gather_facts - fix templating module_defaults for modules executed by these action plugins. (https://github.com/ansible/ansible/issues/85848)
- package_facts - typecast bytes to string while returning facts (https://github.com/ansible/ansible/issues/85937).
- password lookup plugin - replace random.SystemRandom() with secrets.SystemRandom() when generating passwords (https://github.com/ansible/ansible/issues/85956, https://github.com/ansible/ansible/pull/85971).
- pip - Prevent passing ``-e`` to ``pip`` when the ``editable`` and ``requirements`` parameters are both used.
- pip - When installing multiple packages with ``editable=True``, ensure each package is editable (https://github.com/ansible/ansible/issues/77755).
- pluginloader - Fixed non-collection load path for builtin non-Jinja plugins to consult deprecation metadata.
- psrp - ReadTimeout exceptions now mark host as unreachable instead of fatal (https://github.com/ansible/ansible/issues/85966)
- rpm_key - Use librpm library API instead of gpg utility to support version 6 PGP keys (https://github.com/ansible/ansible/issues/86157).
- ssh connection plugin - fix resource leaks when using sshpass
- task conditionals - An error in any task conditional (e.g., ``when``, ``until``, ``failed_when``) always causes the task to report a descriptive failure while preserving the task result. The resulting task failure is always recoverable via ``ignore_errors``. Previous inconsistent error handling in task conditionals could result in warnings, loss of completed task results, recoverable task errors, unrecoverable task errors, or failure of the Ansible controller process.
- task results - The ``invocation`` item result key omitted from registered values for looped task results, unless enabled via ``INJECT_INVOCATION``. Previously, it was deleted from registered non-loop results and only available to callbacks.
- template module - Report the line number for Jinja syntax errors in template files.
- templating - Fix traceback when using ``deepcopy`` on an imported template (https://github.com/ansible/ansible/issues/86723).
- to_yaml / to_nice_yaml filters - Restore pre-2.19 decryption behavior for vaulted values (https://github.com/ansible/ansible/issues/85722). A regression in 2.19.0 previously caused vaulted values to be dumped as ``!vault``-tagged ciphertext.
- unarchive - make timezone aware timestamp for comparison (https://github.com/ansible/ansible/issues/85779).
- user - ``user`` module integration tests can now run multiple times on the same freebsd host (https://github.com/ansible/ansible/issues/86541).
- user - create accounts in an unlocked state by default on BusyBox (https://github.com/ansible/ansible/issues/68676)
- user - emit a warning when the ``seuser`` parameter is set on a system where SELinux is not enabled, instead of silently ignoring it (https://github.com/ansible/ansible/issues/85542).
- user - fix ``FreeBsdUser`` to not create ``/nonexistent`` directory when modifying user to add them to a group on FreeBSD (https://github.com/ansible/ansible/issues/86368)
- user - fix modifying users on BusyBox (https://github.com/ansible/ansible/issues/66679)
- user - make option group required_by option append.
- user - preserve existing password when modifying accounts on BusyBox systems (https://github.com/ansible/ansible/pull/86530)
- user - raise an error if force=true is used while deleting the group on BusyBox based distros (https://github.com/ansible/ansible/issues/85565).
- user - return the actual system groups the user belongs to instead of only the groups specified in the module input (https://github.com/ansible/ansible/issues/80669).
- winrm - Provide a better error message if a domain user is specified using a User Principal Name (``UPN``) but the ``pykerberos`` library is not installed so Kerberos is unavailable.
- yaml loading - Fix traceback when parsing YAML strings (not files) when using the pure Python implementation of PyYAML.
