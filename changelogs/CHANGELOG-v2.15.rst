================================================
ansible-core 2.15 "Ten Years Gone" Release Notes
================================================

.. contents:: Topics


v2.15.0b1
=========

Release Summary
---------------

| Release Date: 2023-04-04
| `Porting Guide <https://docs.ansible.com/ansible-core/2.15/porting_guides/porting_guide_core_2.15.html>`__


Major Changes
-------------

- ansible-test - Docker Desktop on WSL2 is now supported (additional configuration required).
- ansible-test - Docker and Podman are now supported on hosts with cgroup v2 unified. Previously only cgroup v1 and cgroup v2 hybrid were supported.
- ansible-test - Podman now works on container hosts without systemd. Previously only some containers worked, while others required rootfull or rootless Podman, but would not work with both. Some containers did not work at all.
- ansible-test - Podman on WSL2 is now supported.
- ansible-test - When additional cgroup setup is required on the container host, this will be automatically detected. Instructions on how to configure the host will be provided in the error message shown.

Minor Changes
-------------

- Add support for custom salt for vault encoding to make it deterministic (https://github.com/ansible/ansible/issues/35480).
- Added the conditional that was False if ``when`` caused a task to skip under ``false_condition``.
- Allow force deletion of a group even when it is the primary group of a user. (https://github.com/ansible/ansible/issues/77849)
- Ansible.ModuleUtils.AddType - Add support for compiling ``unsafe`` code with the ``//AllowUnsafe`` directive
- Cache field attributes list on the playbook classes
- Cleaned up unused imports in core.
- Get user input for ``pause`` and ``paramiko_ssh`` from the strategy rather than access ``sys.stdin`` in the WorkerProcess.
- Introduce ``Delegatable`` and ``Notifiable`` mixin classes for playbook objects
- Make using blocks as handlers a parser error (https://github.com/ansible/ansible/issues/79968)
- Playbook objects - Replace deprecated stacked ``@classmethod`` and ``@property``
- Raise an error when an incorrect ``isa`` type is passed to ``FieldAttribute``.
- Remove fallback code for when ``defined``/``undefined`` tests were used on objects containing nested undefined variables; due to changes in lazy evalution of Jinja2 expressions it is no longer needed.
- Remove unused Python stdlib imports from module_utils which were not present for backwards compatibility in: common.file, compat.selectors, facts.network.iscsi, facts.network.nvme, yumdnf
- Remove unused internal imports from module_utils which were not present for backwards compatibility in: common.file, common.parameters, facts.system.caps, yumdnf
- Removed ``straight.plugin`` from the build and packaging requirements.
- Removed unused imports from the following action plugins: async_status, command, pause, set_stats, uri, validate_argument_spec
- Removed unused imports from the following lookup plugins: fileglob, template
- Removed unused imports from the following modules: apt, dnf, expect, pip, slurp, user, yum
- Removed unused imports from the following set of test plugins: files
- Removed unused imports from the following strategy plugins: debug
- Removed unused imports from the following vars plugins: host_group_vars
- Use ``ansible.module_utils.six.moves.collections_abc`` instead of ``ansible.module_utils.common._collections_compat`` in modules and module_utils.
- Use ``collections.abc`` instead of ``ansible.module_utils.common._collections_compat`` in controller code.
- ``AnsibleJ2Vars`` class that acts as a storage for all variables for templating purposes now uses ``collections.ChainMap`` internally.
- add parameter ``numeric`` to the iptables module to disable dns lookups when running list -action internally (https://github.com/ansible/ansible/issues/78793).
- allow user to set ansible specific env vars for selecting pager and editor, but still fall back to commonly used defaults.
- ansible-doc - support role extension for semantic markup spec so that ``O()`` and ``RV()`` referring to role entrypoints are rendered more readable (https://github.com/ansible/ansible/pull/80305).
- ansible-doc - support semantic markup in text output (https://github.com/ansible/ansible/pull/80242).
- ansible-doc text output - support ``seealso`` plugin record that was added for filter and test plugin documentation (https://github.com/ansible/ansible/pull/80212).
- ansible-galaxy - Add ability to specify collection versions on the CLI without the need for a colon. Such as ``namespace.name==1.2.3`` vs ``namespace.name:1.2.3``.
- ansible-galaxy - Use Python's native ``raise ... from`` instead of ``six.raise_from``.
- ansible-galaxy - support ``resolvelib >= 0.5.3, < 0.10.0``.
- ansible-galaxy - support ``resolvelib >= 0.5.3, < 1.1.0``.
- ansible-inventory now supports the limit command line options.
- ansible-test - A new ``audit`` option is available when running custom containers. This option can be used to indicate whether a container requires the AUDIT_WRITE capability. The default is ``required``, which most containers will need when using Podman. If necessary, the ``none`` option can be used to opt-out of the capability. This has no effect on Docker, which always provides the capability.
- ansible-test - A new ``cgroup`` option is available when running custom containers. This option can be used to indicate a container requires cgroup v1 or that it does not use cgroup. The default behavior assumes the container works with cgroup v2 (as well as v1).
- ansible-test - Add Alpine 3.17 remote.
- ansible-test - Add Fedora 37 container.
- ansible-test - Add Fedora 37 remote.
- ansible-test - Add FreeBSD 12.4 remote.
- ansible-test - Add RHEL 8.7 remote.
- ansible-test - Add RHEL 9.1 remote.
- ansible-test - Add macOS 13.2 remote.
- ansible-test - Additional log details are shown when containers fail to start or SSH connections to containers fail.
- ansible-test - Connection failures to remote provisioned hosts now show failure details as a warning.
- ansible-test - Containers included with ansible-test no longer disable seccomp by default.
- ansible-test - Disabled the ``ansible-format-automatic-specification`` rule from the ``pylint`` sanity test, now that Python 2.6 is no longer supported.
- ansible-test - Enable the ``trailing-comma-tuple`` rule in the ``pylint`` sanity test.
- ansible-test - Enable the ``unused-import`` rule for the ``pylint`` sanity test for collections.
- ansible-test - Failure to connect to a container over SSH now results in a clear error. Previously tests would be attempted even after initial connection attempts failed.
- ansible-test - Improve consistency of executed ``pylint`` commands by making the plugins ordered.
- ansible-test - Improve consistency of version specific documentation links.
- ansible-test - Integration tests can be excluded from retries triggered by the ``--retry-on-error`` option by adding the ``retry/never`` alias. This is useful for tests that cannot pass on a retry or are too slow to make retries useful.
- ansible-test - Minor cleanup and package updates in distro containers.
- ansible-test - More details are provided about an instance when provisioning fails.
- ansible-test - Moved git handling out of the validate-modules sanity test and into ansible-test.
- ansible-test - Reduce the polling limit for SSHD startup in containers from 60 retries to 10. The one second delay between retries remains in place.
- ansible-test - Removed test containers: fedora36
- ansible-test - Removed test remotes: alpine/3.16, fedora/36, freebsd/12.3, rhel/8.6, rhel/9.0, macos/12.0
- ansible-test - Removed the ``--keep-git`` sanity test option, which was limited to testing ansible-core itself.
- ansible-test - SSH connections from OpenSSH 8.8+ to CentOS 6 containers now work without additional configuration. However, clients older than OpenSSH 7.0 can no longer connect to CentOS 6 containers as a result. The container must have ``centos6`` in the image name for this work-around to be applied.
- ansible-test - SSH shell connections from OpenSSH 8.8+ to ansible-test provisioned network instances now work without additional configuration. However, clients older than OpenSSH 7.0 can no longer open shell sessions for ansible-test provisioned network instances as a result.
- ansible-test - Specify the configuration file location required by test plugins when the config file is not found. This resolves issue: https://github.com/ansible/ansible/issues/79411
- ansible-test - The ``ansible-test env`` command now detects and reports the container ID if running in a container.
- ansible-test - The ``pep8`` sanity test rule ``E203`` is now disabled since it is not PEP 8 compliant. This provides compatibility with output generated by the ``black`` code formatter.
- ansible-test - The ``validate-modules`` sanity test no longer limits the ``__future__`` imports that can be used. Other sanity tests that check ``__future__`` imports remain unchanged. As a result, the error code ``illegal-future-imports`` is no longer used.
- ansible-test - Unit tests now support network disconnect by default when running under Podman. Previously this feature only worked by default under Docker.
- ansible-test - Update Alpine 3 container to 3.17.
- ansible-test - Update Python requirements used for sanity tests.
- ansible-test - Update ``base`` and ``default`` containers to include Python 3.11.0.
- ansible-test - Update ``default`` containers to include new ``docs-build`` sanity test requirements.
- ansible-test - Update error handling code to use Python 3.x constructs, avoiding direct use of ``errno``.
- ansible-test - Update test container to ``7.4.0`` which includes the new PSScriptAnalyzer versions
- ansible-test - Update the CloudStack test plugin to use a newer test container with CloudStack 4.18.0.
- ansible-test - Update the NIOS test plugin to use a newer multi-arch test container.
- ansible-test - Update the ``ansible-bad-import-from`` rule in the ``pylint`` sanity test to recommend ``ansible.module_utils.six.moves.collections_abc`` instead of ``ansible.module_utils.common._collections_compat``.
- ansible-test - Update the ``base`` and ``default`` test containers with the latest requirements.
- ansible-test - Updated the Azure Pipelines CI plugin to work with newer versions of git.
- ansible-test - Use ``stop --time 0`` followed by ``rm`` to remove ephemeral containers instead of ``rm -f``. This speeds up teardown of ephemeral containers.
- ansible-test - Warnings are now shown when using containers that were built with VOLUME instructions.
- ansible-test - When setting the max open files for containers, the container host's limit will be checked. If the host limit is lower than the preferred value, it will be used and a warning will be shown.
- ansible-test - When using Podman, ansible-test will detect if the loginuid used in containers is incorrect. When this occurs a warning is displayed and the container is run with the AUDIT_CONTROL capability. Previously containers would fail under this situation, with no useful warnings or errors given.
- ansible-test acme test container - update version to update used Pebble version, underlying Python and Go base containers, and Python requirements (https://github.com/ansible/ansible/pull/79783).
- ansible-test pslint - Upgrade PSScriptAnalyzer to ``1.21.0`` which enables the ``AvoidMultipleTypeAttributes``, ``AvoidSemicolonsAsLineTerminators``, and ``AvoidUsingBrokenHashAlgorithms`` rules
- ansible-test runtime-metadata sanity test - ensure that ``redirect`` entries in ``meta/runtime.yml`` contain collection names, except for ``module_utils`` plugin redirects and ``import_redirect`` redirects (https://github.com/ansible/ansible/pull/78802).
- ansible-test sanity --test ansible-doc - now also lists documentation for test and filter plugins that are documented (https://github.com/ansible/ansible/pull/77737).
- ansible-test validate-modules - Added support for validating module documentation stored in a sidecar file alongside the module (``{module}.yml`` or ``{module}.yaml``). Previously these files were ignored and documentation had to be placed in ``{module}.py``.
- ansible-test validate-modules - no longer treat falsy non-``False`` values for defaults as ``None`` (https://github.com/ansible/ansible/pull/79267).
- apt - add allow-change-held-packages option to apt remove (https://github.com/ansible/ansible/issues/78131)
- apt_repository - adds ``sources_added`` and ``sources_removed`` to the return of the module (https://github.com/ansible/ansible/issues/79306).
- apt_repository will use the trust repo directories in order of preference (more appropriate to less) as they exist on the target.
- collections - Add additional ignores for commonly rejected file extensions
- collections - Add additional includes for REUSE license files (https://github.com/ansible/ansible/issues/79368)
- deb822_repository - Add new module for managing DEB822 formatted apt repositories
- debug - Perform argspec valdiation in debug action plugin (https://github.com/ansible/ansible/issues/79862)
- dnf5 - Add new module for managing packages and other artifacts via the next version of DNF (https://github.com/ansible/ansible/issues/78898)
- galaxy - include ``license_file`` in the default manifest directives (https://github.com/ansible/ansible/pull-request/79420)
- optimized var loading by caching results as there is no variance in input during run.
- pycompat24 module_utils - Remove support for Python 2.5 and earlier.
- sanity tests - updates the collection-deprecated-version tests to ignore the ``prerelease`` component of the collection version ().
- strftime filter, additional docs and links to source of truth.
- updated the vendored distro library to upstream version (https://github.com/ansible/ansible/pull/79227)
- validate-modules sanity test - add support for semantic markup (https://github.com/ansible/ansible/pull/80243).
- validate-modules sanity test - if the ``check_mode`` attribute is present, check that it coincides with the ``support_check_mode`` parameter of ``AnsibleModule`` (https://github.com/ansible/ansible/pull/80090).
- validate-modules sanity test - remove support for the never implemented ``forced_action_plugin`` attribute (https://github.com/ansible/ansible/pull/79317).
- validate-modules sanity test - support the ``plugin`` see-also part of the semantic markup specification (https://github.com/ansible/ansible/pull/80244).

Breaking Changes / Porting Guide
--------------------------------

- ansible-doc - no longer treat plugins in collections whose name starts with ``_`` as deprecated (https://github.com/ansible/ansible/pull/79217).
- ansible-test - Integration tests which depend on specific file permissions when running in an ansible-test managed host environment may require changes. Tests that require permissions other than ``755`` or ``644`` may need to be updated to set the necessary permissions as part of the test run.
- ansible-test - The ``vcenter`` test plugin now defaults to using a user-provided static configuration instead of the ``govcsim`` simulator for collections. Set the ``ANSIBLE_VCSIM_CONTAINER`` environment variable to ``govcsim`` to use the simulator. Keep in mind that the simulator is deprecated and will be removed in a future release.
- ansible-test sanity - previously plugins and modules in collections whose name started with ``_`` were treated as deprecated, even when they were not marked as deprecated in ``meta/runtime.yml``. This is no longer the case (https://github.com/ansible/ansible/pull/79362).
- ansible-test validate-modules - Removed the ``missing-python-doc`` error code in validate modules, ``missing-documentation`` is used instead for missing PowerShell module documentation.

Deprecated Features
-------------------

- The ``ConnectionBase()._new_stdin`` attribute is deprecated, use ``display.prompt_until(msg)`` instead.
- ansible-test - The ``foreman`` test plugin is now deprecated. It will be removed in a future release.
- ansible-test - The ``govcsim`` simulator in the ``vcenter`` test plugin is now deprecated. It will be removed in a future release. Users should switch to providing their own test environment through a static configuration file.
- password_hash - deprecate using passlib.hash.hashtype if hashtype isn't in the list of documented choices.
- vars - Specifying a list of dictionaries for ``vars:`` is deprecated in favor of specifying a dictionary.

Removed Features (previously deprecated)
----------------------------------------

- Remove deprecated ``ANSIBLE_CALLBACK_WHITELIST`` configuration environment variable, use ``ANSIBLE_CALLBACKS_ENABLED`` instead. (https://github.com/ansible/ansible/issues/78821)
- Remove deprecated ``ANSIBLE_COW_WHITELIST`` configuration environment variable, use ``ANSIBLE_COW_ACCEPTLIST`` instead. (https://github.com/ansible/ansible/issues/78819)
- Remove deprecated ``callback_whitelist`` configuration option, use ``callbacks_enabled`` instead. (https://github.com/ansible/ansible/issues/78822)
- Remove deprecated ``cow_whitelist`` configuration option, use ``cowsay_enabled_stencils`` instead. (https://github.com/ansible/ansible/issues/78820)

Bugfixes
--------

- Ansible.Basic.cs - Ignore compiler warning (reported as an error) when running under PowerShell 7.3.x.
- BSD network facts - Do not assume column indexes, look for ``netmask`` and ``broadcast`` for determining the correct columns when parsing ``inet`` line (https://github.com/ansible/ansible/issues/79117)
- Correctly count rescued tasks in play recap (https://github.com/ansible/ansible/issues/79711)
- Do not crash when templating an expression with a test or filter that is not a valid Ansible filter name (https://github.com/ansible/ansible/issues/78912, https://github.com/ansible/ansible/pull/78913).
- Fix ``MANIFEST.in`` to exclude unwanted files in the ``packaging/`` directory.
- Fix ``MANIFEST.in`` to include ``*.md`` files in the ``test/support/`` directory.
- Fix a traceback occuring when a task is named ``meta`` (https://github.com/ansible/ansible/issues/79459)
- Fix an issue where the value of ``become`` was ignored when used on a role used as a dependency in ``main/meta.yml`` (https://github.com/ansible/ansible/issues/79777)
- Fix bug in `vars` applied to roles, they were being incorrectly exported among others while only vars/main.yml was meant to be. Also adjusted the precedence to act the same as inline params.
- Fix conditionally notifying ``include_tasks` handlers when ``force_handlers`` is used (https://github.com/ansible/ansible/issues/79776)
- Fix reusing a connection in a task loop that uses a redirected or aliased name - https://github.com/ansible/ansible/issues/78425
- Fix setting become activation in a task loop - https://github.com/ansible/ansible/issues/78425
- Fix traceback when using the ``template`` module and running with ``ANSIBLE_DEBUG=1`` (https://github.com/ansible/ansible/issues/79763)
- Fix using ``GALAXY_IGNORE_CERTS`` in conjunction with collections in requirements files which specify a specific ``source`` that isn't in the configured servers.
- Fix using ``GALAXY_IGNORE_CERTS`` when downloading tarballs from Galaxy servers (https://github.com/ansible/ansible/issues/79557).
- Fixes leftover _valid_attrs usage.
- Fixes the password lookup to not rewrite files if they are not changed when using the "encrypt" parameter (#79430).
- Module and role argument validation - include the valid suboption choices in the error when an invalid suboption is provided.
- Perform type check on data passed to Display.display to enforce the requirement of being given a python3 unicode string
- TaskExecutor - don't ignore templated _raw_params that k=v parser failed to parse (https://github.com/ansible/ansible/issues/79862)
- Windows - Display a warning if the module failed to cleanup any temporary files rather than failing the task. The warning contains a brief description of what failed to be deleted.
- Windows - Ensure the module temp directory contains more unique values to avoid conflicts with concurrent runs - https://github.com/ansible/ansible/issues/80294
- Windows - Improve temporary file cleanup used by modules. Will use a more reliable delete operation on Windows Server 2016 and newer to delete files that might still be open by other software like Anti Virus scanners. There are still scenarios where a file or directory cannot be deleted but the new method should work in more scenarios.
- ``ansible-galaxy search rolename`` - give a warning instead of non-zero return code when search results are empty. This is similar to the behavior when listing roles, which gives a warning if a role cannot be found and exits with a return code of ``0``.
- ``ansible_eval_concat`` - avoid redundant unsafe wrapping of templated strings converted to Python types
- ansible-config limit shorthand format to assigned values
- ansible-doc - stop generating wrong module URLs for module see-alsos. The URLs for modules in ansible.builtin do now work, and URLs for modules outside ansible.builtin are no longer added (https://github.com/ansible/ansible/pull/80280).
- ansible-doc now will correctly display short descriptions on listing filters/tests no matter the directory sorting.
- ansible-galaxy - Improve retries for collection installs, to properly retry, and extend retry logic to common URL related connection errors (https://github.com/ansible/ansible/issues/80170 https://github.com/ansible/ansible/issues/80174)
- ansible-galaxy - fix installing collections in git repositories/directories which contain a MANIFEST.json file (https://github.com/ansible/ansible/issues/79796).
- ansible-galaxy - make initial call to Galaxy server on-demand only when installing, getting info about, and listing roles.
- ansible-galaxy collection install - respect symlinks when installing from source or local repository (https://github.com/ansible/ansible/issues/78442)
- ansible-galaxy collection/role init - preserve symlinks (https://github.com/ansible/ansible/issues/39334).
- ansible-galaxy role info - fix unhandled AttributeError by catching the correct exception.
- ansible-inventory will no longer duplicate host entries if they were part of a group's childrens tree.
- ansible-inventory will not explicitly sort groups/hosts anymore, giving a chance (depending on output format) to match the order in the input sources.
- ansible-playbook -K breaks when passwords have quotes (https://github.com/ansible/ansible/issues/79836).
- ansible-test - Add ``wheel < 0.38.0`` constraint for Python 3.6 and earlier.
- ansible-test - Add support for ``pytest`` assertion rewriting when running unit tests on Python 3.5 and later. Resolves issue https://github.com/ansible/ansible/issues/68032
- ansible-test - Added a work-around for a traceback under Python 3.11 when completing certain command line options.
- ansible-test - Allow disabled, unsupported, unstable and destructive integration test targets to be selected using their respective prefixes.
- ansible-test - Allow unstable tests to run when targeted changes are made and the ``--allow-unstable-changed`` option is specified (resolves https://github.com/ansible/ansible/issues/74213).
- ansible-test - Always indicate the Python version being used before installing requirements. Resolves issue https://github.com/ansible/ansible/issues/72855
- ansible-test - Avoid using ``exec`` after container startup when possible. This improves container startup performance and avoids intermittent startup issues with some old containers.
- ansible-test - Connection attempts to managed remote instances no longer abort on ``Permission denied`` errors.
- ansible-test - Detection for running in a Podman or Docker container has been fixed to detect more scenarios. The new detection relies on ``/proc/self/mountinfo`` instead of ``/proc/self/cpuset``. Detection now works with custom cgroups and private cgroup namespaces.
- ansible-test - Exclude ansible-core vendored Python packages from ansible-test payloads.
- ansible-test - Fix broken documentation link for ``aws`` test plugin error messages.
- ansible-test - Fix validate-modules error when retrieving PowerShell argspec when retrieved inside a Cmdlet
- ansible-test - Handle server errors when executing the ``docker info`` command.
- ansible-test - Integration test target prefixes defined in a ``tests/integration/target-prefixes.{group}`` file can now contain an underscore (``_``) character. Resolves issue https://github.com/ansible/ansible/issues/79225
- ansible-test - Multiple containers now work under Podman without specifying the ``--docker-network`` option.
- ansible-test - Pass the ``XDG_RUNTIME_DIR`` environment variable through to container commands.
- ansible-test - Perform PyPI proxy configuration after instances are ready and bootstrapping has been completed. Only target instances are affected, as controller instances were already handled this way. This avoids proxy configuration errors when target instances are not yet ready for use.
- ansible-test - Prevent concurrent / repeat inspections of the same container image.
- ansible-test - Prevent concurrent / repeat pulls of the same container image.
- ansible-test - Prevent concurrent execution of cached methods.
- ansible-test - Removed pointless comparison in diff evaluation logic.
- ansible-test - Set ``PYLINTHOME`` for the ``pylint`` sanity test to prevent failures due to ``pylint`` checking for the existence of an obsolete home directory.
- ansible-test - Show the exception type when reporting errors during instance provisioning.
- ansible-test - Support Podman 4.4.0+ by adding the ``SYS_CHROOT`` capability when running containers.
- ansible-test - Support loading of vendored Python packages from ansible-core.
- ansible-test - The ``validate-modules`` sanity test now properly enforces documentation before imports for plugins. Previously this was only enforced for modules due to a coding error.
- ansible-test - Update the ``pylint`` sanity test requirements to resolve crashes on Python 3.11. (https://github.com/ansible/ansible/issues/78882)
- ansible-test - Update the ``pylint`` sanity test to use version 2.15.4.
- ansible-test - Update the ``pylint`` sanity test to use version 2.15.5.
- ansible-test - Use consistent file permissions when delegating tests to a container or remote host. Files with any execute bit set will use permissions ``755``. All other files will use permissions ``644``. (Resolves issue https://github.com/ansible/ansible/issues/75079)
- ansible-test - fix warning message about failing to run an image to include the image name
- ansible-test runtime-metadata sanity test - do not crash on YAML parsing errors without a context mark (https://github.com/ansible/ansible/pull/78802).
- ansible-test sanity - correctly report invalid YAML in validate-modules (https://github.com/ansible/ansible/issues/75837).
- ansible-vault encrypt_string - started appending a line feed at the end of the encrypted string output. Missing newline character caused problems identifying where the string ends in some shells (like bash) or accidentally copying an extra trailing terminator symbol (e.g., zsh prints out a ``%`` sign to signal where the original output stops) (https://github.com/ansible/ansible/issues/78932).
- ansible_facts.hardware - Define all processor facts on s390x (https://github.com/ansible/ansible/issues/19755)
- apt - set locale to fix updating the cache (https://github.com/ansible/ansible/issues/79523).
- apt module should not traceback on invalid type given as package. issue 78663.
- apt_repository will no longer fail to detect key when unrelated errors/warnings are issued by apt-key.
- argument spec validation - again report deprecated parameters for Python-based modules. This was accidentally removed in ansible-core 2.11 when argument spec validation was refactored (https://github.com/ansible/ansible/issues/79680, https://github.com/ansible/ansible/pull/79681).
- argument spec validation - ensure that deprecated aliases in suboptions are also reported (https://github.com/ansible/ansible/pull/79740).
- argument spec validation - fix warning message when two aliases of the same option are used for suboptions to also mention the option's name they are in (https://github.com/ansible/ansible/pull/79740).
- basic.py module_utils - Perform Python version check much earlier to ensure it runs before other errors occur.
- connection local now avoids traceback on invalid user being used to execuet ansible (valid in host, but not in container).
- copy - fix creating the dest directory in check mode with remote_src=True (https://github.com/ansible/ansible/issues/78611).
- copy - fix reporting changes to file attributes in check mode with remote_src=True (https://github.com/ansible/ansible/issues/77957).
- copy module will no longer move 'non files' set as src when remote_src=true.
- copy remote_src=true - fix copying subdirs recursively when the dest exists and the src and dest have multiple common subdirectories in a common directory (https://github.com/ansible/ansible/issues/74536).
- copy remote_src=true - fix reporting changed for copying empty directories.
- display - reduce risk of post-fork output deadlocks (https://github.com/ansible/ansible/pull/79522)
- file - touch action in check mode was always returning ok. Fix now evaluates the different conditions and returns the appropriate changed status. (https://github.com/ansible/ansible/issues/79360)
- file lookup now handles missing files more gracefully.
- file lookup now plays nice with generic lookup ``errors`` option.
- get_url - Ensure we are passing ciphers to all url_get calls (https://github.com/ansible/ansible/issues/79717)
- get_url module - Added a documentation reference to ``hashlib`` regarding algorithms, as well as a note about ``md5`` support on systems running in FIPS compliant mode.
- get_url module - Removed out-of-date documentation stating that ``hashlib`` is a third-party library.
- handlers - fix an issue where the ``flush_handlers`` meta task could not be used with FQCN: ``ansible.builtin.meta`` (https://github.com/ansible/ansible/issues/79023)
- include_role - Inherit from role parents beyond a depth of 3 (https://github.com/ansible/ansible/issues/47023).
- jinja2_native - fix intermittent 'could not find job' failures when a value of ``ansible_job_id`` from a result of an async task was inadvertently changed during execution; to prevent this a format of ``ansible_job_id`` was changed.
- jinja2_native: preserve quotes in strings (https://github.com/ansible/ansible/issues/79083)
- keyword inheritance - Ensure that we do not squash keywords in validate (https://github.com/ansible/ansible/issues/79021)
- known_hosts - do not return changed status when a non-existing key is removed (https://github.com/ansible/ansible/issues/78598)
- list-tags now shows the 'never' tag, which was being excluded by default. To list all tasks you still need to add `--list-tasks --tags never,all`.
- loops/delegate_to - Do not double calculate the values of loops and ``delegate_to`` (https://github.com/ansible/ansible/issues/80038)
- module_utils/basic.py - Fix detection of available hashing algorithms on Python 3.x. All supported algorithms are now available instead of being limited to a hard-coded list. This affects modules such as ``get_url`` which accept an arbitrary checksum algorithm.
- normal action plugin - remove obsolete ``if`` (https://github.com/ansible/ansible/pull/79690).
- omit on keywords was resetting to default value, ignoring inheritance.
- paramiko - Add a new option to allow paramiko >= 2.9 to easily work with all devices now that rsa-sha2 support was added to paramiko, which prevented communication with numerous platforms. (https://github.com/ansible/ansible/issues/76737)
- paramiko - Add back support for ``ssh_args``, ``ssh_common_args``, and ``ssh_extra_args`` for parsing the ``ProxyCommand`` (https://github.com/ansible/ansible/issues/78750)
- paramiko connection was still using outdated playcontext, this should bring it up to date to use the 'correct' data for each task/loop.
- password lookup now correctly reads stored ident fields.
- password_hash - handle errors using unknown passlib hashtypes more gracefully (https://github.com/ansible/ansible/issues/45392).
- plugin loader, fix detection for existing configuration before initializing for a plugin
- role deduplication - Always create new role object, regardless of deduplication. Deduplication will only affect whether a duplicate call to a role will execute, as opposed to re-using the same object. (https://github.com/ansible/ansible/pull/78661)
- roles - Fix templating ``public``, ``allow_duplicates`` and ``rolespec_validate`` (https://github.com/ansible/ansible/issues/80304).
- service_facts - Use python re to parse service output instead of grep (https://github.com/ansible/ansible/issues/78541)
- strategy plugins now correctly identify bad registered variables, even on skip.
- strategy plugins: get the correctly templated and validated run_once value on strategy linear (https://github.com/ansible/ansible/issues/78492)
- systemd - daemon-reload and daemon-reexec ignore errors when running in a chroot (https://github.com/ansible/ansible/pull/79643)
- templates - Fixed ``TypeError`` when a lookup plugin has an option called ``name``.
- unarchive - allow relative path for ``dest`` (https://github.com/ansible/ansible/issues/64612)
- unarchive - log errors from commands to assist in debugging (https://github.com/ansible/ansible/issues/64612)
- updated error messages to include 'acl' and not just mode changes when failing to set required permissions on remote.
- uri - improve JSON content type detection
- user - fix comparing group IDs to existing group names so groups are not always updated (https://github.com/ansible/ansible/issues/79956).
- user module - Removed ``password_expire_max`` from the return docs, as it is not returned.
- user module - Removed ``password_expire_min`` from the return docs, as it is not returned.
- vault - show filename additionally if missing secrets prevents decryption (https://github.com/ansible/ansible/issues/79723)
- winrm - Increase the read timeout to 10 seconds later than the operation timeout reducing the chances of a false read timeout

Known Issues
------------

- ansible-test - Additional configuration may be required for certain container host and container combinations. Further details are available in the testing documentation.
- ansible-test - Custom containers with ``VOLUME`` instructions may be unable to start, when previously the containers started correctly. Remove the ``VOLUME`` instructions to resolve the issue. Containers with this condition will cause ``ansible-test`` to emit a warning.
- ansible-test - Systems with Podman networking issues may be unable to run containers, when previously the issue went unreported. Correct the networking issues to continue using ``ansible-test`` with Podman.
- ansible-test - Unit tests for collections do not support ``pytest`` assertion rewriting on Python 2.7.
- ansible-test - Using Docker on systems with SELinux may require setting SELinux to permissive mode. Podman should work with SELinux in enforcing mode.
- dnf5 - The DNF5 package manager currently does not provide all functionality to ensure feature parity between the existing ``dnf`` and the new ``dnf5`` module. As a result the following ``dnf5`` options are effectively a no-op: ``cacheonly``, ``enable_plugin``, ``disable_plugin`` and ``lock_timeout``.

New Plugins
-----------

Filter
~~~~~~

- commonpath - gets the common path
- normpath - Normalize a pathname

New Modules
-----------

Lib
~~~

ansible.modules
^^^^^^^^^^^^^^^

- deb822_repository - Add and remove deb822 formatted repositories
- dnf5 - Manages packages with the I(dnf5) package manager
