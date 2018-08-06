***************
Developer Guide
***************

Welcome to the Ansible Developer Guide!

Who should use this guide?
================================================================================

If you want to extend Ansible by creating a module or plugin, using a non-core module or plugin, adding functionality to an existing module, or expanding test coverage, this guide is for you.

I want to use a custom plugin or module locally.
I want to write a custom plugin.
I want to write a custom module.
I want to write a custom module for Windows.
I want to write a series of related custom modules that integrate Ansible with a new product (for example, a database, cloud provider, network platform, etc.).
I want to test my module.
I want to update my module to run on Python 3.
I want to write an inventory system 
I want to contribute content to Ansible Core (including plugins, modules, new functionality, tests, etc.).

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
