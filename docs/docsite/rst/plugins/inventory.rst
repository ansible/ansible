.. _inventory_plugins:

Inventory Plugins
=================

.. contents::
   :local:
   :depth: 2

Inventory plugins allow users to point at data sources to compile the inventory of hosts that Ansible uses to target tasks, either via the ``-i /path/to/file`` and/or ``-i 'host1, host2'`` command line parameters or from other configuration sources.


.. _enabling_inventory:

Enabling inventory plugins
--------------------------

Most inventory plugins shipped with Ansible are disabled by default and need to be whitelisted in your
:ref:`ansible.cfg <ansible_configuration_settings>` file in order to function.  This is how the default whitelist looks in the
config file that ships with Ansible:

.. code-block:: ini

   [inventory]
   enable_plugins = host_list, script, auto, yaml, ini, toml

This list also establishes the order in which each plugin tries to parse an inventory source. Any plugins left out of the list will not be considered, so you can 'optimize' your inventory loading by minimizing it to what you actually use. For example:

.. code-block:: ini

   [inventory]
   enable_plugins = advanced_host_list, constructed, yaml

The ``auto`` inventory plugin can be used to automatically determines which inventory plugin to use for a YAML configuration file. It can also be used for inventory plugins in a collection.

To whitelist specific inventory plugins in a collection you need to use the fully qualified name:

.. code-block:: ini

   [inventory]
   enable_plugins = namespace.collection_name.inventory_plugin_name


.. _using_inventory:

Using inventory plugins
-----------------------

The only requirement for using an inventory plugin after it is enabled is to provide an inventory source to parse.
Ansible will try to use the list of enabled inventory plugins, in order, against each inventory source provided.
Once an inventory plugin succeeds at parsing a source, any remaining inventory plugins will be skipped for that source.

To start using an inventory plugin with a YAML configuration source, create a file with the accepted filename schema for the plugin in question, then add ``plugin: plugin_name``. Each plugin documents any naming restrictions. For example, the aws_ec2 inventory plugin has to end with ``aws_ec2.(yml|yaml)``

.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: aws_ec2

Or for the openstack plugin the file has to be called ``clouds.yml`` or ``openstack.(yml|yaml)``:

.. code-block:: yaml

    # clouds.yml or openstack.(yml|yaml)
    plugin: openstack

To use a plugin in a collection provide the fully qualified name:

.. code-block:: yaml

    plugin: namespace.collection_name.inventory_plugin_name

The ``auto`` inventory plugin is enabled by default and works by using the ``plugin`` field to indicate the plugin that should attempt to parse it. You can configure the whitelist/precedence of inventory plugins used to parse source using the `ansible.cfg` ['inventory'] ``enable_plugins`` list. After enabling the plugin and providing any required options, you can view the populated inventory with ``ansible-inventory -i demo.aws_ec2.yml --graph``:

.. code-block:: text

    @all:
      |--@aws_ec2:
      |  |--ec2-12-345-678-901.compute-1.amazonaws.com
      |  |--ec2-98-765-432-10.compute-1.amazonaws.com
      |--@ungrouped:

If you are using an inventory plugin in a playbook-adjacent collection and want to test your setup with ``ansible-inventory``, you will need to use the ``--playbook-dir`` flag.

You can set the default inventory path (via ``inventory`` in the `ansible.cfg` [defaults] section or the :envvar:`ANSIBLE_INVENTORY` environment variable) to your inventory source(s). Now running ``ansible-inventory --graph`` should yield the same output as when you passed your YAML configuration source(s) directly. You can add custom inventory plugins to your plugin path to use in the same way.

Your inventory source might be a directory of inventory configuration files. The constructed inventory plugin only operates on those hosts already in inventory, so you may want the constructed inventory configuration parsed at a particular point (such as last). Ansible parses the directory recursively, alphabetically. You cannot configure the parsing approach, so name your files to make it work predictably. Inventory plugins that extend constructed features directly can work around that restriction by adding constructed options in addition to the inventory plugin options. Otherwise, you can use ``-i`` with multiple sources to impose a specific order, e.g. ``-i demo.aws_ec2.yml -i clouds.yml -i constructed.yml``.

You can create dynamic groups using host variables with the constructed ``keyed_groups`` option. The option ``groups`` can also be used to create groups and ``compose`` creates and modifies host variables. Here is an aws_ec2 example utilizing constructed features:

.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: aws_ec2
    regions:
      - us-east-1
      - us-east-2
    keyed_groups:
      # add hosts to tag_Name_value groups for each aws_ec2 host's tags.Name variable
      - key: tags.Name
        prefix: tag_Name_
        separator: ""
    groups:
      # add hosts to the group development if any of the dictionary's keys or values is the word 'devel'
      development: "'devel' in (tags|list)"
    compose:
      # set the ansible_host variable to connect with the private IP address without changing the hostname
      ansible_host: private_ip_address

Now the output of ``ansible-inventory -i demo.aws_ec2.yml --graph``:

.. code-block:: text

    @all:
      |--@aws_ec2:
      |  |--ec2-12-345-678-901.compute-1.amazonaws.com
      |  |--ec2-98-765-432-10.compute-1.amazonaws.com
      |  |--...
      |--@development:
      |  |--ec2-12-345-678-901.compute-1.amazonaws.com
      |  |--ec2-98-765-432-10.compute-1.amazonaws.com
      |--@tag_Name_ECS_Instance:
      |  |--ec2-98-765-432-10.compute-1.amazonaws.com
      |--@tag_Name_Test_Server:
      |  |--ec2-12-345-678-901.compute-1.amazonaws.com
      |--@ungrouped

If a host does not have the variables in the configuration above (i.e. ``tags.Name``, ``tags``, ``private_ip_address``), the host will not be added to groups other than those that the inventory plugin creates and the ``ansible_host`` host variable will not be modified.

If an inventory plugin supports caching, you can enable and set caching options for an individual YAML configuration source or for multiple inventory sources using environment variables or Ansible configuration files. If you enable caching for an inventory plugin without providing inventory-specific caching options, the inventory plugin will use fact-caching options. Here is an example of enabling caching for an individual YAML configuration file:

.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: aws_ec2
    cache: yes
    cache_plugin: jsonfile
    cache_timeout: 7200
    cache_connection: /tmp/aws_inventory
    cache_prefix: aws_ec2

Here is an example of setting inventory caching with some fact caching defaults for the cache plugin used and the timeout in an ``ansible.cfg`` file:

.. code-block:: ini

   [defaults]
   fact_caching = jsonfile
   fact_caching_connection = /tmp/ansible_facts
   cache_timeout = 3600

   [inventory]
   cache = yes
   cache_connection = /tmp/ansible_inventory

Besides cache plugins shipped with Ansible, cache plugins eligible for caching inventory can also reside in a custom cache plugin path. Cache plugins in collections are not supported yet for inventory.

.. _inventory_plugin_list:

Plugin List
-----------

You can use ``ansible-doc -t inventory -l`` to see the list of available plugins.
Use ``ansible-doc -t inventory <plugin name>`` to see plugin-specific documentation and examples.

.. toctree:: :maxdepth: 1
    :glob:

    inventory/*

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`callback_plugins`
       Ansible callback plugins
   :ref:`connection_plugins`
       Ansible connection plugins
   :ref:`playbooks_filters`
       Jinja2 filter plugins
   :ref:`playbooks_tests`
       Jinja2 test plugins
   :ref:`playbooks_lookups`
       Jinja2 lookup plugins
   :ref:`vars_plugins`
       Ansible vars plugins
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
