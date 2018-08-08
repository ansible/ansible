***************
Developer Guide
***************

Welcome to the Ansible Developer Guide!

Who should use this guide?
================================================================================

If you want to extend Ansible by using a non-core module or plugin locally, creating a module or plugin, adding functionality to an existing module, or expanding test coverage, this guide is for you. We've included detailed information for developers on how to test and document modules, as well as the pre-requisites for getting your module or plugin accepted into Ansible Core. 

Find the task that best describes what you want to do:

* I want to :ref:`use a custom plugin or module locally <developing_locally>`.
* I want to address a particular use case, and I wonder if :ref:`developing a module is the right approach <module_dev_should_you>`?
* I want to :ref:`write a custom plugin <developing_plugins>`.
* I want to :ref:`write a custom module <developing_modules>`.
* I want to :ref:`write a custom module for Windows <developing_modules_general_windows>`.
* I want to :ref:`write a series of related custom modules <developing_modules_in_groups>` that integrate Ansible with a new product (for example, a database, cloud provider, network platform, etc.).
* I want to :ref:`debug my module code <debugging>`.
* I want to :ref:`test my module <developing_testing>`.
* I want to :ref:`document my module <module_documenting>`.
* I want to :ref:`update my module to run on Python 3 <developing_python_3>`.
* I want to :ref:`connect Ansible to a new source of inventory <developing_inventory>`. 
* I want to :ref:`contribute my module or plugin to Ansible Core <module_contribution>`.

## TODO how much TOC do we want? links to Setting Up Your Environment? 


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
