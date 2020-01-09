.. _plugins_lookup:

********************
Working With Plugins
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
   httpapi
   inventory
   lookup
   netconf
   shell
   strategy
   vars
   ../user_guide/playbooks_filters
   ../user_guide/playbooks_tests
   ../user_guide/plugin_filtering_config

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`ansible_configuration_settings`
       Ansible configuration documentation and settings
   :ref:`command_line_tools`
       Ansible tools, description and options
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
