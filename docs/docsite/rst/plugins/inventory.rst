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

To transition to using an inventory plugin with a YAML configuration source from an inventory script, first create a file with the accepted filename schema for the plugin in question (each plugin should document any naming restrictions). For example, the aws_ec2 inventory plugin takes a file in the format <user_given_name>.aws_ec2.<yml/yaml> and the openstack inventory plugin parses clouds.<yml/yaml> or openstack.<yml/yaml>. After creating the file add ``plugin: plugin_name`` (where plugin_name could be aws_ec2, for example) to the first line.

The 'auto' inventory plugin is enabled by default and works by using the first line of the configuration file to indicate the plugin that should attempt to parse it (which is aws_ec2 here). The whitelist is also configurable. After the plugin is enabled and any required options or credentials have been provided, the output of ``ansible-inventory -i demo.aws_ec2.yml --graph`` should be populated. To make a YAML configuration file accessible by default without specifying ``-i`` you can set the default inventory path (via ``inventory`` in the ansible.cfg [defaults] section or the :envvar:`ANSIBLE_HOSTS` environment variable) to your inventory source(s). Now running ``ansible-inventory --graph`` should yield the same output as when you passed your YAML configuration source(s) directly. Custom inventory plugins and the documentation required to parse sources may also be added in your plugin path to be used in the same way.

The inventory source you provide may be a directory of inventory configuration files. The constructed inventory plugin only operates on those hosts already in inventory, so you may want the constructed inventory configuration parsed at a particular point (such as last). The directory is parsed recursively alphabetically and is not configurable so things should be named accordingly for it to work predictably with constructed. If an inventory plugin you are using supports constructed itself you can work around this by adding your constructed groups to those inventory plugin configuration files (as now it will not use constructed until it has added your hosts from that source). You may also want to reorder the precedence of which plugin attempts to parse a source first using the using the ansible.cfg ['inventory'] `enable_plugins` list.

Many inventory plugins extend features of the constructed inventory plugin that can be used to create custom groups and hostvars from the hosts that have already been added to inventory. The constructed `keyed_groups` option may be used to generate dynamic groups for certain host variables. The options `groups` and `compose` may also be used to create groups from the host variables and create/modify host variables. An example utilizing constructed features::

    plugin: aws_ec2
    regions:
      - us-east-1
      - us-east-2
    keyed_groups:
      # create/add a host to a tag_Name_value group for each aws_ec2 host's tags.Name variable
      - key: tags.Name
        prefix: tag_Name
        separator: ""
    groups:
      # create a development group by scanning for the keyword 'devel' in a list of a dictionary's keys and values
      development: "'devel' in (tags|list)"
    compose:
      # set the ansible_host variable to connect with the private IP address without changing the hostname
      ansible_host: private_ip_address

If a host does not have the variables in the configuration above (i.e. ``tags.Name``, ``tags``, ``private_ip_address``), the host will not be added to groups other than those that the inventory plugin creates and the ansible_host host variable will not be modified.

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
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
