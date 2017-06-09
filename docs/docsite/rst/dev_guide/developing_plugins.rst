Developing Plugins
==================

.. contents:: Topics

Plugins are pieces of code that augment Ansible's core functionality. Ansible ships with a number of handy plugins, and you can easily write your own.

The following types of plugins are available:

- *Action* plugins are front ends to modules and can execute actions on the controller before calling the modules themselves.
- *Cache* plugins are used to keep a cache of 'facts' to avoid costly fact-gathering operations.
- *Callback* plugins enable you to hook into Ansible events for display or logging purposes.
- *Connection* plugins define how to communicate with inventory hosts.
- *Filters* plugins allow you to manipulate data inside Ansible plays and/or templates. This is a Jinja2 feature; Ansible ships extra filter plugins.
- *Lookup* plugins are used to pull data from an external source. These are implemented using a custom Jinja2 function.
- *Strategy* plugins control the flow of a play and execution logic.
- *Shell* plugins deal with low-level commands and formatting for the different shells Ansible can encounter on remote hosts.
- *Test* plugins allow you to validate data inside Ansible plays and/or templates. This is a Jinja2 feature; Ansible ships extra test plugins.
- *Vars* plugins inject additional variable data into Ansible runs that did not come from an inventory, playbook, or the command line.

This section describes the various types of plugins and how to implement them.


.. _developing_callbacks:

Callback Plugins
----------------

Callback plugins enable adding new behaviors to Ansible when responding to events. By default, callback plugins control most of the output you see when running the command line programs.

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

You can activate a custom callback by either dropping it into a callback_plugins directory adjacent to your play or inside a role or by putting it in one of the callback directory sources configured in `ansible.cfg`.

Plugins are loaded in alphanumeric order; for example, a plugin implemented in a file named `1_first.py` would run before a plugin file named `2_second.py`.

Most callbacks shipped with Ansible are disabled by default and need to be whitelisted in your `ansible.cfg` file in order to function. For example::

  #callback_whitelist = timer, mail, mycallbackplugin


Managing stdout
```````````````

You can only have one plugin be the main manager of your console output. If you want to replace the default, you should define CALLBACK_TYPE = stdout in the subclass and then configure the stdout plugin in `ansible.cfg`. For example::

  #stdout_callback = mycallbackplugin



.. _callback_development:

Developing Callback Plugins
+++++++++++++++++++++++++++

Callback plugins are created by creating a new class with the Base(Callbacks) class as the parent:

.. code-block:: python

  from ansible.plugins.callback import CallbackBase
  from ansible import constants as C

  class CallbackModule(CallbackBase):
      pass

From there, override the specific methods from the CallbackBase that you want to provide a callback for. For plugins intended for use with Ansible version 2.0 and later, you should only override methods that start with `v2`. For a complete list of methods that you can override, please see ``__init__.py`` in the `lib/ansible/plugins/callback <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/callback>`_ directory.


The following example shows how Ansible's timer plugin is implemented:

.. code-block:: python

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

Note that the CALLBACK_VERSION and CALLBACK_NAME definitions are required for properly functioning plugins for Ansible >=2.0.

.. _developing_connection_plugins:

Connection Plugins
------------------

By default, Ansible ships with a 'paramiko' SSH, native ssh (just called 'ssh'), 'local' connection type, and there are also some minor players like 'chroot' and 'jail'.  All of these can be used in playbooks and with /usr/bin/ansible to decide how you want to talk to remote machines.  The basics of these connection types
are covered in the :doc:`../intro_getting_started` section.  Should you want to extend Ansible to support other transports (SNMP, Message bus, etc) it's as simple as copying the format of one of the existing modules and dropping it into the connection plugins
directory.   The value of 'smart' for a connection allows selection of paramiko or openssh based on system capabilities, and chooses
'ssh' if OpenSSH supports ControlPersist, in Ansible 1.2.1 and later.  Previous versions did not support 'smart'.

More documentation on writing connection plugins is pending, though you can jump into `lib/ansible/plugins/connection <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/connection>`_ and figure things out pretty easily.

.. _developing_lookup_plugins:

Lookup Plugins
--------------

Lookup plugins are used to pull in data from external data stores. Lookup plugins can be used within playbooks for both looping - playbook language constructs like "with_fileglob" and "with_items" are implemented via lookup plugins - and to return values into a variable or parameter.

Here's a simple lookup plugin implementation - this lookup returns the contents of a text file as a variable:

.. code-block:: python

  from ansible.errors import AnsibleError, AnsibleParserError
  from ansible.plugins.lookup import LookupBase

  try:
      from __main__ import display
  except ImportError:
      from ansible.utils.display import Display
      display = Display()


  class LookupModule(LookupBase):

      def run(self, terms, variables=None, **kwargs):

          ret = []

          for term in terms:
              display.debug("File lookup term: %s" % term)

              # Find the file in the expected search path
              lookupfile = self.find_file_in_search_path(variables, 'files', term)
              display.vvvv(u"File lookup using %s as file" % lookupfile)
              try:
                  if lookupfile:
                      contents, show_data = self._loader._get_file_contents(lookupfile)
                      ret.append(contents.rstrip())
                  else:
                      raise AnsibleParserError()
              except AnsibleParserError:
                  raise AnsibleError("could not locate file in lookup: %s" % term)

          return ret

An example of how this lookup is called::

  ---
  - hosts: all
    vars:
       contents: "{{ lookup('file', '/etc/foo.txt') }}"

    tasks:

       - debug: msg="the value of foo.txt is {{ contents }} as seen today {{ lookup('pipe', 'date +"%Y-%m-%d"') }}"

Errors encountered during execution should be returned by raising AnsibleError() with a message describing the error. Any strings returned by your lookup plugin implementation that could ever contain non-ASCII characters must be converted into Python's unicode type because the strings will be run through jinja2.  To do this, you can use:

.. code-block:: python

    from ansible.module_utils._text import to_text
    result_string = to_text(result_string)

For more example lookup plugins, check out the source code for the lookup plugins that are included with Ansible here: `lib/ansible/plugins/lookup <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/lookup>`_.

For usage examples of lookup plugins, see `Using Lookups <http://docs.ansible.com/ansible/playbooks_lookups.html>`_.

