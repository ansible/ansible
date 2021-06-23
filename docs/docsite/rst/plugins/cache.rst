.. _cache_plugins:

Cache Plugins
=============

.. contents::
   :local:
   :depth: 2

Cache plugin implement a backend caching mechanism that allows Ansible to store gathered facts or inventory source data
without the performance hit of retrieving them from source.

The default cache plugin is the :ref:`memory <memory_cache>` plugin, which only caches the data for the current execution of Ansible. Other plugins with persistent storage are available to allow caching the data across runs.

You can use a separate cache plugin for inventory and facts. If an inventory-specific cache plugin is not provided and inventory caching is enabled, the fact cache plugin is used for inventory.

.. _enabling_cache:

Enabling Fact Cache Plugins
---------------------------

Only one fact cache plugin can be active at a time.

You can enable a cache plugin in the Ansible configuration, either via environment variable:

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

You will also need to configure other settings specific to each plugin. Consult the individual plugin documentation
or the Ansible :ref:`configuration <ansible_configuration_settings>` for more details.

A custom cache plugin is enabled by dropping it into a ``cache_plugins`` directory adjacent to your play, inside a role, or by putting it in one of the directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.


Enabling Inventory Cache Plugins
--------------------------------

Inventory may be cached using a file-based cache plugin (like jsonfile). Check the specific inventory plugin to see if it supports caching. Cache plugins inside a collection are not supported for caching inventory.
If an inventory-specific cache plugin is not specified Ansible will fall back to caching inventory with the fact cache plugin options.

The inventory cache is disabled by default. You may enable it via environment variable:

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

Similarly with fact cache plugins, only one inventory cache plugin can be active at a time and may be set via environment variable:

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

Consult the individual inventory plugin documentation or the Ansible :ref:`configuration <ansible_configuration_settings>` for more details.

.. _using_cache:

Using Cache Plugins
-------------------

Cache plugins are used automatically once they are enabled.


.. _cache_plugin_list:

Plugin List
-----------

You can use ``ansible-doc -t cache -l`` to see the list of available plugins.
Use ``ansible-doc -t cache <plugin name>`` to see specific documentation and examples.

.. toctree:: :maxdepth: 1
    :glob:

    cache/*

.. seealso::

   :ref:`action_plugins`
       Ansible Action plugins
   :ref:`callback_plugins`
       Ansible callback plugins
   :ref:`connection_plugins`
       Ansible connection plugins
   :ref:`inventory_plugins`
       Ansible inventory plugins
   :ref:`shell_plugins`
       Ansible Shell plugins
   :ref:`strategy_plugins`
       Ansible Strategy plugins
   :ref:`vars_plugins`
       Ansible Vars plugins
   `User Mailing List <https://groups.google.com/forum/#!forum/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
