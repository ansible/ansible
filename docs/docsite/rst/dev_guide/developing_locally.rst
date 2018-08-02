************************************************************************
Extending Ansible: Creating or Copying Modules and Plugins for Local Use
************************************************************************

The easiest, quickest, and most popular way to extend Ansible is to copy or write a module or a plugin for local use. You can store local modules and plugins on your Ansible control node for use within your team or organization. If you want to share a local plugin or module more widely, you can embed it in a role and publish it on Ansible Galaxy. 

Extending Ansible locally offers lots of shortcuts:

* you can choose any programming language you like
* you don't have to clone the main Ansible repo
* you don't have to open a pull request
* you don't have to add tests (though we highly recommend that you do!)

This page shows you where to save local modules and plugins so Ansible can find and use them. It's easy. Drop the module or plugin in the correct "magic" directory and start using it right away.

.. _distributing_modules:

Using Local Modules
-------------------
Ansible automatically loads all executable files found in certain directories as modules, so you can create or add a local module in any of these locations:

* any directory added to the ``ANSIBLE_LIBRARY`` environment variable (``$ANSIBLE_LIBRARY`` takes a colon-separated list like ``$PATH``)
* ``~/.ansible/plugins/modules/``
* ``/usr/share/ansible/plugins/modules/``

Once you save your module file in one of these locations, Ansible will load it and you can use it in any local task, playbook, or role. Use the name of the file as the module name: for example, if the module file is `~/.ansible/plugins/modules/local_users.py`, use `local_users` as the module name.

If you want to use your local module only in certain playbooks: 

* store it in a sub-directory called ``library`` in the directory that contains the playbook(s)

If you want to use your local module only in a single role:

* store it in a sub-directory called ``library`` within that role

.. _distributing_plugins:

Using Local Plugins
---------------------
Ansible loads plugins automatically too, loading each type of plugin separately from a directory named for the type of plugin. Here's the full list of plugin directory names:

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

You can create or add a local plugin in any of these locations:

* any directory added to the relevant ``ANSIBLE_plugin_type_PLUGINS`` environment variable (these variables, such as ``$ANSIBLE_FILTER_PLUGINS`` and ``$ANSIBLE_VARS_PLUGINS`` take colon-separated lists like ``$PATH``)
* the directory named for the correct ``plugin_type`` within ``~/.ansible/plugins/`` - for example, ``~/.ansible/plugins/callback_plugins``
* the directory named for the correct ``plugin_type`` within ``/usr/share/ansible/plugins/`` - for example, ``/usr/share/ansible/plugins/plugin_type/action_plugins``

Once your plugin file is in one of these locations, Ansible will load it and you can use it in a any local task, playbook, or role. 

If you want to use your local plugin only in certain playbooks: 

* store it in a sub-directory for the correct ``plugin_type`` (for example, ``filter_plugins`` or ``inventory_plugins``) in the directory that contains the playbook(s)

If you want to use your local plugin only in a single role:

* store it in a sub-directory for the correct ``plugin_type`` (for example, ``cache_plugins`` or ``strategy_plugins``) within that role

When shipped as part of a role, the plugin will be available as soon as the role is called in the play. If you've been using roles off Galaxy, you may have been using local modules and plugins without even realizing it.

If you haven't written your local module or plugin yet, start with the pages on :ref:`developing_modules` and :ref:`developing_plugins`.
