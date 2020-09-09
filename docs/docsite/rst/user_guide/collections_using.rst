
.. _collections:

*****************
Using collections
*****************

Collections are a distribution format for Ansible content that can include playbooks, roles, modules, and plugins. As modules move from the core Ansible repository into collections, the module documentation will move to the :ref:`collections pages <list_of_collections>`.

You can install and use collections through `Ansible Galaxy <https://galaxy.ansible.com>`_.

* For details on how to *develop* collections see :ref:`developing_collections`.
* For the current development status of Collections and FAQ see `Ansible Collections Community Guide <https://github.com/ansible-collections/overview/blob/main/README.rst>`_.

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

Installing a collection from a git repository
---------------------------------------------

.. include:: ../shared_snippets/installing_collections_git_repo.txt

.. _collection_requirements_file:

Install multiple collections with a requirements file
-----------------------------------------------------

.. include:: ../shared_snippets/installing_multiple_collections.txt

.. _collection_offline_download:

Downloading a collection for offline use
-----------------------------------------

.. include:: ../shared_snippets/download_tarball_collections.txt


.. _galaxy_server_config:

Configuring the ``ansible-galaxy`` client
------------------------------------------

.. include:: ../shared_snippets/galaxy_server_list.txt

.. _collections_downloading:

Downloading collections
=======================

To download a collection and its dependencies for an offline install, run ``ansible-galaxy collection download``. This
downloads the collections specified and their dependencies to the specified folder and creates a ``requirements.yml``
file which can be used to install those collections on a host without access to a Galaxy server. All the collections
are downloaded by default to the ``./collections`` folder.

Just like the ``install`` command, the collections are sourced based on the
:ref:`configured galaxy server config <galaxy_server_config>`. Even if a collection to download was specified by a URL
or path to a tarball, the collection will be redownloaded from the configured Galaxy server.

Collections can be specified as one or multiple collections or with a ``requirements.yml`` file just like
``ansible-galaxy collection install``.

To download a single collection and its dependencies:

.. code-block:: bash

   ansible-galaxy collection download my_namespace.my_collection

To download a single collection at a specific version:

.. code-block:: bash

   ansible-galaxy collection download my_namespace.my_collection:1.0.0

To download multiple collections either specify multiple collections as command line arguments as shown above or use a
requirements file in the format documented with :ref:`collection_requirements_file`.

.. code-block:: bash

   ansible-galaxy collection download -r requirements.yml

All the collections are downloaded by default to the ``./collections`` folder but you can use ``-p`` or
``--download-path`` to specify another path:

.. code-block:: bash

   ansible-galaxy collection download my_namespace.my_collection -p ~/offline-collections

Once you have downloaded the collections, the folder contains the collections specified, their dependencies, and a
``requirements.yml`` file. You can use this folder as is with ``ansible-galaxy collection install`` to install the
collections on a host without access to a Galaxy or Automation Hub server.

.. code-block:: bash

   # This must be run from the folder that contains the offline collections and requirements.yml file downloaded
   # by the internet-connected host
   cd ~/offline-collections
   ansible-galaxy collection install -r requirements.yml

.. _collections_listing:

Listing collections
===================

To list installed collections, run ``ansible-galaxy collection list``. This shows all of the installed collections found in the configured collections search paths. It will also show collections under development which contain a galaxy.yml file instead of a MANIFEST.json. The path where the collections are located are displayed as well as version information. If no version information is available, a ``*`` is displayed for the version number.

.. code-block:: shell

      # /home/astark/.ansible/collections/ansible_collections
      Collection                 Version
      -------------------------- -------
      cisco.aci                  0.0.5
      cisco.mso                  0.0.4
      sandwiches.ham             *
      splunk.es                  0.0.5

      # /usr/share/ansible/collections/ansible_collections
      Collection        Version
      ----------------- -------
      fortinet.fortios  1.0.6
      pureport.pureport 0.0.8
      sensu.sensu_go    1.3.0

Run with ``-vvv`` to display more detailed information.

To list a specific collection, pass a valid fully qualified collection name (FQCN) to the command ``ansible-galaxy collection list``. All instances of the collection will be listed.

.. code-block:: shell

      > ansible-galaxy collection list fortinet.fortios

      # /home/astark/.ansible/collections/ansible_collections
      Collection       Version
      ---------------- -------
      fortinet.fortios 1.0.1

      # /usr/share/ansible/collections/ansible_collections
      Collection       Version
      ---------------- -------
      fortinet.fortios 1.0.6

