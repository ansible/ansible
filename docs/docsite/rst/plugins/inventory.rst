.. contents:: Topics

.. _inventory_plugins:

Inventory Plugins
-----------------

Inventory plugins allow users to point at data sources to compile the inventory of hosts that Ansible uses to target tasks, either via the ``-i /path/to/file`` and/or ``-i 'host1, host2'`` command line parameters or from other configuration sources.


.. _enabling_inventory:

Enabling Inventory Plugins
++++++++++++++++++++++++++

Most inventory plugins shipped with Ansible are disabled by default and need to be whitelisted in your
:ref:`ansible.cfg <ansible_configuration_settings>` file in order to function.  This is how the default whitelist looks in the
config file that ships with Ansible:

.. code-block:: ini

   [inventory]
   enable_plugins = host_list, script, yaml, ini

This list also establishes the order in which each plugin tries to parse an inventory source. Any plugins left out of the list will not be considered, so you can 'optimize' your inventory loading by minimizing it to what you actually use. For example:

.. code-block:: ini

   [inventory]
   enable_plugins = advanced_host_list, constructed, yaml


.. _using_inventory:

Using Inventory Plugins
+++++++++++++++++++++++

The only requirement for using an inventory plugin after it is enabled is to provide an inventory source to parse.
Ansible will try to use the list of enabled inventory plugins, in order, against each inventory source provided.
Once an inventory plugin succeeds at parsing a source, the any remaining inventory plugins will be skipped for that source.


.. _inventory_plugin_list:

Plugin List
+++++++++++

You can use ``ansible-doc -t inventory -l`` to see the list of available plugins. 
Use ``ansible-doc -t inventory <plugin name>`` to see plugin-specific documentation and examples.

.. toctree:: :maxdepth: 1
    :glob:

    inventory/*

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :doc:`callback`
       Ansible callback plugins
   :doc:`connection`
       Ansible connection plugins
   :ref:`playbooks_filters`
       Jinja2 filter plugins
   :ref:`playbooks_tests`
       Jinja2 test plugins
   :ref:`playbooks_lookups`
       Jinja2 lookup plugins
   :doc:`vars`
       Ansible vars plugins
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
