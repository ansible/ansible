=========================================================
ansible-core 2.13 "Nobody's Fault but Mine" Release Notes
=========================================================

.. contents:: Topics


v2.13.5
=======

Release Summary
---------------

| Release Date: 2022-10-10
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Bugfixes
--------

- ``ansible-galaxy`` - remove extra server api call during dependency resolution for requirements and dependencies that are already satisfied (https://github.com/ansible/ansible/issues/77443).
- ansible-test - Allow disabled, unsupported, unstable and destructive integration test targets to be selected using their respective prefixes.
- ansible-test - Allow unstable tests to run when targeted changes are made and the ``--allow-unstable-changed`` option is specified (resolves https://github.com/ansible/ansible/issues/74213).
- apt - Fix module failure when a package is not installed and only_upgrade=True. Skip that package and check the remaining requested packages for upgrades. (https://github.com/ansible/ansible/issues/78762)
- apt module should not traceback on invalid type given as package. issue 78663.
- known_hosts - do not return changed status when a non-existing key is removed (https://github.com/ansible/ansible/issues/78598)
- paramiko - Add back support for ``ssh_args``, ``ssh_common_args``, and ``ssh_extra_args`` for parsing the ``ProxyCommand`` (https://github.com/ansible/ansible/issues/78750)
- plugin loader, fix detection for existing configuration before initializing for a plugin

v2.13.4
=======

Release Summary
---------------

| Release Date: 2022-09-12
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Bugfixes
--------

- Fix for network_cli not getting all relevant connection options
- ansible-galaxy - Fix detection of ``--role-file`` in arguments for implicit role invocation (https://github.com/ansible/ansible/issues/78204)
- ansible-galaxy - Fix exit codes for role search and delete (https://github.com/ansible/ansible/issues/78516)
- ansible-test - Fix change detection for ansible-test's own integration tests.
- ansible-test - ansible-doc sanity test - Correctly determine the fully-qualified collection name for plugins in subdirectories, resolving https://github.com/ansible/ansible/issues/78490.
- apt - don't actually update the cache in check mode with update_cache=true.
- apt - don't mark existing packages as manually installed in check mode (https://github.com/ansible/ansible/issues/66413).
- apt - fix package selection to include /etc/apt/preferences(.d) (https://github.com/ansible/ansible/issues/77969)
- urls - Guard imports of ``urllib3`` by catching ``Exception`` instead of ``ImportError`` to prevent exceptions in the import process of optional dependencies from preventing use of ``urls.py`` (https://github.com/ansible/ansible/issues/78648)
- wait_for - Read file and perform comparisons using bytes to avoid decode errors (https://github.com/ansible/ansible/issues/78214)

v2.13.3
=======

Release Summary
---------------

| Release Date: 2022-08-15
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Bugfixes
--------

- Avoid 'unreachable' error when chmod on AIX has 255 as return code.
- Fix PluginLoader to mimic Python import machinery by adding module to sys.modules before exec
- Fix dnf module documentation to indicate that comparison operators for package version require spaces around them (https://github.com/ansible/ansible/issues/78295)
- ansible-connection - decrypt vaulted parameters before sending over the socket, as vault secrets are not available on the other side.
- ansible-galaxy - Fix reinitializing the whole collection directory with ``ansible-galaxy collection init ns.coll --force``. Now directories and files that are not included in the collection skeleton will be removed.
- ansible-galaxy - do not require mandatory keys in the ``galaxy.yml`` of source collections when listing them (https://github.com/ansible/ansible/issues/70180).
- ansible-galaxy - fix listing collections that contains metadata but the namespace or name are not strings.
- ansible-galaxy - fix setting the cache for paginated responses from Galaxy NG/AH (https://github.com/ansible/ansible/issues/77911).
- ansible-test - Delegation for commands which generate output for programmatic consumption no longer redirect all output to stdout. The affected commands and options are ``shell``, ``sanity --lint``, ``sanity --list-tests``, ``integration --list-targets``, ``coverage analyze``
- ansible-test - Delegation now properly handles arguments given after ``--`` on the command line.
- ansible-test - Test configuration for collections is now parsed only once, prior to delegation. Fixes issue: https://github.com/ansible/ansible/issues/78334
- ansible-test - The ``shell`` command no longer redirects all output to stdout when running a provided command. Any command output written to stderr will be mixed with the stderr output from ansible-test.
- ansible-test - The ``shell`` command no longer requests a TTY when using delegation unless an interactive shell is being used. An interactive shell is the default behavior when no command is given to pass to the shell.
- dnf - fix output parsing on systems with ``LANGUAGE`` set to a language other than English (https://github.com/ansible/ansible/issues/78193)
- if a config setting prevents running ansible it should at least show it's "origin".
- prevent type annotation shim failures from causing runtime failures (https://github.com/ansible/ansible/pull/77860)
- template module/lookup - fix ``convert_data`` option that was effectively always set to True for Jinja macros (https://github.com/ansible/ansible/issues/78141)
- uri - properly use uri parameter use_proxy (https://github.com/ansible/ansible/issues/58632)
- yum - fix traceback when ``releasever`` is specified with ``latest`` (https://github.com/ansible/ansible/issues/78058)

v2.13.2
=======

Release Summary
---------------

| Release Date: 2022-07-18
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

- ansible-test - An improved error message is shown when the download of a pip bootstrap script fails. The download now uses ``urllib2`` instead of ``urllib`` on Python 2.

Bugfixes
--------

- Move undefined check from concat to finalize (https://github.com/ansible/ansible/issues/78156)
- ansible-doc - no longer list module and plugin aliases that are created with symlinks (https://github.com/ansible/ansible/pull/78137).
- ansible-doc - when listing modules in collections, proceed recursively. This fixes module listing for community.general 5.x.y and community.network 4.x.y (https://github.com/ansible/ansible/pull/78137).
- ansible-doc will not add 'website for' in ":ref:" substitutions as it made them confusing.
- file backed cache plugins now handle concurrent access by making atomic updates to the files.
- password lookup does not ignore k=v arguments anymore.
- user - Fix error "Permission denied" in user module while generating SSH keys (https://github.com/ansible/ansible/issues/78017).

v2.13.1
=======

Release Summary
---------------

| Release Date: 2022-06-20
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Minor Changes
-------------

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
- ansible-galaxy - Support resolvelib versions 0.6.x, 0.7.x, and 0.8.x. The full range of supported versions is now >= 0.5.3, < 0.9.0.
- ansible-test - Add RHEL 9.0 remote support.
- ansible-test - Add support for Ubuntu VMs using the ``--remote`` option.
- ansible-test - Add support for exporting inventory with ``ansible-test shell --export {path}``.
- ansible-test - Add support for multi-arch remotes.
- ansible-test - Add support for running non-interactive commands with ``ansible-test shell``.
- ansible-test - Avoid using the ``mock_use_standalone_module`` setting for unit tests running on Python 3.8 or later.
- ansible-test - Blocking mode is now enforced for stdin, stdout and stderr. If any of these are non-blocking then ansible-test will exit during startup with an error.
- ansible-test - Improve consistency of output messages by using stdout or stderr for most output, but not both.
- ansible-test - The ``shell`` command can be used outside a collection if no controller delegation is required.

Bugfixes
--------

- Add PyYAML >= 5.1 as a dependency of ansible-core to be compatible with Python 3.8+.
- ansible-config dump - Only display plugin type headers when plugin options are changed if --only-changed is specified.
- ansible-galaxy - handle unsupported versions of resolvelib gracefully.
- ansible-test - Fix internal validation of remote completion configuration.
- ansible-test - Prevent ``--target-`` prefixed options for the ``shell`` command from being combined with legacy environment options.
- ansible-test - Sanity test output with the ``--lint`` option is no longer mixed in with bootstrapping output.
- ansible-test - Subprocesses are now isolated from the stdin, stdout and stderr of ansible-test. This avoids issues with subprocesses tampering with the file descriptors, such as SSH making them non-blocking. As a result of this change, subprocess output from unit and integration tests on stderr now go to stdout.
- ansible-test - Subprocesses no longer have access to the TTY ansible-test is connected to, if any. This maintains consistent behavior between local testing and CI systems, which typically do not provide a TTY. Tests which require a TTY should use pexpect or another mechanism to create a PTY.
- apt module now correctly handles virtual packages.
- lookup plugin - catch KeyError when lookup returns dictionary (https://github.com/ansible/ansible/pull/77789).
- pip - fix cases where resolution of pip Python module fails when importlib.util has not already been imported
- plugin loader - Sort results when fuzzy matching plugin names (https://github.com/ansible/ansible/issues/77966).
- plugin loader will now load config data for plugin by name instead of by file to avoid issues with the same file being loaded under different names (fqcn + short name).
- psrp connection now handles default to inventory_hostname correctly.
- winrm connection now handles default to inventory_hostname correctly.

v2.13.0
=======

Release Summary
---------------

| Release Date: 2022-05-16
| `Porting Guide <https://docs.ansible.com/ansible/devel/porting_guides.html>`__


Major Changes
-------------

- Jinja2 Controller Requirement - Jinja2 3.0.0 or newer is required for the control node (the machine that runs Ansible) (https://github.com/ansible/ansible/pull/75881)
- Templating - remove ``safe_eval`` in favor of using ``NativeEnvironment`` but utilizing ``literal_eval`` only in cases when ``safe_eval`` was used (https://github.com/ansible/ansible/pull/75587)

Minor Changes
-------------

- Action Plugins - Add helper method for argument spec validation, and extend to pause and async_wrapper
- Added AIX root CA certs folders - enhance the TLS support in ``uri`` task on AIX
- Added ``module_utils.compat.typing`` to facilitate type-hinting on all supported Python versions.
- Ansible.Basic - small changes to allow use in PowerShell modules running on non-Windows platforms (https://github.com/ansible/ansible/pull/76924).
- AnsibleModule.run_command() now has a toggle to allow caller to decide to handle exceptions from executing the command itself
- Attach concat function to an environment class (https://github.com/ansible/ansible/pull/76282)
- Clarify in a comment that unrolling an iterator in ``Templar._finalize`` is actually necessary. Also switch to using the ``_unroll_iterator`` decorator directly to deduplicate code in ``Templar._finalize``. (https://github.com/ansible/ansible/pull/76436)
- Installation - modernize our python installation, to reduce dynamic code in setup.py, and migrate what is feasible to setup.cfg. This will enable shipping wheels in the future.
- PlayIterator - introduce public methods to access ``PlayIterator._host_states`` (https://github.com/ansible/ansible/pull/74416)
- PlayIterator - use enums for Iterating and Failed states (https://github.com/ansible/ansible/pull/74511)
- Reduce number of iterations through PlayIterator (https://github.com/ansible/ansible/pull/74175)
- Remove more Python 2.x compatibility code from controller (https://github.com/ansible/ansible/pull/77320).
- Start of moving away from using Six, Python 2 and 3 compatibility library (https://github.com/ansible/ansible/pull/75863)
- The collection loader now reports a Python warning if an attempt is made to install the Ansible collection loader a second time. Previously this condition was reported using an Ansible warning.
- ``ansible-galaxy collection [install|verify]`` - allow user-provided signature sources in addition to those from the Galaxy server. Each collection entry in a requirements file can specify a ``signatures`` key followed by a list of sources. Collection name(s) provided on the CLI can specify additional signature sources by using the ``--signatures`` CLI option. Signature sources should be URIs that can be opened with ``urllib.request.urlopen()``, such as "https://example.com/path/to/detached_signature.asc" or "file:///path/to/detached_signature.asc". The ``--keyring`` option must be specified if signature sources are provided.
- ``ansible-galaxy collection [install|verify]`` - use gpg to verify the authenticity of the signed ``MANIFEST.json`` with ASCII armored detached signatures provided by the Galaxy server. The keyring (which is not managed by ``ansible-galaxy``) must be provided with the ``--keyring`` option to use signature verification. If no ``--keyring`` is specified and the collection to ``install|verify`` has associated detached signatures on the Galaxy server, a warning is provided.
- ``ansible-galaxy collection install`` - Add a global configuration to modify the required number of signatures that must verify the authenticity of the collection. By default, the number of required successful signatures is 1. Set this option to ``all`` to require all signatures verify the collection. To ensure signature verification fails if there are no valid signatures, prepend the value with '+', such as ``+all`` or ``+1``.
- ``ansible-galaxy collection install`` - Add a global ignore list for gpg signature errors. This can be used to ignore certain signatures when the number of required successful signatures is all. When the required number of successful signatures is a positive integer, the only effect this has is to display fewer errors to the user on failure (success is determined by having the minimum number of successful signatures, in which case all errors are disregarded).
- ``ansible-galaxy collection install`` - Add a global toggle to turn off GPG signature verification.
- ``ansible-galaxy collection install`` - Store Galaxy server metadata alongside installed collections for provenance. Signatures obtained from the Galaxy server can be used for offline verification with ``ansible-galaxy collection verify --offline``.
- ansible-console - Provide a  way to customize the stdout callback
- ansible-core modules - Remove unused Python shebangs from built-in modules.
- ansible-doc metadata dump - add option ``--no-fail-on-errors`` which allows to not fail the ansible-doc invocation when errors happen during docs parsing or processing. Instead they are reported in the JSON result in an ``error`` key for the affected plugins (https://github.com/ansible/ansible/pull/77035).
- ansible-galaxy - the option to skip certificate verification now also applies when cloning via SCM (git/hg) (https://github.com/ansible/ansible/issues/41077)
- ansible-test - Accept new-style Python modules without a shebang.
- ansible-test - Add ``--version`` support to show the ansible-core version.
- ansible-test - Add support for ``rhel/8.5`` remote instances.
- ansible-test - Add support for remote testing of FreeBSD 12.3.
- ansible-test - Add support for running container tests with ``podman remote`` (https://github.com/ansible/ansible/pull/75753)
- ansible-test - Added the ``fedora35`` test container.
- ansible-test - Change the maximum number of open files in a test container from the default to ``10240``.
- ansible-test - Declare public dependencies of ansible-core and use to limit unguarded imports in plugins.
- ansible-test - Importing ``distutils`` now results in an error.
- ansible-test - Installation of ``cryptography`` is no longer version constrained when ``openssl`` 1.1.0 or later is installed.
- ansible-test - Miscellaneous code cleanup and type hint fixes.
- ansible-test - PowerShell in the ``base`` and ``default`` containers has been upgraded to version 7.1.4.
- ansible-test - Remove RHEL 8.4 remote (``rhel/8.4``) support.
- ansible-test - Remove ``idna`` constraint.
- ansible-test - Remove obsolete ``MAXFD`` display.
- ansible-test - Remove obsolete constraints for Python 2.6.
- ansible-test - Remove support for FreeBSD 12.2 remote provisioning.
- ansible-test - Remove support for macOS 11.1 remote provisioning.
- ansible-test - Remove support for provisioning remote AIX instances.
- ansible-test - Remove the ``centos8`` test container since CentOS 8 will reach end-of-life soon.
- ansible-test - Remove the ``fedora33`` test container since Fedora 33 will reach end-of-life soon.
- ansible-test - Remove unused Python 2.x compatibility code.
- ansible-test - Removed support for Sherlock from the Azure provisioning plugin.
- ansible-test - Removed used ``MarkupSafe`` constraint for Python 3.5 and earlier.
- ansible-test - Requirements for the plugin import test are now frozen.
- ansible-test - Shellcheck in the ``base`` and ``default`` containers has been upgraded to version 0.7.0.
- ansible-test - Stop early with an error if the current working directory contains an invalid collection namespace or name.
- ansible-test - The ``--help`` option is now available when an unsupported cwd is in use.
- ansible-test - The ``--help`` output now shows the same instructions about cwd as would be shown in error messages if the cwd is unsupported.
- ansible-test - The ``pip`` and ``wheel`` packages are removed from all sanity test virtual environments after installation completes to reduce their size. Previously they were only removed from the environments used for the ``import`` sanity test.
- ansible-test - The explanation about cwd usage has been improved to explain more clearly what is required.
- ansible-test - The hash for all managed sanity test virtual environments has changed. Containers that include ``ansible-test sanity --prime-venvs`` will need to be rebuilt to continue using primed virtual environments.
- ansible-test - Update ``base`` container to version 2.1.0.
- ansible-test - Update ``base`` container to version 2.2.0.
- ansible-test - Update ``default`` containers to version 5.2.0.
- ansible-test - Update ``default`` containers to version 5.4.0.
- ansible-test - Update ``default`` containers to version 5.5.0.
- ansible-test - Update ``default`` containers to version 5.6.2.
- ansible-test - Update ``default`` containers to version 5.7.0.
- ansible-test - Update ``default`` containers to version 5.8.0.
- ansible-test - Update ``default`` containers to version 5.9.0.
- ansible-test - Update ``pip`` used to bootstrap remote FreeBSD instances from version 20.3.4 to 21.3.1.
- ansible-test - Update sanity test requirements.
- ansible-test - Update the NIOS test plugin container to version 1.4.0.
- ansible-test - Update the ``alpine`` container to version 3.3.0. This updates the base image from 3.14.2 to 3.15.0, which includes support for installing binary wheels using pip.
- ansible-test - Update the ``base`` and ``default`` containers from Python 3.10.0rc2 to 3.10.0.
- ansible-test - Update the ``base`` and ``default`` containers from a Ubuntu 18.04 to Ubuntu 20.04 base image.
- ansible-test - Update the ``default`` containers to version 5.1.0.
- ansible-test - Update the ``galaxy`` test plugin to get its container from a copy on quay.io.
- ansible-test - Update the ``openshift`` test plugin to get its container from a copy on quay.io.
- ansible-test - Use Python 3.10 as the default Python version for the ``base`` and ``default`` containers.
- ansible-test - add macOS 12.0 as a remote target (https://github.com/ansible/ansible/pull/76328)
- ansible-test - handle JSON decode error gracefully in podman environment.
- ansible-test pslint - Added the `AvoidLongLines <https://github.com/PowerShell/PSScriptAnalyzer/blob/master/docs/Rules/AvoidLongLines.md>`_ rule set to a length of 160.
- ansible-test pslint - Added the `PlaceCloseBrace <https://github.com/PowerShell/PSScriptAnalyzer/blob/master/docs/Rules/PlaceCloseBrace.md>`_ rule set to enforce close braces on a newline.
- ansible-test pslint - Added the `PlaceOpenBrace <https://github.com/PowerShell/PSScriptAnalyzer/blob/master/docs/Rules/PlaceOpenBrace.md>`_ rule set to enforce open braces on the same line and a subsequent newline.
- ansible-test pslint - Added the `UseConsistentIndentation <https://github.com/PowerShell/PSScriptAnalyzer/blob/master/docs/Rules/UseConsistentIndentation.md>`_ rule to enforce indentation is done with 4 spaces.
- ansible-test pslint - Added the `UseConsistentWhitespace <https://github.com/PowerShell/PSScriptAnalyzer/blob/master/docs/Rules/UseConsistentWhitespace.md>`_ rule to enforce whitespace consistency in PowerShell.
- ansible-test pslint - Updated ``PowerShellScriptAnalyzer`` to 1.20.0
- ansible-test sanity validate-modules - the validate-modules sanity test now also checks the documentation of documentable plugin types (https://github.com/ansible/ansible/pull/71734).
- ansible-test validate-modules sanity test - add more schema checks to improve quality of plugin documentation (https://github.com/ansible/ansible/pull/77268).
- ansible-test validate_modules - allow ``choices`` for return values (https://github.com/ansible/ansible/pull/76009).
- apt - Add support for using ">=" in package version number matching.
- apt - Adds APT option ``--allow-change-held-packages`` as module parameter ``allow_change_held_packages`` to allow APT up- or downgrading a package which is on APTs hold list (https://github.com/ansible/ansible/issues/65325)
- auto inventory plugin will now give plugin loading information on verbose output
- callbacks - Add result serialization format options to ``_dump_results`` allowing plugins such as the ``default`` callback to emit ``YAML`` serialized task results in addition to ``JSON``
- dnf - add more specific error message for GPG validation (https://github.com/ansible/ansible/issues/76192)
- env lookup, add default option
- facts - report prefix length for IPv4 addresses in Linux network facts.
- get_parsable_locale now logs result when in debug mode.
- git - display the destination directory path in error msg when local_mods detects local modifications conflict so that users see the exact location
- iptables - add the ``chain_management`` parameter that controls iptables chain creation and deletion
- jinja2_native - keep same behavior on Python 3.10.
- junit callback - Add support for replacing the directory portion of out-of-tree relative task paths with a placeholder.
- k8s - scenario guides for kubernetes migrated to ``kubernetes.core`` collection.
- module_utils.distro - Add missing ``typing`` import from original code.
- package_facts - add pkg_info support for OpenBSD and NetBSD (https://github.com/ansible/ansible/pull/76580)
- services_facts - Add support for openrc (https://github.com/ansible/ansible/pull/76373).
- setting DEFAULT_FACT_PATH is being deprecated in favor of the generic module_defaults keyword
- uri - Avoid reading the response body when not needed
- uri - Eliminate multiple requests to determine the final URL for file naming with ``dest``
- validate-modules - do some basic validation on the ``M(...)``, ``U(...)``, ``L(..., ...)`` and ``R(..., ...)`` documentation markups (https://github.com/ansible/ansible/pull/76262).
- vmware - migrated vmware scenario guides to `community.vmware` repo.
- yum, dnf - add sslverify option to temporarily disable certificate validation for a repository

Breaking Changes / Porting Guide
--------------------------------

- Module Python Dependency - Drop support for Python 2.6 in module execution.
- Templating - it is no longer allowed to perform arithmetic and concatenation operations outside of the jinja template (https://github.com/ansible/ansible/pull/75587)
- The ``finalize`` method is no longer exposed in the globals for use in templating.

Deprecated Features
-------------------

- ansible-core - Remove support for Python 2.6.
- ansible-test - Remove support for Python 2.6.
- ssh connection plugin option scp_if_ssh in favor of ssh_transfer_method.

Removed Features (previously deprecated)
----------------------------------------

- Remove deprecated ``Templar.set_available_variables()`` method (https://github.com/ansible/ansible/issues/75828)
- cli - remove deprecated ability to set verbosity before the sub-command (https://github.com/ansible/ansible/issues/75823)
- copy - remove deprecated ``thirsty`` alias (https://github.com/ansible/ansible/issues/75824)
- psrp - Removed fallback on ``put_file`` with older ``pypsrp`` versions. Users must have at least ``pypsrp>=0.4.0``.
- url_argument_spec - remove deprecated ``thirsty`` alias for ``get_url`` and ``uri`` modules (https://github.com/ansible/ansible/issues/75825, https://github.com/ansible/ansible/issues/75826)

Security Fixes
--------------

- Do not include params in exception when a call to ``set_options`` fails. Additionally, block the exception that is returned from being displayed to stdout. (CVE-2021-3620)

Bugfixes
--------

- Add a YAML representer for ``NativeJinjaText``
- Add a YAML representer for ``NativeJinjaUnsafeText``
- AnsiballZ - Ensure we use the full python package in the module cache filename to avoid a case where ``collections:`` is used to execute a module via short name, where the short name duplicates another module from ``ansible.builtin`` or another collection that was executed previously.
- Ansible.ModuleUtils.LinkUtil - Ignore the ``LIB`` environment variable when loading the ``LinkUtil`` code
- Ansible.ModuleUtils.SID - Use user principal name as is for lookup in the ``Convert-ToSID`` function - https://github.com/ansible/ansible/issues/77316
- Detect package manager for Amazon Linux 2022 (AL2022) as dnf
- Ensure the correct ``environment_class`` is set on ``AnsibleJ2Template``
- Fix ``AttributeError`` when providing password file via ``--connection-password-file`` (https://github.com/ansible/ansible/issues/76530)
- Fix ``end_play`` to end the current play only (https://github.com/ansible/ansible/issues/76672)
- Fix collection filter/test plugin redirects (https://github.com/ansible/ansible/issues/77192).
- Fix executing includes in the always section in the free strategy (https://github.com/ansible/ansible/issues/75642)
- Fix for when templating empty template file resulted in file with string 'None' (https://github.com/ansible/ansible/issues/76610)
- Fix help message for the 'ansible-galaxy collection verify' positional argument. The positional argument must be a collection name (https://github.com/ansible/ansible/issues/76087).
- Fix module logging issue when using custom module on WSL2 (https://github.com/ansible/ansible/issues/76320)
- Fix task debugger to work with ``run_once`` using ``linear`` strategy (https://github.com/ansible/ansible/issues/76049)
- Fix traceback when installing a collection from a git repository and git is not installed (https://github.com/ansible/ansible/issues/77479).
- Interpreter Discovery - Fallback to OS family if the distro is not found in ``INTERPRETER_PYTHON_DISTRO_MAP`` (https://github.com/ansible/ansible/issues/75560)
- Interpreter discovery - Add ``RHEL`` to ``OS_FAMILY_MAP`` for correct family fallback for interpreter discovery (https://github.com/ansible/ansible/issues/77368)
- Make include_role/include_tasks work with any_errors_fatal (https://github.com/ansible/ansible/issues/50897)
- Parser errors from within includes should not be rescueable (https://github.com/ansible/ansible/issues/73657)
- Prevent losing unsafe on results returned from lookups (https://github.com/ansible/ansible/issues/77535)
- Templating - Ensure we catch exceptions when getting ``.filters`` and ``.tests`` attributes on their respective plugins and properly error, instead of aborting which results in no filters being added to the jinja2 environment
- Trigger an undefined error when an undefined variable is detected within a dictionary and/or list (https://github.com/ansible/ansible/pull/75587)
- _run_loop - Add the task name to the warning (https://github.com/ansible/ansible/issues/76011)
- ``Templar.copy_with_new_env`` - set the ``finalize`` method of the new ``Templar`` object for the new environment (https://github.com/ansible/ansible/issues/76379)
- add_host/group_by: fix using changed_when in a loop (https://github.com/ansible/ansible/issues/71627)
- ansible - Exclude Python 2.6 from Python interpreter discovery.
- ansible-config avoid showing _terms and _input when --only-changed.
- ansible-doc - Fix ansible-doc -l ansible.builtin / ansible.legacy not returning anything
- ansible-doc - ignore plugin deprecation warnings (https://github.com/ansible/ansible/issues/75671)
- ansible-galaxy - Add galaxy_collection_skeleton/galaxy_collection_skeleton_ignore configuration options
- ansible-galaxy - Fix using the '--ignore-certs' option when there is no server-specific configuration for the Galaxy server.
- ansible-galaxy - installing/downloading collections with invalid versions in git repositories and directories now gives a formatted error message (https://github.com/ansible/ansible/issues/76425, https://github.com/ansible/ansible/issues/75404).
- ansible-galaxy - when installing a role properly raise an error when inaccessible path is specified multiple times in roles_path (e.g. via environment variable and command line option) (https://github.com/ansible/ansible/issues/76316)
- ansible-galaxy collection build - Ignore any existing ``MANIFEST.json`` and ``FILES.json`` in the root directory when building a collection.
- ansible-galaxy collection verify - display files/directories not included in the FILES.json as modified content.
- ansible-galaxy publish - Fix warning and error detection in import messages to properly display them in Ansible
- ansible-pull handle case where hostname and nodename are empty
- ansible-test - Add default entry for Windows remotes to be used with unknown versions.
- ansible-test - All virtual environments managed by ansible-test are marked as usable after being bootstrapped, to avoid errors caused by use of incomplete environments. Previously this was only done for sanity tests. Existing environments from previous versions of ansible-test will be recreated on demand due to lacking the new marker.
- ansible-test - Automatic target requirements installation is now based on the target environment instead of the controller environment.
- ansible-test - Correctly detect when running as the ``root`` user (UID 0) on the origin host. The result of the detection was incorrectly being inverted.
- ansible-test - Don't fail if network cannot be disconnected (https://github.com/ansible/ansible/pull/77472)
- ansible-test - Fix Python real prefix detection when running in a ``venv`` virtual environment.
- ansible-test - Fix ``windows-integration`` and ``network-integration`` when used with the ``--docker`` option and user-provided inventory.
- ansible-test - Fix installation and usage of ``pyyaml`` requirement for the ``import`` sanity test for collections.
- ansible-test - Fix path to inventory file for ``windows-integration`` and ``network-integration`` commands for collections.
- ansible-test - Fix plugin loading.
- ansible-test - Fix skipping of tests marked ``needs/python`` on the origin host.
- ansible-test - Fix skipping of tests marked ``needs/root`` on the origin host.
- ansible-test - Fix the ``import`` sanity test to work properly when Ansible's built-in vendoring support is in use.
- ansible-test - Fix the ``validate-modules`` sanity test to avoid double-loading the collection loader and possibly failing on import of the ``packaging`` module.
- ansible-test - Fix traceback in ``import`` sanity test on Python 2.7 when ``pip`` is not available.
- ansible-test - Fix traceback in the ``validate-modules`` sanity test when testing an Ansible module without any callables.
- ansible-test - Fix traceback when running from an install and delegating execution to a different Python interpreter.
- ansible-test - Fix traceback when using the ``--all`` option with PowerShell code coverage.
- ansible-test - Fix type hints.
- ansible-test - Import ``yaml.cyaml.CParser`` instead of ``_yaml.CParser`` in the ``yamllint`` sanity test.
- ansible-test - Limit ``paramiko`` installation to versions before 2.9.0. This is required to maintain support for systems which do not support RSA SHA-2 algorithms.
- ansible-test - Pylint Deprecated Plugin - Use correct message symbols when date or version is not a float or str (https://github.com/ansible/ansible/issues/77085)
- ansible-test - Relocate constants to eliminate symlink.
- ansible-test - Replace the directory portion of out-of-tree paths in JUnit files from integration tests with the ``out-of-tree:`` prefix.
- ansible-test - Sanity tests run with the ``--requirements` option for Python 2.x now install ``virtualenv`` when it is missing or too old. Previously it was only installed if missing. Version 16.7.12 is now installed instead of the latest version.
- ansible-test - Set the ``pytest`` option ``--rootdir`` instead of letting it be auto-detected.
- ansible-test - Show an error message instead of a traceback when running outside of a supported directory.
- ansible-test - Target integration test requirements are now correctly installed for target environments running on the controller.
- ansible-test - The ``import`` sanity test no longer reports errors about ``packaging`` being missing when testing collections.
- ansible-test - Update distribution test containers to version 3.1.0.
- ansible-test - Update help links to reference ``ansible-core`` instead of ``ansible``.
- ansible-test - Update unit tests to use the ``--forked`` option instead of the deprecated ``--boxed`` option.
- ansible-test - Use https://ci-files.testing.ansible.com/ for instance bootstrapping instead of an S3 endpoint.
- ansible-test - Use relative paths in JUnit files generated during integration test runs.
- ansible-test - Use the correct variable to reference the client's SSH key when generating inventory.
- ansible-test - Use the legacy collection loader for ``import`` sanity tests on target-only Python versions.
- ansible-test - Virtual environments managed by ansible-test now use consistent versions of ``pip``, ``setuptools`` and ``wheel``. This avoids issues with virtual environments containing outdated or dysfunctional versions of these tools. The initial bootstrapping of ``pip`` is done by ansible-test from an HTTPS endpoint instead of creating the virtual environment with it already present.
- ansible-test - fix a typo in validate-modules.
- ansible-test - fixed support container failures (eg http-test-container) under podman
- ansible-test compile sanity test - do not crash if a column could not be determined for an error (https://github.com/ansible/ansible/pull/77465).
- ansible-test pslint - Fix error when encountering validation results that are highly nested - https://github.com/ansible/ansible/issues/74151
- ansible-vault encrypt_string - fix ``--output`` option to correctly write encrypted string into given file (https://github.com/ansible/ansible/issues/75101)
- ansible.builtin.file modification_time supports check_mode
- ansible_facts.devices - Fix parsing of device serial number detected via sg_inq for rhel8 (https://github.com/ansible/ansible/issues/75420)
- apt - fails to deploy deb file to old debian systems using python-apt < 0.8.9 (https://github.com/ansible/ansible/issues/47277)
- arg_spec - Fix incorrect ``no_log`` warning when a parameter alias is used (https://github.com/ansible/ansible/pull/77576)
- async - Improve performance of sending async callback events by never sending the full task through the queue (https://github.com/ansible/ansible/issues/76729)
- catch the case that cowsay is broken which would lead to missing output
- cleaning facts will now only warn about the variable name and not post the content, which can be undesireable to disclose
- collection_loader - Implement 'find_spec' and 'exec_module' to override deprecated importlib methods 'find_module' and 'load_module' when applicable (https://github.com/ansible/ansible/issues/74660).
- correctly inherit vars from parent in block (https://github.com/ansible/ansible/issues/75286).
- default callback - Ensure we compare FQCN also in lockstep logic, to ensure using the FQCN of a strategy plugin triggers the correct behavior in the default callback plugin. (https://github.com/ansible/ansible/issues/76782)
- distribution - add EuroLinux to fact gathering (https://github.com/ansible/ansible/pull/76624).
- distribution - detect tencentos and gather correct facts on the distro.
- dnf - ensure releasever is passed into libdnf as string (https://github.com/ansible/ansible/issues/77010)
- extend timeout for ansible-galaxy when communicating with the galaxy server api, and apply it to all interactions with the api
- facts - add support for deepin distro information detection (https://github.com/ansible/ansible/issues/77286).
- first_found - fix to allow for spaces in file names (https://github.com/ansible/ansible/issues/77136)
- gather_facts - Fact gathering now continues even if it fails to read a file
- gather_facts action now handles the move of base connection plugin types into collections to add/prevent subset argument correctly
- gather_facts/setup will not fail anymore if capsh is present but not executable
- git module fix docs and proper use of ssh wrapper script and GIT_SSH_COMMAND depending on version.
- git module is more consistent and clearer about which ssh options are added to git calls.
- git module no longer uses wrapper script for ssh options.
- hacking - fix incorrect usage of deprecated fish-shell redirection operators that failed to honor ``--quiet`` flag when sourced (https://github.com/ansible/ansible/pull/77180).
- hostname - Do not require SystemdStrategy subclasses for every distro (https://github.com/ansible/ansible/issues/76792)
- hostname - Fix Debian strategy KeyError, use `SystemdStrategy` (https://github.com/ansible/ansible/issues/76124)
- hostname - Update the systemd strategy in the ``hostname`` module to not interfere with NetworkManager (https://github.com/ansible/ansible/issues/76958)
- hostname - add hostname support for openEuler distro (https://github.com/ansible/ansible/pull/76619).
- hostname - use ``file_get_content()`` to read the file containing the host name in the ``FileStrategy.get_permanent_hostname()`` method. This prevents a ``TypeError`` from being raised when the strategy is used (https://github.com/ansible/ansible/issues/77025).
- include_vars, properly initialize variable as there is corner case in which it can end up referenced and not defined
- inventory - parameterize ``disable_lookups`` in ``Constructable`` (https://github.com/ansible/ansible/issues/76769).
- inventory manager now respects --flush-cache
- junit callback - Fix traceback during automatic fact gathering when using relative paths.
- junit callback - Fix unicode error when handling non-ASCII task paths.
- module_utils.common.yaml - The ``SafeLoader``, ``SafeDumper`` and ``Parser`` classes now fallback to ``object`` when ``yaml`` is not available. This fixes tracebacks when inheriting from these classes without requiring a ``HAS_YAML`` guard around class definitions.
- parameters - handle blank values when argument is a list (https://github.com/ansible/ansible/issues/77108).
- play_context now compensates for when a conneciton sets the default to inventory_hostname but skips adding it to the vars.
- playbook/strategy have more informative 'attribute' based errors for playbook objects and handlers.
- python modules (new type) will now again prefer the specific python stated in the module's shebang instead of hardcoding to /usr/bin/python.
- replace - Always return ``rc`` to ensure return values are consistent - https://github.com/ansible/ansible/pull/71963
- script - skip in check mode if the plugin cannot determine if a change will occur (i.e. neither `creates` or `removes` are provided).
- service - Fixed handling of sleep arguments during service restarts on AIX. (https://github.com/ansible/ansible/issues/76877)
- service - Fixed service restarts with arguments on AIX. (https://github.com/ansible/ansible/issues/76840)
- service_facts module will now give more meaningful warnings when it fails to gather data.
- set_fact/include_vars correctly handle delegation assignments within loops
- setup - detect docker container with check for ./dockerenv or ./dockinit (https://github.com/ansible/ansible/pull/74349).
- shell/command - only return changed as True if the task has not been skipped.
- shell/command - only skip in check mode if the options `creates` and `removes` are both None.
- ssh connection - properly quote controlpersist path given by user to avoid issues with spaces and other characters
- ssh connection avoid parsing ssh cli debug lines as they can match expected output at high verbosities.
- ssh connection now uses more correct host source as play_context can ignore loop/delegation variations.
- sudo become plugin, fix handling of non interactive flags, previous substitution was too naive
- systemd - check if service is alias so it gets enabled (https://github.com/ansible/ansible/issues/75538).
- systemd - check if service is indirect so it gets enabled (https://github.com/ansible/ansible/issues/76453).
- task_executor reverts the change to push facts into delegated vars on loop finalization as result managing code already handles this and was duplicating effort to wrong result.
- template lookup - restore inadvertently deleted default for ``convert_data`` (https://github.com/ansible/ansible/issues/77004)
- to_json/to_nice_json filters defaults back to unvaulting/no unsafe packing.
- unarchive - Fix zip archive file listing that caused issues with content postprocessing (https://github.com/ansible/ansible/issues/76067).
- unarchive - Make extraction work when the LANGUAGE environment variable is set to a non-English locale.
- unarchive - apply ``owner`` and ``group`` permissions to top folder (https://github.com/ansible/ansible/issues/35426)
- unarchive - include the original error when a handler cannot manage the archive (https://github.com/ansible/ansible/issues/28977).
- unarchive - the ``io_buffer_size`` option added in 2.12 was not accepted by the module (https://github.com/ansible/ansible/pull/77271).
- urls - Allow ``ca_path`` to point to a bundle containing multiple PEM certs (https://github.com/ansible/ansible/issues/75015)
- urls/uri - Address case where ``HTTPError`` isn't fully initialized due to the error, and is missing certain methods and attributes (https://github.com/ansible/ansible/issues/76386)
- user - allow ``password_expiry_min`` and ``password_expiry_min`` to be set to ``0`` (https://github.com/ansible/ansible/issues/75017)
- user - allow password min and max to be set at the same time (https://github.com/ansible/ansible/issues/75017)
- user - update logic to check if user exists or not in MacOS.
- validate_argument_spec - Skip suboption validation if the top level option is an invalid type (https://github.com/ansible/ansible/issues/75612).
- variablemanager, more efficient read of vars files
- vault - Warn instead of fail for missing vault IDs if at least one valid vault secret is found.
- winrm - Ensure ``kinit`` is run with the same ``PATH`` env var as the Ansible process
- yum - prevent storing unnecessary cache data by running `yum makecache fast` (https://github.com/ansible/ansible/issues/76336)

Known Issues
------------

- get_url - document ``check_mode`` correctly with unreliable changed status (https://github.com/ansible/ansible/issues/65687).
