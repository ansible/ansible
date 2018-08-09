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

If you prefer to read the entire guide, here's a list of the pages in order.

.. toctree::
   :maxdepth: 1

   developing_locally
   developing_modules
   developing_modules_general
   developing_modules_best_practices
   developing_python_3
   developing_modules_checklist
   testing
   debugging
   developing_modules_documenting
   developing_modules_general_windows
   developing_modules_in_groups
   developing_rebasing
   module_lifecycle
   developing_plugins
   developing_inventory
   developing_core
   developing_program_flow_modules
   developing_api
   developing_module_utilities

.. toctree::
   :caption: Other Content - Needs Integration
   :maxdepth: 1

   testing_running_locally
   testing_units_modules
   testing_compile
   testing_sanity
   testing_units
   testing_integration
   testing_httptester
   ./style_guide/index


.. toctree::
   :caption: Deprecated Legacy Pages
   :maxdepth: 1

   repomerge
   overview_architecture