To search other paths for collections, use the ``-p`` option. Specify multiple search paths by separating them with a ``:``. The list of paths specified on the command line will be added to the beginning of the configured collections search paths.

.. code-block:: shell

      > ansible-galaxy collection list -p '/opt/ansible/collections:/etc/ansible/collections'

      # /opt/ansible/collections/ansible_collections
      Collection      Version
      --------------- -------
      sandwiches.club 1.7.2

      # /etc/ansible/collections/ansible_collections
      Collection     Version
      -------------- -------
      sandwiches.pbj 1.2.0

      # /home/astark/.ansible/collections/ansible_collections
      Collection                 Version
      -------------------------- -------
      cisco.aci                  0.0.5
      cisco.mso                  0.0.4
      fortinet.fortios           1.0.1
      sandwiches.ham             *
      splunk.es                  0.0.5

      # /usr/share/ansible/collections/ansible_collections
      Collection        Version
      ----------------- -------
      fortinet.fortios  1.0.6
      pureport.pureport 0.0.8
      sensu.sensu_go    1.3.0


.. _using_collections:

Verifying collections
=====================

Verifying collections with ``ansible-galaxy``
---------------------------------------------

Once installed, you can verify that the content of the installed collection matches the content of the collection on the server. This feature expects that the collection is installed in one of the configured collection paths and that the collection exists on one of the configured galaxy servers.

.. code-block:: bash

   ansible-galaxy collection verify my_namespace.my_collection

The output of the ``ansible-galaxy collection verify`` command is quiet if it is successful. If a collection has been modified, the altered files are listed under the collection name.

.. code-block:: bash

    ansible-galaxy collection verify my_namespace.my_collection
    Collection my_namespace.my_collection contains modified content in the following files:
    my_namespace.my_collection
        plugins/inventory/my_inventory.py
        plugins/modules/my_module.py

You can use the ``-vvv`` flag to display additional information, such as the version and path of the installed collection, the URL of the remote collection used for validation, and successful verification output.

.. code-block:: bash

   ansible-galaxy collection verify my_namespace.my_collection -vvv
   ...
   Verifying 'my_namespace.my_collection:1.0.0'.
   Installed collection found at '/path/to/ansible_collections/my_namespace/my_collection/'
   Remote collection found at 'https://galaxy.ansible.com/download/my_namespace-my_collection-1.0.0.tar.gz'
   Successfully verified that checksums for 'my_namespace.my_collection:1.0.0' match the remote collection

If you have a pre-release or non-latest version of a collection installed you should include the specific version to verify. If the version is omitted, the installed collection is verified against the latest version available on the server.

.. code-block:: bash

   ansible-galaxy collection verify my_namespace.my_collection:1.0.0

In addition to the ``namespace.collection_name:version`` format, you can provide the collections to verify in a ``requirements.yml`` file. Dependencies listed in ``requirements.yml`` are not included in the verify process and should be verified separately.

.. code-block:: bash

   ansible-galaxy collection verify -r requirements.yml

Verifying against ``tar.gz`` files is not supported. If your ``requirements.yml`` contains paths to tar files or URLs for installation, you can use the ``--ignore-errors`` flag to ensure that all collections using the ``namespace.name`` format in the file are processed.

.. _collections_using_playbook:

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

Simplifying module names with the ``collections`` keyword
=========================================================

The ``collections`` keyword lets you define a list of collections that your role or playbook should search for unqualified module and action names. So you can use the ``collections`` keyword, then simply refer to modules and action plugins by their short-form names throughout that role or playbook.

.. warning::
   If your playbook uses both the ``collections`` keyword and one or more roles, the roles do not inherit the collections set by the playbook. See below for details.

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
             msg: '{{ lookup("my_namespace.my_collection.lookup1", 'param1')| my_namespace.my_collection.filter1 }}'

The ``collections`` keyword merely creates an ordered 'search path' for non-namespaced plugin and role references. It does not install content or otherwise change Ansible's behavior around the loading of plugins or roles. Note that an FQCN is still required for non-action or module plugins (for example, lookups, filters, tests).

.. seealso::

  :ref:`developing_collections`
      Develop or modify a collection.
  :ref:`collections_galaxy_meta`
       Understand the collections metadata structure.
  `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
  `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
