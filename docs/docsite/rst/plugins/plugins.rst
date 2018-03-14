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
   cache
   callback
   connection
   inventory
   lookup
   shell
   strategy
   vars
   playbooks_filters
   playbooks_tests
   ../user_guide/plugin_filtering_config

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`config`
       Ansible configuration documentation and settings
   :doc:`command_line_tools`
       Ansible tools, description and options
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
