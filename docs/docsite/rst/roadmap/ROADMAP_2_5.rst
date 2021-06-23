===========
Ansible 2.5
===========
**Core Engine Freeze and Module Freeze: 22 January 2018**

**Core and Curated Module Freeze: 22 January 2018**

**Community Module Freeze: 7 February 2018**

**Release Candidate 1 will be 21 February, 2018**

**Target: March 2018**

**Service Release schedule: every 2-3 weeks**

.. contents:: Topics

Release Manager
---------------
Matt Davis (IRC/GitHub: @nitzmahone)


Engine improvements
-------------------
- Assemble module improvements
  - assemble just skips when in check mode, it should be able to test if there is a difference and changed=true/false.
  - The same with diff, it should work as template modules does
- Handle Password reset prompts cleaner
- Tasks stats for rescues and ignores
- Normalize temp dir usage across all subsystems
- Add option to set playbook dir for adhoc, inventory and console to allow for 'relative path loading'


Ansible-Config
--------------
- Extend config to more plugin types and update plugins to support the new config

Inventory
---------
- ansible-inventory option to output group variable assignment and data (--export)
- Create inventory plugins for:
  - aws

Facts
-----
- Namespacing fact variables (via a config option) implemented in ansible/ansible PR `#18445 <https://github.com/ansible/ansible/pull/18445>`_.
  Proposal found in ansible/proposals issue `#17 <https://github.com/ansible/proposals/issues/17>`_.
- Make fact collectors and gather_subset specs finer grained
- Eliminate unneeded deps between fact collectors
- Allow fact collectors to indicate if they need information from another fact collector to be gathered first.

Static Loop Keyword
-------------------

- A simpler alternative to ``with_``, ``loop:`` only takes a list
- Remove complexity from loops, lookups are still available to users
- Less confusing having a static directive vs a one that is dynamic depending on plugins loaded.

Vault
-----
- Vault secrets client inc new 'keyring' client

Runtime Check on Modules for Disabling
--------------------------------------
- Filter on things like "supported_by" in module metadata
- Provide users with an option of "warning, error or allow/ignore"
- Configurable via ansible.cfg and environment variable

Windows
-------
- Implement gather_subset on Windows facts
- Fix Windows async + become to allow them to work together
- Implement Windows become flags for controlling various modes **(done)**
  - logontype
  - elevation behavior
- Convert win_updates to action plugin for auto reboot and extra features **(done)**
- Spike out changing the connection over to PSRP instead of WSMV **(done- it's possible)**
- Module updates

  - win_updates **(done)**

    - Fix win_updates to detect (or request) become
    - Add enable/disable features to win_updates
  - win_dsc further improvements **(done)**

General Cloud
-------------
- Make multi-cloud provisioning easier
- Diff mode will output provisioning task results of ansible-playbook runs
- Terraform module

AWS
---
- Focus on pull requests for various modules
- Triage existing merges for modules
- Module work

  - ec2_instance
  - ec2_vpc: Allow the addition of secondary IPv4 CIDRS to existing VPCs.
  - AWS Network Load Balancer support (NLB module, ASG support, and so on)
  - rds_instance

Azure
-----
- Azure CLI auth **(done)**
- Fix Azure module results to have "high-level" output instead of raw REST API dictionary **(partial, more to come in 2.6)**
- Deprecate Azure automatic storage accounts in azure_rm_virtualmachine **(breaks on Azure Stack, punted until AS supports managed disks)**

Network Roadmap
---------------
- Refactor common network shared code into package **(done)**
- Convert various nxos modules to use declarative intent **(done)**
- Refactor various modules to use the cliconf plugin **(done)**
- Add various missing declarative modules for supported platforms and functions **(done)**
- Implement a feature that handles platform differences and feature unavailability **(done)**
- netconf-config.py should provide control for deployment strategy
- Create netconf connection plugin **(done)**
- Create netconf fact module
- Turn network_cli into a usable connection type **(done)**
- Implements jsonrpc message passing for ansible-connection **(done)**
- Improve logging for ansible-connection **(done)**
- Improve stdout output for failures whilst using persistent connection **(done)**
- Create IOS-XR NetConf Plugin and refactor iosxr modules to use netconf plugin **(done)**
- Refactor junos modules to use netconf plugin **(done)**
- Filters: Add a filter to convert XML response from a network device to JSON object **(done)**

Documentation
-------------
- Extend documentation to more plugins
- Document vault-password-client scripts.
- Network Documentation

  - New landing page (to replace intro_networking) **(done)**
  - Platform specific guides **(done)**
  - Walk through: Getting Started **(done)**
  - Networking and ``become`` **(done)**
  - Best practice **(done)**

Contributor Quality of Life
---------------------------
- Finish PSScriptAnalyer integration with ansible-test (for enforcing Powershell style) **(done)**
- Resolve issues requiring skipping of some integration tests on Python 3.
