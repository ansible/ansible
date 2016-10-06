Developing Plugins
==================

.. contents:: Topics

Plugins are pieces of code that augment Ansible's core functionality. Ansible ships with a number of handy plugins, and you can easily write your own.

The following types of plugins are available:

- *Callback* plugins enable you to hook into Ansible events for display or logging purposes.
- *Connection* plugins define how to communicate with inventory hosts.
- *Lookup* plugins are used to pull data from an external source.
- *Vars* plugins inject additional variable data into Ansible runs that did not come from an inventory, playbook, or the command line. 

This section describes the various types of plugins and how to implement them.


.. _developing_callbacks:

Callback Plugins
----------------

Callback plugins enable adding new behaviors to Ansible when responding to events.

.. _callback_examples:

Example Callback Plugins
++++++++++++++++++++++++

Ansible comes with a number of callback plugins that you can look at for examples. These can be found in `lib/ansible/plugins/callback <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/callback>`_.

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

Configuring Callback Plugins
++++++++++++++++++++++++++++

To activate a callback, drop it in a callback directory as configured in `ansible.cfg`. 

Plugins are loaded in alphanumeric order; for example, a plugin implemented in a file named `1_first.py` would run before a plugin file named `2_second.py`.

Callbacks need to be whitelisted in your `ansible.cfg` file in order to function. For example::
  
  #callback_whitelist = timer, mail, myplugin

.. _callback_development:

Developing Callback Plugins
+++++++++++++++++++++++++++

Callback plugins are created by creating a new class with the Base(Callbacks) class as the parent::

  from ansible.plugins.callback import CallbackBase
  from ansible import constants as C
  
  class CallbackModule(CallbackBase): 

From there, override the specific methods from the CallbackBase that you want to provide a callback for. For plugins intended for use with Ansible version 2.0 and later, you should only override methods that start with `v2`. For a complete list of methods that you can override, please see ``__init__.py`` in the `lib/ansible/plugins/callback <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/callback>`_ directory.


The following example shows how Ansible's timer plugin is implemented::

  # Make coding more python3-ish
  from __future__ import (absolute_import, division, print_function)
  __metaclass__ = type

  from datetime import datetime

  from ansible.plugins.callback import CallbackBase


  class CallbackModule(CallbackBase):
      """
      This callback module tells you how long your plays ran for.
      """
      CALLBACK_VERSION = 2.0
      CALLBACK_TYPE = 'aggregate'
      CALLBACK_NAME = 'timer'
      CALLBACK_NEEDS_WHITELIST = True
  
      def __init__(self):
  
          super(CallbackModule, self).__init__()
  
          self.start_time = datetime.now()
  
      def days_hours_minutes_seconds(self, runtime):
          minutes = (runtime.seconds // 60) % 60
          r_seconds = runtime.seconds - (minutes * 60)
          return runtime.days, runtime.seconds // 3600, minutes, r_seconds
  
      def playbook_on_stats(self, stats):
          self.v2_playbook_on_stats(stats)
  
      def v2_playbook_on_stats(self, stats):
          end_time = datetime.now()
          runtime = end_time - self.start_time
          self._display.display("Playbook run took %s days, %s hours, %s minutes, %s seconds" % (self.days_hours_minutes_seconds(runtime)))

Note that the CALLBACK_VERSION and CALLBACK_NAME definitons are required. If your callback plugin needs to write to stdout, you should define CALLBACK_TYPE = stdout in the subclass, and then the stdout plugin needs to be configured in `ansible.cfg` to override the default. For example::

  #stdout_callback = mycallbackplugin




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

.. _distributing_plugins:

Distributing Plugins
--------------------

Plugins are loaded from both Python's site_packages (those that ship with ansible) and a configured plugins directory, which defaults
to /usr/share/ansible/plugins, in a subfolder for each plugin type::

    * action
    * lookup
    * callback
    * connection
    * filter
    * strategy
    * cache
    * test
    * shell

To change this path, edit the ansible configuration file.

In addition, plugins can be shipped in a subdirectory relative to a top-level playbook, in folders named the same as indicated above.

They can also be shipped as part of a role, in a subdirectory named as indicated above. The plugin will be availiable as soon as the role
is called.

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
