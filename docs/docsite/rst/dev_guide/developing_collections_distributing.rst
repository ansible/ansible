.. _distributing_collections:

************************
Distributing collections
************************

You can distribute your collections by publishing them on a distribution server. Distribution servers include Ansible Galaxy, Red Hat Automation Hub, and privately hosted Automation Hub instances. You can publish any collection to Ansible Galaxy and/or to a privately hosted Automation Hub instance. If your collection is certified by Red Hat, you can publish it to the Red Hat Automation Hub.

Distributing collections involves three major steps:
#. Configuring your distribution server(s)
#. Building your collection artifact
#. Publishing your collection

.. contents::
   :local:
   :depth: 2

Configuring your distribution server or servers
================================================

1. Get a namespace on each distribution server you want to use (Galaxy, private Automation Hub, Red Hat Automation Hub).
2. Get an API token for each distribution server you want to use.
3. Specify the API token for each distribution server you want to use.

Getting a namespace
-------------------

You need a namespace on Galaxy and/or Automation Hub to upload your collection. To get a namespace:

* For Galaxy, see `Galaxy namespaces <https://galaxy.ansible.com/docs/contributing/namespaces.html#galaxy-namespaces>`_ on the Galaxy docsite for details.
* For Automation Hub, see the `Ansible Certified Content FAQ <https://access.redhat.com/articles/4916901>`_.

.. _galaxy_get_token:

Getting your API token
----------------------

You need an API token for Galaxy and/or Automation Hub to upload your collection. Use the API token(s) to authenticate your connection to the distribution server(s) and protect your content.

To get your API token:

* For Galaxy, go to the `Galaxy profile preferences <https://galaxy.ansible.com/me/preferences>`_ page and click :guilabel:`API Key`.
* For Automation Hub, go to `the token page <https://cloud.redhat.com/ansible/automation-hub/token/>`_ and click :guilabel:`Load token`.

Specifying your API token
-------------------------

Once you have retrieved your API token, you can specify the correct token for each distribution server in two ways:

* Pass the token to  the ``ansible-galaxy`` command using the ``--token``.
* Configure the token within a Galaxy server list in your :file:`ansible.cfg` file.

Specifying your API token with the ``--token`` argument
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can use the ``--token`` argument with the ``ansible-galaxy`` command (in conjunction with the ``--server`` argument or :ref:`GALAXY_SERVER` setting in your :file:`ansible.cfg` file). You cannot use ``apt-key`` with any servers defined in your :ref:`Galaxy server list <galaxy_server_config>`.

.. code-block:: text

    ansible-galaxy collection publish ./geerlingguy-collection-1.2.3.tar.gz --token=<key goes here>

Specifying your API token with a Galaxy server list
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can configure one or more distribution servers for Galaxy in your :file:`ansible.cfg` file under the ``galaxy_server_list`` section. For each server, you also configure the token.


.. code-block:: ini

   [galaxy]
   server_list = release_galaxy

   [galaxy_server.release_galaxy]
   url=https://galaxy.ansible.com/
   token=my_token

See :ref:`galaxy_server_config` for complete details.

.. _building_collections:

Building a collection tarball
=============================

Once you have configured one or more distribution servers, you must build a collection tarball. To build a collection, run ``ansible-galaxy collection build`` from inside the root directory of the collection:

.. code-block:: bash

    collection_dir#> ansible-galaxy collection build

This creates a tarball of the built collection in the current directory which can be uploaded to your distribution server::

    my_collection/
    ├── galaxy.yml
    ├── ...
    ├── my_namespace-my_collection-1.0.0.tar.gz
    └── ...

.. note::
   * Certain files and folders are excluded when building the collection artifact. See :ref:`ignoring_files_and_folders_collections`  to exclude other files you would not want to distribute.
   * If you used the now-deprecated ``Mazer`` tool for any of your collections, delete any and all files it added to your :file:`releases/` directory before you build your collection with ``ansible-galaxy``.
   * The current Galaxy maximum tarball size is 2 MB.

This tarball is mainly intended to upload to Galaxy as a distribution method, but you can use it directly to install the collection on target systems.

.. _ignoring_files_and_folders_collections:

Ignoring files and folders
--------------------------

By default the build step will include all the files in the collection directory in the final build artifact except for the following:

* ``galaxy.yml``
* ``*.pyc``
* ``*.retry``
* ``tests/output``
* previously built artifacts in the root directory
* various version control directories like ``.git/``

To exclude other files and folders when building the collection, you can set a list of file glob-like patterns in the
``build_ignore`` key in the collection's ``galaxy.yml`` file. These patterns use the following special characters for
wildcard matching:

* ``*``: Matches everything
* ``?``: Matches any single character
* ``[seq]``: Matches and character in seq
* ``[!seq]``:Matches any character not in seq

For example, if you wanted to exclude the :file:`sensitive` folder within the ``playbooks`` folder as well any ``.tar.gz`` archives you
can set the following in your ``galaxy.yml`` file:

