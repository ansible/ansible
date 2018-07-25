.. _developing_inventory:

Developing Dynamic Inventory
============================

.. contents:: Topics
   :local:

As described in :ref:`dynamic_inventory`, Ansible can pull inventory information from dynamic sources,
including cloud sources, using the supplied :ref:`inventory plugins <inventory_plugins>`.
If the source you want is not currently covered by existing plugins, you can create your own as with any other plugin type.

In previous versions you had to create a script or program that can output JSON in the correct format when invoked with the proper arguments.
You can still use and write inventory scripts, as we ensured backwards compatiblity via the :ref:`script inventory plugin <script_inventory>`
and there is no restriction on the programming language used.
If you choose to write a script, however, you will need to implement some features youself.
i.e caching, configuration management, dynamic variable and group composition, etc.
While with :ref:`inventory plugins <inventory_plugins>` you can leverage the Ansible codebase to add these common features.


.. _inventory_sources:

Inventory sources
-----------------

Inventory sources are strings (i.e what you pass to ``-i`` in the command line),
they can represent a path to a file/script or just be the raw data for the plugin to use.
Here are some plugins and the type of source they use:

+--------------------------------------------+--------------------------------------+
|  Plugin                                    | Source                               |
+--------------------------------------------+--------------------------------------+
| :ref:`host list <host_list_inventory>`     | A comma separated list of hosts      |
+--------------------------------------------+--------------------------------------+
| :ref:`yaml <yaml_inventory>`               | Path to a YAML format data file      |
+--------------------------------------------+--------------------------------------+
| :ref:`constructed <constructed_inventory>` | Path to a YAML configuration file    |
+--------------------------------------------+--------------------------------------+
| :ref:`ini <ini_inventory>`                 | Path to An ini formated data file    |
+--------------------------------------------+--------------------------------------+
| :ref:`virtualbox <virtualbox_inventory>`   | Path to a YAML configuration file    |
+--------------------------------------------+--------------------------------------+
| :ref:`script plugin <script_inventory>`    | Path to an executable outputing JSON |
+--------------------------------------------+--------------------------------------+



.. _developing_inventory_inventory_plugins:

Inventory Plugins
-----------------

Like most plugin types (except modules) they must be developed in Python, since they execute on the controller they should match the same requirements :ref:`control_machine_requirements`.

Most of the documentation in :ref:`developing_plugins` also applies here, so as to not repeat ourselves, you should read that document first and we'll include inventory plugin specifics next.

Inventory plugins normally only execute at the start of a run, before playbooks/plays and roles are loaded,
but they can be 're-executed' via the ``meta: refresh_inventory`` task, which will clear out the existing inventory and rebuild it.

When using the 'persistent' cache, inventory plugins can also use the configured cache plugin to store and retrieve data to avoid costly external calls.

.. _developing_an_inventory_plugin:

Developing an Inventory Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first thing you want to do is use the base class:

.. code-block:: python

    from ansible.plugins.inventory import BaseInventoryPlugin

    class InventoryModule(BaseInventoryPlugin):

        NAME = 'myplugin'  # used internally by Ansible, it should match the file name but not required

This class has a couple of methods each plugin should implement and a few helpers for parsing the inventory source and updating the inventory.

After you have the basic plugin working you might want to to incorporate other features by adding more base classes:

.. code-block:: python

    from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

    class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

        NAME = 'myplugin'

For the bulk of the work in the plugin, We mostly want to deal with 2 methods ``verify_file`` and ``parse``.

.. _inventory_plugin_verify_file:

verify_file
"""""""""""

This method is used by Ansible to make a quick determination if the inventory source is usable by the plugin. It does not need to be 100% accurate as there might be overlap in what plugins can handle and Ansible will try the enabled plugins (in order) by default.

.. code-block:: python

    def verify_file(self, path):
        ''' return true/false if this is possibly a valid file for this plugin to consume '''
        valid = False
        if super(InventoryModule, self).verify_file(path):
            # base class verifies that file exists and is readable by current user
            if path.endswith(('.vbox.yaml', '.vbox.yml')):
                valid = True
        return valid

In this case, from the :ref:`virtualbox inventory plugin <virtualbox_inventory>`, we screen for specific file name patterns to avoid attempting to consume any valid yaml file. You can add any type of condition here, but the most common one is 'extension matching'

Another example that actually does not use a 'file' but the inventory source string itself,
from the :ref:`host list <host_list_inventory>` plugin:

.. code-block:: python

    def verify_file(self, path):
        ''' don't call base class as we don't expect a path, but a host list '''
        host_list = path
        valid = False
        b_path = to_bytes(host_list, errors='surrogate_or_strict')
        if not os.path.exists(b_path) and ',' in host_list:
            # the path does NOT exist and there is a comma to indicate this is a 'host list'
            valid = True
        return valid

This method is just to expedite the inventory process and avoid uneccessary parsing of sources that are easy to filter out before causing a parse error.

.. _inventory_plugin_parse:

parse
"""""

This method does the bulk of the work in the plugin.

It takes the following paramters:

 * inventory: inventory object with existing data and the methods to add hosts/groups/variables to inventory
 * loader: Ansible's DataLoader. The DataLoader can read files, auto load JSON/YAML and decrypt vaulted data, and cache read files.
 * path: string with inventory source (this is usually a path, but is not required)
 * cache: indicates whether the plugin should use or avoid caches (cache plugin and/or loader)


The base class does some minimal assignment for reuse in other methods.

.. code-block:: python

       def parse(self, inventory, loader, path, cache=True):

        self.loader = loader
        self.inventory = inventory
        self.templar = Templar(loader=loader)

It is up to the plugin now to deal with the inventory source provided and translate that into the Ansible inventory.
To facilitate this there are a few of helper functions used in the example below:

.. code-block:: python

       NAME = 'myplugin'

       def parse(self, inventory, loader, path, cache=True):

            # call base method to ensure properties are available for use with other helper methods
            super(InventoryModule, self).parse(inventory, loader, path, cache)

            # this method will parse 'common format' inventory sources and
            # update any options declared in DOCUMENTATION as needed
            config = self._read_config_data(self, path)

            # if NOT using _read_config_data you should call set_options directly,
            # to process any defined configuration for this plugin,
            # if you dont define any options you can skip
            #self.set_options()

            # example consuming options from inventory source
            mysession = apilib.session(user=self.get_option('api_user'),
                                       password=self.get_option('api_pass'),
                                       server=self.get_option('api_server')
            )


            # make requests to get data to feed into inventorya
            mydata = myselss.getitall()

            #parse data and create inventory objects:
            for colo in mydata:
                for server in mydata[colo]['servers']:
                    self.inventory.add_host(server['name'])
                    self.inventory.set_varaible('ansible_host', server['external_ip'])

The specifics will vary depending on API and structure returned. But one thing to keep in mind, if the inventory source or any other issue crops up you should ``raise AnsibleParserError`` to let Ansible know that the source was invalid or the process failed.

For examples on how to implement an inventory plug in, see the source code here:
`lib/ansible/plugins/inventory <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/inventory>`_.

.. _inventory_source_common_format:

inventory source common format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To simplify development, most plugins use a mostly standard configuration file as the inventory source, YAML based and with just one required field ``plugin`` which should contain the name of the plugin that is expected to consume the file.
Depending on other common features used, other fields might be needed, but each plugin can also add it's own custom options as needed.
For example, if you use the integrated caching, ``cache_plugin``, ``cache_timeout`` and other cache related fields could be present.

.. _inventory_development_auto:

The 'auto' plugin
^^^^^^^^^^^^^^^^^

