
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


To install a collection with the ``ansible-galaxy collection install`` command, you must first obtain an API token (``--api-key`` in the ``ansible-galaxy`` CLI command or ``token`` in the :file:`ansible.cfg` file under the ``galaxy_server`` section). The API token is a secret token used to protect your content.

To get your API token:

* For Galaxy, go to the `Galaxy profile preferences <https://galaxy.ansible.com/me/preferences>`_ page and click :guilabel:`API token`.
* For Automation Hub, go to https://cloud.redhat.com/ansible/automation-hub/token/ and click :guilabel:`Get API token` from the version dropdown.

Storing or using your API token
-------------------------------

Once you have retrieved your API token, you have the following options on how you can store or use that token for collections:

* Pass the token to  the ``ansible-galaxy`` command using the ``--api-key``.
* Specify the token within a Galaxy server list in your :file:`ansible.cfg` file.

Using the ``api-key``
^^^^^^^^^^^^^^^^^^^^^

You can use the ``--api-key`` argument with the ``ansible-galaxy`` command (in conjunction with the ``--server`` argument or :ref:`GALAXY_SERVER` setting in your :file:`ansible.cfg` file). You cannot use ``apt-key``  with any servers defined in your :ref:`Galaxy server list <galaxy_server_config>`.

.. code-block:: bash

    ansible-galaxy collection install ./geerlingguy-collection-1.2.3.tar.gz --api-key=<key goes here>


Specify the token within a Galaxy server list
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With this option, you configure one or more servers for Galaxy in your :file:`ansible.cfg` file under the ``galaxy_server_list`` section. For each server, you also configure the token.


.. code-block:: ini

   [galaxy]
   server_list = release_galaxy

   [galaxy_server.release_galaxy]
     url=https://galaxy.ansible.com/
     token=my_token

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


To avoid a lot of typing, you can use the ``collections`` keyword added in Ansible 2.8:


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

This keyword creates a 'search path' for non namespaced plugin references. It does not import roles or anything else.
Notice that you still need the FQCN for non-action or module plugins.

.. seealso::

  :ref:`developing_collections`
      Develop or modify a collection.
  :ref:`collections_galaxy_meta`
       Understand the collections metadata structure.
  `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
  `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
