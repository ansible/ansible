Developing Dynamic Inventory Sources
====================================

.. contents:: Topics
   :local:

As described in :doc:`../intro_dynamic_inventory`, Ansible can pull inventory information from dynamic sources, including cloud sources.

How do we write a new one?

Simple!  We just create a script or program that can print JSON in the right format when fed the proper arguments.
You can do this in any language.

.. _inventory_script_conventions:

Script Conventions
``````````````````

When the external node script is called with the single argument ``--list``, the script must output a JSON encoded hash/dictionary of all the groups to be managed to stdout. Each group's value should be either a hash/dictionary containing a list of each host/IP, potential child groups, and potential group variables, or simply a list of host/IP addresses, like so::

    {
        "databases": {
            "hosts": ["host1.example.com", "host2.example.com"],
            "vars": {
                "a": true
            }
        },
        "webservers": ["host2.example.com", "host3.example.com"],
        "atlanta": {
            "hosts": ["host1.example.com", "host4.example.com", "host5.example.com"],
            "vars": {
                "b": false
            },
            "children": ["marietta", "5points"]
        },
        "marietta": ["host6.example.com"],
        "5points": ["host7.example.com"]
    }

.. versionadded:: 1.0

Before version 1.0, each group could only have a list of hostnames/IP addresses, like the webservers, marietta, and 5points groups above.

When called with the arguments ``--host <hostname>`` (where <hostname> is a host from above), the script must print either an empty JSON
hash/dictionary, or a hash/dictionary of variables to make available to templates and playbooks.  Printing variables is optional,
if the script does not wish to do this, printing an empty hash/dictionary is the way to go::

    {
        "favcolor": "red",
        "ntpserver": "wolf.example.com",
        "monitoring": "pack.example.com"
    }

.. _inventory_script_tuning:

Tuning the External Inventory Script
````````````````````````````````````

.. versionadded:: 1.3

The stock inventory script system detailed above works for all versions of Ansible, but calling
``--host`` for every host can be rather expensive,  especially if it involves expensive API calls to
a remote subsystem.  In Ansible
1.3 or later, if the inventory script returns a top level element called "_meta", it is possible
to return all of the host variables in one inventory script call.  When this meta element contains
a value for "hostvars", the inventory script will not be invoked with ``--host`` for each host.  This
results in a significant performance increase for large numbers of hosts, and also makes client
side caching easier to implement for the inventory script.

The data to be added to the top level JSON dictionary looks like this::

    {

        # results of inventory script as above go here
        # ...

        "_meta": {
            "hostvars": {
                "moocow.example.com": {
                    "asdf" : 1234
                },
                "llama.example.com": {
                    "asdf": 5678
                }
            }
        }
    }

To satisfy the requirements of using ``_meta``, to prevent ansible from calling your inventory with ``--host`` you must at least populate ``_meta`` with an empty ``hostvars`` dictionary, such as::

    {

        # results of inventory script as above go here
        # ...

        "_meta": {
            "hostvars": {}
        }
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
