======================================================
ansible-core 2.20 "Good Times Bad Times" Release Notes
======================================================

.. contents:: Topics

v2.20.0rc1
==========

Release Summary
---------------

| Release Date: 2025-10-14
| `Porting Guide <https://docs.ansible.com/ansible-core/2.20/porting_guides/porting_guide_core_2.20.html>`__

Minor Changes
-------------

- ansible-test - Default to Python 3.14 in the ``base`` and ``default`` test containers.
- ansible-test - Filter out pylint messages for invalid filenames and display a notice when doing so.
- ansible-test - Update astroid imports in custom pylint checkers.
- ansible-test - Update pinned ``pip`` version to 25.2.
- ansible-test - Update pinned sanity test requirements, including upgrading to pylint 4.0.0.

Bugfixes
--------

- SIGINT/SIGTERM Handling - Make SIGINT/SIGTERM handling more robust by splitting concerns between forks and the parent.

v2.20.0b2
=========

Release Summary
---------------

| Release Date: 2025-10-06
| `Porting Guide <https://docs.ansible.com/ansible-core/2.20/porting_guides/porting_guide_core_2.20.html>`__

Minor Changes
-------------

- DataLoader - Update ``DataLoader.get_basedir`` to be an abspath
- known_hosts - return rc and stderr when ssh-keygen command fails for further debugging (https://github.com/ansible/ansible/issues/85850).

Deprecated Features
-------------------

- Deprecate the ``ansible.module_utils.six`` module. Use the Python standard library equivalent instead.

Removed Features (previously deprecated)
----------------------------------------

- ansible-galaxy - remove support for resolvelib >= 0.5.3, < 0.8.0.

Bugfixes
--------

- Fix issue where play tags prevented executing notified handlers (https://github.com/ansible/ansible/issues/85475)
- Fix issues with keywords being incorrectly validated on ``import_tasks`` (https://github.com/ansible/ansible/issues/85855, https://github.com/ansible/ansible/issues/85856)
- Fix traceback when trying to import non-existing file via nested ``import_tasks`` (https://github.com/ansible/ansible/issues/69882)
- ansible-doc - prevent crash when scanning collections in paths that have more than one ``ansible_collections`` in it (https://github.com/ansible/ansible/issues/84909, https://github.com/ansible/ansible/pull/85361).
- fetch - also return ``file`` in the result when changed is ``True`` (https://github.com/ansible/ansible/pull/85729).

v2.20.0b1
=========

Release Summary
---------------

| Release Date: 2025-09-23
| `Porting Guide <https://docs.ansible.com/ansible-core/2.20/porting_guides/porting_guide_core_2.20.html>`__

Major Changes
-------------

- ansible - Add support for Python 3.14.
- ansible - Drop support for Python 3.11 on the controller.
- ansible - Drop support for Python 3.8 on targets.

Minor Changes
-------------

- Add tech preview play argument spec validation, which can be enabled by setting the play keyword ``validate_argspec`` to ``True`` or the name of an argument spec. When ``validate_argspec`` is set to ``True``, a play ``name`` is required and used as the argument spec name. When enabled, the argument spec is loaded from a file matching the pattern <playbook_name>.meta.yml. At minimum, this file should contain ``{"argument_specs": {"name": {"options": {}}}}``, where "name" is the name of the play or configured argument spec.
- Added Univention Corporate Server as a part of Debian OS distribution family (https://github.com/ansible/ansible/issues/85490).
- AnsibleModule - Add temporary internal monkeypatch-able hook to alter module result serialization by splitting serialization from ``_return_formatted`` into ``_record_module_result``.
- Python type hints applied to ``to_text`` and ``to_bytes`` functions for better type hint interactions with code utilizing these functions.
- ansible now warns if you use reserved tags that were only meant for selection and not for use in play.
- ansible-doc - Return a more verbose error message when the ``description`` field is missing.
- ansible-doc - show ``notes``, ``seealso``, and top-level ``version_added`` for role entrypoints (https://github.com/ansible/ansible/pull/81796).
- ansible-doc adds support for RETURN documentation to support doc fragment plugins
- ansible-test - Implement new authentication methods for accessing the Ansible Core CI service.
- ansible-test - Improve formatting of generated coverage config file.
- ansible-test - Removed support for automatic provisioning of obsolete instances for network-integration tests.
- ansible-test - Replace FreeBSD 14.2 with 14.3.
- ansible-test - Replace RHEL 9.5 with 9.6.
- ansible-test - Update Ubuntu containers.
- ansible-test - Update base/default containers to include Python 3.14.0.
- ansible-test - Update pinned sanity test requirements.
- ansible-test - Update test containers.
- ansible-test - Upgrade Alpine 3.21 to 3.22.
- ansible-test - Upgrade Fedora 41 to Fedora 42.
- ansible-test - Upgrade to ``coverage`` version 7.10.7 for Python 3.9 and later.
- ansible-test - Use OS packages to satisfy controller requirements on FreeBSD 13.5 during managed instance bootstrapping.
- apt_repository - use correct debug method to print debug message.
- blockinfile - add new module option ``encoding`` to support files in encodings other than UTF-8 (https://github.com/ansible/ansible/pull/85291).
- deb822_repository - Add automatic installation of the ``python3-debian`` package if it is missing by adding the parameter ``install_python_debian``
- default callback plugin - add option to configure indentation for JSON and YAML output (https://github.com/ansible/ansible/pull/85497).
- encrypt - check datatype of salt_size in password_hash filter.
- fetch_file - add ca_path and cookies parameter arguments (https://github.com/ansible/ansible/issues/85172).
- include_vars - Raise an error if 'extensions' is not specified as a list.
- include_vars - Raise an error if 'ignore_files' is not specified as a list.
- lineinfile - add new module option ``encoding`` to support files in encodings other than UTF-8 (https://github.com/ansible/ansible/pull/84999).
- regex - Document the match_type fullmatch.
- regex - Ensure that match_type is one of match, fullmatch, or search (https://github.com/ansible/ansible/pull/85629).
- replace - read/write files in text-mode as unicode chars instead of as bytes and switch regex matching to unicode chars instead of bytes. (https://github.com/ansible/ansible/pull/85785).
- service_facts - handle keyerror exceptions with warning.
- service_facts - warn user about missing service details instead of ignoring.
- setup - added new subkey ``lvs`` within each entry of ``ansible_facts['vgs']`` to provide complete logical volume data scoped by volume group. The top level ``lvs`` fact by comparison, deduplicates logical volume names across volume groups and may be incomplete. (https://github.com/ansible/ansible/issues/85632)
- six - bump six version from 1.16.0 to 1.17.0 (https://github.com/ansible/ansible/issues/85408).
- stat module - add SELinux context as a return value, and add a new option to trigger this return, which is False by default. (https://github.com/ansible/ansible/issues/85217).
- tags now warn when using reserved keywords.
- wrapt - bump version from 1.15.0 to 1.17.2 (https://github.com/ansible/ansible/issues/85407).

Breaking Changes / Porting Guide
--------------------------------

- powershell - Removed code that tried to remote quotes from paths when performing Windows operations like copying and fetching file. This should not affect normal playbooks unless a value is quoted too many times.

Deprecated Features
-------------------

- Deprecated the shell plugin's ``wrap_for_exec`` function. This API is not used in Ansible or any known collection and is being removed to simplify the plugin API. Plugin authors should wrap their command to execute within an explicit shell or other known executable.
- INJECT_FACTS_AS_VARS configuration currently defaults to ``True``, this is now deprecated and it will switch to ``False`` by Ansible 2.24. You will only get notified if you are accessing 'injected' facts (for example, ansible_os_distribution vs ansible_facts['os_distribution']).
- hash_params function in roles/__init__ is being deprecated as it is not in use.
- include_vars - Specifying 'ignore_files' as a string is deprecated.
- vars, the internal variable cache will be removed in 2.24. This cache, once used internally exposes variables in inconsistent states, the 'vars' and 'varnames' lookups should be used instead.

Removed Features (previously deprecated)
----------------------------------------

- Removed the option to set the ``DEFAULT_TRANSPORT`` configuration to ``smart`` that selects the default transport as either ``ssh`` or ``paramiko`` based on the underlying platform configuraton.
- ``vault``/``unvault`` filters - remove the deprecated ``vaultid`` parameter.
- ansible-doc - role entrypoint attributes are no longer shown
- ansible-galaxy - removed the v2 Galaxy server API. Galaxy servers hosting collections must support v3.
- dnf/dnf5 - remove deprecated ``install_repoquery`` option.
- encrypt - remove deprecated passlib_or_crypt API.
- paramiko - Removed the ``PARAMIKO_HOST_KEY_AUTO_ADD`` and ``PARAMIKO_LOOK_FOR_KEYS`` configuration keys, which were previously deprecated.
- py3compat - remove deprecated ``py3compat.environ`` call.
- vars plugins - removed the deprecated ``get_host_vars`` or ``get_group_vars`` fallback for vars plugins that do not inherit from ``BaseVarsPlugin`` and define a ``get_vars`` method.
- yum_repository - remove deprecated ``keepcache`` option.

Bugfixes
--------

- Do not re-add ``tags`` on blocks from within ``import_tasks``.
- The ``ansible_failed_task`` variable is now correctly exposed in a rescue section, even when a failing handler is triggered by the ``flush_handlers`` task in the corresponding ``block`` (https://github.com/ansible/ansible/issues/85682)
- Windows async - Handle running PowerShell modules with trailing data after the module result
- ``ansible-galaxy collection list`` - fail when none of the configured collection paths exist.
- ``ternary`` filter - evaluate values lazily (https://github.com/ansible/ansible/issues/85743)
- ansible-doc --list/--list_files/--metadata-dump - fixed relative imports in nested filter/test plugin files (https://github.com/ansible/ansible/issues/85753).
- ansible-galaxy - Use the provided import task url, instead of parsing to get the task id and reconstructing the URL
- ansible-galaxy no longer shows the internal protomatter collection when listing.
- ansible-test - Always exclude the ``tests/output/`` directory from a collection's code coverage. (https://github.com/ansible/ansible/issues/84244)
- ansible-test - Fix a traceback that can occur when using delegation before the ansible-test temp directory is created.
- ansible-test - Limit package install retries during managed remote instance bootstrapping.
- ansible-test - Use a consistent coverage config for all collection testing.
- apt - mark dependencies installed as part of deb file installation as auto (https://github.com/ansible/ansible/issues/78123).
- argspec validation - The ``str`` argspec type treats ``None`` values as empty string for better consistency with pre-2.19 templating conversions.
- cache plugins - close temp cache file before moving it to fix error on WSL. (https://github.com/ansible/ansible/pull/85816)
- callback plugins - fix displaying the rendered ``ansible_host`` variable with ``delegate_to`` (https://github.com/ansible/ansible/issues/84922).
- callback plugins - improve consistency accessing the Task object's resolved_action attribute.
- conditionals - When displaying a broken conditional error or deprecation warning, the origin of the non-boolean result is included (if available), and the raw result is omitted.
- display - Fixed reference to undefined `_DeferredWarningContext` when issuing early warnings during startup. (https://github.com/ansible/ansible/issues/85886)
- dnf - Check if installroot is directory or not (https://github.com/ansible/ansible/issues/85680).
- failed_when - When using ``failed_when`` to suppress an error, the ``exception`` key in the result is renamed to ``failed_when_suppressed_exception``. This prevents the error from being displayed by callbacks after being suppressed. (https://github.com/ansible/ansible/issues/85505)
- import_tasks - fix templating parent include arguments.
- include_role - allow host specific values in all ``*_from`` arguments (https://github.com/ansible/ansible/issues/66497)
- pip - Fix pip module output so that it returns changed when the only operation is initializing a venv.
- plugins config, get_option_and_origin now correctly displays the value and origin of the option.
- run_command - Fixed premature selector unregistration on empty read from stdout/stderr that caused truncated output or hangs in rare situations.
- script inventory plugin will now show correct 'incorrect' type when doing implicit conversions on groups.
- ssh connection - fix documented variables for the ``host`` option. Connection options can be configured with delegated variables in general.
- template lookup - Skip finalization on the internal templating operation to allow markers to be returned and handled by, e.g. the ``default`` filter. Previously, finalization tripped markers, causing an exception to end processing of the current template pipeline. (https://github.com/ansible/ansible/issues/85674)
- templating - Avoid tripping markers within Jinja generated code. (https://github.com/ansible/ansible/issues/85674)
- templating - Ensure filter plugin result processing occurs under the correct call context. (https://github.com/ansible/ansible/issues/85585)
- templating - Fix slicing of tuples in templating (https://github.com/ansible/ansible/issues/85606).
- templating - Multi-node template results coerce embedded ``None`` nodes to empty string (instead of rendering literal ``None`` to the output).
- templating - Undefined marker values sourced from the Jinja ``getattr->getitem`` fallback are now accessed correctly, raising AnsibleUndefinedVariable for user plugins that do not understand markers. Previously, these values were erroneously returned to user plugin code that had not opted in to marker acceptance.
- tqm - use display.error_as_warning instead of display.warning_as_error.
- tqm - use display.error_as_warning instead of self.warning.
- uri - fix form-multipart file not being found when task is retried (https://github.com/ansible/ansible/issues/85009)
- validate-modules sanity test - fix handling of missing doc fragments (https://github.com/ansible/ansible/pull/85638).

Known Issues
------------

- templating - Exceptions raised in a Jinja ``set`` or ``with`` block which are not accessed by the template are ignored in the same manner as undefined values.
- templating - Passing a container created in a Jinja ``set`` or ``with`` block to a method results in a copy of that container. Mutations to that container which are not returned by the method will be discarded.
