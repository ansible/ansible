
.. _collections:

*****************
Using collections
*****************

Collections are a distribution format for Ansible content that can include playbooks, roles, modules, and plugins.
You can install and use collections through `Ansible Galaxy <https://galaxy.ansible.com>`_.

.. contents::
   :local:
   :depth: 2

.. _collections_installing:

Installing collections
======================


Installing collections with ``ansible-galaxy``
----------------------------------------------

.. include:: ../shared_snippets/installing_collections.txt

.. _collections_older_version:

Installing an older version of a collection
-------------------------------------------

.. include:: ../shared_snippets/installing_older_collection.txt

.. _collection_requirements_file:

Install multiple collections with a requirements file
-----------------------------------------------------

.. include:: ../shared_snippets/installing_multiple_collections.txt

.. _galaxy_server_config:

Configuring the ``ansible-galaxy`` client
------------------------------------------

.. include:: ../shared_snippets/galaxy_server_list.txt


.. _using_collections:

Using collections in a Playbook
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

The ``collections`` keyword
===========================

The ``collections`` keyword lets you define the collections you want your role or playbook to use for modules and for action plugins. Ansible searches those collections first for any modules or action plugins without an FQCN. So you can use the ``collections`` keyword, then call modules and action plugins using their short-form names later in that role or playbook.

.. warning::
   If your playbook uses both the ``collections`` keyword and one or more roles, the roles do not inherit the collections set by the playbook. See below for details.

Using ``collections`` in roles
------------------------------

In a role, you can control which collections Ansible searches for modules and action plugins globally with the ``collections`` keyword. Define the collections in the ``metadata/main.yml`` file within your role, and Ansible will use them for your role every time, in any context. Ansible will use the collections defined by a role even if the playbook that calls the role defines different collections in a separate ``collections`` keyword entry.

Using ``collections`` in playbooks
----------------------------------

In a playbook, you can control the collections Ansible searches for modules and action plugins, but only for tasks, not for roles. Some roles rely on particular collections to work properly, so Ansible does not apply ``collections`` from a playbook to any roles within that playbook. This is true even if the role does not define its own ``collections`` keyword.

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
             msg: '{{ lookup("my_namespace.my_collection.lookup1", 'param1')| my_namespace.my_collection.filter1 }}'

The ``collections`` keyword creates a 'search path' for non-namespaced plugin references. It does not import roles or anything else. Notice that you still need the FQCN for non-action or module plugins.

.. seealso::

  :ref:`developing_collections`
      Develop or modify a collection.
  :ref:`collections_galaxy_meta`
       Understand the collections metadata structure.
  `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
  `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
