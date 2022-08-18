.. _user_guide_index:

##########
User Guide
##########

.. note::

    **Making Open Source More Inclusive**

    Red Hat is committed to replacing problematic language in our code, documentation, and web properties. We are beginning with these four terms: master, slave, blacklist, and whitelist. We ask that you open an issue or pull request if you come upon a term that we have missed. For more details, see `our CTO Chris Wright's message <https://www.redhat.com/en/blog/making-open-source-more-inclusive-eradicating-problematic-language>`_.

Welcome to the Ansible User Guide! This guide covers how to work with Ansible, including using the command line, working with inventory, interacting with data, writing tasks, plays, and playbooks; executing playbooks, and reference materials.
Quickly find answers in the following sections or expand the table of contents below to scroll through all resources.

Interacting with data
=====================

* I need to access sensitive data like passwords with Ansible. How can I protect that data with :ref:`Ansible vault <vault>`?
* I use certain modules frequently. How do I streamline my inventory and playbooks by :ref:`setting default values for module parameters <module_defaults>`?

Advanced features and reference
===============================

* Manipulating :ref:`complex data <complex_data_manipulation>`
* Using :ref:`plugins <plugins_lookup>`
* Rejecting :ref:`specific modules <plugin_filtering_config>`
* Module :ref:`maintenance <modules_support>`

Table of contents
=================

Here is the complete list of resources in the Ansible User Guide:

.. toctree::
   :maxdepth: 2

   vault
   complex_data_manipulation
   plugin_filtering_config
   sample_setup
   modules
   ../plugins/plugins
   collections_using
