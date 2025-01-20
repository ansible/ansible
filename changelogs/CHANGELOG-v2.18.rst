==================================================
ansible-core 2.18 "Fool in the Rain" Release Notes
==================================================

.. contents:: Topics

v2.18.2rc1
==========

Release Summary
---------------

| Release Date: 2025-01-20
| `Porting Guide <https://docs.ansible.com/ansible-core/2.18/porting_guides/porting_guide_core_2.18.html>`__

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
- ssh - Improve the logic for parsing CLIXML data in stderr when working with Windows host. This fixes issues when the raw stderr contains invalid UTF-8 byte sequences and improves embedded CLIXML sequences.
- ssh - connection options were incorrectly templated during ``reset_connection`` tasks (https://github.com/ansible/ansible/pull/84238).

v2.18.1
=======

Release Summary
---------------

| Release Date: 2024-12-02
| `Porting Guide <https://docs.ansible.com/ansible-core/2.18/porting_guides/porting_guide_core_2.18.html>`__

Minor Changes
-------------

- ansible-test - When detection of the current container network fails, a warning is now issued and execution continues. This simplifies usage in cases where the current container cannot be inspected, such as when running in GitHub Codespaces.

Security Fixes
--------------

- Templating will not prefer AnsibleUnsafe when a variable is referenced via hostvars - CVE-2024-11079

Bugfixes
--------

- Fix returning 'unreachable' for the overall task result. This prevents false positives when a looped task has unignored unreachable items (https://github.com/ansible/ansible/issues/84019).
- ansible-test - Fix traceback that occurs after an interactive command fails.
- dnf5 - fix installing a package using ``state=latest`` when a binary of the same name as the package is already installed (https://github.com/ansible/ansible/issues/84259)
- dnf5 - matching on a binary can be achieved only by specifying a full path (https://github.com/ansible/ansible/issues/84334)
- runas become - Fix up become logic to still get the SYSTEM token with the most privileges when running as SYSTEM.

v2.18.0
=======

Release Summary
---------------

| Release Date: 2024-11-04
| `Porting Guide <https://docs.ansible.com/ansible-core/2.18/porting_guides/porting_guide_core_2.18.html>`__

Minor Changes
-------------

- Add ``gid_min``, ``gid_max`` to the group plugin to overwrite the defaults provided by the ``/etc/login.defs`` file (https://github.com/ansible/ansible/pull/81770).
- Add ``python3.13`` to the default ``INTERPRETER_PYTHON_FALLBACK`` list.
- Add ``uid_min``, ``uid_max`` to the user plugin to overwrite the defaults provided by the ``/etc/login.defs`` file (https://github.com/ansible/ansible/pull/81770).
- Add a new meta task ``end_role`` (https://github.com/ansible/ansible/issues/22286)
- Add a new mount_facts module to support gathering information about mounts that are excluded by default fact gathering.
- Introducing COLOR_INCLUDED parameter. This can set a specific color for "included" events.
- Removed the shell ``environment`` config entry as this is already covered by the play/task directives documentation and the value itself is not used in the shell plugins. This should remove any confusion around how people set the environment for a task.
- Suppress cryptography deprecation warnings for Blowfish and TripleDES when the ``paramiko`` Python module is installed.
- The minimum supported Python version on targets is now Python 3.8.
- ``ansible-galaxy collection publish`` - add configuration options for the initial poll interval and the exponential when checking the import status of a collection, since the default is relatively slow.
- ansible-config has new 'validate' option to find mispelled/forgein configurations in ini file or environment variables.
- ansible-doc - show examples in role entrypoint argument specs (https://github.com/ansible/ansible/pull/82671).
- ansible-galaxy - Handle authentication errors and token expiration
- ansible-test - Add Ubuntu 24.04 remote.
- ansible-test - Add support for Python 3.13.
- ansible-test - An ``ansible_core.egg-info`` directory is no longer generated when running tests.
- ansible-test - Connection options can be set for ansible-test managed remote Windows instances.
- ansible-test - Default to Python 3.13 in the ``base`` and ``default`` containers.
- ansible-test - Disable the ``deprecated-`` prefixed ``pylint`` rules as their results vary by Python version.
- ansible-test - Improve container runtime probe error handling. When unexpected probe output is encountered, an error with more useful debugging information is provided.
- ansible-test - Improve the error message shown when an unknown ``--remote`` or ``--docker`` option is given.
- ansible-test - Remove Python 2.7 compatibility imports.
- ansible-test - Removed the ``vyos/1.1.8`` network remote as it is no longer functional.
- ansible-test - Replace Alpine 3.19 container and remote with Alpine 3.20.
- ansible-test - Replace Fedora 39 container and remote with Fedora 40.
- ansible-test - Replace FreeBSD 14.0 remote with FreeBSD 14.1.
- ansible-test - Replace RHEL 9.3 remote with RHEL 9.4.
- ansible-test - Replace Ubuntu 20.04 container with Ubuntu 24.04 container.
- ansible-test - The ``empty-init`` sanity test no longer applies to ``module_utils`` packages.
- ansible-test - Update ``ansible-test-utility-container`` to version 3.1.0.
- ansible-test - Update ``base`` and ``default`` containers to omit Python 3.7.
- ansible-test - Update ``coverage`` to version 7.6.1.
- ansible-test - Update ``http-test-container`` to version 3.0.0.
- ansible-test - Update ``nios-test-container`` to version 5.0.0.
- ansible-test - Update ``pylint`` sanity test to use version 3.3.1.
- ansible-test - Update ``pypi-test-container`` to version 3.2.0.
- ansible-test - Update the ``base`` and ``default`` containers.
- ansible-test - Updated the frozen requirements for all sanity tests.
- ansible-test - Upgrade ``pip`` used in ansible-test managed virtual environments from version 24.0 to 24.2.
- ansible-test - Virtual environments created by ansible-test no longer include the ``wheel`` or ``setuptools`` packages.
- ansible-test - update HTTP test container to 3.2.0 (https://github.com/ansible/ansible/pull/83469).
- ansible.log now also shows log severity field
- distribution.py - Added SL-Micro in Suse OS Family. (https://github.com/ansible/ansible/pull/83541)
- dnf - minor internal changes in how the errors from the dnf API are handled; rely solely on the exceptions rather than inspecting text embedded in them
- dnf - remove legacy code for unsupported dnf versions
- dnf5 - implement ``enable_plugin`` and ``disable_plugin`` options
- fact gathering - Gather /proc/sysinfo facts on s390 Linux on Z
- facts - add systemd version and features
- find - change the datatype of ``elements`` to ``path`` in option ``paths`` (https://github.com/ansible/ansible/pull/83575).
- ini lookup - add new ``interpolation`` option (https://github.com/ansible/ansible/issues/83755)
- isidentifier - remove unwanted Python 2 specific code.
- loop_control - add a break_when option to to break out of a task loop early based on Jinja2 expressions (https://github.com/ansible/ansible/issues/83442).
- package_facts module now supports using aliases for supported package managers, for example managers=yum or managers=dnf will resolve to using the underlying rpm.
- plugins, deprecations and warnings concerning configuration are now displayed to the user, technical issue that prevented 'de-duplication' have been resolved.
- psrp - Remove connection plugin extras vars lookup. This should have no affect on existing users as all options have been documented.
- remove extraneous selinux import (https://github.com/ansible/ansible/issues/83657).
- replace random with secrets library.
- rpm_key - allow validation of gpg key with a subkey fingerprint
- rpm_key - enable gpg validation that requires presence of multiple fingerprints
- service_mgr - add support for dinit service manager (https://github.com/ansible/ansible/pull/83489).
- task timeout now returns timedout key with frame/code that was in execution when the timeout is triggered.
- timedout test for checking if a task result represents a 'timed out' task.
- unarchive - Remove Python 2.7 compatibility imports.
- validate-modules sanity test - detect if names of an option (option name + aliases) do not match between argument spec and documentation (https://github.com/ansible/ansible/issues/83598, https://github.com/ansible/ansible/pull/83599).
- validate-modules sanity test - reject option/aliases names that are identical up to casing but belong to different options (https://github.com/ansible/ansible/pull/83530).
- vaulted_file test filter added, to test if the provided path is an 'Ansible vaulted' file
- yum_repository - add ``excludepkgs`` alias to the ``exclude`` option.

Breaking Changes / Porting Guide
--------------------------------

- Stopped wrapping all commands sent over SSH on a Windows target with a ``powershell.exe`` executable. This results in one less process being started on each command for Windows to improve efficiency, simplify the code, and make ``raw`` an actual raw command run with the default shell configured on the Windows sshd settings. This should have no affect on most tasks except for ``raw`` which now is not guaranteed to always be running in a PowerShell shell and from having the console output codepage set to UTF-8. To avoid this issue either swap to using ``ansible.windows.win_command``, ``ansible.windows.win_shell``, ``ansible.windows.win_powershell`` or manually wrap the raw command with the shell commands needed to set the output console encoding.
- persistent connection plugins - The ``ANSIBLE_CONNECTION_PATH`` config option no longer has any effect.

Deprecated Features
-------------------

- Deprecate ``ansible.module_utils.basic.AnsibleModule.safe_eval`` and ``ansible.module_utils.common.safe_eval`` as they are no longer used.
- persistent connection plugins - The ``ANSIBLE_CONNECTION_PATH`` config option no longer has any effect, and will be removed in a future release.
- yum_repository - deprecate ``async`` option as it has been removed in RHEL 8 and will be removed in ansible-core 2.22.
- yum_repository - the following options are deprecated: ``deltarpm_metadata_percentage``, ``gpgcakey``, ``http_caching``, ``keepalive``, ``metadata_expire_filter``, ``mirrorlist_expire``, ``protect``, ``ssl_check_cert_permissions``, ``ui_repoid_vars`` as they have no effect for dnf as an underlying package manager. The options will be removed in ansible-core 2.22.

Removed Features (previously deprecated)
----------------------------------------

- Play - removed deprecated ``ROLE_CACHE`` property in favor of ``role_cache``.
- Remove deprecated `VariableManager._get_delegated_vars` method (https://github.com/ansible/ansible/issues/82950)
- Removed Python 3.10 as a supported version on the controller. Python 3.11 or newer is required.
- Removed support for setting the ``vars`` keyword to lists of dictionaries. It is now required to be a single dictionary.
- loader - remove deprecated non-inclusive words (https://github.com/ansible/ansible/issues/82947).
- paramiko_ssh - removed deprecated ssh_args from the paramiko_ssh connection plugin (https://github.com/ansible/ansible/issues/82939).
- paramiko_ssh - removed deprecated ssh_common_args from the paramiko_ssh connection plugin (https://github.com/ansible/ansible/issues/82940).
- paramiko_ssh - removed deprecated ssh_extra_args from the paramiko_ssh connection plugin (https://github.com/ansible/ansible/issues/82941).
- play_context - remove deprecated PlayContext.verbosity property (https://github.com/ansible/ansible/issues/82945).
- utils/listify - remove deprecated 'loader' argument from listify_lookup_plugin_terms API (https://github.com/ansible/ansible/issues/82949).

Security Fixes
--------------

- include_vars action - Ensure that result masking is correctly requested when vault-encrypted files are read. (CVE-2024-8775)
- task result processing - Ensure that action-sourced result masking (``_ansible_no_log=True``) is preserved. (CVE-2024-8775)
- user action won't allow ssh-keygen, chown and chmod to run on existing ssh public key file, avoiding traversal on existing symlinks (CVE-2024-9902).

Bugfixes
--------

- -> runas become - Generate new token for the SYSTEM token to use for become. This should result in the full SYSTEM token being used and problems starting the process that fails with ``The process creation has been blocked``.
- Add a version ceiling constraint for pypsrp to avoid potential breaking changes in the 1.0.0 release.
- Add descriptions for ``ansible-galaxy install --help` and ``ansible-galaxy role|collection install --help``.
- Avoid truncating floats when casting into int, as it can lead to truncation and unexpected results. 0.99999 will be 0, not 1.
- COLOR_SKIP will not alter "included" events color display anymore.
- Callbacks now correctly get the resolved connection plugin name as the connection used.
- Darwin - add unit tests for Darwin hardware fact gathering.
- Errors now preserve stacked error messages even when YAML is involved.
- Fix ``SemanticVersion.parse()`` to store the version string so that ``__repr__`` reports it instead of ``None`` (https://github.com/ansible/ansible/pull/83831).
- Fix a traceback when an environment variable contains certain special characters (https://github.com/ansible/ansible/issues/83498)
- Fix an issue when setting a plugin name from an unsafe source resulted in ``ValueError: unmarshallable object`` (https://github.com/ansible/ansible/issues/82708)
- Fix an issue where registered variable was not available for templating in ``loop_control.label`` on skipped looped tasks (https://github.com/ansible/ansible/issues/83619)
- Fix disabling SSL verification when installing collections and roles from git repositories. If ``--ignore-certs`` isn't provided, the value for the ``GALAXY_IGNORE_CERTS`` configuration option will be used (https://github.com/ansible/ansible/issues/83326).
- Fix for ``meta`` tasks breaking host/fork affinity with ``host_pinned`` strategy (https://github.com/ansible/ansible/issues/83294)
- Fix handlers not being executed in lockstep using the linear strategy in some cases (https://github.com/ansible/ansible/issues/82307)
- Fix rapid memory usage growth when notifying handlers using the ``listen`` keyword (https://github.com/ansible/ansible/issues/83392)
- Fix the task attribute ``resolved_action`` to show the FQCN instead of ``None`` when ``action`` or ``local_action`` is used in the playbook.
- Fix using ``module_defaults`` with ``local_action``/``action`` (https://github.com/ansible/ansible/issues/81905).
- Fix using the current task's directory for looking up relative paths within roles (https://github.com/ansible/ansible/issues/82695).
- Improve performance on large inventories by reducing the number of implicit meta tasks.
- Remove deprecated config options DEFAULT_FACT_PATH, DEFAULT_GATHER_SUBSET, and DEFAULT_GATHER_TIMEOUT in favor of setting ``fact_path``, ``gather_subset`` and ``gather_timeout`` as ``module_defaults`` for ``ansible.builtin.setup``.
  These will apply to both the ``gather_facts`` play keyword, and any ``ansible.builtin.setup`` tasks.
  To configure these options only for the ``gather_facts`` keyword, set these options as play keywords also.
- Set LANGUAGE environment variable is set to a non-English locale (https://github.com/ansible/ansible/issues/83608).
- Use the requested error message in the ansible.module_utils.facts.timeout timeout function instead of hardcoding one.
- ``ansible-galaxy install --help`` - Fix the usage text and document that the requirements file passed to ``-r`` can include collections and roles.
- ``ansible-galaxy role install`` - update the default timeout to download archive URLs from 20 seconds to 60 (https://github.com/ansible/ansible/issues/83521).
- ``end_host`` - fix incorrect return code when executing ``end_host`` in the ``rescue`` section (https://github.com/ansible/ansible/issues/83447)
- ``package``/``dnf`` action plugins - provide the reason behind the failure to gather the ``ansible_pkg_mgr`` fact to identify the package backend
- addressed issue of trailing text been ignored, non-ASCII characters are parsed, enhance white space handling and fixed overly permissive issue of human_to_bytes filter(https://github.com/ansible/ansible/issues/82075)
- ansible-config will now properly template defaults before dumping them.
- ansible-doc - fixed "inicates" typo in output
- ansible-doc - format top-level descriptions with multiple paragraphs as multiple paragraphs, instead of concatenating them (https://github.com/ansible/ansible/pull/83155).
- ansible-doc - handle no_fail condition for role.
- ansible-doc - make colors configurable.
- ansible-galaxy collection install - remove old installation info when installing collections (https://github.com/ansible/ansible/issues/83182).
- ansible-galaxy role install - fix symlinks (https://github.com/ansible/ansible/issues/82702, https://github.com/ansible/ansible/issues/81965).
- ansible-test - Enable the ``sys.unraisablehook`` work-around for the ``pylint`` sanity test on Python 3.11. Previously the work-around was only enabled for Python 3.12 and later. However, the same issue has been discovered on Python 3.11.
- ansible-test - The ``pylint`` sanity test now includes the controller/target context of files when grouping them. This allows the ``--py-version`` option to be passed to ``pylint`` to indicate the minimum supported Python version for each test context, preventing ``pylint`` from defaulting to the Python version used to invoke the test.
- ansible-test action-plugin-docs - Fix to check for sidecar documentation for action plugins
- ansible_managed restored it's 'templatability' by ensuring the possible injection routes are cut off earlier in the process.
- apt - report changed=True when some packages are being removed (https://github.com/ansible/ansible/issues/46314).
- apt_* - add more info messages raised while updating apt cache (https://github.com/ansible/ansible/issues/77941).
- assemble - update argument_spec with 'decrypt' option which is required by action plugin (https://github.com/ansible/ansible/issues/80840).
- atomic_move - fix using the setgid bit on the parent directory when creating files (https://github.com/ansible/ansible/issues/46742, https://github.com/ansible/ansible/issues/67177).
- config, restored the ability to set module compression via a variable
- connection plugins using the 'extras' option feature would need variables to match the plugin's loaded name, sometimes requiring fqcn, which is not the same as the documented/declared/expected variables. Now we fall back to the 'basename' of the fqcn, but plugin authors can still set the expected value directly.
- copy - mtime/atime not updated. Fix now update mtime/atime(https://github.com/ansible/ansible/issues/83013)
- csvfile lookup - give an error when no search term is provided using modern config syntax (https://github.com/ansible/ansible/issues/83689).
- debconf - fix normalization of value representation for boolean vtypes in new packages (https://github.com/ansible/ansible/issues/83594)
- debconf - set empty password values (https://github.com/ansible/ansible/issues/83214).
- delay keyword is now a float, matching the underlying 'time' API and user expectations.
- display - warn user about empty log filepath (https://github.com/ansible/ansible/issues/79959).
- display now does a better job of mapping warnings/errors to the proper log severity when using ansible.log. We still use color as a fallback mapping (now prioritiezed by severity) but mostly rely on it beind directly set by warnning/errors calls.
- distro package - update the distro package version from 1.8.0 to 1.9.0  (https://github.com/ansible/ansible/issues/82935)
- dnf - Ensure that we are handling DownloadError properly in the dnf module
- dnf - Substitute variables in DNF cache path (https://github.com/ansible/ansible/pull/80094).
- dnf - fix an issue where two packages of the same ``evr`` but different arch failed to install (https://github.com/ansible/ansible/issues/83406)
- dnf - honor installroot for ``cachedir``, ``logdir`` and ``persistdir``
- dnf - perform variable substitutions in ``logdir`` and ``persistdir``
- dnf, dnf5 - fix for installing a set of packages by specifying them using a wildcard character (https://github.com/ansible/ansible/issues/83373)
- dnf5 - fix traceback when ``enable_plugins``/``disable_plugins`` is used on ``python3-libdnf5`` versions that do not support this functionality
- dnf5 - re-introduce the ``state: installed`` alias to ``state: present`` (https://github.com/ansible/ansible/issues/83960)
- dnf5 - replace removed API calls
- ensure we have logger before we log when we have increased verbosity.
- facts - `support_discard` now returns `0` if either `discard_granularity` or `discard_max_hw_bytes` is zero; otherwise it returns the value of `discard_granularity`, as before (https://github.com/ansible/ansible/pull/83480).
- facts - add a generic detection for VMware in product name.
- facts - add facts about x86_64 flags to detect microarchitecture (https://github.com/ansible/ansible/issues/83331).
- facts - skip if distribution file path is directory, instead of raising error (https://github.com/ansible/ansible/issues/84006).
- fetch - add error message when using ``dest`` with a trailing slash that becomes a local directory - https://github.com/ansible/ansible/issues/82878
- file - retrieve the link's full path when hard linking a soft link with follow (https://github.com/ansible/ansible/issues/33911).
- fixed the issue of creating user directory using tilde(~) always reported "changed".(https://github.com/ansible/ansible/issues/82490)
- fixed unit test test_borken_cowsay to address mock not been properly applied when existing unix system already have cowsay installed.
- freebsd - refactor dmidecode fact gathering code for simplicity.
- freebsd - update disk and slices regex for fact gathering (https://github.com/ansible/ansible/pull/82081).
- get_url - Verify checksum using tmpsrc, not dest (https://github.com/ansible/ansible/pull/64092)
- git - check if git version is available or not before using it for comparison (https://github.com/ansible/ansible/issues/72321).
- include_tasks - Display location when attempting to load a task list where ``include_*`` did not specify any value - https://github.com/ansible/ansible/issues/83874
- known_hosts - the returned module invocation now accurately reflects the module arguments.
- linear strategy now provides a properly templated task name to the v2_runner_on_started callback event.
- linear strategy: fix handlers included via ``include_tasks`` handler to be executed in lockstep (https://github.com/ansible/ansible/issues/83019)
- linux - remove extraneous get_bin_path API call.
- local - handle error while parsing values in ini files (https://github.com/ansible/ansible/issues/82717).
- lookup - Fixed examples of csv lookup plugin (https://github.com/ansible/ansible/issues/83031).
- module_defaults - do not display action/module deprecation warnings when using an action_group that contains a deprecated plugin (https://github.com/ansible/ansible/issues/83490).
- module_utils atomic_move (used by most file based modules), now correctly handles permission copy and setting mtime correctly across all paths
- package_facts - apk fix when cache is empty (https://github.com/ansible/ansible/issues/83126).
- package_facts - no longer fails silently when the selected package manager is unable to list packages.
- package_facts - returns the correct warning when package listing fails.
- persistent connection plugins - The correct Ansible persistent connection helper is now always used. Previously, the wrong script could be used, depending on the value of the ``PATH`` environment variable. As a result, users were sometimes required to set ``ANSIBLE_CONNECTION_PATH`` to use the correct script.
- powershell - Implement more robust deletion mechanism for C# code compilation temporary files. This should avoid scenarios where the underlying temporary directory may be temporarily locked by antivirus tools or other IO problems. A failure to delete one of these temporary directories will result in a warning rather than an outright failure.
- powershell - Improve CLIXML decoding to decode all control characters and unicode characters that are encoded as surrogate pairs.
- psrp - Fix bug when attempting to fetch a file path that contains special glob characters like ``[]``
- replace - Updated before/after example (https://github.com/ansible/ansible/issues/83390).
- runtime-metadata sanity test - do not crash on deprecations if ``galaxy.yml`` contains an empty ``version`` field (https://github.com/ansible/ansible/pull/83831).
- service - fix order of CLI arguments on FreeBSD (https://github.com/ansible/ansible/pull/81377).
- service_facts - don't crash if OpenBSD rcctl variable contains '=' character (https://github.com/ansible/ansible/issues/83457)
- service_facts will now detect failed services more accurately across systemd implementations.
- setup module (fact gathering), added fallbcak code path to handle mount fact gathering in linux when threading is not available
- setup/gather_facts will skip missing ``sysctl`` instead of being a fatal error (https://github.com/ansible/ansible/pull/81297).
- shell plugin - properly quote all needed components of shell commands (https://github.com/ansible/ansible/issues/82535)
- ssh - Fix bug when attempting to fetch a file path with characters that should be quoted when using the ``piped`` transfer method
- support the countme option when using yum_repository
- systemd - extend systemctl is-enabled check to handle "enabled-runtime" (https://github.com/ansible/ansible/pull/77754).
- systemd facts - handle AttributeError raised while gathering facts on non-systemd hosts.
- systemd_service - handle mask operation failure (https://github.com/ansible/ansible/issues/81649).
- templating hostvars under native jinja will not cause serialization errors anymore.
- the raw arguments error now just displays the short names of modules instead of every possible variation
- unarchive - Better handling of files with an invalid timestamp in zip file (https://github.com/ansible/ansible/issues/81092).
- unarchive - trigger change when size and content differ when other properties are unchanged (https://github.com/ansible/ansible/pull/83454).
- unsafe data - Address an incompatibility when iterating or getting a single index from ``AnsibleUnsafeBytes``
- unsafe data - Address an incompatibility with ``AnsibleUnsafeText`` and ``AnsibleUnsafeBytes`` when pickling with ``protocol=0``
- unsafe data - Enable directly using ``AnsibleUnsafeText`` with Python ``pathlib`` (https://github.com/ansible/ansible/issues/82414)
- uri - deprecate 'yes' and 'no' value for 'follow_redirects' parameter.
- user action will now require O(force) to overwrite the public part of an ssh key when generating ssh keys, as was already the case for the private part.
- user module now avoids changing ownership of files symlinked in provided home dir skeleton
- vault - handle vault password file value when it is directory (https://github.com/ansible/ansible/issues/42960).
- vault.is_encrypted_file is now optimized to be called in runtime and not for being called in tests
- vault_encrypted test documentation, name and examples have been fixed, other parts were clarified
- winrm - Add retry after exceeding commands per user quota that can occur in loops and action plugins running multiple commands.

Known Issues
------------

- ansible-test - When using ansible-test containers with Podman on a Ubuntu 24.04 host, ansible-test must be run as a non-root user to avoid permission issues caused by AppArmor.
- ansible-test - When using the Fedora 40 container with Podman on a Ubuntu 24.04 host, the ``unix-chkpwd`` AppArmor profile must be disabled on the host to allow SSH connections to the container.

New Plugins
-----------

Test
~~~~

- timedout - did the task time out
- vaulted_file - Is this file an encrypted vault

New Modules
-----------

Lib
~~~

ansible.modules
^^^^^^^^^^^^^^^

- mount_facts - Retrieve mount information.