.. _developing_vars_plugins:

Vars Plugins
------------

Playbook constructs like 'host_vars' and 'group_vars' work via 'vars' plugins.  They inject additional variable
data into ansible runs that did not come from an inventory, playbook, or command line.  Note that variables
can also be returned from inventory, so in most cases, you won't need to write or understand vars_plugins.

More documentation on writing vars plugins is pending, though you can jump into `lib/ansible/plugins <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/>`_ and figure
things out pretty easily.

If you find yourself wanting to write a vars_plugin, it's more likely you should write an inventory script instead.

.. _developing_filter_plugins:

Filter Plugins
--------------

Filter plugins are used for manipulating data. They are a feature of Jinja2 and are also available in Jinja2 templates used by the `template` module. As with all plugins, they can be easily extended, but instead of having a file for each one you can have several per file. Most of the filter plugins shipped with Ansible reside in a `core.py`.

See `lib/ansible/plugins/filter <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/filter>`_ for details.

.. _developing_test_plugins:

Test Plugins
------------

Test plugins are for verifying data. They are a feature of Jinja2 and are also available in Jinja2 templates used by the `template` module. As with all plugins, they can be easily extended, but instead of having a file for each one you can have several per file. Most of the test plugins shipped with Ansible reside in a `core.py`. These are specially useful in conjunction with some filter plugins like `map` and `select`; they are also available for conditional directives like `when:`.

See `lib/ansible/plugins/test <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/test>`_ for details.

.. _distributing_plugins:

Distributing Plugins
--------------------

Plugins are loaded from the library installed path and the configured plugins directory (check your `ansible.cfg`).
The location can vary depending on how you installed Ansible (pip, rpm, deb, etc) or by the OS/Distribution/Packager.
Plugins are automatically loaded when you have one of the following subfolders adjacent to your playbook or inside a role:

    * action_plugins
    * lookup_plugins
    * callback_plugins
    * connection_plugins
    * filter_plugins
    * strategy_plugins
    * cache_plugins
    * test_plugins
    * shell_plugins

When shipped as part of a role, the plugin will be available as soon as the role is called in the play.

.. seealso::

   :doc:`../modules`
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
