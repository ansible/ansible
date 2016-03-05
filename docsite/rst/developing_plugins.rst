Developing Plugins
==================

.. contents:: Topics

Ansible is pluggable in a lot of other ways separate from inventory scripts and callbacks.  Many of these features are there to cover fringe use cases and are infrequently needed, and others are pluggable simply because they are there to implement core features
in ansible and were most convenient to be made pluggable.

This section will explore these features, though they are generally not common in terms of things people would look to extend quite
as often.

.. _developing_connection_type_plugins:

Connection Type Plugins
-----------------------

By default, ansible ships with a 'paramiko' SSH, native ssh (just called 'ssh'), 'local' connection type, and there are also some minor players like 'chroot' and 'jail'.  All of these can be used
in playbooks and with /usr/bin/ansible to decide how you want to talk to remote machines.  The basics of these connection types
are covered in the :doc:`intro_getting_started` section.  Should you want to extend Ansible to support other transports (SNMP? Message bus?
Carrier Pigeon?) it's as simple as copying the format of one of the existing modules and dropping it into the connection plugins
directory.   The value of 'smart' for a connection allows selection of paramiko or openssh based on system capabilities, and chooses
'ssh' if OpenSSH supports ControlPersist, in Ansible 1.2.1 and later.  Previous versions did not support 'smart'.

More documentation on writing connection plugins is pending, though you can jump into `lib/ansible/plugins/connection <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/connection>`_ and figure things out pretty easily.

.. _developing_lookup_plugins:

Lookup Plugins
--------------

Language constructs like "with_fileglob" and "with_items" are implemented via lookup plugins.  Just like other plugin types, you can write your own.

More documentation on writing lookup plugins is pending, though you can jump into `lib/ansible/plugins/lookup <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/lookup>`_ and figure
things out pretty easily.

.. _developing_vars_plugins:

Vars Plugins
------------

Playbook constructs like 'host_vars' and 'group_vars' work via 'vars' plugins.  They inject additional variable
data into ansible runs that did not come from an inventory, playbook, or command line.  Note that variables
can also be returned from inventory, so in most cases, you won't need to write or understand vars_plugins.

More documentation on writing vars plugins is pending, though you can jump into `lib/ansible/inventory/vars_plugins <https://github.com/ansible/ansible/tree/devel/lib/ansible/inventory/vars_plugins>`_ and figure
things out pretty easily.

If you find yourself wanting to write a vars_plugin, it's more likely you should write an inventory script instead.

.. _developing_filter_plugins:

Filter Plugins
--------------

If you want more Jinja2 filters available in a Jinja2 template (filters like to_yaml and to_json are provided by default), they can be extended by writing a filter plugin.  Most of the time, when someone comes up with an idea for a new filter they would like to make available in a playbook, we'll just include them in 'core.py' instead.

Jump into `lib/ansible/plugins/filter <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/filter>`_ for details.

.. _developing_callbacks:

Callbacks
---------

Callbacks are one of the more interesting plugin types.  Adding additional callback plugins to Ansible allows for adding new behaviors when responding to events.

.. _callback_examples:

Examples
++++++++

Example callbacks are shown in `lib/ansible/plugins/callback <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/callback>`_.

The `log_plays
<https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/log_plays.py>`_
callback is an example of how to intercept playbook events to a log
file, and the `mail
<https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/mail.py>`_
callback sends email when playbooks complete.

The `osx_say
<https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/osx_say.py>`_
callback provided is particularly entertaining -- it will respond with
computer synthesized speech on OS X in relation to playbook events,
and is guaranteed to entertain and/or annoy coworkers.

.. _configuring_callbacks:

Configuring
+++++++++++

To activate a callback drop it in a callback directory as configured in :ref:`ansible.cfg <callback_plugins>`.

.. _callback_development:

Development
+++++++++++

More information will come later, though see the source of any of the existing callbacks and you should be able to get started quickly.
They should be reasonably self-explanatory.

.. _distributing_plugins:

Distributing Plugins
--------------------

Plugins are loaded from both Python's site_packages (those that ship with ansible) and a configured plugins directory, which defaults
to /usr/share/ansible/plugins, in a subfolder for each plugin type::

    * action_plugins
    * lookup_plugins
    * callback_plugins
    * connection_plugins
    * filter_plugins
    * vars_plugins
    * strategy_plugins

To change this path, edit the ansible configuration file.

In addition, plugins can be shipped in a subdirectory relative to a top-level playbook, in folders named the same as indicated above.

.. seealso::

   :doc:`modules`
       List of built-in modules
   :doc:`developing_api`
       Learn about the Python API for task execution
   :doc:`developing_inventory`
       Learn about how to develop dynamic inventory sources
   :doc:`developing_modules`
       Learn about how to write Ansible modules
   `Mailing List <http://groups.google.com/group/ansible-devel>`_
       The development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
