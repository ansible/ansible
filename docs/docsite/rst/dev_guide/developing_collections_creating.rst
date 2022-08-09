.. _creating_collections:

********************
Creating collections
********************

To create a collection:

#. Create a :ref:`collection skeleton<creating_collections_skeleton>` with the ``collection init`` command.
#. Add modules and other content to the collection.
#. Build the collection into a collection artifact with :ref:`ansible-galaxy collection build<building_collections>`.
#. Publish the collection artifact to Galaxy with :ref:`ansible-galaxy collection publish<publishing_collections>`.

A user can then install your collection on their systems.

.. contents::
   :local:
   :depth: 2

.. _creating_collections_skeleton:

Creating a collection skeleton
==============================

To start a new collection, run the following command in your collections directory:

.. code-block:: bash

    ansible_collections#> ansible-galaxy collection init my_namespace.my_collection

.. note::

	Both the namespace and collection names use the same strict set of requirements. See `Galaxy namespaces <https://galaxy.ansible.com/docs/contributing/namespaces.html#galaxy-namespaces>`_ on the Galaxy docsite for those requirements.

It will create the structure ``[my_namespace]/[my_collection]/[collection skeleton]``.
.. hint:: If Git is used for version control, the corresponding repository should be initialized in the collection directory.
Once the skeleton exists, you can populate the directories with the content you want inside the collection. See `ansible-collections <https://github.com/ansible-collections/>`_ GitHub Org to get a better idea of what you can place inside a collection.

Reference: the ``ansible-galaxy collection`` command

Currently the ``ansible-galaxy collection`` command implements the following sub commands:

* ``init``: Create a basic collection skeleton based on the default template included with Ansible or your own template.
* ``build``: Create a collection artifact that can be uploaded to Galaxy or your own repository.
* ``publish``: Publish a built collection artifact to Galaxy.
* ``install``: Install one or more collections.

To learn more about the ``ansible-galaxy`` command-line tool, see the :ref:`ansible-galaxy` man page.

.. seealso::

   :ref:`collections`
       Learn how to install and use collections.
   :ref:`collection_structure`
       Directories and files included in the collection skeleton
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   :ref:`communication_irc`
       How to join Ansible chat channels
