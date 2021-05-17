=======================================================
Ansible Base 2.10 "When the Levee Breaks" Release Notes
=======================================================

.. contents:: Topics


v2.10.10rc1
===========

Release Summary
---------------

| Release Date: 2021-05-17
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Bugfixes
--------

- Correctly set template_path and template_fullpath for usage in template lookup and action plugins.
- Fix fileglob bug where it could return different results for different order of parameters (https://github.com/ansible/ansible/issues/72873).
- Improve resilience of ``ansible-galaxy collection`` by increasing the page size to make fewer requests overall and retrying queries with a jittered exponential backoff when rate limiting HTTP codes (520 and 429) occur. (https://github.com/ansible/ansible/issues/74191)
- ansible-test - Use documented API to retrieve build information from Azure Pipelines.
- ansible.builtin.cron - Keep non-empty crontabs, when removing cron jobs (https://github.com/ansible/ansible/pull/74497).
- ansible_test - add constraint for ``MarkupSafe`` (https://github.com/ansible/ansible/pull/74666)
- filter plugins - patch new versions of Jinja2 to prevent warnings/errors on renamed filter decorators (https://github.com/ansible/ansible/issues/74667)
- service - compare version without LooseVersion API (https://github.com/ansible/ansible/issues/74488).

v2.10.9
=======

Release Summary
---------------

| Release Date: 2021-05-03
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Major Changes
-------------

- ansible-test - Tests run with the ``centos6`` and ``default`` test containers now use a PyPI proxy container to access PyPI when Python 2.6 is used. This allows tests running under Python 2.6 to continue functioning even though PyPI is discontinuing support for non-SNI capable clients.

Minor Changes
-------------

- Switch to hashlib.sha256() for ansible-test to allow for FIPs mode.

Bugfixes
--------

- Prevent ``ansible_failed_task`` from further templating (https://github.com/ansible/ansible/issues/74036)
- ansible-test - Avoid publishing the port used by the ``pypi-test-container`` since it is only accessed by other containers. This avoids issues when trying to run tests in parallel on a single host.
- ansible-test - Fix docker container IP address detection. The ``bridge`` network is no longer assumed to be the default.
- ansible-test - ensure the correct unit test target is given when the ``__init__.py`` file is modified inside the connection plugins directory
- ansible.utils.encrypt now handles missing or unusable 'crypt' library.
- facts - detect homebrew installed at /opt/homebrew/bin/brew
- interpreter discovery - Debian 8 and lower will avoid unsupported Python3 version in interpreter discovery
- undeprecate hash_merge setting and add more docs clarifying its use and why not to use it.
- wait_for module, move missing socket into function to get proper comparrison in time.

v2.10.8
=======

Release Summary
---------------

| Release Date: 2021-04-12
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- module payload builder - module_utils imports in any nested block (eg, ``try``, ``if``) are treated as optional during module payload builds; this allows modules to implement runtime fallback behavior for module_utils that do not exist in older versions of Ansible.

Bugfixes
--------

- Fix adding unrelated candidate names to the plugin loader redirect list.
- Strategy - When building the task in the Strategy from the Worker, ensure it is properly marked as finalized and squashed. Addresses an issue with ``ansible_failed_task``. (https://github.com/ansible/ansible/issues/57399)
- ansible-test - The ``--export`` option for ``ansible-test coverage`` is now limited to the ``combine`` command. It was previously available for reporting commands on which it had no effect.
- ansible-test - The ``ansible-test coverage combine`` option ``--export`` now exports relative paths. This avoids loss of coverage data when aggregating across systems with different absolute paths. Paths will be converted back to absolute when generating reports.
- ansible-test - ensure unit test paths for connection and inventory plugins are correctly identified for collections (https://github.com/ansible/ansible/issues/73876).
- apt - fix policy_rc_d parameter throwing an exception when restoring original file (https://github.com/ansible/ansible/issues/66211)
- debug action - prevent setting facts when displaying ansible_facts (https://github.com/ansible/ansible/issues/74060).
- find - fix default pattern when use_regex is true (https://github.com/ansible/ansible/issues/50067).
- restrict module valid JSON parsed output to objects as lists are not valid responses.
- setup - fix error handling on bad subset given.
- setup, don't give up on all local facts gathering if one script file fails.
- su become plugin - ensure correct type for localization option (https://github.com/ansible/ansible/issues/73837).

v2.10.7
=======

Release Summary
---------------

| Release Date: 2021-03-15
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- ansible-test - Generation of an ``egg-info`` directory, if needed, is now done after installing test dependencies and before running tests. When running from an installed version of ``ansible-test`` a temporary directory is used to avoid permissions issues. Previously it was done before installing test dependencies and adjacent to the installed directory.
- ansible-test - now makes a better attempt to support podman when calling ``docker images`` and asking for JSON format.

Bugfixes
--------

- ConfigManager - Normalize ConfigParser between Python2 and Python3 to for handling comments (https://github.com/ansible/ansible/issues/73709)
- InventoryManager - Fix unhandled exception when given limit file was actually a directory.
- InventoryManager - Fix unhandled exception when inventory directory was empty or contained empty subdirectories (https://github.com/ansible/ansible/issues/73658).
- add AlmaLinux to fact gathering (https://github.com/ansible/ansible/pull/73458)
- ansible-galaxy - fixed galaxy role init command (https://github.com/ansible/ansible/issues/71977).
- ansible-inventory CLI - Deal with failures when sorting JSON and you have incompatible key types (https://github.com/ansible/ansible/issues/68950).
- ansible-test - Running tests using an installed version of ``ansible-test`` against one Python version from another no longer fails due to a missing ``egg-info`` directory. This could occur when testing plugins which import ``pkg_resources``.
- ansible-test - Running tests using an installed version of ``ansible-test`` no longer generates an error attempting to create an ``egg-info`` directory when an existing one is not found in the expected location. This could occur if the existing ``egg-info`` directory included a Python version specifier in the name.
- default callback - Ensure that the ``host_pinned`` strategy is not treated as lockstep (https://github.com/ansible/ansible/issues/73364)
- ensure find_mount_point consistently returns text.
- ensure we don't clobber role vars data when getting an empty file
- find module - Stop traversing directories past the requested depth. (https://github.com/ansible/ansible/issues/73627)
- hostname - add Almalinux support (https://github.com/ansible/ansible/pull/73619)
- runtime routing - redirect ``firewalld`` to ``ansible.posix.firewalld`` FQCN (https://github.com/ansible/ansible/issues/73689).
- the unvault lookup plugin returned a byte string. Now returns a real string.
- yamllint - do not raise an ``AttributeError`` if a value is assigned to a module attribute at the top of the module.

v2.10.6
=======

Release Summary
---------------

| Release Date: 2021-02-17
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- ansible-test - Added Ubuntu 20.04 LTS image to the default completion list
- inventory cache - do not show a warning when the cache file does not (yet) exist.

Security Fixes
--------------

- **security issue** - Mask default and fallback values for ``no_log`` module options (CVE-2021-20228)

Bugfixes
--------

- Added unsafe_writes test.
- Always mention the name of the deprecated or tombstoned plugin in routing deprecation/tombstone messages (https://github.com/ansible/ansible/pull/73059).
- Correct the inventory source error parse handling, specifically make the config INVENTORY_ANY_UNPARSED_IS_FAILED work as expected.
- Enabled unsafe_writes for get_url which was ignoring the paramter.
- Fix incorrect variable scoping when using ``import with context`` in Jinja2 templates. (https://github.com/ansible/ansible/issues/72615)
- Restored unsafe_writes functionality which was being skipped.
- allow become method 'su' to work on 'local' connection by allocating a fake tty.
- ansble-test - only require a collection name in deprecation warnings when necessary (https://github.com/ansible/ansible/pull/72987)
- ansible-test - Temporarily limit ``cryptography`` to versions before 3.4 to enable tests to function.
- ansible-test - The ``--remote`` option has been updated for Python 2.7 to work around breaking changes in the newly released ``get-pip.py`` bootstrapper.
- ansible-test - The ``--remote`` option has been updated to use a versioned ``get-pip.py`` bootstrapper to avoid issues with future releases.
- ansible-test sanity changelog test - bump dependency on antsibull-changelog to 0.9.0 so that `fragments that add new plugins or objects <https://github.com/ansible-community/antsibull-changelog/blob/main/docs/changelogs.rst#adding-new-roles-playbooks-test-and-filter-plugins>`_ will not fail validation (https://github.com/ansible/ansible/pull/73428).
- display correct error information when an error exists in the last line of the file (https://github.com/ansible/ansible/issues/16456)
- facts - properly report virtualization facts for Linux guests running on bhyve (https://github.com/ansible/ansible/issues/73167)
- git - Only pass ``--raw`` flag to git verify commands (verify-tag, verify-commit) when ``gpg_whitelist`` is in use. Otherwise don't pass it so that non-whitelist GPG validation still works on older Git versions. (https://github.com/ansible/ansible/issues/64469)
- import_playbook - change warning about extra parameters to deprecation (https://github.com/ansible/ansible/issues/72745)
- pause - do not warn when running in the background if a timeout is provided (https://github.com/ansible/ansible/issues/73042)
- psrp connection plugin - ``to_text(stdout)`` before ``json.loads`` in psrp.Connection.put_file in case ``stdout`` is bytes.
- validate-modules - do not raise an ``AttributeError`` if a value is assigned to a module attribute in a try/except block.

v2.10.5
=======

Release Summary
---------------

| Release Date: 2021-01-18
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- ansible-test - Changed the internal name of the custom plugin used to identify use of unwanted imports and functions.
- ansible-test - The ``pylint`` sanity test is now skipped with a warning on Python 3.9 due to unresolved upstream regressions.
- ansible-test - The ``pylint`` sanity test is now supported on Python 3.8.
- ansible-test - add macOS 11.1 as a remote target (https://github.com/ansible/ansible/pull/72622)
- ansible-test - remote macOS instances no longer install ``virtualenv`` during provisioning
- ansible-test - virtualenv helper scripts now prefer ``venv`` on Python 3 over ``virtualenv`` if the ``ANSIBLE_TEST_PREFER_VENV`` environment variable is set

Bugfixes
--------

- Apply ``_wrap_native_text`` only for builtin filters specified in STRING_TYPE_FILTERS.
- Documentation change to the apt module to reference lock files (https://github.com/ansible/ansible/issues/73079).
- Fix --list-tasks format `role_name : task_name` when task name contains the role name. (https://github.com/ansible/ansible/issues/72505)
- Fix ansible-galaxy collection list to show collections in site-packages (https://github.com/ansible/ansible/issues/70147)
- Fix bytestring vs string comparison in module_utils.basic.is_special_selinux_path() so that special-cased filesystems which don't support SELinux context attributes still allow files to be manipulated on them. (https://github.com/ansible/ansible/issues/70244)
- Fix notifying handlers via `role_name : handler_name` when handler name contains the role name. (https://github.com/ansible/ansible/issues/70582)
- async - Fix Python 3 interpreter parsing from module by comparing with bytes (https://github.com/ansible/ansible/issues/70690)
- inventory - pass the vars dictionary to combine_vars instead of an individual key's value (https://github.com/ansible/ansible/issues/72975).
- paramiko connection plugin - Ensure we only reset the connection when one has been previously established (https://github.com/ansible/ansible/issues/65812)
- systemd - preserve the full unit name when using a templated service and ``systemd`` failed to parse dbus due to a known bug in ``systemd`` (https://github.com/ansible/ansible/pull/72985)
- user - do the right thing when ``password_lock=True`` and ``password`` are used together (https://github.com/ansible/ansible/issues/72992)

v2.10.4
=======

Release Summary
---------------

| Release Date: 2020-12-14
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- ansible-doc - provide ``has_action`` field in JSON output for modules. That information is currently only available in the text view (https://github.com/ansible/ansible/pull/72359).
- ansible-galaxy - find any collection dependencies in the globally configured Galaxy servers and not just the server the parent collection is from.
- ansible-test - Added a ``--export`` option to the ``ansible-test coverage combine`` command to facilitate multi-stage aggregation of coverage in CI pipelines.
- ansible-test - Added the ``-remote rhel/7.9`` option to run tests on RHEL 7.9
- ansible-test - CentOS 8 container is now 8.2.2004 (https://github.com/ansible/distro-test-containers/pull/45).
- ansible-test - Fix container hostname/IP discovery for the ``acme`` test plugin.
- ansible-test - OpenSuse container now uses Leap 15.2 (https://github.com/ansible/distro-test-containers/pull/48).
- ansible-test - Ubuntu containers as well as ``default-test-container`` and ``ansible-base-test-container`` are now slightly smaller due to apt cleanup (https://github.com/ansible/distro-test-containers/pull/46).
- ansible-test - ``default-test-container`` and ``ansible-base-test-container`` now use Python 3.9.0 instead of 3.9.0rc1.
- ansible-test - centos6 end of life - container image updated to point to vault base repository (https://github.com/ansible/distro-test-containers/pull/54)
- ansible-test validate-modules - no longer assume that ``default`` for ``type=bool`` options is ``false``, as the default is ``none`` and for some modules, ``none`` and ``false`` mean different things (https://github.com/ansible/ansible/issues/69561).
- iptables - reorder comment postition to be at the end (https://github.com/ansible/ansible/issues/71444).

Bugfixes
--------

- Adjust various hard-coded action names to also include their ``ansible.builtin.`` and ``ansible.legacy.`` prefixed version (https://github.com/ansible/ansible/issues/71817, https://github.com/ansible/ansible/issues/71818, https://github.com/ansible/ansible/pull/71824).
- AnsibleModule - added arg ``ignore_invalid_cwd`` to ``AnsibleModule.run_command()``, to control its behaviour when ``cwd`` is invalid. (https://github.com/ansible/ansible/pull/72390)
- Fixed issue when `netstat` is either missing or doesn't have execution permissions leading to incorrect command being executed.
- Improve Ansible config deprecations to show the source of the deprecation (ansible-base). Also remove space before a comma in config deprecations (https://github.com/ansible/ansible/pull/72697).
- Skip invalid collection names when listing in ansible-doc instead of throwing exception. Issue#72257
- The ``docker`` and ``k8s`` action groups / module default groups now also support the moved modules in `community.docker <https://galaxy.ansible.com/community/docker>`_, `community.kubevirt <https://github.com/ansible-collections/community.kubevirt>`_, `community.okd <https://galaxy.ansible.com/community/okd>`_, and `kubernetes.core <https://galaxy.ansible.com/kubernetes/core>`_ (https://github.com/ansible/ansible/pull/72428).
- account for bug in Python 2.6 that occurs during interpreter shutdown to avoid stack trace
- ansible-test - Correctly detect changes in a GitHub pull request when running on Azure Pipelines.
- ansible-test - Skip installing requirements if they are already installed.
- ansible-test - ``cryptography`` is now limited to versions prior to 3.2 only when an incompatible OpenSSL version (earlier than 1.1.0) is detected
- ansible-test - add constraint for ``cffi`` to prevent failure on systems with older versions of ``gcc`` (https://foss.heptapod.net/pypy/cffi/-/issues/480)
- ansible-test - convert target paths to unicode on Python 2 to avoid ``UnicodeDecodeError`` (https://github.com/ansible/ansible/issues/68398, https://github.com/ansible/ansible/pull/72623).
- ansible-test - improve classification of changes to ``.gitignore``, ``COPYING``, ``LICENSE``, ``Makefile``, and all files ending with one of ``.in`, ``.md`, ``.rst``, ``.toml``, ``.txt`` in the collection root directory (https://github.com/ansible/ansible/pull/72353).
- ansible-test validate-modules - when a module uses ``add_file_common_args=True`` and does not use a keyword argument for ``argument_spec`` in ``AnsibleModule()``, the common file arguments were not considered added during validation (https://github.com/ansible/ansible/pull/72334).
- basic.AnsibleModule - AnsibleModule.run_command silently ignores a non-existent directory in the ``cwd`` argument (https://github.com/ansible/ansible/pull/72390).
- blockinfile - properly insert a block at the end of a file that does not have a trailing newline character (https://github.com/ansible/ansible/issues/72055)
- dnf - fix filtering to avoid dependncy conflicts (https://github.com/ansible/ansible/issues/72316)
- ensure 'local' connection always has the correct default user for actions to consume.
- pause - Fix indefinite hang when using a pause task on a background process (https://github.com/ansible/ansible/issues/32142)
- remove redundant remote_user setting in play_context for local as plugin already does it, also removes fork/thread issue from use of pwd library.
- set_mode_if_different - handle symlink if it is inside a directory with sticky bit set (https://github.com/ansible/ansible/pull/45198)
- systemd - account for templated unit files using ``@`` when searching for the unit file (https://github.com/ansible/ansible/pull/72347#issuecomment-730626228)
- systemd - follow up fix to https://github.com/ansible/ansible/issues/72338 to use ``list-unit-files`` rather than ``list-units`` in order to show all units files on the system.
- systemd - work around bug with ``systemd`` 245 and 5.8 kernel that does not correctly report service state (https://github.com/ansible/ansible/issues/71528)
- wait_for - catch and ignore errors when getting active connections with psutil (https://github.com/ansible/ansible/issues/72322)

v2.10.3
=======

Release Summary
---------------

| Release Date: 2020-11-02
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- ansible-test - Add a ``--docker-network`` option to choose the network for running containers when using the ``--docker`` option.
- ansible-test - Collections can now specify pip constraints for unit and integration test requirements using ``tests/unit/constraints.txt`` and ``tests/integration/constraints.txt`` respectively.
- ansible-test - python-cryptography is now bounded at <3.2, as 3.2 drops support for OpenSSL 1.0.2 upon which some of our CI infrastructure still depends.
- dnf - now shows specific package changes (installations/removals) under ``results`` in check_mode. (https://github.com/ansible/ansible/issues/66132)

Breaking Changes / Porting Guide
--------------------------------

- ansible-galaxy login command has been removed (see https://github.com/ansible/ansible/issues/71560)

Bugfixes
--------

- Collection callbacks were ignoring options and rules for stdout and adhoc cases.
- Collections - Ensure ``action_loader.get`` is called with ``collection_list`` to properly find collections when ``collections:`` search is specified (https://github.com/ansible/ansible/issues/72170)
- Fix ``RecursionError`` when templating large vars structures (https://github.com/ansible/ansible/issues/71920)
- ansible-doc - plugin option deprecations now also get ``collection_name`` added (https://github.com/ansible/ansible/pull/71735).
- ansible-test - Always connect additional Docker containers to the network used by the current container (if any).
- ansible-test - Always map ``/var/run/docker.sock`` into test containers created by the ``--docker`` option if the docker host is not ``localhost``.
- ansible-test - Attempt to detect the Docker hostname instead of assuming ``localhost``.
- ansible-test - Correctly detect running in a Docker container on Azure Pipelines.
- ansible-test - Prefer container IP at ``.NetworkSettings.Networks.{NetworkName}.IPAddress`` over ``.NetworkSettings.IPAddress``.
- ansible-test - The ``cs`` and ``openshift`` test plugins now search for containers on the current network instead of assuming the ``bridge`` network.
- ansible-test - Using the ``--remote`` option on Azure Pipelines now works from a job running in a container.
- async_wrapper - Fix race condition when ``~/.ansible_async`` folder tries to be created by multiple async tasks at the same time - https://github.com/ansible/ansible/issues/59306
- dnf - it is now possible to specify both ``security: true`` and ``bugfix: true`` to install updates of both types. Previously, only security would get installed if both were true. (https://github.com/ansible/ansible/issues/70854)
- facts - fix distribution fact for SLES4SAP (https://github.com/ansible/ansible/pull/71559).
- is_string/vault - Ensure the is_string helper properly identifies AnsibleVaultEncryptedUnicode as a string (https://github.com/ansible/ansible/pull/71609)
- powershell - remove getting the PowerShell version from the env var ``POWERSHELL_VERSION``. This feature never worked properly and can cause conflicts with other libraries that use this var
- url lookup - make sure that options supplied in ansible.cfg are actually used (https://github.com/ansible/ansible/pull/71736).
- user - AnsibleModule.run_command returns a tuple of return code, stdout and stderr. The module main function of the user module expects user.create_user to return a tuple of return code, stdout and stderr. Fix the locations where stdout and stderr got reversed.
- user - Local users with an expiry date cannot be created as the ``luseradd`` / ``lusermod`` commands do not support the ``-e`` option. Set the expiry time in this case via ``lchage`` after the user was created / modified. (https://github.com/ansible/ansible/issues/71942)

v2.10.2
=======

Release Summary
---------------

| Release Date: 2020-10-05
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- ansible-test - Raise the number of bytes scanned by ansible-test to determine if a file is binary to 4096.

Bugfixes
--------

- Pass the connection's timeout to connection plugins instead of the task's timeout.
- Provide more information in AnsibleUndefinedVariable (https://github.com/ansible/ansible/issues/55152)
- ansible-doc - properly show plugin name when ``name:`` is used instead of ``<plugin_type>:`` (https://github.com/ansible/ansible/pull/71966).
- ansible-test - Change classification using ``--changed`` now consistently handles common configuration files for supported CI providers.
- ansible-test - The ``resource_prefix`` variable provided to tests running on Azure Pipelines is now converted to lowercase to match other CI providers.
- collection loader - fix bogus code coverage entries for synthetic packages
- psrp - Fix hang when copying an empty file to the remote target
- runas - create a new token when running as ``SYSTEM`` to ensure it has the full privileges assigned to that account

v2.10.1
=======

Release Summary
---------------

| Release Date: 2020-09-14
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- Fixed ansible-doc to not substitute for words followed by parenthesis.  For instance, ``IBM(International Business Machines)`` will no longer be substituted with a link to a non-existent module. https://github.com/ansible/ansible/pull/71070
- Updated network integration auth timeout to 90 secs.
- ansible-doc will now format, ``L()``, ``R()``, and ``HORIZONTALLINE`` in plugin docs just as the website docs do.  https://github.com/ansible/ansible/pull/71070
- ansible-test - Add ``macos/10.15`` as a supported value for the ``--remote`` option.
- ansible-test - Allow custom ``--remote-stage`` options for development and testing.
- ansible-test - Fix ``ansible-test coverage`` reporting sub-commands (``report``, ``html``, ``xml``) on Python 2.6.
- ansible-test - Remove ``pytest < 6.0.0`` constraint for managed installations on Python 3.x now that pytest 6 is supported.
- ansible-test - Remove the discontinued ``us-east-2`` choice from the ``--remote-aws-region`` option.
- ansible-test - Request remote resources by provider name for all provider types.
- ansible-test - Show a warning when the obsolete ``--remote-aws-region`` option is used.
- ansible-test - Support custom remote endpoints with the ``--remote-endpoint`` option.
- ansible-test - Update built-in service endpoints for the ``--remote`` option.
- ansible-test - Use new endpoint for Parallels based instances with the ``--remote`` option.
- ansible-test - default container now uses default-test-container 2.7.0 and ansible-base-test-container 1.6.0. This brings in Python 3.9.0rc1 for testing.
- ansible-test - the ACME test container was updated, it now supports external account creation and has a basic OCSP responder (https://github.com/ansible/ansible/pull/71097, https://github.com/ansible/acme-test-container/releases/tag/2.0.0).
- galaxy - add documentation about galaxy parameters in examples/ansible.cfg (https://github.com/ansible/ansible/issues/68402).
- iptables - add a note about ipv6-icmp in protocol parameter (https://github.com/ansible/ansible/issues/70905).
- setup.py - Skip doing conflict checks for ``sdist`` and ``egg_info`` commands (https://github.com/ansible/ansible/pull/71310)
- subelements - clarify the lookup plugin documentation for parameter handling (https://github.com/ansible/ansible/issues/38182).

Security Fixes
--------------

- **security issue** - copy - Redact the value of the no_log 'content' parameter in the result's invocation.module_args in check mode. Previously when used with check mode and with '-vvv', the module would not censor the content if a change would be made to the destination path. (CVE-2020-14332)
- The fix for CVE-2020-1736 has been reverted. Users are encouraged to specify a ``mode`` parameter in their file-based tasks when the files being manipulated contain sensitive data.
- dnf - Previously, regardless of the ``disable_gpg_check`` option, packages were not GPG validated. They are now. (CVE-2020-14365)

Bugfixes
--------

- ANSIBLE_COLLECTIONS_PATHS - remove deprecation so that users of Ansible 2.9 and 2.10+ can use the same var when specifying a collection path without a warning.
- Confirmed commit fails with TypeError in IOS XR netconf plugin (https://github.com/ansible-collections/cisco.iosxr/issues/74)
- Ensure password passed in by -k is used on delegated hosts that do not have ansible_password set
- Fix an exit code for a non-failing playbook (https://github.com/ansible/ansible/issues/71306)
- Fix execution of the meta tasks 'clear_facts', 'clear_host_errors', 'end_play', 'end_host', and 'reset_connection' when the CLI flag '--flush-cache' is provided.
- Fix statistics reporting when rescue block contains another block (issue https://github.com/ansible/ansible/issues/61253).
- Fixed Ansible reporting validate not supported by netconf server when enabled in netconf - (https://github.com/ansible-collections/ansible.netcommon/issues/119).
- Skip literal_eval for string filters results in native jinja. (https://github.com/ansible/ansible/issues/70831)
- Strategy - Ensure we only process expected types from the results queue and produce warnings for any object we receive from the queue that doesn't match our expectations. (https://github.com/ansible/ansible/issues/70023)
- TOML inventory - Ensure we register dump functions for ``AnsibleUnsafe`` to support dumping unsafe values. Note that the TOML format has no functionality to mark that the data is unsafe for re-consumption. (https://github.com/ansible/ansible/issues/71307)
- ansible-galaxy download - fix bug when downloading a collection in a SCM subdirectory
- ansible-test units - fixed collection location code to work under pytest >= 6.0.0
- avoid clobbering existing facts inside loop when task also returns ansible_facts.
- cron - cron file should not be empty after adding var (https://github.com/ansible/ansible/pull/71207)
- fortimanager httpapi plugin - fix redirect to point to the ``fortinet.fortimanager`` collection (https://github.com/ansible/ansible/pull/71073).
- gluster modules - fix redirect to point to the ``gluster.gluster`` collection (https://github.com/ansible/ansible/pull/71240).
- linux network facts - get the correct value for broadcast address (https://github.com/ansible/ansible/issues/64384)
- native jinja2 types - properly handle Undefined in nested data.
- powershell - fix escaping of strings that broken modules like fetch when dealing with special chars - https://github.com/ansible/ansible/issues/62781
- powershell - fix the CLIXML parser when it contains nested CLIXML objects - https://github.com/ansible/ansible/issues/69550
- psrp - Use native PSRP mechanism when copying files to support custom endpoints
- strftime filter - Input epoch is allowed to be a float (https://github.com/ansible/ansible/issues/71257)
- systemd - fixed chroot usage on new versions of systemd, that broke because of upstream changes in systemctl output
- systemd - made the systemd module work correctly when the SYSTEMD_OFFLINE environment variable is set
- templating - fix error message for ``x in y`` when y is undefined (https://github.com/ansible/ansible/issues/70984)
- unarchive - check ``fut_gid`` against ``run_gid`` in addition to supplemental groups (https://github.com/ansible/ansible/issues/49284)

v2.10.0
=======

Release Summary
---------------

| Release Date: 2020-08-13
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Major Changes
-------------

- Both ansible-doc and ansible-console's help command will error for modules and plugins whose return documentation cannot be parsed as YAML. All modules and plugins passing ``ansible-test sanity --test yamllint`` will not be affected by this.
- Collections may declare a list of supported/tested Ansible versions for the collection. A warning is issued if a collection does not support the Ansible version that loads it (can also be configured as silent or a fatal error). Collections that do not declare supported Ansible versions do not issue a warning/error.
- Plugin routing allows collections to declare deprecation, redirection targets, and removals for all plugin types.
- Plugins that import module_utils and other ansible namespaces that have moved to collections should continue to work unmodified.
- Routing data built into Ansible 2.10 ensures that 2.9 content should work unmodified on 2.10. Formerly included modules and plugins that were moved to collections are still accessible by their original unqualified names, so long as their destination collections are installed.
- When deprecations are done in code, they to specify a ``collection_name`` so that deprecation warnings can mention which collection - or ansible-base - is deprecating a feature. This affects all ``Display.deprecated()`` or ``AnsibleModule.deprecate()`` or ``Ansible.Basic.Deprecate()`` calls, and ``removed_in_version``/``removed_at_date`` or ``deprecated_aliases`` in module argument specs.
- ansible-test now uses a different ``default`` test container for Ansible Collections

Minor Changes
-------------

- 'Edit on GitHub' link for plugin, cli documentation fixed to navigate to correct plugin, cli source.
- Add 'auth_url' field to galaxy server config stanzas in ansible.cfg The url should point to the token_endpoint of a Keycloak server.
- Add --ask-vault-password and --vault-pass-file options to ansible cli commands
- Add ``--pre`` flag to ``ansible-galaxy collection install`` to allow pulling in the most recent pre-release version of a collection (https://github.com/ansible/ansible/issues/64905)
- Add a global toggle to control when vars plugins are executed (per task by default for backward compatibility or after importing inventory).
- Add a new config parameter, WIN_ASYNC_STARTUP_TIMEOUT, which allows configuration of the named pipe connection timeout under Windows when launching async tasks.
- Add a per-plugin stage option to override the global toggle to control the execution of individual vars plugins (per task, after inventory, or both).
- Add an additional check for importing journal from systemd-python module (https://github.com/ansible/ansible/issues/60595).
- Add an example for using var in with_sequence (https://github.com/ansible/ansible/issues/68836).
- Add new magic variable ``ansible_collection`` that contains the collection name
- Add new magic variable ``ansible_role_name`` that contains the FQCN of the role
- Add standard Python 2/3 compatibility boilerplate to setup script, module_utils and docs_fragments which were missing them.
- Added PopOS as a part of Debian OS distribution family (https://github.com/ansible/ansible/issues/69286).
- Added hostname support for PopOS in hostname module.
- Added openEuler OS in RedHat OS Family.
- Added the ability to set ``DEFAULT_NO_TARGET_SYSLOG`` through the ``ansible_no_target_syslog`` variable on a task
- Ansible CLI fails with warning if extra_vars parameter is used with filename without @ sign (https://github.com/ansible/ansible/issues/51857).
- Ansible modules created with ``add_file_common_args=True`` added a number of undocumented arguments which were mostly there to ease implementing certain action plugins. The undocumented arguments ``src``, ``follow``, ``force``, ``content``, ``backup``, ``remote_src``, ``regexp``, ``delimiter``, and ``directory_mode`` are now no longer added. Modules relying on these options to be added need to specify them by themselves. Also, action plugins relying on these extra elements in ``FILE_COMMON_ARGUMENTS`` need to be adjusted.
- Ansible now allows deprecation by date instead of deprecation by version. This is possible for plugins and modules (``meta/runtime.yml`` and ``deprecated.removed_at_date`` in ``DOCUMENTATION``, instead of ``deprecated.removed_in``), for plugin options (``deprecated.date`` instead of ``deprecated.version`` in ``DOCUMENTATION``), for module options (``removed_at_date`` instead of ``removed_in_version`` in argument spec), and for module option aliases (``deprecated_aliases.date`` instead of ``deprecated_aliases.version`` in argument spec).
- Ansible should fail with error when non-existing limit file is provided in command line.
- Ansible.Basic - Added the ability to specify multiple fragments to load in a generic way for modules that use a module_util with fragment options
- Ansible.Basic.cs - Added support for ``deprecated_aliases`` to deprecated aliases in a standard way
- Ansible.ModuleUtils.WebRequest - Move username and password aliases out of util to avoid option name collision
- Change order of arguments in ansible cli to use --ask-vault-password and --vault-password-file by default
- CollectionRequirement - Add a metadata property to update and retrieve the _metadata attribute.
- Command module: Removed suggestions to use modules which have moved to collections and out of ansible-base
- Enable Ansible Collections loader to discover and import collections from ``site-packages`` dir and ``PYTHONPATH``-added locations.
- Enable testing the AIX platform as a remote OS in ansible-test
- Flatten the directory hierarchy of modules
- Ignore plesk-release file while parsing distribution release (https://github.com/ansible/ansible/issues/64101).
- Openstack inventory script is migrated to ansible-openstack-collection, adjusted the link in documentation accordingly.
- Openstack inventory script is moved to openstack.cloud from community.general.
- PowerShell Add-Type - Add an easier way to reference extra types when compiling C# code on PowerShell Core
- PowerShell Add-Type - Added the ``X86`` and ``AMD64`` preprocessor symbols for conditional compiling
- Prevent losing useful error information by including both the loop and the conditional error messages (https://github.com/ansible/ansible/issues/66529)
- Provides additional information about collection namespace name restrictions (https://github.com/ansible/ansible/issues/65151).
- Raise error when no task file is provided to import_tasks (https://github.com/ansible/ansible/issues/54095).
- Refactor test_distribution_version testcases.
- Remove the deprecation message for the ``TRANSFORM_INVALID_GROUP_CHARS`` setting. (https://github.com/ansible/ansible/issues/61889)
- Removed extras_require support from setup.py (and [azure] extra). Requirements will float with the collections, so it's not appropriate for ansible-base to host requirements for them any longer.
- Simplify dict2items filter example in loop documentation (https://github.com/ansible/ansible/issues/65505).
- Templating - Add globals to the jinja2 environment at ``Templar`` instantiation, instead of customizing the template object. Only customize the template object, to disable lookups. (https://github.com/ansible/ansible/pull/69278)
- Templating - Add support to auto unroll generators produced by jinja2 filters, to prevent the need of explicit use of ``|list`` (https://github.com/ansible/ansible/pull/68014)
- The plugin loader now keeps track of the collection where a plugin was resolved to, in particular whether the plugin was loaded from ansible-base's internal paths (``ansible.builtin``) or from user-supplied paths (no collection name).
- The results queue and counter for results are now split for standard / handler results. This allows the governing strategy to be truly independent from the handler strategy, which basically follows the linear methodology.
- Update required library message with correct grammer in basic.py.
- Updated inventory script location for EC2, Openstack, and Cobbler after collection (https://github.com/ansible/ansible/issues/68897).
- Updated inventory script location for infoblox, ec2 and other after collection migration (https://github.com/ansible/ansible/issues/69139).
- Updates ``ansible_role_names``, ``ansible_play_role_names``, and ``ansible_dependent_role_names`` to include the FQCN
- Use OrderedDict by default when importing mappings from YAML.
- Windows - Add a check for the minimum PowerShell version so we can create a friendly error message on older hosts
- Windows - add deprecation notice in the Windows setup module when running on Server 2008, 2008 R2, and Windows 7
- `AnsibleModule.fail_json()` has always required that a message be passed in which informs the end user why the module failed.  In the past this message had to be passed as the `msg` keyword argument but it can now be passed as the first positional argument instead.
- ``AnsibleModule.load_file_common_arguments`` now allows to simply override ``path``.
- add mechanism for storing warnings and deprecations globally and not attached to an ``AnsibleModule`` object (https://github.com/ansible/ansible/pull/58993)
- added more ways to configure new uri options in 2.10.
- ansible-doc - improve suboptions formatting (https://github.com/ansible/ansible/pull/69795).
- ansible-doc - now indicates if an option is added by a doc fragment from another collection by prepending the collection name, or ``ansible.builtin`` for ansible-base, to the version number.
- ansible-doc - return values will be properly formatted (https://github.com/ansible/ansible/pull/69796).
- ansible-galaxy - Add ``download`` option for ``ansible-galaxy collection`` to download collections and their dependencies for an offline install
- ansible-galaxy - Add a `verify` subcommand to `ansible-galaxy collection`. The collection found on the galaxy server is downloaded to a tempfile to compare the checksums of the files listed in the MANIFEST.json and the FILES.json with the contents of the installed collection.
- ansible-galaxy - Add installation successful message
- ansible-galaxy - Added the ability to display the progress wheel through the C.GALAXY_DISPLAY_PROGRESS config option. Also this now defaults to displaying the progress wheel if stdout has a tty.
- ansible-galaxy - Added the ability to ignore further files and folders using a pattern with the ``build_ignore`` key in a collection's ``galaxy.yml`` (https://github.com/ansible/ansible/issues/59228).
- ansible-galaxy - Allow installing collections from git repositories.
- ansible-galaxy - Always ignore the ``tests/output`` directory when building a collection as it is used by ``ansible-test`` for test output (https://github.com/ansible/ansible/issues/59228).
- ansible-galaxy - Change the output verbosity level of the download message from 3 to 0 (https://github.com/ansible/ansible/issues/70010)
- ansible-galaxy - Display message if both collections and roles are specified in a requirements file but can't be installed together.
- ansible-galaxy - Install both collections and roles with ``ansible-galaxy install -r requirements.yml`` in certain scenarios.
- ansible-galaxy - Requirement entries for collections now support a 'type' key to indicate whether the collection is a galaxy artifact, file, url, or git repo.
- ansible-galaxy - add ``--token`` argument which is the same as ``--api-key`` (https://github.com/ansible/ansible/issues/65955)
- ansible-galaxy - add ``collection list`` command for listing installed collections (https://github.com/ansible/ansible/pull/65022)
- ansible-galaxy - add ``validate_collection_path()`` utility function ()
- ansible-galaxy - add collections path argument
- ansible-galaxy - allow role to define dependency requirements that will be only installed by defining them in ``meta/requirements.yml`` (https://github.com/ansible/proposals/issues/57)
- ansible-test - --docker flag now has an associated --docker-terminate flag which controls if and when the docker container is removed following tests
- ansible-test - Add a test to prevent ``state=get``
- ansible-test - Add a test to prevent ``state=list`` and ``state=info``
- ansible-test - Add a verbosity option for displaying warnings.
- ansible-test - Add support for Python 3.9.
- ansible-test - Added CI provider support for Azure Pipelines.
- ansible-test - Added a ``ansible-test coverage analyze targets filter`` command to filter aggregated coverage reports by path and/or target name.
- ansible-test - Added a ``ansible-test coverage analyze targets`` command to analyze integration test code coverage by test target.
- ansible-test - Added support for Ansible Core CI request signing for Shippable.
- ansible-test - Added support for testing on Fedora 32.
- ansible-test - General code cleanup.
- ansible-test - Now includes testing support for RHEL 8.2
- ansible-test - Provisioning of RHEL instances now includes installation of pinned versions of ``packaging`` and ``pyparsing`` to match the downstream vendored versions.
- ansible-test - Refactor code to consolidate filesystem access and improve handling of encoding.
- ansible-test - Refactored CI related logic into a basic provider abstraction.
- ansible-test - Remove obsolete support for provisioning remote vCenter instances. The supporting services are no longer available.
- ansible-test - Report the correct line number in the ``yamllint`` sanity test when reporting ``libyaml`` parse errors in module documentation.
- ansible-test - Support writing compact JSON files instead of formatting and indenting the output.
- ansible-test - Update Ubuntu 18.04 test container to version 1.13 which includes ``venv``
- ansible-test - Update ``default-test-container`` to version 1.11, which includes Python 3.9.0a4.
- ansible-test - Updated the default test containers to include Python 3.9.0b3.
- ansible-test - Upgrade OpenSUSE containers to use Leap 15.1.
- ansible-test - Upgrade distro test containers from 1.16.0 to 1.17.0
- ansible-test - Upgrade from ansible-base-test-container 1.1 to 2.2
- ansible-test - Upgrade from default-test-container 2.1 to 2.2
- ansible-test - ``mutually_exclusive``, ``required_if``, ``required_by``, ``required_together`` and ``required_one_of`` in modules are now validated.
- ansible-test - ``validate-modules`` now also accepts an ISO 8601 formatted date as ``deprecated.removed_at_date``, instead of requiring a version number in ``deprecated.removed_in``.
- ansible-test - ``validate-modules`` now makes sure that module documentation deprecation removal version and/or date matches with removal version and/or date in meta/runtime.yml.
- ansible-test - ``validate-modules`` now validates all version numbers in documentation and argument spec. Version numbers for collections are checked for being valid semantic versioning version number strings.
- ansible-test - add ``validate-modules`` tests for ``removed_in_version`` and ``deprecated_aliases`` (https://github.com/ansible/ansible/pull/66920/).
- ansible-test - add check for ``print()`` calls in modules and module_utils.
- ansible-test - added a ``--no-pip-check`` option
- ansible-test - added a ``--venv-system-site-packages`` option for use with the ``--venv`` option
- ansible-test - added new ``changelog`` test, which runs if a `antsibull-changelog <https://pypi.org/project/antsibull-changelog/>`_ configuration or files in ``changelogs/fragments/`` are found (https://github.com/ansible/ansible/pull/69313).
- ansible-test - allow delegation config to specify equivalents to the ``--no-pip-check``, ``--disable-httptester`` and `--no-temp-unicode`` options
- ansible-test - allow sanity tests to check for optional errors by specifying ``--enable-optional-errors`` (https://github.com/ansible/ansible/pull/66920/).
- ansible-test - also run the ``ansible-doc`` sanity test with ``--json`` to ensure that the documentation does not contain something that cannot be exported as JSON (https://github.com/ansible/ansible/issues/69238).
- ansible-test - enable deprecated version testing for modules and ``module.deprecate()`` calls (https://github.com/ansible/ansible/pull/66920/).
- ansible-test - extend alias validation.
- ansible-test - fixed ``units`` command with ``--docker`` to (mostly) work under podman
- ansible-test - improve module validation so that ``default``, ``sample`` and ``example`` contain JSON values and not arbitrary YAML values, like ``datetime`` objects or dictionaries with non-string keys.
- ansible-test - module validation will now consider arguments added by ``add_file_common_arguments=True`` correctly.
- ansible-test - switch from testing RHEL 8.0 and RHEL 8.1 Beta to RHEL 8.1
- ansible-test - the argument spec of modules is now validated by a YAML schema.
- ansible-test - the module validation code now checks whether ``elements`` documentation for options matches the argument_spec.
- ansible-test - the module validation code now checks whether ``elements`` is defined when ``type=list``
- ansible-test - the module validation code now checks whether ``requirement`` for options is documented correctly.
- ansible-test add pyparsing constraint for Python 2.x to avoid compatibility issues with the upcoming pyparsing 3 release
- ansible-test defaults to redacting sensitive values (disable with the ``--no-redact`` option)
- ansible-test has been updated to use ``default-test-container:1.13`` which includes fewer Python requirements now that most modules and tests have been migrated to collections.
- ansible-test no longer detects ``git`` submodule directories as files.
- ansible-test no longer provides a ``--tox`` option. Use the ``--venv`` option instead. This only affects testing the Ansible source. The feature was never available for Ansible Collections or when running from an Ansible install.
- ansible-test no longer tries to install sanity test dependencies on unsupported Python versions
- ansible-test now checks for the minimum and maximum supported versions when importing ``coverage``
- ansible-test now filters out unnecessary warnings and messages from pip when installing its own requirements
- ansible-test now has a ``--list-files`` option to list files using the ``env`` command.
- ansible-test now includes the ``pylint`` plugin ``mccabe`` in optional sanity tests enabled with ``--enable-optional-errors``
- ansible-test now places the ansible source and collections content in separate directories when using the ``--docker`` or ``--remote`` options.
- ansible-test now provides a more helpful error when loading coverage files created by ``coverage`` version 5 or later
- ansible-test now supports provisioning of network resources when testing network collections
- ansible-test now supports skip aliases in the format ``skip/{arch}/{platform}`` and ``skip/{arch}/{platform}/{version}`` where ``arch`` can be ``power``. These aliases are only effective for the ``--remote`` option.
- ansible-test now supports skip aliases in the format ``skip/{platform}/{version}`` for the ``--remote`` option. This is preferred over the older ``skip/{platform}{version}`` format which included no ``/`` between the platform and version.
- ansible-test now supports testing against RHEL 7.8 when using the ``--remote`` option.
- ansible-test now supports the ``--remote power/centos/7`` platform option.
- ansible-test now validates the schema of ansible_builtin_runtime.yml and a collections meta/runtime.yml file.
- ansible-test provides clearer error messages when failing to detect the provider to use with the ``--remote`` option.
- ansible-test provisioning of network devices for ``network-integration`` has been updated to use collections.
- ansible_native_concat() - use ``to_text`` function rather than Jinja2's ``text_type`` which has been removed in Jinja2 master branch.
- apt - Implemented an exponential backoff behaviour when retrying to update the cache with new params ``update_cache_retry_max_delay`` and ``update_cache_retries`` to control the behavior.
- apt_repository - Implemented an exponential backoff behaviour when retrying to update the apt cache with new params ``update_cache_retry_max_delay`` and ``update_cache_retries`` to control the behavior.
- blockinfile - Update module documentation to clarify insertbefore/insertafter usage.
- callbacks - Allow modules to return `None` as before/after entries for diff. This should make it easier for modules to report the "not existing" state of the entity they touched.
- combine filter - now accept a ``list_merge`` argument which modifies its behaviour when the hashes to merge contain arrays/lists.
- conditionals - change the default of CONDITIONAL_BARE_VARS to False (https://github.com/ansible/ansible/issues/70682).
- config - accept singular version of ``collections_path`` ini setting and ``ANSIBLE_COLLECTIONS_PATH`` environment variable setting
- core filters - Adding ``path_join`` filter to the core filters list
- debconf - add a note about no_log=True since module might expose sensitive information to logs (https://github.com/ansible/ansible/issues/32386).
- default_callback - moving 'check_mode_markers' documentation in default_callback doc_fragment (https://github.com/ansible-collections/community.general/issues/565).
- distro - Update bundled version of distro from 1.4.0 to 1.5.0
- dnf - Properly handle idempotent transactions with package name wildcard globs (https://github.com/ansible/ansible/issues/62809)
- dnf - Properly handle module AppStreams that don't define stream (https://github.com/ansible/ansible/issues/63683)
- dnf param to pass allowerasing
- downstream packagers may install packages under ansible._vendor, which will be added to head of sys.path at ansible package load
- file - specifying ``src`` without ``state`` is now an error
- get_bin_path() - change the interface to always raise ``ValueError`` if the command is not found (https://github.com/ansible/ansible/pull/56813)
- get_url - Remove deprecated string format support for the headers option (https://github.com/ansible/ansible/issues/61891)
- git - added an ``archive_prefix`` option to set a prefix to add to each file path in archive
- host_group_vars plugin - Require whitelisting and whitelist by default.
- new magic variable - ``ansible_config_file`` - full path of used Ansible config file
- package_facts.py - Add support for Pacman package manager.
- pipe lookup - update docs for Popen with shell=True usages (https://github.com/ansible/ansible/issues/70159).
- plugin loader - Add MODULE_IGNORE_EXTS config option to skip over certain extensions when looking for script and binary modules.
- powershell (shell plugin) - Fix `join_path` to support UNC paths (https://github.com/ansible/ansible/issues/66341)
- regexp_replace filter - add multiline support for regex_replace filter (https://github.com/ansible/ansible/issues/61985)
- rename ``_find_existing_collections()`` to ``find_existing_collections()`` to reflect its use across multiple files
- reorganized code for the ``ansible-test coverage`` command for easier maintenance and feature additions
- service_facts - Added undocumented 'indirect' and 'static' as service status (https://github.com/ansible/ansible/issues/69752).
- ssh - connection plugin now supports a new variable ``sshpass_prompt`` which gets passed to ``sshpass`` allowing the user to set a custom substring to search for a password prompt (requires sshpass 1.06+)
- systemd - default scope is now explicitly "system"
- tests - Add new ``truthy`` and ``falsy`` jinja2 tests to evaluate the truthiness or falsiness of a value
- to_nice_json filter - Removed now-useless exception handler
- to_uuid - add a named parameter to let the user optionally set a custom namespace
- update ansible-test default-test-container from version 1.13 to 1.14, which includes an update from Python 3.9.0a6 to Python 3.9.0b1
- update ansible-test default-test-container from version 1.9.1 to 1.9.2
- update ansible-test default-test-container from version 1.9.2 to 1.9.3
- update ansible-test default-test-container from version 1.9.3 to 1.10.1
- update ansible-test images to 1.16.0, which includes system updates and pins CentOS versions
- uri/galaxy - Add new ``prepare_multipart`` helper function for creating a ``multipart/form-data`` body (https://github.com/ansible/ansible/pull/69376)
- url_lookup_plugin - add parameters to match what is available in ``module_utils/urls.py``
- user - allow groups, append parameters with local
- user - usage of ``append: True`` without setting a list of groups. This is currently a no-op with a warning, and will change to an error in 2.14. (https://github.com/ansible/ansible/pull/65795)
- validate-modules checks for deprecated in collections against meta/runtime.yml
- validation - Sort missing parameters in exception message thrown by check_required_arguments
- vars plugins - Support vars plugins in collections by adding the ability to whitelist plugins.
- vars_prompt - throw error when encountering unsupported key
- win_package - Added proxy support for retrieving packages from a URL - https://github.com/ansible/ansible/issues/43818
- win_package - Added support for ``.appx``, ``.msix``, ``.appxbundle``, and ``.msixbundle`` package - https://github.com/ansible/ansible/issues/50765
- win_package - Added support for ``.msp`` packages - https://github.com/ansible/ansible/issues/22789
- win_package - Added support for specifying the HTTP method when getting files from a URL - https://github.com/ansible/ansible/issues/35377
- win_package - Read uninstall strings from the ``QuietUninstallString`` if present to better support argumentless uninstalls of registry based packages.
- win_package - Scan packages in the current user's registry hive - https://github.com/ansible/ansible/issues/45950
- windows collections - Support relative module util imports in PowerShell modules and module_utils

Deprecated Features
-------------------

- Using the DefaultCallback without the correspodning doc_fragment or copying the documentation.
- hash_behaviour - Deprecate ``hash_behaviour`` for future removal.
- script inventory plugin - The 'cache' option is deprecated and will be removed in 2.12. Its use has been removed from the plugin since it has never had any effect.

Removed Features (previously deprecated)
----------------------------------------

- core - remove support for ``check_invalid_arguments`` in ``AnsibleModule``, ``AzureModule`` and ``UTMModule``.

Security Fixes
--------------

- **security issue** - Convert CLI provided passwords to text initially, to prevent unsafe context being lost when converting from bytes->text during post processing of PlayContext. This prevents CLI provided passwords from being incorrectly templated (CVE-2019-14856)
- **security issue** - Redact cloud plugin secrets in ansible-test when running integration tests using cloud plugins. Only present in 2.9.0b1.
- **security issue** - TaskExecutor - Ensure we don't erase unsafe context in TaskExecutor.run on bytes. Only present in 2.9.0beta1 (https://github.com/ansible/ansible/issues/62237)
- **security issue** - The ``subversion`` module provided the password via the svn command line option ``--password`` and can be retrieved from the host's /proc/<pid>/cmdline file. Update the module to use the secure ``--password-from-stdin`` option instead, and add a warning in the module and in the documentation if svn version is too old to support it. (CVE-2020-1739)
- **security issue** - Update ``AnsibleUnsafeText`` and ``AnsibleUnsafeBytes`` to maintain unsafe context by overriding ``.encode`` and ``.decode``. This prevents future issues with ``to_text``, ``to_bytes``, or ``to_native`` removing the unsafe wrapper when converting between string types (CVE-2019-14856)
- **security issue** - properly hide parameters marked with ``no_log`` in suboptions when invalid parameters are passed to the module (CVE-2019-14858)
- **security issue** atomic_move - change default permissions when creating temporary files so they are not world readable (https://github.com/ansible/ansible/issues/67794) (CVE-2020-1736)
- **security issue** win_unzip - normalize paths in archive to ensure extracted files do not escape from the target directory (CVE-2020-1737)
- **security_issue** - create temporary vault file with strict permissions when editing and prevent race condition (CVE-2020-1740)
- Ensure we get an error when creating a remote tmp if it already exists. CVE-2020-1733
- In fetch action, avoid using slurp return to set up dest, also ensure no dir traversal CVE-2020-1735.
- Sanitize no_log values from any response keys that might be returned from the uri module (CVE-2020-14330).
- ansible-galaxy - Error when install finds a tar with a file that will be extracted outside the collection install directory - CVE-2020-10691

Bugfixes
--------

- ActionBase - Add new ``cleanup`` method that is explicitly run by the ``TaskExecutor`` to ensure that the shell plugins ``tmpdir`` is always removed. This change means that individual action plugins need not be responsible for removing the temporary directory, which ensures that we don't have code paths that accidentally leave behind the temporary directory.
- Add example setting for ``collections_paths`` parameter to ``examples/ansible.cfg``
- Add missing gcp modules to gcp module defaults group
- Added support for Flatcar Container Linux in distribution and hostname modules. (https://github.com/ansible/ansible/pull/69627)
- Added support for OSMC distro in hostname module (https://github.com/ansible/ansible/issues/66189).
- Address compat with rpmfluff-0.6 for integration tests
- Address the deprecation of the use of stdlib distutils in packaging. It's a short-term hotfix for the problem (https://github.com/ansible/ansible/issues/70456, https://github.com/pypa/setuptools/issues/2230, https://github.com/pypa/setuptools/commit/bd110264)
- Allow TypeErrors on Undefined variables in filters to be handled or deferred when processing for loops.
- Allow tasks to notify a fqcn handler name (https://github.com/ansible/ansible/issues/68181)
- An invalid value is hard to track down if you don't know where it came from, return field name instead.
- Ansible output now uses stdout to determine column width instead of stdin
- Ansible.Basic - Fix issue when setting a ``no_log`` parameter to an empty string - https://github.com/ansible/ansible/issues/62613
- Ansible.ModuleUtils.WebRequest - actually set no proxy when ``use_proxy: no`` is set on a Windows module - https://github.com/ansible/ansible/issues/68528
- AnsibleDumper - Add a representer for AnsibleUnsafeBytes (https://github.com/ansible/ansible/issues/62562).
- AnsibleModule.run_command() - set ``close_fds`` to ``False`` on Python 2 if ``pass_fds`` are passed to ``run_command()``. Since ``subprocess.Popen()`` on Python 2 does not have the ``pass_fds`` option, there is no way to exclude a specific list of file descriptors from being closed.
- Avoid bare select() for running commands to avoid too large file descriptor numbers failing tasks
- Avoid running subfunctions that are passed to show_vars function when it will be a noop.
- By passing the module_tmpdir as a parameter in the write_ssh_wrapper function instead of initalizing module_tmpdir via get_module_path()
- CLI - the `ANSIBLE_PLAYBOOK_DIR` envvar or `playbook_dir` config can now substitute for the --playbook-dir arg on CLIs that support it (https://github.com/ansible/ansible/issues/59464)
- Check NoneType for raw_params before proceeding in include_vars (https://github.com/ansible/ansible/issues/64939).
- Collections - Allow a collection role to call a stand alone role, without needing to explicitly add ``ansible.legacy`` to the collection search order within the collection role. (https://github.com/ansible/ansible/issues/69101)
- Correctly process raw_params in add_hosts.
- Create an ``import_module`` compat util, for use across the codebase, to allow collection loading to work properly on Python26
- DUPLICATE_YAML_DICT_KEY - Fix error output when configuration option DUPLICATE_YAML_DICT_KEY is set to error (https://github.com/ansible/ansible/issues/65366)
- Do not keep empty blocks in PlayIterator after skipping tasks with tags.
- Ensure DataLoader temp files are removed at appropriate times and that we observe the LOCAL_TMP setting.
- Ensure that ``--version`` works with non-ascii ansible project paths (https://github.com/ansible/ansible/issues/66617)
- Ensure that keywords defined as booleans are correctly interpreting their input, before patch any random string would be interpreted as False
- Ensure we don't allow ansible_facts subkey of ansible_facts to override top level, also fix 'deprefixing' to prevent key transforms.
- Fact Delegation - Add ability to indicate which facts must always be delegated. Primarily for ``discovered_interpreter_python`` right now, but extensible later. (https://github.com/ansible/ansible/issues/61002)
- Fix ``delegate_facts: true`` when ``ansible_python_interpreter`` is not set. (https://github.com/ansible/ansible/issues/70168)
- Fix a bug when a host was not removed from a play after ``meta: end_host`` and as a result the host was still present in ``ansible_play_hosts`` and ``ansible_play_batch`` variables.
- Fix an issue with the ``fileglob`` plugin where passing a subdirectory of non-existent directory would cause it to fail - https://github.com/ansible/ansible/issues/69450
- Fix case sensitivity for ``lookup()`` (https://github.com/ansible/ansible/issues/66464)
- Fix collection install error that happened if a dependency specified dependencies to be null (https://github.com/ansible/ansible/issues/67574).
- Fix https://github.com/ansible/galaxy-dev/issues/96 Add support for automation-hub authentication to ansible-galaxy
- Fix incorrect "Could not match supplied host pattern" warning (https://github.com/ansible/ansible/issues/66764)
- Fix issue git module cannot use custom `key_file` or `ssh_opts` as non-root user on system with noexec `/tmp` (https://github.com/ansible/ansible/issues/30064).
- Fix issue git module ignores remote_tmp (https://github.com/ansible/ansible/issues/33947).
- Fix issue where the collection loader tracebacks if ``collections_paths = ./`` is set in the config
- Fix issue with callbacks ``set_options`` method that was not called with collections
- Fix label lookup in the default callback for includes (https://github.com/ansible/ansible/issues/65904)
- Fix regression when ``ansible_failed_task`` and ``ansible_failed_result`` are not defined in the rescue block (https://github.com/ansible/ansible/issues/64789)
- Fix string parsing of inline vault strings for plugin config variable sources
- Fix traceback when printing ``HostVars`` on native Jinja2 (https://github.com/ansible/ansible/issues/65365)
- Fix warning for default permission change when no mode is specified. Follow up to https://github.com/ansible/ansible/issues/67794. (CVE-2020-1736)
- Fixed a bug with the copy action plugin where mode=preserve was being passed on symlink files and causing a traceback (https://github.com/ansible/ansible/issues/68471).
- Fixed the equality check for IncludedFiles to ensure they are not accidently merged when process_include_results runs.
- Fixes ansible-test traceback when plugin author is not a string or a list of strings (https://github.com/ansible/ansible/pull/70507)
- Fixes in network action plugins load from collections using module prefix (https://github.com/ansible/ansible/issues/65071)
- Force collection names to be static so that a warning is generated because templating currently does not work (see https://github.com/ansible/ansible/issues/68704).
- Handle empty extra vars in ansible cli (https://github.com/ansible/ansible/issues/61497).
- Handle empty roles and empty collections in requirements.yml in ansible-galaxy install command (https://github.com/ansible/ansible/issues/68186).
- Handle exception encountered while parsing the argument description in module when invoked via ansible-doc command (https://github.com/ansible/ansible/issues/60587).
- Handle exception when /etc/shadow file is missing or not found, while operating user operation in user module (https://github.com/ansible/ansible/issues/63490).
- HostVarsVars - Template the __repr__ value (https://github.com/ansible/ansible/issues/64128).
- JSON Encoder - Ensure we treat single vault encrypted values as strings (https://github.com/ansible/ansible/issues/70784)
- Make netconf plugin configurable to set ncclient device handler name in netconf plugin (https://github.com/ansible/ansible/pull/65718)
- Make sure if a collection is supplied as a string that we transform it into a list.
- Misc typo fixes in various documentation pages.
- Module arguments in suboptions which were marked as deprecated with ``removed_in_version`` did not result in a warning.
- On HTTP status code 304, return status_code
- Plugin Metadata is supposed to have default values.  When the metadata was missing entirely, we were properly setting the defaults.  Fixed the metadata parsing so that the defaults are also set when we were missing just a few fields.
- Prevent a race condition when running handlers using a combination of the free strategy and include_role.
- Prevent rewriting nested Block's data in filter_tagged_tasks
- Prevent templating unused variables for {% include %} (https://github.com/ansible/ansible/issues/68699)
- Properly handle unicode in ``safe_eval``. (https://github.com/ansible/ansible/issues/66943)
- Python module_utils finder - refactor logic to eliminate many corner cases, remove recursion, fix base module_utils redirections
- Remove a temp directory created by wait_for_connection action plugin (https://github.com/ansible/ansible/issues/62407).
- Remove the unnecessary warning about aptitude not being installed (https://github.com/ansible/ansible/issues/56832).
- Remove unused Python imports in ``ansible-inventory``.
- Restore the ability for changed_when/failed_when to function with group_by (#70844).
- Role Installation - Ensure that a role containing files with non-ascii characters can be installed (https://github.com/ansible/ansible/issues/69133)
- RoleRequirement - include stderr in the error message if a scm command fails (https://github.com/ansible/ansible/issues/41336)
- SSH plugin - Improve error message when ssh client is not found on the host
- Skipping of become for ``network_cli`` connections now works when ``network_cli`` is sourced from a collection.
- Stop adding the connection variables to the output results
- Strictly check string datatype for 'tasks_from', 'vars_from', 'defaults_from', and 'handlers_from' in include_role (https://github.com/ansible/ansible/issues/68515).
- Strip no log values from module response keys (https://github.com/ansible/ansible/issues/68400)
- TaskExecutor - Handle unexpected errors as failed while post validating loops (https://github.com/ansible/ansible/issues/70050).
- TaskQueueManager - Explicitly set the mutliprocessing start method to ``fork`` to avoid issues with the default on macOS now being ``spawn``.
- Template connection variables before using them (https://github.com/ansible/ansible/issues/70598).
- Templating - Ansible was caching results of Jinja2 expressions in some cases where these expressions could have dynamic results, like password generation (https://github.com/ansible/ansible/issues/34144).
- Terminal plugins - add "\e[m" to the list of ANSI sequences stripped from device output
- The `ansible_become` value was not being treated as a boolean value when set in an INI format inventory file (fixes bug https://github.com/ansible/ansible/issues/70476).
- The ansible-galaxy publish command was using an incorrect URL for v3 servers. The configuration for v3 servers includes part of the path fragment that was added in the new test.
- The machine-readable changelog ``changelogs/changelog.yaml`` is now contained in the release.
- Update ActionBase._low_level_execute_command to honor executable (https://github.com/ansible/ansible/issues/68054)
- Update the warning message for ``CONDITIONAL_BARE_VARS`` to list the original conditional not the value of the original conditional (https://github.com/ansible/ansible/issues/67735)
- Use ``sys.exit`` instead of ``exit`` in ``ansible-inventory``.
- Use fqcr from command module invocation using shell module. Fixes https://github.com/ansible/ansible/issues/69788
- Use hostnamectl command to get current hostname for host while using systemd strategy (https://github.com/ansible/ansible/issues/59438).
- Using --start-at-task would fail when it attempted to skip over tasks with no name.
- Validate include args in handlers.
- Vault - Allow single vault encrypted values to be used directly as module parameters. (https://github.com/ansible/ansible/issues/68275)
- Vault - Make the single vaulted value ``AnsibleVaultEncryptedUnicode`` class work more like a string by replicating the behavior of ``collections.UserString`` from Python. These changes don't allow it to be considered a string, but most common python string actions will now work as expected. (https://github.com/ansible/ansible/pull/67823)
- ``AnsibleUnsafe``/``AnsibleContext``/``Templar`` - Do not treat ``AnsibleUndefined`` as being "unsafe" (https://github.com/ansible/ansible/issues/65198)
- account for empty strings in when splitting the host pattern (https://github.com/ansible/ansible/issues/61964)
- action plugins - change all action/module delegations to use FQ names while allowing overrides (https://github.com/ansible/ansible/issues/69788)
- add constraints file for ``anisble_runner`` test since an update to ``psutil`` is now causing test failures
- add magic/connection vars updates from delegated host info.
- add parameter name to warning message when values are converted to strings (https://github.com/ansible/ansible/pull/57145)
- add_host action now correctly shows idempotency/changed status
- added 'unimplemented' prefix to file based caching
- added new option for default callback to compat variable to avoid old 3rd party plugins from erroring out.
- adhoc CLI - when playbook-dir is specified and inside a collection, use default collection logic to resolve modules/actions
- allow external collections to be created in the 'ansible' collection namespace (https://github.com/ansible/ansible/issues/59988)
- also strip spaces around config values in pathlist as we do in list types
- ansiballz - remove '' and '.' from sys.path to fix a permissions issue on OpenBSD with pipelining (#69320)
- ansible command now correctly sends v2_playbook_on_start to callbacks
- ansible-connection persists even after playbook run is completed (https://github.com/ansible/ansible/pull/61591)
- ansible-doc - Allow and give precedence to `removed_at_date` for deprecated modules.
- ansible-doc - collection name for plugin top-level deprecation was not inserted when deprecating by version (https://github.com/ansible/ansible/pull/70344).
- ansible-doc - improve error message in text formatter when ``description`` is missing for a (sub-)option or a return value or its ``contains`` (https://github.com/ansible/ansible/pull/70046).
- ansible-doc - improve man page formatting to avoid problems when YAML anchors are used (https://github.com/ansible/ansible/pull/70045).
- ansible-doc - include the collection name in the text output (https://github.com/ansible/ansible/pull/70401).
- ansible-doc now properly handles removed modules/plugins
- ansible-galaxy - Default collection install path to first path in COLLECTIONS_PATHS (https://github.com/ansible/ansible/pull/62870)
- ansible-galaxy - Display proper error when invalid token is used for Galaxy servers
- ansible-galaxy - Ensure we preserve the new URL when appending ``/api`` for the case where the GET succeeds on galaxy.ansible.com
- ansible-galaxy - Expand the ``User-Agent`` to include more information and add it to more calls to Galaxy endpoints.
- ansible-galaxy - Fix ``collection install`` when installing from a URL or a file - https://github.com/ansible/ansible/issues/65109
- ansible-galaxy - Fix ``multipart/form-data`` body to include extra CRLF (https://github.com/ansible/ansible/pull/67942)
- ansible-galaxy - Fix issue when compared installed dependencies with a collection having no ``MANIFEST.json`` or an empty version string in the json
- ansible-galaxy - Fix pagination issue when retrieving role versions for install - https://github.com/ansible/ansible/issues/64355
- ansible-galaxy - Fix up pagination searcher for collection versions on Automation Hub
- ansible-galaxy - Fix url building to not truncate the URL (https://github.com/ansible/ansible/issues/61624)
- ansible-galaxy - Handle the different task resource urls in API responses from publishing collection artifacts to galaxy servers using v2 and v3 APIs.
- ansible-galaxy - Preserve symlinks when building and installing a collection
- ansible-galaxy - Remove uneeded verbose messages when accessing local token file
- ansible-galaxy - Return the HTTP code reason if no error msg was returned by the server - https://github.com/ansible/ansible/issues/64850
- ansible-galaxy - Send SHA256 hashes when publishing a collection
- ansible-galaxy - Set ``User-Agent`` to Ansible version when interacting with Galaxy or Automation Hub
- ansible-galaxy - Treat the ``GALAXY_SERVER_LIST`` config entry that is defined but with no values as an empty list
- ansible-galaxy - Utilize ``Templar`` for templating skeleton files, so that they have access to Ansible filters/tests/lookups (https://github.com/ansible/ansible/issues/69104)
- ansible-galaxy - fix a bug where listing a specific role if it was not in the first path failed to find the role
- ansible-galaxy - fix regression that prenented roles from being listed
- ansible-galaxy - hide warning during collection installation if other installed collections do not contain a ``MANIFEST.json`` (https://github.com/ansible/ansible/issues/67490)
- ansible-galaxy - properly list roles when the role name also happens to be in the role path (https://github.com/ansible/ansible/issues/67365)
- ansible-galaxy - properly show the role description when running offline (https://github.com/ansible/ansible/issues/60167)
- ansible-galaxy cli - fixed ``--version`` argument
- ansible-galaxy collection - Preserve executable bit on build and preserve mode on install from what tar member is set to - https://github.com/ansible/ansible/issues/68415
- ansible-galaxy collection download - fix downloading tar.gz files and collections in git repositories (https://github.com/ansible/ansible/issues/70429)
- ansible-galaxy collection install - fix fallback mechanism if the AH server did not have the collection requested - https://github.com/ansible/ansible/issues/70940
- ansible-galaxy role - Fix issue where ``--server`` was not being used for certain ``ansible-galaxy role`` actions - https://github.com/ansible/ansible/issues/61609
- ansible-galaxy- On giving an invalid subcommand to ansible-galaxy, the help would be shown only for role subcommand (collection subcommand help is not shown). With this change, the entire help for ansible-galaxy (same as ansible-galaxy --help) is displayed along with the help for role subcommand. (https://github.com/ansible/ansible/issues/69009)
- ansible-inventory - Fix long standing bug not loading vars plugins for group vars relative to the playbook dir when the '--playbook-dir' and '--export' flags are used together.
- ansible-inventory - Fix regression loading vars plugins. (https://github.com/ansible/ansible/issues/65064)
- ansible-inventory - Properly hide arguments that should not be shown (https://github.com/ansible/ansible/issues/61604)
- ansible-inventory - Restore functionality to allow ``--graph`` to be limited by a host pattern
- ansible-test - Add ``pytest < 6.0.0`` constraint for managed installations on Python 3.x to avoid issues with relative imports.
- ansible-test - Change detection now properly resolves relative imports instead of treating them as absolute imports.
- ansible-test - Code cleanup.
- ansible-test - Disabled the ``duplicate-code`` and ``cyclic-import`` checks for the ``pylint`` sanity test due to inconsistent results.
- ansible-test - Do not try to validate PowerShell modules ``setup.ps1``, ``slurp.ps1``, and ``async_status.ps1``
- ansible-test - Do not warn on missing PowerShell or C# util that are in other collections
- ansible-test - Fix PowerShell module util analysis to properly detect the names of a util when running in a collection
- ansible-test - Fix regression introduced in https://github.com/ansible/ansible/pull/67063 which caused module_utils analysis to fail on Python 2.x.
- ansible-test - Fix traceback in validate-modules test when argument_spec is None.
- ansible-test - Make sure import sanity test virtual environments also remove ``pkg-resources`` if it is not removed by uninstalling ``setuptools``.
- ansible-test - Remove out-of-date constraint on installing paramiko versions 2.5.0 or later in tests.
- ansible-test - The ``ansible-doc`` sanity test now works for ``netconf`` plugins.
- ansible-test - The ``import`` sanity test now correctly blocks access to python modules, not just packages, in the ``ansible`` package.
- ansible-test - The ``import`` sanity test now correctly provides an empty ``ansible`` package.
- ansible-test - The shebang sanity test now correctly identifies modules in subdirectories in collections.
- ansible-test - Updated Python constraints for installing ``coverage`` to resolve issues on multiple Python versions when using the ``--coverage`` option.
- ansible-test - Updated requirements to limit ``boto3`` and ``botocore`` versions on Python 2.6 to supported versions.
- ansible-test - Use ``sys.exit`` instead of ``exit``.
- ansible-test - Use ``virtualenv`` versions before 20 on provisioned macOS instances to remain compatible with an older pip install.
- ansible-test - avoid use of deprecated junit_xml method
- ansible-test - bump version of ACME test container. The new version includes updated dependencies.
- ansible-test - during module validation, handle add_file_common_args only for top-level arguments.
- ansible-test - during module validation, improve alias handling.
- ansible-test - for local change detection, allow to specify branch to compare to with ``--base-branch`` for all types of tests (https://github.com/ansible/ansible/pull/69508).
- ansible-test - improve ``deprecate()`` call checker.
- ansible-test - integration and unit test change detection now works for filter, lookup and test plugins
- ansible-test can now install argparse with ``--requirements`` or delegation when the pip version in use is older than version 7.1
- ansible-test change detection - Run only sanity tests on ``docs/`` and ``changelogs/`` in collections, to avoid triggering full CI runs of integration and unit tests when files in these directories change.
- ansible-test coverage - Fix the ``--all`` argument when generating coverage reports - https://github.com/ansible/ansible/issues/62096
- ansible-test import sanity test now consistently reports errors against the file being tested.
- ansible-test import sanity test now consistently reports warnings as errors.
- ansible-test import sanity test now properly handles relative imports.
- ansible-test import sanity test now properly invokes Ansible modules as scripts.
- ansible-test is now able to find its ``egg-info`` directory when it contains the Ansible version number
- ansible-test no longer errors reporting coverage when no Python coverage exists. This fixes issues reporting on PowerShell only coverage from collections.
- ansible-test no longer fails when downloading test results for a collection without a ``tests`` directory when using the ``--docker`` option.
- ansible-test no longer optimizes setting ``PATH`` by prepending the directory containing the selected Python interpreter when it is named ``python``. This avoids unintentionally making other programs available on ``PATH``, including an already installed version of Ansible.
- ansible-test no longer tracebacks during change analysis due to processing an empty python file
- ansible-test no longer tries to install ``coverage`` 5.0+ since those versions are unsupported
- ansible-test no longer tries to install ``setuptools`` 45+ on Python 2.x since those versions are unsupported
- ansible-test now always uses the ``--python`` option for ``virtualenv`` to select the correct interpreter when creating environments with the ``--venv`` option
- ansible-test now correctly collects code coverage on the last task in a play. This should resolve issues with missing code coverage, empty coverage files and corrupted coverage files resulting from early worker termination.
- ansible-test now correctly enumerates submodules when a collection resides below the repository root
- ansible-test now correctly excludes the test results temporary directory when copying files from the remote test system to the local system
- ansible-test now correctly includes inventory files ignored by git when running tests with the ``--docker`` option
- ansible-test now correctly installs the requirements specified by the collection's unit and integration tests instead of the requirements specified for Ansible's own unit and integration tests
- ansible-test now correctly recognizes imports in collections when using the ``--changed`` option.
- ansible-test now correctly rewrites coverage paths for PowerShell files when testing collections
- ansible-test now creates its integration test temporary directory within the collection so ansible-playbook can properly detect the default collection
- ansible-test now enables color ``ls`` on a remote host only if the host supports the feature
- ansible-test now ignores empty ``*.py`` files when analyzing module_utils imports for change detection
- ansible-test now ignores version control within subdirectories of collections. Previously this condition was an error.
- ansible-test now ignores warnings when comparing pip versions before and after integration tests run
- ansible-test now installs sanity test requirements specific to each test instead of installing requirements for all sanity tests
- ansible-test now installs the correct version of ``cryptography`` with ``--requirements`` or delegation when setuptools is older than version 18.5
- ansible-test now limits Jinja2 installs to version 2.10 and earlier on Python 2.6
- ansible-test now limits ``pathspec`` to versions prior to 0.6.0 on Python 2.6 to avoid installation errors
- ansible-test now limits installation of ``hcloud`` to Python 2.7 and 3.5 - 3.8 since other versions are unsupported
- ansible-test now limits the version of ``setuptools`` on Python 2.6 to versions older than 37
- ansible-test now loads the collection loader plugin early enough for ansible_collections imports to work in unit test conftest.py modules
- ansible-test now preserves existing SSH authorized keys when provisioning a remote host
- ansible-test now properly activates the vcenter plugin for vcenter tests when docker is available
- ansible-test now properly activates virtual environments created using the --venv option
- ansible-test now properly creates a virtual environment using ``venv`` when running in a ``virtualenv`` created virtual environment
- ansible-test now properly excludes the ``tests/output/`` directory from code coverage
- ansible-test now properly handles creation of Python execv wrappers when the selected interpreter is a script
- ansible-test now properly handles enumeration of git submodules. Enumeration is now done with ``git submodule status --recursive`` without specifying ``.`` for the path, since that could cause the command to fail. Instead, relative paths outside the current directory are filtered out of the results. Errors from ``git`` commands will now once again be reported as errors instead of warnings.
- ansible-test now properly handles warnings for removed modules/plugins
- ansible-test now properly ignores the ``tests/output//`` directory when not using git
- ansible-test now properly installs requirements for multiple Python versions when running sanity tests
- ansible-test now properly recognizes modules and module_utils in collections when using the ``blacklist`` plugin for the ``pylint`` sanity test
- ansible-test now properly registers its own code in a virtual environment when running from an install
- ansible-test now properly reports import errors for collections when running the import sanity test
- ansible-test now properly searches for ``pythonX.Y`` instead of ``python`` when looking for the real python that created a ``virtualenv``
- ansible-test now properly sets PYTHONPATH for tests when running from an Ansible installation
- ansible-test now properly sets ``ANSIBLE_PLAYBOOK_DIR`` for integration tests so unqualified collection references work for adhoc ``ansible`` usage
- ansible-test now properly uses a fresh copy of environment variables for each command invocation to avoid mixing vars between commands
- ansible-test now shows sanity test doc links when installed (previously the links were only visible when running from source)
- ansible-test now shows the correct source path instead of ``%s`` for collection role based test targets when the ``-v`` option is used
- ansible-test now supports submodules using older ``git`` versions which require querying status from the top level directory of the repo.
- ansible-test now updates SSH keys it generates with newer versions of ssh-keygen to function with Paramiko
- ansible-test now upgrades ``pip`` with `--requirements`` or delegation as needed when the pip version in use is older than version 7.1
- ansible-test now uses GNU tar format instead of the Python default when creating payloads for remote systems
- ansible-test now uses ``pycodestyle`` frozen at version 2.6.0 for consistent test results.
- ansible-test now uses modules from the ``ansible.windows`` collection for setup and teardown of ``windows-integration`` tests and code coverage
- ansible-test once again properly collects code coverage for ``ansible-connection``
- ansible-test validate-modules - Fix arg spec collector for PowerShell to find utils in both a collection and base.
- ansible-test validate-modules - ``version_added`` on module level was not validated for modules in collections (https://github.com/ansible/ansible/pull/70869).
- ansible-test validate-modules - return correct error codes ``option-invalid-version-added`` resp. ``return-invalid-version-added`` instead of the wrong error ``deprecation-either-date-or-version`` when an invalid value of ``version_added`` is specified for an option or a return value (https://github.com/ansible/ansible/pull/70869).
- ansible-test validate-modules sanity test code ``missing-module-utils-import-c#-requirements`` is now ``missing-module-utils-import-csharp-requirements`` (fixes ignore bug).
- ansible-test validate-modules sanity test code ``multiple-c#-utils-per-requires`` is now ``multiple-csharp-utils-per-requires`` (fixes ignore bug).
- ansible-test validate-modules sanity test now checks for AnsibleModule initialization instead of module_utils imports, which did not work in many cases.
- ansible-test validate-modules sanity test now properly handles collections imports using the Ansible collection loader.
- ansible-test validate-modules sanity test now properly handles relative imports.
- ansible-test validate-modules sanity test now properly handles sys.exit in modules.
- ansible-test validate-modules sanity test now properly invokes Ansible modules as scripts.
- ansible-test windows coverage - Ensure coverage reports are UTF-8 encoded without a BOM
- ansible-test windows coverage - Output temp files as UTF-8 with BOM to standardise against non coverage runs
- ansible-vault - Fix ``encrypt_string`` output in a tty when using ``--sdtin-name`` option (https://github.com/ansible/ansible/issues/65121)
- ansible-vault create - Fix exception on no arguments given
- api - time.clock is removed in Python 3.8, add backward compatible code (https://github.com/ansible/ansible/issues/70649).
- apt - Fixed the issue the cache being updated while auto-installing its dependencies even when ``update_cache`` is set to false.
- apt - include exception message from apt python library in error output
- assemble - fix decrypt argument in the module (https://github.com/ansible/ansible/issues/65450).
- assemble module - fix documentation - the remote_src property specified a default value of no but it's actually yes.
- avoid fatal traceback when a bad FQCN for a callback is supplied in the whitelist (#69401).
- basic - use PollSelector implementation when DefaultSelector fails (https://github.com/ansible/ansible/issues/70238).
- become - Fix various plugins that still used play_context to get the become password instead of through the plugin - https://github.com/ansible/ansible/issues/62367
- blockinfile - fix regression that results in incorrect block in file when the block to be inserted does not end in a line separator (https://github.com/ansible/ansible/pull/69734)
- blockinfile - preserve line endings on update (https://github.com/ansible/ansible/issues/64966)
- clean_facts - use correct variable to avoid unnecessary handling of ``AttributeError``
- code - removes some Python compatibility code for dealing with socket timeouts in ``wait_for``
- collection loader - ensure Jinja function cache is fully-populated before lookup
- collection loader - fixed relative imports on Python 2.7, ensure pluginloader caches use full name to prevent names from being clobbered (https://github.com/ansible/ansible/pull/60317)
- collection metadata - ensure collection loader uses libyaml/CSafeLoader to parse collection metadata if available
- collection_loader - sort Windows modules below other plugin types so the correct builtin plugin inside a role is selected (https://github.com/ansible/ansible/issues/65298)
- collections - Handle errors better for filters and tests in collections, where a non-existent collection is specified, or importing the plugin results in an exception (https://github.com/ansible/ansible/issues/66721)
- combine filter - ``[dict1, [dict2]] | combine`` now raise an error; previously ``combine`` had an undocumented behaviour where it was flattening the list before combining it (https://github.com/ansible/ansible/pull/57894#discussion_r339517518).
- config - encoding failures on config values should be non-fatal (https://github.com/ansible/ansible/issues/63310)
- copy - Fix copy modes when using remote_src=yes and src is a directory with trailing slash.
- copy - Fixed copy module not working in case that remote_src is enabled and dest ends in a / (https://github.com/ansible/ansible/pull/47238)
- copy - recursive copy with ``remote_src=yes`` now recurses beyond first level. (Fixes https://github.com/ansible/ansible/issues/58284)
- core - remove unneeded Python version checks.
- core - replace a compatibility import of pycompat24.literal_eval with ast.literal_eval.
- core filters - fix ``extract()`` filter when key does not exist in container (https://github.com/ansible/ansible/issues/64957)
- cron - encode and decode crontab files in UTF-8 explicitly to allow non-ascii chars in cron filepath and job (https://github.com/ansible/ansible/issues/69492)
- cron and cronvar - use get_bin_path utility to locate the default crontab executable instead of the hardcoded /usr/bin/crontab. (https://github.com/ansible/ansible/pull/59765)
- cron cronvar - only run ``get_bin_path()`` once
- cronvar - use correct binary name (https://github.com/ansible/ansible/issues/63274)
- deal with cases in which just a file is pased and not a path with directories, now fileglob correctly searches in 'files/' subdirs.
- debug - fixed an issue introduced in Ansible 2.4 where a loop of debug tasks would lose the "changed" status on each item.
- discovery will NOT update incorrect host anymore when in delegate_to task.
- display - Improve method of removing extra new line after warnings so it does not break Tower/Runner (https://github.com/ansible/ansible/pull/68517)
- display - remove extra new line after warnings (https://github.com/ansible/ansible/pull/65199)
- display - remove leading space when displaying WARNING messages
- display logging - Fix issue where 3rd party modules will print tracebacks when attempting to log information when ``ANSIBLE_LOG_PATH`` is set - https://github.com/ansible/ansible/issues/65249
- display logging - Fixed up the logging formatter to use the proper prefixes for ``u=user`` and ``p=process``
- display logging - Re-added the ``name`` attribute to the log formatter so that the source of the log can be seen
- dnf - Fix idempotence of `state: installed` (https://github.com/ansible/ansible/issues/64963)
- dnf - Unified error messages when trying to install a nonexistent package with newer dnf (4.2.18) vs older dnf (4.2.9)
- dnf - Unified error messages when trying to remove a wildcard name that is not currently installed, with newer dnf (4.2.18) vs older dnf (4.2.9)
- dnf - enable logging using setup_loggers() API in dnf-4.2.17-6 or later
- dnf - remove custom ``fetch_rpm_from_url`` method in favor of more general ``ansible.module_utils.urls.fetch_file``.
- dnf module - Ensure the modules exit_json['msg'] response is always string, not sometimes a tuple.
- ensure delegated vars can resolve hostvars object and access vars from hostvars[inventory_hostname].
- ensure we pass on interpreter discovery values to delegated host.
- env lookup plugin - Fix handling of environment variables values containing utf-8 characters. (https://github.com/ansible/ansible/issues/65298)
- fact gathering - Display warnings and deprecation messages that are created during the fact gathering phase
- facts - account for Slackware OS with ``+`` in the name (https://github.com/ansible/ansible/issues/38760)
- facts - fix detection of virtualization type when dmi product name is KVM Server
- facts - fix incorrect UTC timestamp in ``iso8601_micro`` and ``iso8601``
- facts - introduce fact "ansible_processor_nproc" which reflects the number of vcpus available to processes (falls back to the number of vcpus available to the scheduler)
- file - Removed unreachable code in module
- file - change ``_diff_peek`` in argument spec to be the correct type, which is ``bool`` (https://github.com/ansible/ansible/issues/59433)
- file - return ``'state': 'absent'`` when a file does not exist (https://github.com/ansible/ansible/issues/66171)
- find - clarify description of ``contains`` (https://github.com/ansible/ansible/issues/61983)
- fix issue in which symlinked collection cannot be listed, though the docs/plugins can be loaded if referenced directly.
- fix issue with inventory_hostname and delegated host vars mixing on connection settings.
- fix wrong command line length calculation in ``ansible-console`` when long command inputted
- for those running uids for invalid users (containers), fallback to uid=<uid> when logging fixes #68007
- free strategy - Include failed hosts when filtering notified hosts for handlers. The strategy base should determine whether or not to run handlers on those hosts depending on whether forcing handlers is enabled (https://github.com/ansible/ansible/issues/65254).
- galaxy - Fix an AttributeError on ansible-galaxy install with an empty requirements.yml (https://github.com/ansible/ansible/issues/66725).
- get_url - Don't treat no checksum as a checksum match (https://github.com/ansible/ansible/issues/61978)
- get_url pass incorrect If-Modified-Since header (https://github.com/ansible/ansible/issues/67417)
- git - when force=True, apply --force flag to git fetches as well
- group - The group module was not correctly detecting whether a local group is existing or not with local set to yes if the same group exists in a non local group repository e.g. LDAP. (https://github.com/ansible/ansible/issues/58619)
- group_by now should correctly refect changed status.
- hostname - Fixed an issue where the hostname on the cloudlinux 6 server could not be set.
- hostname - make module work on Manjaro Linux (https://github.com/ansible/ansible/issues/61382)
- hurd - Address FIXMEs. Extract functionality and exit early.
- if the ``type`` for a module parameter in the argument spec is callable, do not pass ``kwargs`` to avoid errors (https://github.com/ansible/ansible/issues/70017)
- include_vars - fix stack trace when passing ``dirs`` in an ad-hoc command (https://github.com/ansible/ansible/issues/62633)
- interpreter discovery will now use correct vars (from delegated host) when in delegate_to task.
- junit callback - avoid use of deprecated junit_xml method
- lineinfile - add example of using alternative backrefs syntax (https://github.com/ansible/ansible/issues/42794)
- lineinfile - don't attempt mkdirs when path doesn't contain directory path
- lineinfile - fix bug that caused multiple line insertions (https://github.com/ansible/ansible/issues/58923).
- lineinfile - fix not subscriptable error in exception handling around file creation
- lineinfile - properly handle inserting a line when backrefs are enabled and the line already exists in the file (https://github.com/ansible/ansible/issues/63756)
- lineinfile - use ``module.tmpdir`` to allow configuration of the remote temp directory (https://github.com/ansible/ansible/issues/68218)
- lineinfile - use correct index value when inserting a line at the end of a file (https://github.com/ansible/ansible/issues/63684)
- loops - Do not indiscriminately mark loop items as unsafe, only apply unsafe to ``with_`` style loops. The items from ``loop`` should not be explicitly wrapped in unsafe. The underlying templating mechanism should dictate this. (https://github.com/ansible/ansible/issues/64379)
- make ``no_log=False`` on a module option silence the ``no_log`` warning (https://github.com/ansible/ansible/issues/49465 https://github.com/ansible/ansible/issues/64656)
- match docs for ssh and ensure pipelining is configurable per connection plugin.
- module executor - Address issue where changes to Ansiballz module code, change the behavior of module execution as it pertains to ``__file__`` and ``sys.modules`` (https://github.com/ansible/ansible/issues/64664)
- module_defaults - support candidate action names for relocated content
- module_defaults - support short group names for content relocated to collections
- now correclty merge and not just overwrite facts when gathering using multiple modules.
- objects - Remove FIXME comment because no fix is needed.
- optimize 'smart' detection from being run over and over and preferably do it at config time.
- package_facts - fix value of ``vital`` attribute which is returned when ``pkg`` manager is used
- package_facts - use module warnings rather than a custom implementation for reporting warnings
- packaging_yum - replace legacy file handling with a file manager.
- paramiko - catch and handle exception to prevent stack trace when running in FIPS mode
- paramiko_ssh - Removed redundant conditional statement in ``_parse_proxy_command`` that always evaluated to True.
- paramiko_ssh - improve authentication error message so it is less confusing
- paramiko_ssh - optimized file handling by using a context manager.
- pause - handle exception when there is no stdout (https://github.com/ansible/ansible/pull/47851)
- pip - The virtualenv_command option can now include arguments without requiring the full path to the binary. (https://github.com/ansible/ansible/issues/52275)
- pip - check_mode with ``state: present`` now returns the correct state for pre-release versioned packages
- playbooks - detect and propagate failures in ``always`` blocks after ``rescue`` (https://github.com/ansible/ansible/issues/70000)
- plugins - Allow ensure_type to decrypt the value for string types (and implicit string types) when value is an inline vault.
- psexec - Fix issue where the Kerberos package was not detected as being available.
- psexec - Fix issue where the ``interactive`` option was not being passed down to the library.
- reboot - Add support for the runit init system, used on Void Linux, that does not support the normal Linux syntax.
- reboot, win_reboot - add ``boot_time_command`` parameter to override the default command used to determine whether or not a system was rebooted (https://github.com/ansible/ansible/issues/58868)
- remove update/restore of vars from play_context as it is now redundant.
- replace use of deprecated functions from ``ansible.module_utils.basic``.
- reset logging level to INFO due to CVE-2019-14846.
- roles - Ensure that ``allow_duplicates: true`` enables to run single role multiple times (https://github.com/ansible/ansible/issues/64902)
- runas - Fix the ``runas`` ``become_pass`` variable fallback from ``ansible_runas_runas`` to ``ansible_runas_pass``
- service_facts - Now correctly parses systemd list-unit-files for systemd >=245
- setup - properly detect yum package manager for IBM i.
- setup - service_mgr - detect systemd even if it isn't running, such as during a container build
- shell - fix quoting of mkdir command in creation of remote_tmp in order to allow spaces and other special characters (https://github.com/ansible/ansible/issues/69577).
- shell cmd - Properly escape double quotes in the command argument
- splunk httpapi plugin - switch from splunk.enterprise_security to splunk.es in runtime.yml to reflect upstream change of Collection Name
- ssh connection plugin - use ``get_option()`` rather than ``_play_context`` to ensure ``ANSBILE_SSH_ARGS`` are applied properly (https://github.com/ansible/ansible/issues/70437)
- synchronize - allow data to be passed between two managed nodes when using the docker connection plugin (https://github.com/ansible/ansible/pull/65698)
- synchronize - fix password authentication on Python 2 (https://github.com/ansible/ansible/issues/56629)
- sysctl - Remove FIXME comments to avoid confusion
- systemd - don't require systemd to be running to enable/disable or mask/unmask units
- systemd - the module should fail in check_mode when service not found on host (https://github.com/ansible/ansible/pull/68136).
- sysvinit - Add missing parameter ``module`` in call to ``daemonize()``.
- template lookup - ensure changes to the templar in the lookup, do not affect the templar context outside of the lookup (https://github.com/ansible/ansible/issues/60106)
- template lookup - fix regression when templating hostvars (https://github.com/ansible/ansible/issues/63940)
- the default parsing will now show existing JSON errors and not just YAML (last attempted), also we avoid YAML parsing when we know we only want JSON issue
- throttle: the linear strategy didn't always stuck with the throttle limit
- unarchive - Remove incorrect and unused function arguments.
- unsafe_proxy - Ensure that data within a tuple is marked as unsafe (https://github.com/ansible/ansible/issues/65722)
- update ``user`` module to support silencing ``no_log`` warnings in the future (see: https://github.com/ansible/ansible/pull/64733)
- uri - Don't return the body even if it failed (https://github.com/ansible/ansible/issues/21003)
- user - allow 13 asterisk characters in password field without warning
- user - don't create home directory and missing parents when create_home == false (https://github.com/ansible/ansible/pull/70600).
- user - fix comprasion on macOS so module does not improperly report a change (https://github.com/ansible/ansible/issues/62969)
- user - fix stack trace on AIX when attempting to parse shadow file that does not exist (https://github.com/ansible/ansible/issues/62510)
- user - on systems using busybox, honor the ``on_changed`` parameter to prevent unnecessary password changing (https://github.com/ansible/ansible/issues/65711)
- user - update docs to reflect proper way to remove account from all groups
- validate-modules - Fix hang when inspecting module with a delegate args spec type
- virtual facts - detect generic container environment based on non-empty "container" env var
- wait_for_connection - with pipelining enabled, interpreter discovery would fail if the first connection attempt was not successful
- win setup - Fix redirection path for the windows setup module
- win_exec_wrapper - Be more defensive when it comes to getting unhandled exceptions
- win_package - Handle quoted and unquoted strings in the registry ``UninstallString`` value - https://github.com/ansible/ansible/issues/40973
- win_uri win_get_url - Fix the behaviour of ``follow_redirects: safe`` to actual redirect on ``GET`` and ``HEAD`` requests - https://github.com/ansible/ansible/issues/65556
- windows async - use full path when calling PowerShell to reduce reliance on environment vars being correct - https://github.com/ansible/ansible/issues/70655
- windows environment - Support env vars that contain the unicode variant of single quotes - https://github.com/ansible-collections/ansible.windows/issues/45
- winrm - preserve winrm forensic data on put_file failures
- yum - fix bug that caused ``enablerepo`` to not be honored when used with disablerepo all wildcard/glob (https://github.com/ansible/ansible/issues/66549)
- yum - fixed the handling of releasever parameter
- yum - performance bugfix, the YumBase object was being  instantiated multiple times unnecessarily, which lead to considerable overhead when operating against large sets of packages.
- yum - yum tasks can no longer end up running non-yum modules
- yum/dnf - check type of elements in a name

New Plugins
-----------

Lookup
~~~~~~

- unvault - read vaulted file(s) contents
