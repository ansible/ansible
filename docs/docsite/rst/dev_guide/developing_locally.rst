************************************************************************
Extending Ansible: Creating or Copying Modules and Plugins for Local Use
************************************************************************

The easiest, quickest, and most popular way to extend Ansible is to copy or write a module or a plugin for local use. You can store modules and plugins on your Ansible control node for use within your team or organization. If you want to share a local plugin or module more widely, you can embed it in a role and publish it on Ansible Galaxy. 

Extending Ansible locally offers lots of shortcuts:

* you can choose any programming language you like
* you don't have to clone the main Ansible repo
* you don't have to open a pull request
* you don't have to add tests (though we highly recommend that you do!)

If you've already copied or written a local module or plugin, you can drop it in one of the "magic" directories and start using it right away.

.. _distributing_modules:

Loading Local Modules
---------------------
Ansible automatically loads all executable files found in certain directories as modules, so you can create or add a local module in any of these locations:

* any directory added to the ``ANSIBLE_LIBRARY`` environment variable (``$ANSIBLE_LIBRARY`` takes a colon-separated list like ``$PATH``)
* ``~/.ansible/plugins/modules/``
* ``/usr/share/ansible/plugins/modules/``

Once your module file is in one of these locations, Ansible will load it and you can use it in a any local task, playbook, or role. Use the name of the file as the module name: for example, if the module file is `~/.ansible/plugins/modules/local_users.py`, use `local_users` as the module name.

If you want to use your local module only in certain playbooks: 

* store it in a sub-directory called ``library`` in the directory that contains the playbook(s)

If you want to use your local module only in a single role:

* store it in a sub-directory called ``library`` within that role

.. _distributing_plugins:

Distributing Plugins
---------------------

Plugins are loaded from the library installed path and the configured plugins directory (check your `ansible.cfg`).
The location can vary depending on how you installed Ansible (pip, rpm, deb, etc) or by the OS/Distribution/Packager.
Plugins are automatically loaded when you have one of the following subfolders adjacent to your playbook or inside a role:

    * action_plugins
    * cache_plugins
    * callback_plugins
    * connection_plugins
    * filter_plugins
    * inventory_plugins
    * lookup_plugins
    * shell_plugins
    * strategy_plugins
    * test_plugins
    * vars_plugins


Loading Local Plugins
---------------------
Ansible loads plugins automatically too, loading each type of plugin separately. You'll need to know the ``plugin_type`` you're copying or creating (for example, cache, callback, filter, inventory, strategy, etc.). Once you know the type of plugin, you can create or add a local plugin in any of these locations:

* any directory added to the relevant ``ANSIBLE_plugin_type_PLUGINS`` environment variable (these variables, like ``$ANSIBLE_FILTER_PLUGINS`` and ``$ANSIBLE_VARS_PLUGINS`` take colon-separated lists like ``$PATH``)
* the directory named for the correct ``plugin_type`` within ``~/.ansible/plugins/`` - for example, ``~/.ansible/plugins/callback_plugins``
* the directory named for the correct ``plugin_type`` within ``/usr/share/ansible/plugins/`` - for example, ``/usr/share/ansible/plugins/plugin_type/action_plugins``

Once your plugin file is in one of these locations, Ansible will load it and you can use it in a any local task, playbook, or role. 

If you want to use your local plugin only in certain playbooks: 

* store it in a sub-directory for the correct ``plugin_type`` (for example, ``filter_plugins`` or ``inventory_plugins``) in the directory that contains the playbook(s)

If you want to use your local plugin only in a single role:

* store it in a sub-directory for the correct ``plugin_type`` (for example, ``cache_plugins`` or ``strategy_plugins``) within that role

When shipped as part of a role, the plugin will be available as soon as the role is called in the play.

If you haven't written your local module or plugin yet, start with the pages on :ref:`developing_modules` and :ref:`developing_plugins`.