.. code-block:: yaml

     build_ignore:
     - playbooks/sensitive
     - '*.tar.gz'

.. note::
     This feature is only supported when running ``ansible-galaxy collection build`` with Ansible 2.10 or newer.

.. _collection_versions:

Collection versions
===================

Each time you publish your collection, you create a new version. Once you publish a version of a collection, you cannot delete or modify that version. Ensure that everything looks okay before publishing. The only way to change a collection is to release a new version. The latest version of a collection (by highest version number) will be the version displayed everywhere in Galaxy or Automation Hub; however, users will still be able to download older versions.

Collection versions use `Semantic Versioning <https://semver.org/>`_ for version numbers. Please read the official documentation for details and examples. In summary:

* Increment major (for example: x in `x.y.z`) version number for an incompatible API change.
* Increment minor (for example: y in `x.y.z`) version number for new functionality in a backwards compatible manner (for example new modules/plugins, parameters, return values).
* Increment patch (for example: z in `x.y.z`) version number for backwards compatible bug fixes.


.. _trying_collection_locally:

Trying collections locally
==========================

Before you publish your collection, test it out locally. Every time you publish a tarball, you create a :ref:`new version <collection_versions>` of your collection. Testing the collection locally gives you confidence that the new version will contain the functionality you want without unexpected behavior.

Trying your collection from the tarball
---------------------------------------

You can try your collection locally by installing it from the tarball. The following will enable an adjacent playbook to access the collection:

.. code-block:: bash

   ansible-galaxy collection install my_namespace-my_collection-1.0.0.tar.gz -p ./collections


You should use one of the values configured in :ref:`COLLECTIONS_PATHS` for your path. This is also where Ansible itself will
expect to find collections when attempting to use them. If you don't specify a path value, ``ansible-galaxy collection install``
installs the collection in the first path defined in :ref:`COLLECTIONS_PATHS`, which by default is ``~/.ansible/collections``.

If you want to use a collection directly out of a checked out git repository, see :ref:`hacking_collections`.

Next, try using the local collection inside a playbook. For examples and more details see :ref:`Using collections <using_collections>`

.. _collections_scm_install:

Trying your collection from a git repository
--------------------------------------------

You can also test a version of your collection in development by installing it from a git repository.

.. code-block:: bash

   ansible-galaxy collection install git+https://github.com/org/repo.git,devel

.. include:: ../shared_snippets/installing_collections_git_repo.txt

Publishing a collection
=======================

Once you have a namespace and an API token for each distribution server you want to use, and you have created and tested a collection tarball, you can distribute your collection by publishing the tarball to Ansible Galaxy, Red Hat Automation Hub, or a privately hosted Automation Hub instance. You can use either the ``ansible-galaxy collection publish`` command or the distribution server (Galaxy, Automation Hub) itself.

Each time you add features or make changes to your collection, you must create a new collection artifact and publish a new version of the collection. For details on versioning, see :ref:`collection_versions`.

.. _upload_collection_ansible_galaxy:

Publish a collection using ``ansible-galaxy``
---------------------------------------------

.. note::
  By default, ``ansible-galaxy`` uses https://galaxy.ansible.com as the Galaxy server (as listed in the :file:`ansible.cfg` file under :ref:`galaxy_server`). If you are only publishing your collection to Ansible Galaxy, you do not need any further configuration. If you are using Red Hat Automation Hub or any other Galaxy server, see :ref:`Configuring the ansible-galaxy client <galaxy_server_config>`.

To upload the collection artifact with the ``ansible-galaxy`` command:

.. code-block:: bash

     ansible-galaxy collection publish path/to/my_namespace-my_collection-1.0.0.tar.gz

.. note::

	The above command assumes you have retrieved and stored your API token as part of a Galaxy server list. See :ref:`galaxy_get_token` for details.

The ``ansible-galaxy collection publish`` command triggers an import process, just as if you uploaded the collection through the Galaxy website. The command waits until the import process completes before reporting the status back. If you want to continue without waiting for the import result, use the ``--no-wait`` argument and manually look at the import progress in your `My Imports <https://galaxy.ansible.com/my-imports/>`_ page.


.. _upload_collection_galaxy:

Publishing a collection using the Galaxy website
------------------------------------------------

To publish your collection directly on the Galaxy website:

#. Go to the `My Content <https://galaxy.ansible.com/my-content/namespaces>`_ page, and click the **Add Content** button on one of your namespaces.
#. From the **Add Content** dialogue, click **Upload New Collection**, and select the collection archive file from your local filesystem.

When you upload a collection, it always uploads to the namespace specified in the collection metadata in the ``galaxy.yml`` file, no matter which namespace you select on the website. If you are not an owner of the namespace specified in your collection metadata, the upload request will fail.

Once Galaxy uploads and accepts a collection, you will be redirected to the **My Imports** page, which displays output from the import process, including any errors or warnings about the metadata and content contained in the collection.

.. seealso::

   :ref:`collections`
       Learn how to install and use collections.
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
