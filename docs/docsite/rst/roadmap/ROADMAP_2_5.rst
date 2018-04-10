===========
Ansible 2.5
===========
**Core Engine Freeze and Module Freeze: 22 January 2018**

**Core and Curated Module Freeze: 22 January 2018**

**Community Module Freeze: 7 February 2018**

**Release Candidate 1 will be 21 February, 2018**

**Target: March 2018**

.. contents:: Topics

Engine improvements
-------------------
- Polish and consolidate CLI

  - Add a debug flag that prints log entries to stdout
  - Investigate implementing subcommands
- Clean up output formatting
- Reimplement task result `invocation` injection control-side, but only when module didn't return it.

  - always use heuristic sensitive-value filtering on injected values
  - if heuristic filter triggers, add a warning that perhaps use of task-level no_log should be considered
  - consider skipping injection for Python module type (even if it's missing, eg catastrophic module failure) to prevent potentially injecting a value that was arg-level no_log'd on the target side.
  - consider addition of NO_INVOCATION config
- Assemble module improvements

  - assemble just skips when in check mode, it should be able to test if there is a difference and changed=true/false.
  - The same with diff, it should work as template modules does
- Include AWX facts as default fact modules in Ansible
- Handle Password reset prompts cleaner
- Tasks stats for rescues and ignores
- Make 'persistent' a generic feature so multiple actions can occur seamlessly in same connection.
- New property for module documentation to manage expectations of the behaviour of the module.
- Normalize temp dir usage across all subsystems
- Currently ignored keywords do not notify user they were ignored, throw a warning on these.
- Deprecation version enforcement
- sysvinit service module
- Add option to set playbook dir for adhoc, inventory and console to allow for 'relative path loading'


Ansible Content Management
--------------------------
- Have ansible-galaxy handle installation of modules, plugins, etc not included with the install package

Ansible-Config
--------------
- New yaml format for config
- Extend config to rest of plugin types and update plugins to support the new config
- Create an playbook directory option

Inventory
---------
- ansible-inventory option to output group variable assignment and data
- Convert the following dynamic inventory scripts into plugins:

  - ec2
  - Azure
  - GCE
  - Foreman

Facts
-----
- Namespacing fact variables (via a config option) implemented in ansible/ansible PR `#18445 <https://github.com/ansible/ansible/pull/18445>`_. **(done)**
  Proposal found in ansible/proposals issue `#17 <https://github.com/ansible/proposals/issues/17>`_.
- Make fact collectors and gather_subset specs finer grained
- Eliminate unneeded deps between fact collectors
- Allow fact collectors to indicate if they need information from another fact collector to be gathered first.

PluginLoader
------------
- Over the past couple releases we've had some thoughts about how PluginLoader might be better structured

  - Load the loaders via an initialization function(), not when importing
    the module. (stretch goal, doesn't impact the CLI)
  - Separate duties of ``PluginLoader`` from ``PluginFinder``.  Most plugins need
    both but Modules and Module_utils only need a PluginFinder
  - Write different ``PluginFinder`` subclasses for module_utils and perhaps
    Modules.  Most Plugin types have a flattened namespace and are single
    python files.  Modules include code that is not written in python.
    Module_utils are vastly different from the other Plugins as they
    maintain a hierarchical namespace and are multi-file.
  - Potentially split module_utils loader for python from module_utils
    loader for powershell.  Currently we only support generic module_utils
    for python modules.  The powershell modules always include a single,
    hardcoded powershell module_utils file.  If we add generic module_utils
    for powershell, we'll need to decide how to organize the code.

Static Loop Keyword
-------------------
**(done)**

- Deprecate (not on standard deprecation cycle) ``with_`` in favor of ``loop:``
- This ``loop:`` will take only a list
- Remove complexity from loops, lookups are still available to users
- Less confusing having a static directive vs a one that is dynamic depending on plugins loaded.

Vault
-----
- In some cases diff users might want to use the same play with different access levels,
  being able to change vault failure to decrypt to a warning or something else allows for this.
- Allow vault password files to be vault encrypted
- Vault secrets client inc new 'keyring' client **(done)**

Role Versioning
---------------
- ansible-galaxy will install roles using name + version
- On role install, If an existing role is found in the 'bare name' handle version
- removing roles should detect multiple versions and prompt for 'all' or a specific version(s)
- When referencing a role in a play, ansible-playbook should now also check if version is specified and use that if found
- Option for galaxy to remove 'old roles' on install (upgrade?), this is not clear cut as version can be a commit SHA and order there is not related to sorting, clear 'versions 1.1, 1.2' can use loose versioning comparisons.
- ansible-galaxy cli should also be able to change the 'base role name' to point to specific versions, this solves the issue when the 'latest' is not actually the one existing plays should be using, again this mimics the 'alternatives' functionality.

Globalize Callbacks
-------------------
- Make send_callback available to other code that cannot use it.
- Would allow for 'full formatting' of output (see JSON callback)
- Fixes static 'include' display problem

Runtime Check on Modules for Blacklisting
-----------------------------------------
- Filter on things like "supported_by" in module metadata
- Provide users with an option of "warning, error or allow/ignore"
- Configurable via ansible.cfg and environment variable

Windows
-------
- Implement gather_subset on Windows facts
- Move setup.ps1 guts to module_utils to allow arbitrary modules to call/refresh individual facts.
- Fix Windows binary module support to work properly with become/env/async in all cases.
- Fix Windows async + become to allow them to work together
- Solve Windows become/env support for raw/script
- Implement Windows become flags for controlling various modes

  - logontype
  - elevation behavior
  - Add dict support to become_flags.
- Fix Windows auto-kinit with threaded workers (or disallow it)
- Finish C#/Powershell module_utils rewrite, convert core modules to use it.
- Convert win_updates to action plugin for auto reboot and extra features
- Spike out support for Windows Nano Server
- Spike out changing the connection over to PSRP instead of WSMV
- Module updates

  - win_updates

    - Fix win_updates to detect (or request) become
    - Add whitelist/blacklist features to win_updates
  - win_dsc further improvements

General Cloud
-------------
- Make multi-cloud provisioning easier

  - Document multi-instance provisioning with loop directive
  - Extend async_status to accept a list or build new action to simplify the with_items/register/until:finish patterns.
- Diff mode will output provisioning task results of ansible-playbook runs
- Terraform module

AWS
---
- Focus on pull requests for various modules
- Triage existing merges for modules
- Module work

  - ec2_instance
  - ec2_vpc: Allow the addition of secondary IPv4 CIDRS to existing VPCs.
  - AWS Network Load Balancer support (NLB module, ASG support, etc)
  - rds_instance

Azure
-----
- Azure CLI auth
- Fix Azure module results to have "high-level" output instead of raw REST API dictionary
- Deprecate Azure automatic storage accounts in azure_rm_virtualmachine

Network Roadmap
---------------
- Refactor common network shared code into package **(done)**
- Convert various nxos modules to leverage declarative intent **(done)**
- Refactor various modules to leverage the cliconf plugin **(done)**
- Add various missing declarative modules for supported platforms and functions **(done)**
- Implement a feature that handles platform differences and feature unavailability **(done)**
- netconf-config.py should provide control for deployment strategy
- Create netconf connection plugin **(done)**
- Create netconf fact module
- Turn network_cli into a usable connection type **(done)**
- Implements jsonrpc message passing for ansible-connection **(done)**
- Improve logging for ansible-connection **(done)**
- Improve stdout output for failures whilst using persistent connection **(done)**
- Create IOS-XR NetConf Plugin and refactor iosxr modules to leverage netconf plugin **(done)**
- Refactor junos modules to use netconf plugin **(done)**
- Filters: Add a filter to convert XML response from a network device to JSON object **(done)**

Documentation
-------------
- Extend documentation to all existing plugins
- Document vault-password-client scripts.
- Network Documentation

  - New landing page (to replace intro_networking)
  - Platform specific guides
  - Walk through: Getting Started
  - Networking and ``become`` **(done)**
  - Best practice **(done)**

Contributor Quality of Life
---------------------------
- Pester unit test support in ansible-test
- Finish PSScriptAnalyer integration with ansible-test (for enforcing Powershell style)
- Add static code analysis to CI for PowerShell.
- Resolve issues requiring skipping of some integration tests on Python 3.
