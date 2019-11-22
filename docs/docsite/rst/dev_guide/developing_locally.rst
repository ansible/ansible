.. _using_local_modules_and_plugins:
.. _developing_locally:

**********************************
Adding modules and plugins locally
**********************************

.. contents::
   :local:

The easiest, quickest, and most popular way to extend Ansible is to copy or write a module or a plugin for local use. You can store local modules and plugins on your Ansible control node for use within your team or organization. You can also share a local plugin or module by embedding it in a role and publishing it on Ansible Galaxy. If you've been using roles off Galaxy, you may have been using local modules and plugins without even realizing it. If you're using a local module or plugin that already exists, this page is all you need.

Extending Ansible with local modules and plugins offers lots of shortcuts:

* You can copy other people's modules and plugins.
* If you're writing a new module, you can choose any programming language you like.
* You don't have to clone the main Ansible repo.
* You don't have to open a pull request.
* You don't have to add tests (though we recommend that you do!).

To save a local module or plugin so Ansible can find and use it, drop the module or plugin in the correct "magic" directory. For local modules, use the name of the file as the module name: for example, if the module file is ``~/.ansible/plugins/modules/local_users.py``, use ``local_users`` as the module name.

.. _modules_vs_plugins:

Modules and plugins: what's the difference?
===========================================
If you're looking to add local functionality to Ansible, you may be wondering whether you need a module or a plugin. Here's a quick overview of the differences:

* Modules are reusable, standalone scripts that can be used by the Ansible API, the :command:`ansible` command, or the :command:`ansible-playbook` command. Modules provide a defined interface, accepting arguments and returning information to Ansible by printing a JSON string to stdout before exiting. Modules execute on the target system (usually that means on a remote system) in separate processes.
* :ref:`Plugins <plugins_lookup>` augment Ansible's core functionality and execute on the control node within the ``/usr/bin/ansible`` process. Plugins offer options and extensions for the core features of Ansible - transforming data, logging output, connecting to inventory, and more.

.. _local_modules:

Adding a module locally
=======================
Ansible automatically loads all executable files found in certain directories as modules, so you can create or add a local module in any of these locations:

* any directory added to the ``ANSIBLE_LIBRARY`` environment variable (``$ANSIBLE_LIBRARY`` takes a colon-separated list like ``$PATH``)
* ``~/.ansible/plugins/modules/``
* ``/usr/share/ansible/plugins/modules/``

Once you save your module file in one of these locations, Ansible will load it and you can use it in any local task, playbook, or role.

To confirm that ``my_custom_module`` is available:

* type ``ansible-doc -t module my_custom_module``. You should see the documentation for that module.

To use a local module only in certain playbooks:

* store it in a sub-directory called ``library`` in the directory that contains the playbook(s)

To use a local module only in a single role:

* store it in a sub-directory called ``library`` within that role

.. _distributing_plugins:
.. _local_plugins:

Adding a plugin locally
=======================
Ansible loads plugins automatically too, loading each type of plugin separately from a directory named for the type of plugin. Here's the full list of plugin directory names:

    * action_plugins*
    * cache_plugins
    * callback_plugins
    * connection_plugins
    * filter_plugins*
    * inventory_plugins
    * lookup_plugins
    * shell_plugins
    * strategy_plugins
    * test_plugins*
    * vars_plugins

To load your local plugins automatically, create or add them in any of these locations:

* any directory added to the relevant ``ANSIBLE_plugin_type_PLUGINS`` environment variable (these variables, such as ``$ANSIBLE_INVENTORY_PLUGINS`` and ``$ANSIBLE_VARS_PLUGINS`` take colon-separated lists like ``$PATH``)
* the directory named for the correct ``plugin_type`` within ``~/.ansible/plugins/`` - for example, ``~/.ansible/plugins/callback``
* the directory named for the correct ``plugin_type`` within ``/usr/share/ansible/plugins/`` - for example, ``/usr/share/ansible/plugins/action``

Once your plugin file is in one of these locations, Ansible will load it and you can use it in a any local module, task, playbook, or role. Alternatively, you can edit your ``ansible.cfg`` file to add directories that contain local plugins - see :ref:`ansible_configuration_settings` for details.

To confirm that ``plugins/plugin_type/my_custom_plugin`` is available:

* type ``ansible-doc -t <plugin_type> my_custom_lookup_plugin``. For example, ``ansible-doc -t lookup my_custom_lookup_plugin``. You should see the documentation for that plugin. This works for all plugin types except the ones marked with ``*`` in the list above  - see :ref:`ansible-doc` for more details.

To use your local plugin only in certain playbooks:

* store it in a sub-directory for the correct ``plugin_type`` (for example, ``callback_plugins`` or ``inventory_plugins``) in the directory that contains the playbook(s)

To use your local plugin only in a single role:

* store it in a sub-directory for the correct ``plugin_type`` (for example, ``cache_plugins`` or ``strategy_plugins``) within that role

When shipped as part of a role, the plugin will be available as soon as the role is called in the play.
