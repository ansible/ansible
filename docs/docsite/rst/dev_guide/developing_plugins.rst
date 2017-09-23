Developing Plugins
==================

.. contents:: Topics

Plugins are pieces of code that augment Ansible's core functionality. Ansible ships with a number of handy plugins, and you can easily write your own.
This section describes the various types of plugins and how to implement them.

.. _plugin_guidelines:

General Guidelines
------------------

Some things that should apply to any type of plugin you develop.

Raising Errors
``````````````

In general, errors encountered during execution should be returned by raising AnsibleError() or similar class with a message describing the error.
When wrapping other exceptions into error messages you should always use the `to_text` Ansible function to ensure proper string compatiblity across
Python versions:

.. code-block:: python

    from ansible.module_utils._text import to_native

    try:
        cause_an_exeption()
    except Exception as e:
        AnsibleError('Something happend, this was original exception: %s' % to_native(e))

Check the different AnsibleError objects and see which one applies the best to your situation.

String encoding
```````````````
Any strings returned by your plugin that could ever contain non-ASCII characters must be converted into Python's unicode type
because the strings will be run through jinja2.  To do this, you can use:

.. code-block:: python

    from ansible.module_utils._text import to_text
    result_string = to_text(result_string)

Plugin configuration
````````````````````

Starting in 2.4 and going forward, we are unifying how each plugin type is configured and how they get those settings, plugins will be able to 'declare'
their needs and have Ansible provide them with the 'resolved' configuration. As of 2.4 both Callback and Connection type plugins can use this system,
most plugins will be able to use  `self._options[<optionname>]` to access the settings, except callbacks that due to prexisting collsion
use `self._plugin_optoins[<optionname>]`.

Plugins that supprot docs (see `ansible-doc` for the list) are now required to provide documentation to be considered for merge into the Ansible repo.

Also be aware that if you inherit from a plugin you must ALSO document the optoins it takes, either via a documentation fragment or as a copy.

.. _developing_callbacks:

Callback Plugins
----------------

See :doc: plugins/callback as to what they are and how to use them. This section explains how to use them.


Callback plugins are created by creating a new class with the Base(Callbacks) class as the parent:

.. code-block:: python

  from ansible.plugins.callback import CallbackBase

  class CallbackModule(CallbackBase):
      pass

From there, override the specific methods from the CallbackBase that you want to provide a callback for.
For plugins intended for use with Ansible version 2.0 and later, you should only override methods that start with `v2`.
For a complete list of methods that you can override, please see ``__init__.py`` in the
`lib/ansible/plugins/callback <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/callback>`_ directory.


The following example shows a modified example Ansible's timer plugin is implemented,
but with an extra option so you can see how configuration works in Ansible >= 2.4:

.. code-block:: python

  # Make coding more python3-ish, this is required for contributions to Ansible
  from __future__ import (absolute_import, division, print_function)
  __metaclass__ = type

  # not only visible to ansible-doc, it also 'declares' the options the plugin requires and how to configure them.
  DOCUMENTATION = '''
    callback: timer
    callback_type: aggregate
    requirements:
      - whitelist in configuration
    short_description: Adds time to play stats
    version_added: "2.0"
    description:
        - This callback just adds total play duration to the play stats.
    options:
      format_string:
        description: format of the string shown to user at play end
        ini:
          - section: callback_timer
            key: format_string
        env:
          - name: ANSIBLE_CALLBACK_TIMER_FORMAT
        default: "Playbook run took %s days, %s hours, %s minutes, %s seconds"
  '''
  from datetime import datetime

  from ansible.plugins.callback import CallbackBase


  class CallbackModule(CallbackBase):
      """
      This callback module tells you how long your plays ran for.
      """
      CALLBACK_VERSION = 2.0
      CALLBACK_TYPE = 'aggregate'
      CALLBACK_NAME = 'timer'

      # only needed if you ship it and dont want to enable by default
      CALLBACK_NEEDS_WHITELIST = True

      def __init__(self):

          # make sure the expected objects are present, calling the base's __init__
          super(CallbackModule, self).__init__()

          # start the timer when the plugin is loaded, the first play should start a few miliseconds after.
          self.start_time = datetime.now()

      def _days_hours_minutes_seconds(self, runtime):
          ''' internal helper method for this callback '''
          minutes = (runtime.seconds // 60) % 60
          r_seconds = runtime.seconds - (minutes * 60)
          return runtime.days, runtime.seconds // 3600, minutes, r_seconds

      # this is only event we care about for display, when the play shows it's summary stats, the rest are ignored by the base class
      def v2_playbook_on_stats(self, stats):
          end_time = datetime.now()
          runtime = end_time - self.start_time

          # Shows the usage of a config option declared in the DOCUMENTATION variable, Ansible will have set it when it loads the plugin.
          # Also note the use of the display object to print to screen, available to all callbacks, you should prefer this over printing yoruself
          self._display.display(self._plugin_options['format_string'] % (self._days_hours_minutes_seconds(runtime)))

Note that the CALLBACK_VERSION and CALLBACK_NAME definitions are required for properly functioning plugins for Ansible >=2.0.
CALLBACK_TYPE is mostly needed to distinguish 'stout' plugins from the rest, as you can only load one of that type.

.. _developing_connection_plugins:

Connection Plugins
------------------

By default, Ansible ships with a 'paramiko' SSH, native ssh (just called 'ssh'), 'local' connection type, and there are also some minor players like 'chroot' and 'jail'.  All of these can be used in playbooks and with /usr/bin/ansible to decide how you want to talk to remote machines.  The basics of these connection types
are covered in the :doc:`../intro_getting_started` section.  Should you want to extend Ansible to support other transports (SNMP, Message bus, etc) it's as simple as copying the format of one of the existing modules and dropping it into the connection plugins
directory.   The value of 'smart' for a connection allows selection of paramiko or openssh based on system capabilities, and chooses
'ssh' if OpenSSH supports ControlPersist, in Ansible 1.2.1 and later.  Previous versions did not support 'smart'.

More documentation on writing connection plugins is pending, though you can jump into
`lib/ansible/plugins/connection <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/connection>`_ and figure things out pretty easily.

.. _developing_inventory_plugins:

Inventory Plugins
-----------------

Added in Ansible 2.4 they are in charge of parsing inventory sources and forming the 'in memory' representation of the Inventory.

They are invoked via the InventoryManager and are given access to any existing inventory data added previouslly,
they are given an 'inventory source' as supplied to Ansible (via config/optoins/defaults/etc), which they can ignore
(return false from the `verify_file` method), or attempt to parse (via `parse` method) and return an `AnsibleParserError` on failure.

.. code-block:: python

   def parse(self, inventory, loader, path, cache=True):
        pass # your code goes here

The parameters are:

 * inventory: inventory object with existing data and the methods to add hosts/groups/variables to inventory
 * loader: Ansible's DataLoader, it can read files, auto load JSON/YAML and decrypt vaulted data, it also caches read filesh.
 * path: string with inventory source (normally a path, but not required)
 * cache: hint to the plugin if it should use or avoid caches (Cache plugin and/or loader)

Inventory sources are strings, most of the time they correspond to a file path, but can also be a comma separated list,
a uri or anything your plugin can use as input.
The 'inventory source' provided can be either a string (`host_list` plugin), a data file (like consumed by the `yaml` and `ini` plugins),
a configuration file (see `virtualbox` and `constructed`) or even a script or executable (the `script` uses those) which is how 'inventory scripts' work.

Inventory plugins can also use the configured Cache plugin to store and retrieve data to avoid costly external calls,
of course this only works if using a 'persistent' cache (i.e not the memory one).

Be aware that inventory plugins normally only execute at the start of the run, before playbooks/plays and roles are found,
but they can be 're-executed' via the `meta: refresh_inventory` task, which will clear out the existing inventory and rebuild it.

More documentation on writing inventory plugins is pending, though you can jump into
`lib/ansible/plugins/inventory <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/inventory>`_ and figure things out pretty easily.

.. _developing_lookup_plugins:

Lookup Plugins
--------------

Lookup plugins are used to pull in data from external data stores. Lookup plugins can be used within playbooks for both looping - playbook language constructs like "with_fileglob" and "with_items" are implemented via lookup plugins - and to return values into a variable or parameter.

Here's a simple lookup plugin implementation - this lookup returns the contents of a text file as a variable:

.. code-block:: python

  # python 3ish headers, required if submitting to Ansible
  from __future__ import (absolute_import, division, print_function)
  __metaclass__ = type

  DOCUMENTATION = """
        lookup: file
          author: Daniel Hokka Zakrisson <daniel@hozac.com>
          version_added: "0.9"
          short_description: read file contents
          description:
              - This lookup returns the contents from a file on the Ansible controller's file system.
          options:
            _terms:
              description: path(s) of files to read
              required: True
          notes:
            - if read in variable context, the file can be interpreted as YAML if the content is valid to the parser.
            - this lookup does not understand 'globing', use the fileglob lookup instead.
  """
  from ansible.errors import AnsibleError, AnsibleParserError
  from ansible.plugins.lookup import LookupBase

  try:
      from __main__ import display
  except ImportError:
      from ansible.utils.display import Display
      display = Display()


  class LookupModule(LookupBase):

      def run(self, terms, variables=None, **kwargs):


          # lookups in general are expected to both take a list as input and output a list
          # this is done so they work with the looping construct `with_`.
          ret = []
          for term in terms:
              display.debug("File lookup term: %s" % term)

              # Find the file in the expected search path, using a class method
              # that implements the 'expected' search path for Ansible plugins.
              lookupfile = self.find_file_in_search_path(variables, 'files', term)

              # Don't use print or your own logging, the display class
              # takes care of it in a unified way.
              display.vvvv(u"File lookup using %s as file" % lookupfile)
              try:
                  if lookupfile:
                      contents, show_data = self._loader._get_file_contents(lookupfile)
                      ret.append(contents.rstrip())
                  else:
                      # Always use ansible error classes to throw 'final' exceptions,
                      # so the Ansible engine will know how to deal with them.
                      # The Parser error indicates invalid options passed
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

For more example lookup plugins, check out the source code for the lookup plugins that are included with Ansible here: `lib/ansible/plugins/lookup <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/lookup>`_.

For usage examples of lookup plugins, see `Using Lookups <http://docs.ansible.com/ansible/playbooks_lookups.html>`_.

