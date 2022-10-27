.. _using_collections:
.. _collections_using_playbook:

Using collections in a playbook
===============================

Once installed, you can reference a collection content by its fully qualified collection name (FQCN):

.. code-block:: yaml

     - hosts: all
       tasks:
         - my_namespace.my_collection.mymodule:
             option1: value

This works for roles or any type of plugin distributed within the collection:

.. code-block:: yaml

     - hosts: all
       tasks:
         - import_role:
             name: my_namespace.my_collection.role1

         - my_namespace.mycollection.mymodule:
             option1: value

         - debug:
             msg: '{{ lookup("my_namespace.my_collection.lookup1", 'param1')| my_namespace.my_collection.filter1 }}'

Simplifying module names with the ``collections`` keyword
---------------------------------------------------------

The ``collections`` keyword lets you define a list of collections that your role or playbook should search for unqualified module and action names. So you can use the ``collections`` keyword, then simply refer to modules and action plugins by their short-form names throughout that role or playbook.

.. warning::
   If your playbook uses both the ``collections`` keyword and one or more roles, the roles do not inherit the collections set by the playbook. This is one of the reasons we recommend you always use FQCN. See below for roles details.

Using ``collections`` in roles
------------------------------

Within a role, you can control which collections Ansible searches for the tasks inside the role using the ``collections`` keyword in the role's ``meta/main.yml``. Ansible will use the collections list defined inside the role even if the playbook that calls the role defines different collections in a separate ``collections`` keyword entry. Roles defined inside a collection always implicitly search their own collection first, so you don't need to use the ``collections`` keyword to access modules, actions, or other roles contained in the same collection.

.. code-block:: yaml

   # myrole/meta/main.yml
   collections:
     - my_namespace.first_collection
     - my_namespace.second_collection
     - other_namespace.other_collection

Using ``collections`` in playbooks
----------------------------------

In a playbook, you can control the collections Ansible searches for modules and action plugins to execute. However, any roles you call in your playbook define their own collections search order; they do not inherit the calling playbook's settings. This is true even if the role does not define its own ``collections`` keyword.

.. code-block:: yaml

     - hosts: all
       collections:
         - my_namespace.my_collection

       tasks:
         - import_role:
             name: role1

         - mymodule:
             option1: value

         - debug:
             msg: '{{ lookup("my_namespace.my_collection.lookup1", "param1")| my_namespace.my_collection.filter1 }}'

The ``collections`` keyword merely creates an ordered 'search path' for non-namespaced plugin and role references. It does not install content or otherwise change Ansible's behavior around the loading of plugins or roles. Note that an FQCN is still required for non-action or module plugins (for example, lookups, filters, tests).

When using the ``collections`` keyword, it is not necessary to add in ``ansible.builtin`` as part of the search list. When left omitted, the following content is available by default:

1. Standard ansible modules and plugins available through ``ansible-base``/``ansible-core``

2. Support for older 3rd party plugin paths

In general, it is preferable to use a module or plugin's FQCN over the ``collections`` keyword and the short name for all content in ``ansible-core``

Using a playbook from a collection
----------------------------------

.. versionadded:: 2.11

You can also distribute playbooks in your collection and invoke them using the same semantics you use for plugins:

.. code-block:: shell

    ansible-playbook my_namespace.my_collection.playbook1 -i ./myinventory

From inside a playbook:

.. code-block:: yaml

    - import_playbook: my_namespace.my_collection.playbookX


A few recommendations when creating such playbooks, ``hosts:`` should be generic or at least have a variable input.

.. code-block:: yaml

 - hosts: all  # Use --limit or customized inventory to restrict hosts targeted

 - hosts: localhost  # For things you want to restrict to the controller

 - hosts: '{{target|default("webservers")}}'  # Assumes inventory provides a 'webservers' group, but can also use ``-e 'target=host1,host2'``


This will have an implied entry in the ``collections:`` keyword of ``my_namespace.my_collection`` just as with roles.

.. note::
    * Playbook names, like other collection resources, have a restricted set of valid characters.
      Names can contain only lowercase alphanumeric characters, plus _ and must start with an alpha character. The dash ``-`` character is not valid for playbook names in collections.
      Playbooks whose names contain invalid characters are not addressable: this is a limitation of the Python importer that is used to load collection resources.

    * Playbooks in collections do not support 'adjacent' plugins, all plugins must be in the collection specific directories.
