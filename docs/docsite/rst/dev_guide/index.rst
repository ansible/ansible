************************************************************
Extending Ansible: A Guide for Developers and Contributors
************************************************************

Welcome to the Extending Ansible Guide!

Who should use this guide?
================================================================================

This guide is intended for developers who want to extend Ansible by creating new modules, adding functionality within existing modules, expanding test coverage, or enriching documentation.

If you want to develop a module for local use (for yourself or your team), you only need the first section.

If you want to contribute changes back to the main Ansible repo, you need both sections, but should probably start by setting up your environment.

This guide shows you how to extend Ansible in many ways, from creating a plugin or module for local use, to contributing documentation, testing, or code back to the main project repo. If you want to add specialized functionality to Ansible, or you want to make the project better, this guide will support your goals.


.. toctree::
   :caption: Section 1: Developing Locally
   :maxdepth: 1

   developing_locally
   developing_plugins
   developing_inventory
   developing_modules
   developing_modules_general
   developing_modules_best_practices
   developing_modules_checklist
   developing_modules_in_groups
   developing_modules_general_windows
   developing_api
   developing_module_utilities
   testing_running_locally
   testing_units_modules
   testing_compile
   testing_sanity
   developing_modules_documenting
   developing_modules_maintenance
   developing_python_3
   repomerge
   testing
   testing_units
   testing_integration
   testing_httptester
   ./style_guide/index


.. toctree::
   :caption: Section 2: Contributing to Ansible/Ansible
   :maxdepth: 1

   developing_core
   overview_architecture
   developing_program_flow_modules
   developing_rebasing
   ../reference_appendices/release_and_maintenance
   ../community/committer_guidelines
