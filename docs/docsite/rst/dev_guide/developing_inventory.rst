.. _developing_inventory:

Developing Dynamic Inventory Sources
====================================

.. contents:: Topics
   :local:

As described in :ref:`dynamic_inventory`, Ansible can pull inventory information from dynamic sources, including cloud sources. You can also create a new dynamic inventory provider by creating a script or program that can output JSON in the correct format when invoked with the proper arguments. There is no restriction on the language used for creating a dynamic inventory provider.

.. _inventory_script_conventions:

Script Conventions
``````````````````

Dynamic inventory providers must accept the ``--list`` and ``--host <hostname>`` arguments.

When the dynamic inventory provider is called with the single argument ``--list``, the script must output to stdout a JSON-encoded hash or dictionary containing all of the groups to be managed. Each group's value should be either a hash or dictionary containing a list of each host, any child groups, and potential group variables, or simply a list of hosts::

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

Printing variables is optional. If the inventory provider does not do this, it should print an empty hash or dictionary. 

.. _inventory_script_tuning:

Tuning the External Inventory Script
````````````````````````````````````

.. versionadded:: 1.3

The stock inventory script system detailed above works for all versions of
Ansible, but calling ``--host`` for every host can be rather inefficient,
especially if it involves API calls to a remote subsystem.  In Ansible 1.3 or
later, if the inventory script returns a top level element called "_meta", it
is possible to return all of the host variables in one inventory provider call.
When this meta element contains a value for "hostvars", the inventory script
will not be invoked with ``--host`` for each host.  This results in a
significant performance increase for large numbers of hosts, and also makes
client-side caching easier to implement for the inventory provider.

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

To satisfy the requirements of using ``_meta``, to prevent ansible from calling your inventory with ``--host`` you must at least populate ``_meta`` with an empty ``hostvars`` dictionary. For example::

    {

        # results of inventory script as above go here
        # ...

        "_meta": {
            "hostvars": {}
        }
    }


.. _replacing_inventory_ini_with_dynamic_provider:

If you intend to replace an existing inventory ini file with a dynamic provider,
it must return a JSON object which contains an 'all' group that includes every
host in the inventory as a member and every group in the inventory as a child.
It should also include an 'ungrouped' group which contains all hosts which are not members of
any other group.  A skeleton example of this JSON object is::

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