.. _developing_vars_plugins:

Vars Plugins
------------

Playbook constructs like 'host_vars' and 'group_vars' work via 'vars' plugins.
They inject additional variable data into ansible runs that did not come from an inventory source, playbook, or command line.

Vars plugins got rewritten in 2.4 and had been semi-functional since 2.0.

Older pugins used a `run` method as their main body/work:

.. code-block:: python

    def run(self, name, vault_password=None):
        pass # your code goes here


But Ansible 2.0 did not pass passwords to them so vaults were unavilable.
Most of the work now  happens in the `get_vars` method which is called from the VariableManager when needed.

.. code-block:: python

    def get_vars(self, loader, path, entities):
        pass # your code goes here

The parameters are:

 * loader: Ansible's DataLoader, it can read files, auto load JSON/YAML and decrypt vaulted data, it also caches read filesh.
 * path: this is 'directory data' for every inventory source and the current play's playbook directory, so they can search for data
         in reference to them, `get_vars` will be called at least once per available path.
 * entities: these are host or group names that are pertinent to the variables needed, the plugin will get called once for hosts and again for groups.

This method just needs to return a dictionary structure with the pertinent variables.

Since Ansible 2.4, vars plugins execute as needed when preparing to execute a task, this avoids the costly 'always execute' that used
to happend during inventory construction.

More documentation on writing vars plugins is pending, though you can jump into
`lib/ansible/plugins/vars <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/vars>`_ and figure things out pretty easily.


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
    * inventory_plugins
    * filter_plugins
    * strategy_plugins
    * cache_plugins
    * test_plugins
    * shell_plugins
    * vars_plugins


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
