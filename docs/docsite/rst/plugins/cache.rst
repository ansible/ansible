.. _cache_plugins:

Cache plugins
=============

.. contents::
   :local:
   :depth: 2

Cache plugins allow Ansible to store gathered facts or inventory source data without the performance hit of retrieving them from source.

The default cache plugin is the :ref:`memory <memory_cache>` plugin, which only caches the data for the current execution of Ansible. Other plugins with persistent storage are available to allow caching the data across runs. Some of these cache plugins write to files, others write to databases.

You can use different cache plugins for inventory and facts. If you enable inventory caching without setting an inventory-specific cache plugin, Ansible uses the fact cache plugin for both facts and inventory. If necessary, you can :ref:`create custom cache plugins <developing_cache_plugins>`.

.. _enabling_cache:

Enabling fact cache plugins
---------------------------

Fact caching is always enabled. However, only one fact cache plugin can be active at a time. You can select the cache plugin to use for fact caching in the Ansible configuration, either with an environment variable:

.. code-block:: shell

    export ANSIBLE_CACHE_PLUGIN=jsonfile

or in the ``ansible.cfg`` file:

.. code-block:: ini

    [defaults]
    fact_caching=redis

If the cache plugin is in a collection use the fully qualified name:

.. code-block:: ini

    [defaults]
    fact_caching = namespace.collection_name.cache_plugin_name

To enable a custom cache plugin, save it in a ``cache_plugins`` directory adjacent to your play, inside a role, or in one of the directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.

You also need to configure other settings specific to each plugin. Consult the individual plugin documentation or the Ansible :ref:`configuration <ansible_configuration_settings>` for more details.

Enabling inventory cache plugins
--------------------------------

Inventory caching is disabled by default. To cache inventory data, you must enable inventory caching and then select the specific cache plugin you want to use. Not all inventory plugins support caching, so check the documentation for the inventory plugin(s) you want to use. You can enable inventory caching with an environment variable:

.. code-block:: shell

    export ANSIBLE_INVENTORY_CACHE=True

or in the ``ansible.cfg`` file:

.. code-block:: ini

    [inventory]
    cache=True

or if the inventory plugin accepts a YAML configuration source, in the configuration file:

.. code-block:: yaml

    # dev.aws_ec2.yaml
    plugin: aws_ec2
    cache: True

Only one inventory cache plugin can be active at a time. You can set it with an environment variable:

.. code-block:: shell

    export ANSIBLE_INVENTORY_CACHE_PLUGIN=jsonfile

or in the ansible.cfg file:

.. code-block:: ini

    [inventory]
    cache_plugin=jsonfile

or if the inventory plugin accepts a YAML configuration source, in the configuration file:

.. code-block:: yaml

    # dev.aws_ec2.yaml
    plugin: aws_ec2
    cache_plugin: jsonfile

To cache inventory with a custom plugin in your plugin path, follow the :ref:`developer guide on cache plugins<developing_cache_plugins>`.

To cache inventory with a cache plugin in a collection, use the FQCN:

.. code-block:: ini

   [inventory]
   cache_plugin=collection_namespace.collection_name.cache_plugin

If you enable caching for inventory plugins without selecting an inventory-specific cache plugin, Ansible falls back to caching inventory with the fact cache plugin you configured. Consult the individual inventory plugin documentation or the Ansible :ref:`configuration <ansible_configuration_settings>` for more details.

.. Note: In Ansible 2.7 and earlier, inventory plugins can only use file-based cache plugins, such as jsonfile, pickle, and yaml.


.. _using_cache:

Using cache plugins
-------------------

Cache plugins are used automatically once they are enabled.


.. _cache_plugin_list:

Plugin list
-----------

You can use ``ansible-doc -t cache -l`` to see the list of available plugins.
Use ``ansible-doc -t cache <plugin name>`` to see specific documentation and examples.

.. seealso::

   :ref:`action_plugins`
       Action plugins
   :ref:`callback_plugins`
       Callback plugins
   :ref:`connection_plugins`
       Connection plugins
   :ref:`inventory_plugins`
       Inventory plugins
   :ref:`shell_plugins`
       Shell plugins
   :ref:`strategy_plugins`
       Strategy plugins
   :ref:`vars_plugins`
       Vars plugins
   `User Mailing List <https://groups.google.com/forum/#!forum/ansible-devel>`_
       Have a question?  Stop by the google group!
   :ref:`communication_irc`
       How to join Ansible chat channels
