==============================================
ansible-core 2.17 "Gallows Pole" Release Notes
==============================================

.. contents:: Topics

v2.17.8rc1
==========

Release Summary
---------------

| Release Date: 2025-01-20
| `Porting Guide <https://docs.ansible.com/ansible-core/2.17/porting_guides/porting_guide_core_2.17.html>`__

Bugfixes
--------

- Ansible will now also warn when reserved keywords are set via a module (set_fact, include_vars, etc).
- Ansible.Basic - Fix ``required_if`` check when the option value to check is unset or set to null.
- Use consistent multiprocessing context for action write locks
- ansible-test - Fix up coverage reporting to properly translate the temporary path of integration test modules to the expected static test module path.
- ansible-vault will now correctly handle `--prompt`, previously it would issue an error about stdin if no 2nd argument was passed
- copy action now prevents user from setting internal options.
- gather_facts action now defaults to `ansible.legacy.setup` if `smart` was set, no network OS was found and no other alias for `setup` was present.
- gather_facts action will now issues errors and warnings as appropriate if a network OS is detected but no facts modules are defined for it.
- ssh - connection options were incorrectly templated during ``reset_connection`` tasks (https://github.com/ansible/ansible/pull/84238).

v2.17.7
=======

Release Summary
---------------

| Release Date: 2024-12-02
| `Porting Guide <https://docs.ansible.com/ansible-core/2.17/porting_guides/porting_guide_core_2.17.html>`__

Minor Changes
-------------

- remove extraneous selinux import (https://github.com/ansible/ansible/issues/83657).

Security Fixes
--------------

- Templating will not prefer AnsibleUnsafe when a variable is referenced via hostvars - CVE-2024-11079

Bugfixes
--------

- Fix returning 'unreachable' for the overall task result. This prevents false positives when a looped task has unignored unreachable items (https://github.com/ansible/ansible/issues/84019).
- ansible-test - Fix traceback that occurs after an interactive command fails.
- dnf5 - fix installing a package using ``state=latest`` when a binary of the same name as the package is already installed (https://github.com/ansible/ansible/issues/84259)
- dnf5 - matching on a binary can be achieved only by specifying a full path (https://github.com/ansible/ansible/issues/84334)

v2.17.6
=======

Release Summary
---------------

| Release Date: 2024-11-04
| `Porting Guide <https://docs.ansible.com/ansible-core/2.17/porting_guides/porting_guide_core_2.17.html>`__

Minor Changes
-------------

- ansible-test - Improve container runtime probe error handling. When unexpected probe output is encountered, an error with more useful debugging information is provided.

Security Fixes
--------------

- include_vars action - Ensure that result masking is correctly requested when vault-encrypted files are read. (CVE-2024-8775)
- task result processing - Ensure that action-sourced result masking (``_ansible_no_log=True``) is preserved. (CVE-2024-8775)
- user action won't allow ssh-keygen, chown and chmod to run on existing ssh public key file, avoiding traversal on existing symlinks (CVE-2024-9902).

Bugfixes
--------

- Fix disabling SSL verification when installing collections and roles from git repositories. If ``--ignore-certs`` isn't provided, the value for the ``GALAXY_IGNORE_CERTS`` configuration option will be used (https://github.com/ansible/ansible/issues/83326).
- Improve performance on large inventories by reducing the number of implicit meta tasks.
- Use the requested error message in the ansible.module_utils.facts.timeout timeout function instead of hardcoding one.
- ansible-test - Enable the ``sys.unraisablehook`` work-around for the ``pylint`` sanity test on Python 3.11. Previously the work-around was only enabled for Python 3.12 and later. However, the same issue has been discovered on Python 3.11.
- debconf - set empty password values (https://github.com/ansible/ansible/issues/83214).
- facts - skip if distribution file path is directory, instead of raising error (https://github.com/ansible/ansible/issues/84006).
- user action will now require O(force) to overwrite the public part of an ssh key when generating ssh keys, as was already the case for the private part.
- user module now avoids changing ownership of files symlinked in provided home dir skeleton

v2.17.5
=======

Release Summary
---------------

| Release Date: 2024-10-07
| `Porting Guide <https://docs.ansible.com/ansible-core/2.17/porting_guides/porting_guide_core_2.17.html>`__

Bugfixes
--------

- Add descriptions for ``ansible-galaxy install --help` and ``ansible-galaxy role|collection install --help``.
- Errors now preserve stacked error messages even when YAML is involved.
- ``ansible-galaxy install --help`` - Fix the usage text and document that the requirements file passed to ``-r`` can include collections and roles.
- copy - mtime/atime not updated. Fix now update mtime/atime(https://github.com/ansible/ansible/issues/83013)
- delay keyword is now a float, matching the underlying 'time' API and user expectations.
- dnf5 - re-introduce the ``state: installed`` alias to ``state: present`` (https://github.com/ansible/ansible/issues/83960)
- module_utils atomic_move (used by most file based modules), now correctly handles permission copy and setting mtime correctly across all paths

v2.17.4
=======

Release Summary
---------------

| Release Date: 2024-09-09
| `Porting Guide <https://docs.ansible.com/ansible-core/2.17/porting_guides/porting_guide_core_2.17.html>`__

Bugfixes
--------

- Fix ``SemanticVersion.parse()`` to store the version string so that ``__repr__`` reports it instead of ``None`` (https://github.com/ansible/ansible/pull/83831).
- Fix an issue where registered variable was not available for templating in ``loop_control.label`` on skipped looped tasks (https://github.com/ansible/ansible/issues/83619)
- Fix for ``meta`` tasks breaking host/fork affinity with ``host_pinned`` strategy (https://github.com/ansible/ansible/issues/83294)
- Fix using the current task's directory for looking up relative paths within roles (https://github.com/ansible/ansible/issues/82695).
- atomic_move - fix using the setgid bit on the parent directory when creating files (https://github.com/ansible/ansible/issues/46742, https://github.com/ansible/ansible/issues/67177).
- connection plugins using the 'extras' option feature would need variables to match the plugin's loaded name, sometimes requiring fqcn, which is not the same as the documented/declared/expected variables. Now we fall back to the 'basename' of the fqcn, but plugin authors can still set the expected value directly.
- csvfile lookup - give an error when no search term is provided using modern config syntax (https://github.com/ansible/ansible/issues/83689).
- include_tasks - Display location when attempting to load a task list where ``include_*`` did not specify any value - https://github.com/ansible/ansible/issues/83874
- powershell - Improve CLIXML decoding to decode all control characters and unicode characters that are encoded as surrogate pairs.
- psrp - Fix bug when attempting to fetch a file path that contains special glob characters like ``[]``
- runtime-metadata sanity test - do not crash on deprecations if ``galaxy.yml`` contains an empty ``version`` field (https://github.com/ansible/ansible/pull/83831).
- ssh - Fix bug when attempting to fetch a file path with characters that should be quoted when using the ``piped`` transfer method

v2.17.3
=======

Release Summary
---------------

| Release Date: 2024-08-12
| `Porting Guide <https://docs.ansible.com/ansible-core/2.17/porting_guides/porting_guide_core_2.17.html>`__

Minor Changes
-------------

- ansible-test - Improve the error message shown when an unknown ``--remote`` or ``--docker`` option is given.
- ansible-test - Removed the ``vyos/1.1.8`` network remote as it is no longer functional.

Bugfixes
--------

- Warning now includes filename and line number of variable when specifying a list of dictionaries for vars (https://github.com/ansible/ansible/issues/82528).
- config, restored the ability to set module compression via a variable
- debconf - fix normalization of value representation for boolean vtypes in new packages (https://github.com/ansible/ansible/issues/83594)
- linear strategy: fix handlers included via ``include_tasks`` handler to be executed in lockstep (https://github.com/ansible/ansible/issues/83019)

v2.17.2
=======

Release Summary
---------------

| Release Date: 2024-07-15
| `Porting Guide <https://docs.ansible.com/ansible-core/2.17/porting_guides/porting_guide_core_2.17.html>`__

Bugfixes
--------

- Fix a traceback when an environment variable contains certain special characters (https://github.com/ansible/ansible/issues/83498)
- dnf - reverted incomplete fix from 2.17.2rc1 (https://github.com/ansible/ansible/pull/83504)
- dnf, dnf5 - fix for installing a set of packages by specifying them using a wildcard character (https://github.com/ansible/ansible/issues/83373)
- linear strategy now provides a properly templated task name to the v2_runner_on_started callback event.
- package_facts - ignore warnings sent by apk on stderr (https://github.com/ansible/ansible/issues/83501).
- replace - Updated before/after example (https://github.com/ansible/ansible/issues/83390).
- templating hostvars under native jinja will not cause serialization errors anymore.

v2.17.1
=======

Release Summary
---------------

| Release Date: 2024-06-17
| `Porting Guide <https://docs.ansible.com/ansible-core/2.17/porting_guides/porting_guide_core_2.17.html>`__

Minor Changes
-------------

- ansible-test - Update ``pypi-test-container`` to version 3.1.0.

Bugfixes
--------

- Fix rapid memory usage growth when notifying handlers using the ``listen`` keyword (https://github.com/ansible/ansible/issues/83392)
- Fix the task attribute ``resolved_action`` to show the FQCN instead of ``None`` when ``action`` or ``local_action`` is used in the playbook.
- Fix using ``module_defaults`` with ``local_action``/``action`` (https://github.com/ansible/ansible/issues/81905).
- fixed unit test test_borken_cowsay to address mock not been properly applied when existing unix system already have cowsay installed.
- powershell - Implement more robust deletion mechanism for C# code compilation temporary files. This should avoid scenarios where the underlying temporary directory may be temporarily locked by antivirus tools or other IO problems. A failure to delete one of these temporary directories will result in a warning rather than an outright failure.
- shell plugin - properly quote all needed components of shell commands (https://github.com/ansible/ansible/issues/82535)

v2.17.0
=======

Release Summary
---------------

| Release Date: 2024-05-20
| `Porting Guide <https://docs.ansible.com/ansible-core/2.17/porting_guides/porting_guide_core_2.17.html>`__

Major Changes
-------------

- urls.py - Removed support for Python 2

Minor Changes
-------------

- Add ``dump`` and ``passno`` mount information to facts component (https://github.com/ansible/ansible/issues/80478)
- Added MIRACLE LINUX 9.2 in RedHat OS Family.
- Interpreter Discovery - Remove hardcoded references to specific python interpreters to use for certain distro versions, and modify logic for python3 to become the default.
- Use Python's built-in ``functools.update_wrapper`` instead an inline copy from Python 3.7.
- User can now set ansible.log to record higher verbosity than what is specified for display via new configuration item LOG_VERBOSITY.
- ``DEFAULT_PRIVATE_ROLE_VARS`` is now overridden by explicit setting of ``public`` for ``include_roles`` and ``import_roles``.
- ``ansible-galaxy role|collection init`` - accept ``--extra-vars`` to supplement/override the variables ``ansible-galaxy`` injects for templating ``.j2`` files in the skeleton.
- ``import_role`` action now also gets a ``public`` option that controls variable exports,  default depending on ``DEFAULT_PRIVATE_ROLE_VARS`` (if using defaults equates to ``public=True``).
- added configuration item ``TARGET_LOG_INFO`` that allows the user/author to add an information string to the log output on targets.
- ansible-doc - treat double newlines in documentation strings as paragraph breaks. This is useful to create multi-paragraph notes in module/plugin documentation (https://github.com/ansible/ansible/pull/82465).
- ansible-doc output has been revamped to make it more visually pleasing when going to a terminal, also more concise, use -v to show extra information.
- ansible-galaxy - Started normalizing build directory with a trailing separator when building collections, internally. (https://github.com/ansible/ansible/pull/81619).
- ansible-galaxy dependency resolution messages have changed the unexplained 'virtual' collection for the specific type ('scm', 'dir', etc) that is more user friendly
- ansible-test - Add Alpine 3.19 container.
- ansible-test - Add Alpine 3.19 to remotes.
- ansible-test - Add Fedora 39 container.
- ansible-test - Add Fedora 39 remote.
- ansible-test - Add a work-around for permission denied errors when using ``pytest >= 8`` on multi-user systems with an installed version of ``ansible-test``.
- ansible-test - Add support for RHEL 9.3 remotes.
- ansible-test - Added a macOS 14.3 remote VM.
- ansible-test - Bump the ``nios-test-container`` from version 2.0.0 to version 3.0.0.
- ansible-test - Containers and remotes managed by ansible-test will have their Python ``EXTERNALLY-MANAGED`` marker (PEP668) removed. This provides backwards compatibility for existing tests running in newer environments which mark their Python as externally managed. A future version of ansible-test may change this behavior, requiring tests to be adapted to such environments.
- ansible-test - Make Python 3.12 the default version used in the ``base`` and ``default`` containers.
- ansible-test - Remove Alpine 3(.18) container.
- ansible-test - Remove Alpine 3.18 from remotes.
- ansible-test - Remove Fedora 38 remote support.
- ansible-test - Remove Fedora 38 test container.
- ansible-test - Remove rhel/9.2 test remote
- ansible-test - Remove the FreeBSD 13.2 remote.
- ansible-test - Removed fallback to ``virtualenv`` when ``-m venv`` is non-functional.
- ansible-test - Removed test remotes: macos/13.2
- ansible-test - Removed the ``no-basestring`` sanity test. The test is no longer necessary now that Python 3 is required.
- ansible-test - Removed the ``no-dict-iteritems``, ``no-dict-iterkeys`` and ``no-dict-itervalues`` sanity tests. The tests are no longer necessary since Python 3 is required.
- ansible-test - Removed the ``no-main-display`` sanity test. The unwanted pattern is unlikely to occur, since the test has existed since Ansible 2.8.
- ansible-test - Removed the ``no-unicode-literals`` sanity test. The test is unnecessary now that Python 3 is required and the ``unicode_literals`` feature has no effect.
- ansible-test - Special handling for installation of ``cryptography`` has been removed, as it is no longer necessary.
- ansible-test - The ``shellcheck`` sanity test no longer disables the ``SC2164`` check. In most cases, seeing this error means the script is missing ``set -e``.
- ansible-test - The ``unidiomatic-typecheck`` rule has been enabled in the ``pylint`` sanity test.
- ansible-test - The ``unidiomatic-typecheck`` rule has been removed from the ``validate-modules`` sanity test.
- ansible-test - Update the base and default containers to use Ubuntu 22.04 for the base image. This also updates PowerShell to version 7.4.0 with .NET 8.0.0 and ShellCheck to version 0.8.0.
- ansible-test - Updated the CloudStack test container to version 1.7.0.
- ansible-test - Updated the distro test containers to version 6.3.0 to include coverage 7.3.2 for Python 3.8+. The alpine3 container is now based on 3.18 instead of 3.17 and includes Python 3.11 instead of Python 3.10.
- ansible-test - Updated the distro test containers to version 7.1.0.
- ansible-test - When ansible-test installs requirements, it now instructs pip to allow installs on externally managed environments as defined by PEP 668. This only occurs in ephemeral environments managed by ansible-test, such as containers, or when the `--requirements` option is used.
- ansible-test - When invoking ``sleep`` in containers during container setup, the ``env`` command is used to avoid invoking the shell builtin, if present.
- ansible-test - document block name now included in error message for YAML parsing errors (https://github.com/ansible/ansible/issues/82353).
- ansible-test - sanity test allows ``EXAMPLES`` to be multi-document YAML (https://github.com/ansible/ansible/issues/82353).
- ansible-test now has FreeBSD 13.3 and 14.0 support
- ansible.builtin.user - Remove user not found warning (https://github.com/ansible/ansible/issues/80267)
- apt_repository.py - use api.launchpad.net endpoint instead of launchpad.net/api
- async tasks can now also support check mode at the same time.
- async_status now supports check mode.
- constructed inventory plugin - Adding a note that only group_vars of explicit groups are loaded (https://github.com/ansible/ansible/pull/82580).
- csvfile - add a keycol parameter to specify in which column to search.
- dnf - add the ``best`` option
- dnf5 - add the ``best`` option
- filter plugin - Add the count and mandatory_count parameters in the regex_replace filter
- find - add a encoding parameter to specify which encoding of the files to be searched.
- git module - gpg_allowlist name was added in 2.17 and we will eventually deprecate the gpg_whitelist alias.
- import_role - allow subdirectories with ``_from`` options for parity with ``include_role`` (https://github.com/ansible/ansible/issues/82584).
- module argument spec - Allow module authors to include arbitrary additional context in the argument spec, by making use of a new top level key called ``context``. This key should be a dict type. This allows for users to customize what they place in the argument spec, without having to ignore sanity tests that validate the schema.
- modules - Add the ability for an action plugin to call ``self._execute_module(*, ignore_unknown_opts=True)`` to execute a module with options that may not be supported for the version being called. This tells the module basic wrapper to ignore validating the options provided match the arg spec.
- package action now has a configuration that overrides the detected package manager, it is still overridden itself by the use option.
- py3compat - Remove ``ansible.utils.py3compat`` as it is no longer necessary
- removed the unused argument ``create_new_password`` from ``CLI.build_vault_ids`` (https://github.com/ansible/ansible/pull/82066).
- urls - Add support for TLS 1.3 post handshake certificate authentication - https://github.com/ansible/ansible/issues/81782
- urls - reduce complexity of ``Request.open``
- user - accept yescrypt hash as user password
- validate-modules tests now correctly handles ``choices`` in dictionary format.

Breaking Changes / Porting Guide
--------------------------------

- assert - Nested templating may result in an inability for the conditional to be evaluated. See the porting guide for more information.

Deprecated Features
-------------------

- Old style vars plugins which use the entrypoints `get_host_vars` or `get_group_vars` are deprecated. The plugin should be updated to inherit from `BaseVarsPlugin` and define a `get_vars` method as the entrypoint.
- The 'required' parameter in 'ansible.module_utils.common.process.get_bin_path' API is deprecated (https://github.com/ansible/ansible/issues/82464).
- ``module_utils`` - importing the following convenience helpers from ``ansible.module_utils.basic`` has been deprecated: ``get_exception``, ``literal_eval``, ``_literal_eval``, ``datetime``, ``signal``, ``types``, ``chain``, ``repeat``, ``PY2``, ``PY3``, ``b``, ``binary_type``, ``integer_types``, ``iteritems``, ``string_types``, ``test_type``, ``map`` and ``shlex_quote``.
- ansible-doc - role entrypoint attributes are deprecated and eventually will no longer be shown in ansible-doc from ansible-core 2.20 on (https://github.com/ansible/ansible/issues/82639, https://github.com/ansible/ansible/pull/82678).
- paramiko connection plugin, configuration items in the global scope are being deprecated and will be removed in favor or the existing same options in the plugin itself. Users should not need to change anything (how to configure them are the same) but plugin authors using the global constants should move to using the plugin's get_option().

Removed Features (previously deprecated)
----------------------------------------

- Remove deprecated APIs from ansible-docs (https://github.com/ansible/ansible/issues/81716).
- Remove deprecated JINJA2_NATIVE_WARNING environment variable (https://github.com/ansible/ansible/issues/81714)
- Remove deprecated ``scp_if_ssh`` from ssh connection plugin (https://github.com/ansible/ansible/issues/81715).
- Remove deprecated crypt support from ansible.utils.encrypt (https://github.com/ansible/ansible/issues/81717)
- Removed Python 2.7 and Python 3.6 as a supported remote version. Python 3.7+ is now required for target execution.
- With the removal of Python 2 support, the yum module and yum action plugin are removed and redirected to ``dnf``.

Security Fixes
--------------

- ANSIBLE_NO_LOG - Address issue where ANSIBLE_NO_LOG was ignored (CVE-2024-0690)
- ansible-galaxy - Prevent roles from using symlinks to overwrite files outside of the installation directory (CVE-2023-5115)
- templating - Address issues where internal templating can cause unsafe variables to lose their unsafe designation (CVE-2023-5764)

Bugfixes
--------

- Add a version ceiling constraint for pypsrp to avoid potential breaking changes in the 1.0.0 release.
- All core lookups now use set_option(s) even when doing their own custom parsing. This ensures that the options are always the proper type.
- Allow for searching handler subdir for included task via include_role (https://github.com/ansible/ansible/issues/81722)
- AnsibleModule.atomic_move - fix preserving extended ACLs of the destination when it exists (https://github.com/ansible/ansible/issues/72929).
- Cache host_group_vars after instantiating it once and limit the amount of repetitive work it needs to do every time it runs.
- Call PluginLoader.all() once for vars plugins, and load vars plugins that run automatically or are enabled specifically by name subsequently.
- Consolidate systemd detection logic into one place (https://github.com/ansible/ansible/issues/80975).
- Consolidated the list of internal static vars, centralized them as constant and completed from some missing entries.
- Do not print undefined error message twice (https://github.com/ansible/ansible/issues/78703).
- Enable file cache for vaulted files during vars lookup to fix a strong performance penalty in huge and complex playbboks.
- Fix NEVRA parsing of package names that include digit(s) in them (https://github.com/ansible/ansible/issues/76463, https://github.com/ansible/ansible/issues/81018)
- Fix ``force_handlers`` not working with ``any_errors_fatal`` (https://github.com/ansible/ansible/issues/36308)
- Fix ``run_once`` being incorrectly interpreted on handlers (https://github.com/ansible/ansible/issues/81666)
- Fix an issue when setting a plugin name from an unsafe source resulted in ``ValueError: unmarshallable object`` (https://github.com/ansible/ansible/issues/82708)
- Fix check for missing _sub_plugin attribute in older connection plugins (https://github.com/ansible/ansible/pull/82954)
- Fix condition for unquoting configuration strings from ini files (https://github.com/ansible/ansible/issues/82387).
- Fix for when ``any_errors_fatal`` was ignored if error occurred in a block with always (https://github.com/ansible/ansible/issues/31543)
- Fix handlers not being executed in lockstep using the linear strategy in some cases (https://github.com/ansible/ansible/issues/82307)
- Fix handling missing urls in ansible.module_utils.urls.fetch_file for Python 3.
- Fix issue where an ``include_tasks`` handler in a role was not able to locate a file in ``tasks/`` when ``tasks_from`` was used as a role entry point and ``main.yml`` was not present (https://github.com/ansible/ansible/issues/82241)
- Fix issues when tasks withing nested blocks wouldn't run when ``force_handlers`` is set (https://github.com/ansible/ansible/issues/81533)
- Fix loading vars_plugins in roles (https://github.com/ansible/ansible/issues/82239).
- Fix notifying role handlers by listen keyword topics with the "role_name : " prefix (https://github.com/ansible/ansible/issues/82849).
- Fix setting proper locale for git executable when running on non english systems, ensuring git output can always be parsed.
- Fix tasks in always section not being executed for nested blocks with ``any_errors_fatal`` (https://github.com/ansible/ansible/issues/73246)
- Fixes permission for cache json file from 600 to 644 (https://github.com/ansible/ansible/issues/82683).
- Give the tombstone error for ``include`` pre-fork like other tombstoned action/module plugins.
- Harden python templates for respawn and ansiballz around str literal quoting
- Include the task location when a module or action plugin is deprecated (https://github.com/ansible/ansible/issues/82450).
- Interpreter discovery - Add ``Amzn`` to ``OS_FAMILY_MAP`` for correct family fallback for interpreter discovery (https://github.com/ansible/ansible/issues/80882).
- Mirror the behavior of dnf on the command line when handling NEVRAs with omitted epoch (https://github.com/ansible/ansible/issues/71808)
- Plugin loader does not dedupe nor cache filter/test plugins by file basename, but full path name.
- Properly template tags in parent blocks (https://github.com/ansible/ansible/issues/81053)
- Provide additional information about the alternative plugin in the deprecation message (https://github.com/ansible/ansible/issues/80561).
- Remove the galaxy_info field ``platforms`` from the role templates (https://github.com/ansible/ansible/issues/82453).
- Restoring the ability of filters/tests can have same file base name but different tests/filters defined inside.
- Reword the error message when the module fails to parse parameters in JSON format (https://github.com/ansible/ansible/issues/81188).
- Reword warning if the reserved keyword _ansible_ used as a module parameter (https://github.com/ansible/ansible/issues/82514).
- Run all handlers with the same ``listen`` topic, even when notified from another handler (https://github.com/ansible/ansible/issues/82363).
- Slight optimization to hostvars (instantiate template only once per host, vs per call to var).
- Stopped misleadingly advertising ``async`` mode support in the ``reboot`` module (https://github.com/ansible/ansible/issues/71517).
- ``ansible-galaxy role import`` - fix using the ``role_name`` in a standalone role's ``galaxy_info`` metadata by disabling automatic removal of the ``ansible-role-`` prefix. This matches the behavior of the Galaxy UI which also no longer implicitly removes the ``ansible-role-`` prefix. Use the ``--role-name`` option or add a ``role_name`` to the ``galaxy_info`` dictionary in the role's ``meta/main.yml`` to use an alternate role name.
- ``ansible-test sanity --test runtime-metadata`` - add ``action_plugin`` as a valid field for modules in the schema (https://github.com/ansible/ansible/pull/82562).
- ``ansible.module_utils.service`` - ensure binary data transmission in ``daemonize()``
- ``any_errors_fatal`` should fail all hosts and rescue all of them when a ``rescue`` section is specified (https://github.com/ansible/ansible/issues/80981)
- ``include_role`` - properly execute ``v2_playbook_on_include`` and ``v2_runner_on_failed`` callbacks as well as increase ``ok`` and ``failed`` stats in the play recap, when appropriate (https://github.com/ansible/ansible/issues/77336)
- allow_duplicates - fix evaluating if the current role allows duplicates instead of using the initial value from the duplicate's cached role.
- ansible-config init will now dedupe ini entries from plugins.
- ansible-config will now properly template defaults before dumping them.
- ansible-doc - fixed "inicates" typo in output
- ansible-doc - format top-level descriptions with multiple paragraphs as multiple paragraphs, instead of concatenating them (https://github.com/ansible/ansible/pull/83155).
- ansible-galaxy - Deprecate use of the Galaxy v2 API (https://github.com/ansible/ansible/issues/81781)
- ansible-galaxy - Provide a better error message when using a requirements file with an invalid format - https://github.com/ansible/ansible/issues/81901
- ansible-galaxy - Resolve issue with the dataclass used for galaxy.yml manifest caused by using future annotations
- ansible-galaxy - ensure path to ansible collection when installing or downloading doesn't have a backslash (https://github.com/ansible/ansible/pull/79705).
- ansible-galaxy - started allowing the use of pre-releases for collections that do not have any stable versions published. (https://github.com/ansible/ansible/pull/81606)
- ansible-galaxy - started allowing the use of pre-releases for dependencies on any level of the dependency tree that specifically demand exact pre-release versions of collections and not version ranges. (https://github.com/ansible/ansible/pull/81606)
- ansible-galaxy error on dependency resolution will not error itself due to 'virtual' collections not having a name/namespace.
- ansible-galaxy info - fix reporting no role found when lookup_role_by_name returns None.
- ansible-galaxy role import - exit with 1 when the import fails (https://github.com/ansible/ansible/issues/82175).
- ansible-galaxy role install - fix installing roles from Galaxy that have version ``None`` (https://github.com/ansible/ansible/issues/81832).
- ansible-galaxy role install - fix symlinks (https://github.com/ansible/ansible/issues/82702, https://github.com/ansible/ansible/issues/81965).
- ansible-galaxy role install - normalize tarfile paths and symlinks using ``ansible.utils.path.unfrackpath`` and consider them valid as long as the realpath is in the tarfile's role directory (https://github.com/ansible/ansible/issues/81965).
- ansible-inventory - index available_hosts for major performance boost when dumping large inventories
- ansible-pull now will expand relative paths for the ``-d|--directory`` option is now expanded before use.
- ansible-pull will now correctly handle become and connection password file options for ansible-playbook.
- ansible-test - Add a ``pylint`` plugin to work around a known issue on Python 3.12.
- ansible-test - Explicitly supply ``ControlPath=none`` when setting up port forwarding over SSH to address the scenario where the local ssh configuration uses ``ControlPath`` for all hosts, and would prevent ports to be forwarded after the initial connection to the host.
- ansible-test - Fix parsing of cgroup entries which contain a ``:`` in the path (https://github.com/ansible/ansible/issues/81977).
- ansible-test - Include missing ``pylint`` requirements for Python 3.10.
- ansible-test - Properly detect docker host when using ``ssh://`` protocol for connecting to the docker daemon.
- ansible-test - The ``libexpat`` package is automatically upgraded during remote bootstrapping to maintain compatibility with newer Python packages.
- ansible-test - The ``validate-modules`` sanity test no longer attempts to process files with unrecognized extensions as Python (resolves https://github.com/ansible/ansible/issues/82604).
- ansible-test - Update ``pylint`` to version 3.0.1.
- ansible-test ansible-doc sanity test - do not remove underscores from plugin names in collections before calling ``ansible-doc`` (https://github.com/ansible/ansible/pull/82574).
- ansible-test validate-modules sanity test - do not treat leading underscores for plugin names in collections as an attempted deprecation (https://github.com/ansible/ansible/pull/82575).
- ansible-test — Python 3.8–3.12 will use ``coverage`` v7.3.2.
- ansible.builtin.apt - calling clean = true does not properly clean certain cache files such as /var/cache/apt/pkgcache.bin and /var/cache/apt/pkgcache.bin (https://github.com/ansible/ansible/issues/82611)
- ansible.builtin.uri - the module was ignoring the ``force`` parameter and always requesting a cached copy (via the ``If-Modified-Since`` header) when downloading to an existing local file. Disable caching when ``force`` is ``true``, as documented (https://github.com/ansible/ansible/issues/82166).
- ansible_managed restored it's 'templatability' by ensuring the possible injection routes are cut off earlier in the process.
- apt - honor install_recommends and dpkg_options while installing python3-apt library (https://github.com/ansible/ansible/issues/40608).
- apt - install recommended packages when installing package via deb file (https://github.com/ansible/ansible/issues/29726).
- apt_repository - do not modify repo files if the file is a symlink (https://github.com/ansible/ansible/issues/49809).
- apt_repository - update PPA URL to point to https URL (https://github.com/ansible/ansible/issues/82463).
- assemble - fixed missing parameter 'content' in _get_diff_data API (https://github.com/ansible/ansible/issues/82359).
- async - Fix bug that stopped running async task in ``--check`` when ``check_mode: False`` was set as a task attribute - https://github.com/ansible/ansible/issues/82811
- blockinfile - when ``create=true`` is used with a filename without path, the module crashed (https://github.com/ansible/ansible/pull/81638).
- check if there are attributes to set before attempting to set them (https://github.com/ansible/ansible/issues/76727)
- copy action now also generates temprary files as hidden ('.' prefixed) to avoid accidental pickup by running services that glob by extension.
- copy action now ensures that tempfiles use the same suffix as destination, to allow for ``validate`` to work with utilities that check extensions.
- deb822_repository - handle idempotency if the order of parameters is changed (https://github.com/ansible/ansible/issues/82454).
- debconf - allow user to specify a list for value when vtype is multiselect (https://github.com/ansible/ansible/issues/81345).
- delegate_to when set to an empty or undefined variable will now give a proper error.
- distribution.py - Recognize ALP-Dolomite as part of the SUSE OS family in Ansible, fixing its previous misidentification (https://github.com/ansible/ansible/pull/82496).
- distro - bump bundled distro version from 1.6.0 to 1.8.0 (https://github.com/ansible/ansible/issues/81713).
- dnf - fix an issue when cached RPMs were left in the cache directory even when the keepcache setting was unset (https://github.com/ansible/ansible/issues/81954)
- dnf - fix an issue when installing a package by specifying a file it provides could result in installing a different package providing the same file than the package already installed resulting in resolution failure (https://github.com/ansible/ansible/issues/82461)
- dnf - properly set gpg check options on enabled repositories according to the ``disable_gpg_check`` option (https://github.com/ansible/ansible/issues/80110)
- dnf - properly skip unavailable packages when ``skip_broken`` is enabled (https://github.com/ansible/ansible/issues/80590)
- dnf - the ``nobest`` option only overrides the distribution default when explicitly used, and is used for all supported operations (https://github.com/ansible/ansible/issues/82616)
- dnf5 - replace removed API calls
- dnf5 - respect ``allow_downgrade`` when installing packages directly from rpm files
- dnf5 - the ``nobest`` option only overrides the distribution default when used
- dwim functions for lookups should be better at detectging role context even in abscense of tasks/main.
- ensure we have logger before we log when we have increased verbosity.
- expect - fix argument spec error using timeout=null (https://github.com/ansible/ansible/issues/80982).
- fact gathering on linux now handles thread count by using rounding vs dropping decimals, it should give slightly more accurate numbers.
- facts - add a generic detection for VMware in product name.
- facts - detect VMware ESXi 8.0 virtualization by product name VMware20,1
- fetch - Do not calculate the file size for Windows fetch targets to improve performance.
- fetch - add error message when using ``dest`` with a trailing slash that becomes a local directory - https://github.com/ansible/ansible/issues/82878
- find - do not fail on Permission errors (https://github.com/ansible/ansible/issues/82027).
- first_found lookup now always returns a full (absolute) and normalized path
- first_found lookup now always takes into account k=v options
- flush_handlers - properly handle a handler failure in a nested block when ``force_handlers`` is set (http://github.com/ansible/ansible/issues/81532)
- galaxy - skip verification for unwanted Python compiled bytecode files (https://github.com/ansible/ansible/issues/81628).
- handle exception raised while validating with elements='int' and value is not within choices (https://github.com/ansible/ansible/issues/82776).
- include_tasks - include `ansible_loop_var` and `ansible_index_var` in a loop (https://github.com/ansible/ansible/issues/82655).
- include_vars - fix calculating ``depth`` relative to the root and ensure all files are included (https://github.com/ansible/ansible/issues/80987).
- interpreter_discovery - handle AnsibleError exception raised while interpreter discovery (https://github.com/ansible/ansible/issues/78264).
- iptables - add option choices 'src,src' and 'dst,dst' in match_set_flags (https://github.com/ansible/ansible/issues/81281).
- iptables - set jump to DSCP when set_dscp_mark or set_dscp_mark_class is set (https://github.com/ansible/ansible/issues/77077).
- known_hosts - Fix issue with `@cert-authority` entries in known_hosts incorrectly being removed.
- module no_log will no longer affect top level booleans, for example ``no_log_module_parameter='a'`` will no longer hide ``changed=False`` as a 'no log value' (matches 'a').
- moved assemble, raw, copy, fetch, reboot, script and wait_for_connection to query task instead of play_context ensuring they get the lastest and most correct data.
- reboot action now handles connections with 'timeout' vs only 'connection_timeout' settings.
- role params now have higher precedence than host facts again, matching documentation, this had unintentionally changed in 2.15.
- roles, code cleanup and performance optimization of dependencies, now cached,  and ``public`` setting is now determined once, at role instantiation.
- roles, the ``static`` property is now correctly set, this will fix issues with ``public`` and ``DEFAULT_PRIVATE_ROLE_VARS`` controls on exporting vars.
- set_option method for plugins to update config now properly passes through type casting and validation.
- ssh - add tests for the SSH connection plugin.
- support url-encoded credentials in URLs like http://x%40:%40@example.com (https://github.com/ansible/ansible/pull/82552)
- syslog - Handle ValueError exception raised when sending Null Characters to syslog with Python 3.12.
- systemd_services - update documentation regarding required_one_of and required_by parameters (https://github.com/ansible/ansible/issues/82914).
- template - Fix error when templating an unsafe string which corresponds to an invalid type in Python (https://github.com/ansible/ansible/issues/82600).
- template action will also inherit the behavior from copy (as it uses it internally).
- templating - ensure syntax errors originating from a template being compiled into Python code object result in a failure (https://github.com/ansible/ansible/issues/82606)
- unarchive - add support for 8 character permission strings for zip archives (https://github.com/ansible/ansible/pull/81705).
- unarchive - force unarchive if symlink target changes (https://github.com/ansible/ansible/issues/30420).
- unarchive modules now uses zipinfo options without relying on implementation defaults, making it more compatible with all OS/distributions.
- unsafe data - Address an incompatibility when iterating or getting a single index from ``AnsibleUnsafeBytes``
- unsafe data - Address an incompatibility with ``AnsibleUnsafeText`` and ``AnsibleUnsafeBytes`` when pickling with ``protocol=0``
- unsafe data - Enable directly using ``AnsibleUnsafeText`` with Python ``pathlib`` (https://github.com/ansible/ansible/issues/82414)
- uri - update the documentation for follow_redirects.
- uri action plugin now skipped during check mode (not supported) instead of even trying to execute the module, which already skipped, this does not really change the result, but returns much faster.
- vars - handle exception while combining VarsWithSources and dict (https://github.com/ansible/ansible/issues/81659).
- wait_for should not handle 'non mmapable files' again.
- winrm - Better handle send input failures when communicating with hosts under load
- winrm - Do not raise another exception during cleanup when a task is timed out - https://github.com/ansible/ansible/issues/81095
- winrm - does not hang when attempting to get process output when stdin write failed
