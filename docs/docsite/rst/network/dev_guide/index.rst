.. _network_developer_guide:

**************************************
Developer Guide for Network Automation
**************************************

Welcome to the Developer Guide for Ansible Network Automation!

**Who should use this guide?**

If you want to extend Ansible for Network Automation by creating a module or plugin, this guide is for you. This guide is specific to networking. You should already be familiar with how to create, test, and document modules and plugins, as well as the prerequisites for getting your module or plugin accepted into the main Ansible repository.  See the  :ref:`developer_guide` for details. Before you proceed, please read:

* How  to :ref:`add a custom plugin or module locally <developing_locally>`.
* How to figure out if :ref:`developing a module is the right approach <module_dev_should_you>` for my use case.
* How to :ref:`set up my Python development environment <environment_setup>`.
* How to :ref:`get started writing a module <developing_modules_general>`.


Find the network developer task that best describes what you want to do:

   * I want to :ref:`develop a network resource module <developing_resource_modules>`.
   * I want to :ref:`develop a network connection plugin <developing_plugins_network>`.
   * I want to :ref:`document my set of modules for a network platform <documenting_modules_network>`.

If you prefer to read the entire guide, here's a list of the pages in order.

.. toctree::
  :maxdepth: 1

  developing_resource_modules_network
  developing_plugins_network
  documenting_modules_network
