.. _plugins_lookup:
.. _working_with_plugins:

********************
Working with plugins
********************

Plugins are pieces of code that augment Ansible's core functionality. Ansible uses a plugin architecture to enable a rich, flexible and expandable feature set.

Ansible ships with a number of handy plugins, and you can easily write your own.

This section covers the various types of plugins that are included with Ansible:

.. toctree::
   :maxdepth: 1

   action
   become
   cache
   callback
   cliconf
   connection
   docs_fragment
   filter
   httpapi
   inventory
   lookup
   module
   module_util
   netconf
   shell
   strategy
   terminal
   test
   vars

.. seealso::

   :ref:`plugin_filtering_config`
       Controlling access to modules
   :ref:`ansible_configuration_settings`
       Ansible configuration documentation and settings
   :ref:`command_line_tools`
       Ansible tools, description and options
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   :ref:`communication_irc`
       How to join Ansible chat channels
