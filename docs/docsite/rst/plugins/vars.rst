.. _vars_plugins:

Vars plugins
============

.. contents::
   :local:
   :depth: 2

Vars plugins inject additional variable data into Ansible runs that did not come from an inventory source, playbook, or command line. Playbook constructs like 'host_vars' and 'group_vars' work using vars plugins. For more details about variables in Ansible, see :ref:`playbooks_variables`.

Vars plugins were partially implemented in Ansible 2.0 and rewritten to be fully implemented starting with Ansible 2.4.

The :ref:`host_group_vars <host_group_vars_vars>` plugin shipped with Ansible enables reading variables from :ref:`host_variables` and :ref:`group_variables`.

.. _enable_vars:

Enabling vars plugins
---------------------

You can activate a custom vars plugin by either dropping it into a ``vars_plugins`` directory adjacent to your play, inside a role, or by putting it in one of the directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.

Most vars plugins are disabled by default. To enable a vars plugin, set ``vars_plugins_enabled`` in the ``defaults`` section of :ref:`ansible.cfg <ansible_configuration_settings>` or set the ``ANSIBLE_VARS_ENABLED`` environment variable to the list of vars plugins you want to execute. By default, the :ref:`host_group_vars <host_group_vars_vars>` plugin shipped with Ansible is enabled.

Starting in Ansible 2.10, you can use vars plugins in collections. All vars plugins in collections must be explicitly enabled and must use the fully qualified collection name in the format ``namespace.collection_name.vars_plugin_name``.

.. code-block:: yaml

    [defaults]
    vars_plugins_enabled = host_group_vars,namespace.collection_name.vars_plugin_name

.. _using_vars:

Using vars plugins
------------------

By default, vars plugins are used on demand automatically after they are enabled.

Starting in Ansible 2.10, vars plugins can be made to run at specific times. `ansible-inventory` does not use these settings, and always loads vars plugins.

The global setting ``RUN_VARS_PLUGINS`` can be set in ``ansible.cfg`` using ``run_vars_plugins`` in the ``defaults`` section or by the ``ANSIBLE_RUN_VARS_PLUGINS`` environment variable. The default option, ``demand``, runs any enabled vars plugins relative to inventory sources whenever variables are demanded by tasks. You can use the option ``start`` to run any enabled vars plugins relative to inventory sources after importing that inventory source instead.

You can also control vars plugin execution on a per-plugin basis for vars plugins that support the ``stage`` option. To run the :ref:`host_group_vars <host_group_vars_vars>` plugin after importing inventory you can add the following to :ref:`ansible.cfg <ansible_configuration_settings>`:

.. code-block:: ini

    [vars_host_group_vars]
    stage = inventory

.. _vars_plugin_list:

Plugin list
-----------

You can use ``ansible-doc -t vars -l`` to see the list of available vars plugins. Use ``ansible-doc -t vars <plugin name>`` to see plugin-specific documentation and examples.


.. seealso::

   :ref:`cache_plugins`
       Cache plugins
   :ref:`lookup_plugins`
       Lookup plugins
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   :ref:`communication_irc`
       How to join Ansible chat channels