Since Ansible 2.5, we include the :ref:`auto inventory plugin <auto_inventory>` enabled by default, which itself just loads other plugins if they use the common YAML configuration format that specifies a ``plugin`` field that matches an inventory plugin name, this makes it easier to use your plugin w/o having to update configurations.


.. _inventory_scripts:
.. _developing_inventory_scripts:

Inventory Scripts
-----------------

Even though we now have inventory plugins, we still support inventory scripts, not only for backwards compatibility but also to allow users to leverage other programming languages.


.. _inventory_script_conventions:

Inventory script conventions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Inventory scripts must accept the ``--list`` and ``--host <hostname>`` arguments, other arguments are allowed but Ansible will not use them.
They might still be useful for when executing the scripts directly.

When the script is called with the single argument ``--list``, the script must output to stdout a JSON-encoded hash or
dictionary containing all of the groups to be managed.
Each group's value should be either a hash or dictionary containing a list of each host, any child groups,
and potential group variables, or simply a list of hosts::


    {
        "group001": {
            "hosts": ["host001", "host002"],
            "vars": {
                "var1": true
            },
            "children": ["group002"]
        },
        "group002": {
            "hosts": ["host003","host004"],
            "vars": {
                "var2": 500
            },
            "children":[]
        }

    }

If any of the elements of a group are empty they may be omitted from the output.

When called with the argument ``--host <hostname>`` (where <hostname> is a host from above), the script must print either an empty JSON hash/dictionary, or a hash/dictionary of variables to make available to templates and playbooks. For example::


    {
        "VAR001": "VALUE",
        "VAR002": "VALUE",
    }

Printing variables is optional. If the script does not do this, it should print an empty hash or dictionary.

.. _inventory_script_tuning:

Tuning the External Inventory Script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 1.3

The stock inventory script system detailed above works for all versions of Ansible,
but calling ``--host`` for every host can be rather inefficient,
especially if it involves API calls to a remote subsystem.

To avoid this inefficiency, if the inventory script returns a top level element called "_meta",
it is possible to return all of the host variables in one script execution.
When this meta element contains a value for "hostvars",
the inventory script will not be invoked with ``--host`` for each host.
This results in a significant performance increase for large numbers of hosts.

The data to be added to the top level JSON dictionary looks like this::

    {

        # results of inventory script as above go here
        # ...

        "_meta": {
            "hostvars": {
                "host001": {
                    "var001" : "value"
                },
                "host002": {
                    "var002": "value"
                }
            }
        }
    }

To satisfy the requirements of using ``_meta``, to prevent ansible from calling your inventory with ``--host`` you must at least populate ``_meta`` with an empty ``hostvars`` dictionary.
For example::

    {

        # results of inventory script as above go here
        # ...

        "_meta": {
            "hostvars": {}
        }
    }


.. _replacing_inventory_ini_with_dynamic_provider:

If you intend to replace an existing static inventory file with an inventory script,
it must return a JSON object which contains an 'all' group that includes every
host in the inventory as a member and every group in the inventory as a child.
It should also include an 'ungrouped' group which contains all hosts which are not members of any other group.
A skeleton example of this JSON object is::

	{
		"_meta": {
			"hostvars": {}
		},
		"all": {
			"children": [
				"ungrouped"
			]
		},
		"ungrouped": {}
	}

An easy way to see how this should look is using :ref:`ansible-inventory`, which also supports ``--list`` and ``--host`` parameters like an inventory script would.

.. seealso::

   :doc:`developing_api`
       Python API to Playbooks and Ad Hoc Task Execution
   :doc:`developing_modules`
       How to develop modules
   :doc:`developing_plugins`
       How to develop plugins
   `Ansible Tower <https://ansible.com/ansible-tower>`_
       REST API endpoint and GUI for Ansible, syncs with dynamic inventory
   `Development Mailing List <http://groups.google.com/group/ansible-devel>`_
       Mailing list for development topics
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
