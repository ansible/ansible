.. _developer_guide:

***************
Developer Guide
***************

.. note::

    **Making Open Source More Inclusive**

    Red Hat is committed to replacing problematic language in our code, documentation, and web properties. We are beginning with these four terms: master, slave, blacklist, and whitelist. We ask that you open an issue or pull request if you come upon a term that we have missed. For more details, see `our CTO Chris Wright's message <https://www.redhat.com/en/blog/making-open-source-more-inclusive-eradicating-problematic-language>`_.

Welcome to the Ansible Developer Guide!

**Who should use this guide?**

If you want to extend Ansible by using a custom module or plugin locally, creating a module or plugin, adding functionality to an existing module, or expanding test coverage, this guide is for you. We've included detailed information for developers on how to test and document modules, as well as the prerequisites for getting your module or plugin accepted into the main Ansible repository.

Find the task that best describes what you want to do:

* I'm looking for a way to address a use case:

   * I want to :ref:`add a custom plugin or module locally <developing_locally>`.
   * I want to figure out if :ref:`developing a module is the right approach <module_dev_should_you>` for my use case.
   * I want to :ref:`develop a collection <developing_collections>`.
   * I want to :ref:`contribute to an Ansible-maintained collection <contributing_maintained_collections>`.
   * I want to :ref:`contribute to a community-maintained collection <hacking_collections>`.
   * I want to :ref:`migrate a role to a collection <migrating_roles>`.

* I've read the info above, and I'm sure I want to develop a module:

   * What do I need to know before I start coding?
   * I want to :ref:`set up my Python development environment <environment_setup>`.
   * I want to :ref:`get started writing a module <developing_modules_general>`.
   * I want to write a specific kind of module:
      * a :ref:`network module <developing_modules_network>`
      * a :ref:`Windows module <developing_modules_general_windows>`.
      * an :ref:`Amazon module <AWS_module_development>`.
      * an :ref:`OpenStack module <OpenStack_module_development>`.
      * an :ref:`oVirt/RHV module <oVirt_module_development>`.
      * a :ref:`VMware module <VMware_module_development>`.
   * I want to :ref:`write a series of related modules <developing_modules_in_groups>` that integrate Ansible with a new product (for example, a database, cloud provider, network platform, and so on).

* I want to refine my code:

   * I want to :ref:`debug my module code <debugging_modules>`.
   * I want to :ref:`add tests <developing_testing>`.
   * I want to :ref:`document my module <module_documenting>`.
   * I want to :ref:`document my set of modules for a network platform <documenting_modules_network>`.
   * I want to follow :ref:`conventions and tips for clean, usable module code <developing_modules_best_practices>`.
   * I want to :ref:`make sure my code runs on Python 2 and Python 3 <developing_python_3>`.

* I want to work on other development projects:

   * I want to :ref:`write a plugin <developing_plugins>`.
   * I want to :ref:`connect Ansible to a new source of inventory <developing_inventory>`.
   * I want to :ref:`deprecate an outdated module <deprecating_modules>`.

* I want to contribute back to the Ansible project:

  * I want to :ref:`understand how to contribute to Ansible <ansible_community_guide>`.
  * I want to :ref:`contribute my module or plugin <developing_modules_checklist>`.
  * I want to :ref:`understand the license agreement <contributor_license_agreement>` for contributions to Ansible.

If you prefer to read the entire guide, here's a list of the pages in order.

.. toctree::
   :maxdepth: 2

   developing_locally
   developing_modules
   developing_modules_general
   developing_modules_checklist
   developing_modules_best_practices
   developing_python_3
   debugging
   developing_modules_documenting
   developing_modules_general_windows
   developing_modules_general_aci
   platforms/aws_guidelines
   platforms/openstack_guidelines
   platforms/ovirt_dev_guide
   platforms/vmware_guidelines
   platforms/vmware_rest_guidelines
   developing_modules_in_groups
   testing
   module_lifecycle
   developing_plugins
   developing_inventory
   developing_core
   developing_program_flow_modules
   developing_api
   developing_rebasing
   developing_module_utilities
   developing_collections
   migrating_roles
   collections_galaxy_meta
   overview_architecture
