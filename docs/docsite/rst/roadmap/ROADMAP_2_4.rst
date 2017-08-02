============================
Ansible by Red Hat, Core 2.4
============================
**Core Engine Freeze and Module Freeze: 15 August 2017**

**Core and Curated Module Freeze: 15 August 2017**

**Community Module Freeze: 29 August 2017**

**Target: Mid-September 2017**

.. contents:: Topics

Administrivia and Process
-------------------------
- Starting with 2.4, all items that are deprecated will be removed in 4 major releases unless otherwise stated.

  - For example: A module that is deprecated in 2.4 will be removed in 2.8

Python 2.4 and 2.5 support discontinuation
------------------------------------------
- Ansible will not support Python 2.4 nor 2.5 on the target hosts anymore.
  Going forward, Python 2.6+ will be required on targets, as already is the case on the controller.

Python 3
--------
- Ansible Core Engine and Core modules will be tested on Python 3

  - All Core modules now have at least a smoketest integration test.
    Additional coverage is welcomed to find more bugs and prevent regressions.

- Communicate with Linux distros to provide Ansible running on Python 3

  - Python3 based Ansible packages are now available to run on Fedora Linux

Ansible-Config
--------------
- Proposal found in ansible/proposals issue `#35 <https://github.com/ansible/proposals/issues/35>`_.
- Initial PR of code found in ansible/ansible PR `#12797 <https://github.com/ansible/ansible/pull/12797>`_. **(done)**
- Per plugin configuration (depends on plugin docs below). **(WIP)**
- New yaml format for config **(possibly pushed to future roadmap)**
- Extend the ability of the current config system by adding an ``ansible-config`` command and add the following:

  - Dump existing config settings **(working, fine tuning)**
  - Update / write a config entry **(pushed to future roadmap)**
  - Show available options (ini entry, yaml, env var, etc) **(working, fine tuning)**


Inventory
---------
**(done, needs docs)**
- Proposal found in ansible/proposals issue `#41 <https://github.com/ansible/proposals/issues/41>`_.
- Current inventory is overly complex, non modular and mostly still a legacy from inception.

Facts
-----
- Configurable list of ‘fact modules’ for ``gather_facts`` **(done)**
- Fact gathering policy finer grained **(done)**
- Make ``setup.py``/``facts`` more pluggable **(done)**
- Improve testing of ``setup.py``/``facts.py`` **(done)**
- Namespacing fact variables (via a config option) implemented in ansible/ansible PR `#18445 <https://github.com/ansible/ansible/pull/18445>`_. **(done)**
  Proposal found in ansible/proposals issue `#17 <https://github.com/ansible/proposals/issues/17>`_.

PluginLoader
------------
**(pushed out to future release)**
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
- Deprecate (not on standard deprecation cycle) ``with_`` in favor of ``loop:``
- This ``loop:`` will take only a list
- Remove complexity from loops, lookups are still available to users
- Less confusing having a static directive vs a one that is dynamic depending on plugins loaded.

Vault
-----
- Support for multiple vault passwords.  **(done)**

  - Each decrypted item should know which secret to request **(done)**
  - Support requesting credentials (password prompt) as callbacks

- Ability to open and edit file with encrypted vars deencrypted, and encrypt/format on save

Globalize Callbacks
-------------------
**(pushed out to future release)**
- Make send_callback available to other code that cannot use it.
- Would allow for ‘full formatting’ of output (see JSON callback)
- Fixes static ‘include’ display problem

Plugins
-------
- Allow plugins to have embedded docs (like modules) **(done)**
- Update ansible-doc and website to generate docs from these ansible/ansible PR `#22796 <https://github.com/ansible/ansible/pull/22796>`_. **(ansible-doc working, todo:website)**

Group Priorities
----------------
**(done)**
- Start using existing group priority variable to sort/merge group vars
- Implementation for this in ansible/ansible PR `#22580 <https://github.com/ansible/ansible/pull/22580>`_.
- Documentation of group priority variable

Runtime Check on Modules for Blacklisting
-----------------------------------------
**(pushed out to future release)**
- Filter on things like "supported_by" in module metadata
- Provide users with an option of "warning, error or allow/ignore"
- Configurable via ansible.cfg and environment variable

Disambiguate Includes
---------------------
- Create import_x for ‘static includes’ (import_task, import_play, import_role)

  - Any directives are applied to the ‘imported’ tasks

