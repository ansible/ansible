Inventory Plugins
-----------------

Inventory plugins allow users to point at data sources to compile the inventory of hosts that Ansible uses to target it's tasks.
They control what happens when with ``-i /path/to/file`` and/or ``-i 'host1, host2`` when passed into Ansible (or from other configuration sources).

.. _enabling_inventory_plugins:

Enabling Inventory Plugins
++++++++++++++++++++++++++

Most inventory plugins shipped with Ansible are disabled by default and need to be whitelisted in your `ansible.cfg` file in order to function.
For example, this is how the default looks like:

.. code-block:: ini

   [inventory]
   enable_plugins = 'host_list', 'script', 'yaml', 'ini'

This list also establishes the order in which each plugin tries to parse an inventory source (in the case 2 plugins can use the same source).
Any plugins left out of the list will not be considered, so you can 'optimize' your inventory loading by minimizing it to what you actually use:

.. code-block:: ini

   [inventory]
   enable_plugins = 'host_list', 'yaml'

You can use ``ansible-doc -t inventory -l`` to see the list of available plugins,
use ``ansible-doc -t inventory <plugin name>`` to see specific documents and examples.

.. toctree:: :maxdepth: 1
    :glob:

    inventory/*

.. seealso::

   :doc:`../playbooks`
       An introduction to playbooks
   :doc:`callback`
       Ansible callback plugins
   :doc:`connection`
       Ansible connection plugins
   :doc:`../playbooks_filters`
       Jinja2 filter plugins
   :doc:`../playbooks_tests`
       Jinja2 test plugins
   :doc:`../playbooks_lookups`
       Jinja2 lookup plugins
   :doc:`vars`
       Ansible vars plugins
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