- Create include_x for ‘dynamic includes’ (include_task, include_role)

  - Any directives apply to the ‘include’  itself

Windows
-------
- New PS/.NET module API **(in progress)**
- Windows Nano Server support
- Windows module_utils pluginloader **(done)**
- Refactor duplicated module code into new module_utils files **(in progress)**
- Evaluate #Requires directives (existing and new: PS version, OS version, etc)
- Improve module debug support/persistence **(done)**
- Explore official DSC support **(done)**
- Explore module intermediate output
- Explore Powershell module unit testing **(in progress)**
- Explore JEA support (stretch)
- Extended become support with network/service/batch logon types
- Module updates

  - Split "Windows" category into multiple subs
  - Domain user/group management modules **(in progress)**
  - win_mapped_drive module **(in progress)**
  - win_hotfix
  - win_updates rewrite to require become
  - win_package changes required to deprecate win_msi
  - win_copy re-write

AWS
---
- Focus on pull requests for various modules
- Triage existing merges for modules
- Module work

  - elb-target-groups `#19492 <https://github.com/ansible/ansible/pull/19492>`_, `#24583 <https://github.com/ansible/ansible/pull/24583>`_. **(done)**
  - alb* `#19491 <https://github.com/ansible/ansible/pull/19491>`_, `#24584 <https://github.com/ansible/ansible/pull/24584>`_. **(done)**
  - ecs `#20618 <https://github.com/ansible/ansible/pull/20618>`_. **(in review process)**
  - Data Pipelines `#22878 <https://github.com/ansible/ansible/pull/22878>`_. **(in review process)**
  - VPN `#24385 <https://github.com/ansible/ansible/pull/24385>`_. **(in review process)**
  - DirectConnect `#26152 <https://github.com/ansible/ansible/pull/26152>`_. **(connection module in review process, several more to come)**

Azure
-----
- Expose endpoint overrides **(in progress)**
- Reformat/document module output to collapse internal API structures and surface important data (eg, public IPs, NICs, data disks)
- Add load balancer module **(in progress)**
- Add Azure Functions module **(in progress)**

Google Cloud Platform
---------------------
- New Module: DataProc
- Support for Cross-Region HTTP Load Balancing
- New Module: GKE

Network Roadmap
---------------
- Removal of ``*_template`` modules
- Distributed Continuous Integration Infrastructure
- RPC Connection Plugin
- Module Work

  - Declarative intent modules
  - OpenVSwitch
  - Minimal Viable Platform Agnostic Modules

Contributor Quality of Life
---------------------------
- All Core and Curated modules will work towards having unit testing. **(edit: integration and/or unit tests)**
- More bot improvements!

  - Bot comments on PRs with details of test failures. **(done)**

- Test Infrastructure changes

  - Shippable + Bot Integration

    - Provide verified test results to the bot from Shippable so the bot can comment on PRs with CI failures. **(done, compile and sanity tests only)**
    - Enable the bot to mark PRs with ``ci_verified`` if all CI failures are verified. **(done)**

  - Windows Server 2016 Integration Tests

    - Restore Windows Server 2016 integration tests on Shippable.

      - Originally enabled during the 2.3 release cycle, but later disabled due to intermittent WinRM issues.
      - Depends on resolution of WinRM connection issues.

  - Windows Server Nano Integration Tests

    - Add support to ansible-core-ci for Windows Server 2016 Nano and enable on Shippable.
    - This will use a subset of the existing Windows integration tests.
    - Depends on resolution of WinRM connection issues.

  - Windows + Python 3 Tests

    - Run basic Windows tests using Python 3 as the controller. **(partially done, not all planned tests running yet)**
    - Depends on resolution of WinRM Python 3 issues.

  - Cloud Integration Tests

    - Run existing cloud integration tests as part of CI for:

      - AWS **(done, some tests excluded due to test duration)**
      - Azure **(in progress)**
      - GCP as part of CI. **(possibly pushed to future roadmap)**

    - Tests to be run only on cloud module (and module_utils) PRs and merges for the relevant cloud provider. **(done)**

  - Test Reliability

    - Further improve test reliability to reduce false positives on Shippable. **(ongoing)**
    - This continues work from the 2.3 release cycle.

  - Static Code Analysis

    - Further expand the scope and coverage of static analysis. **(ongoing)**
    - This continues work from the 2.3 release cycle.
