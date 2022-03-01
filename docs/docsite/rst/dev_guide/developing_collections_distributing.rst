.. _distributing_collections:

************************
Distributing collections
************************

A collection is a distribution format for Ansible content. A typical collection contains modules and other plugins that address a set of related use cases. For example, a collection might automate administering a particular database. A collection can also contain roles and playbooks.

To distribute your collection and allow others to use it, you can publish your collection on one or more distribution servers. Distribution servers include:

================================= ========================================================
Distribution server               Collections accepted
================================= ========================================================
Ansible Galaxy                    All collections
Red Hat Automation Hub            Only collections certified by Red Hat
Privately hosted Automation Hub   Collections authorized by the owners
================================= ========================================================

Distributing collections involves four major steps:

#. Initial configuration of your distribution server or servers
#. Building your collection tarball
#. Preparing to publish your collection
#. Publishing your collection

.. contents::
   :local:
   :depth: 2

.. _config_distribution_server:

Initial configuration of your distribution server or servers
============================================================

Configure a connection to one or more distribution servers so you can publish collections there. You only need to configure each distribution server once. You must repeat the other steps (building your collection tarball, preparing to publish, and publishing your collection) every time you publish a new collection or a new version of an existing collection.

1. Create a namespace on each distribution server you want to use.
2. Get an API token for each distribution server you want to use.
3. Specify the API token for each distribution server you want to use.

.. _get_namespace:

Creating a namespace
--------------------

You must upload your collection into a namespace on each distribution server. If you have a login for Ansible Galaxy, your Ansible Galaxy username is usually also an Ansible Galaxy namespace.

.. warning::

   Namespaces on Ansible Galaxy cannot include hyphens. If you have a login for Ansible Galaxy that includes a hyphen, your Galaxy username is not also a Galaxy namespace. For example, ``awesome-user`` is a valid username for Ansible Galaxy, but it is not a valid namespace.

You can create additional namespaces on Ansible Galaxy if you choose. For Red Hat Automation Hub and private Automation Hub you must create a namespace before you can upload your collection. To create a namespace:

* To create a namespace on Galaxy, see `Galaxy namespaces <https://galaxy.ansible.com/docs/contributing/namespaces.html#galaxy-namespaces>`_ on the Galaxy docsite for details.
* To create a namespace on Red Hat Automation Hub, see the `Ansible Certified Content FAQ <https://access.redhat.com/articles/4916901>`_.

Specify the namespace in the :file:`galaxy.yml` file for each collection. For more information on the :file:`galaxy.yml` file, see :ref:`collections_galaxy_meta`.

.. _galaxy_get_token:

Getting your API token
----------------------

An API token authenticates your connection to each distribution server. You need a separate API token for each distribution server. Use the correct API token to connect to each distribution server securely and protect your content.

To get your API token:

* To get an API token for Galaxy, go to the `Galaxy profile preferences <https://galaxy.ansible.com/me/preferences>`_ page and click :guilabel:`API Key`.
* To get an API token for Automation Hub, go to `the token page <https://cloud.redhat.com/ansible/automation-hub/token/>`_ and click :guilabel:`Load token`.

.. _galaxy_specify_token:

Specifying your API token and distribution server
-------------------------------------------------

Each time you publish a collection, you must specify the API token and the distribution server to create a secure connection. You have two options for specifying the token and distribution server:

* You can configure the token in configuration, as part of a ``galaxy_server_list`` entry in your :file:`ansible.cfg` file. Using configuration is the most secure option.
* You can pass the token at the command line as an argument to the ``ansible-galaxy`` command. If you pass the token at the command line, you can specify the server at the command line, by using the default setting, or by setting the server in configuration. Passing the token at the command line is insecure, because typing secrets at the command line may expose them to other users on the system.

.. _galaxy_token_ansible_cfg:

Specifying the token and distribution server in configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Ansible Galaxy is configured as the only distribution server. You can add other distribution servers and specify your API token or tokens in configuration by editing the ``galaxy_server_list`` section of your :file:`ansible.cfg` file. This is the most secure way to manage authentication for distribution servers. Specify a URL and token for each server. For example:

.. code-block:: ini

   [galaxy]
   server_list = release_galaxy

   [galaxy_server.release_galaxy]
   url=https://galaxy.ansible.com/
   token=abcdefghijklmnopqrtuvwxyz

You cannot use ``apt-key`` with any servers defined in your :ref:`galaxy_server_list <galaxy_server_config>`. See :ref:`galaxy_server_config` for complete details.

.. _galaxy_use_token_arg:

Specifying the token at the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can specify the API token at the command line using the ``--token`` argument of the :ref:`ansible-galaxy` command. There are three ways to specify the distribution server when passing the token at the command line:

* using the ``--server`` argument of the :ref:`ansible-galaxy` command
* relying on the default (https://galaxy.ansible.com)
* setting a server in configuration by creating a :ref:`GALAXY_SERVER` setting in your :file:`ansible.cfg` file

For example:

.. code-block:: bash

     ansible-galaxy collection publish path/to/my_namespace-my_collection-1.0.0.tar.gz --token abcdefghijklmnopqrtuvwxyz

.. warning::

   Using the ``--token`` argument is insecure. Passing secrets at the command line may expose them to others on the system.

.. _building_collections:

Building your collection tarball
================================

After configuring one or more distribution servers, build a collection tarball. The collection tarball is the published artifact, the object that you upload and other users download to install your collection. To build a collection tarball:

#. Review the version number in your :file:`galaxy.yml` file. Each time you publish your collection, it must have a new version number. You cannot make changes to existing versions of your collection on a distribution server. If you try to upload the same collection version more than once, the distribution server returns the error ``Code: conflict.collection_exists``. Collections follow semantic versioning rules. For more information on versions, see :ref:`collection_versions`. For more information on the :file:`galaxy.yml` file, see :ref:`collections_galaxy_meta`.
#. Run ``ansible-galaxy collection build`` from inside the top-level directory of the collection. For example:

.. code-block:: bash

    collection_dir#> ansible-galaxy collection build

This command builds a tarball of the collection in the current directory, which you can upload to your selected distribution server::

    my_collection/
    ├── galaxy.yml
    ├── ...
    ├── my_namespace-my_collection-1.0.0.tar.gz
    └── ...

.. note::
   * To reduce the size of collections, certain files and folders are excluded from the collection tarball by default. See :ref:`ignoring_files_and_folders_collections` if your collection directory contains other files you want to exclude.
   * The current Galaxy maximum tarball size is 2 MB.

You can upload your tarball to one or more distribution servers. You can also distribute your collection locally by copying the tarball to install your collection directly on target systems.

.. _ignoring_files_and_folders_collections:

Ignoring files and folders
--------------------------

By default the build step includes all the files in the collection directory in the tarball except for the following:

* ``galaxy.yml``
* ``*.pyc``
* ``*.retry``
* ``tests/output``
* previously built tarballs in the root directory
* various version control directories such as ``.git/``

To exclude other files and folders from your collection tarball, set a list of file glob-like patterns in the ``build_ignore`` key in the collection's ``galaxy.yml`` file. These patterns use the following special characters for wildcard matching:

* ``*``: Matches everything
* ``?``: Matches any single character
* ``[seq]``: Matches any character in sequence
* ``[!seq]``:Matches any character not in sequence

For example, to exclude the :file:`sensitive` folder within the ``playbooks`` folder as well any ``.tar.gz`` archives, set the following in your ``galaxy.yml`` file:

.. code-block:: yaml

     build_ignore:
     - playbooks/sensitive
     - '*.tar.gz'

For more information on the :file:`galaxy.yml` file, see :ref:`collections_galaxy_meta`.

.. note::
     The ``build_ignore`` feature is only supported with ``ansible-galaxy collection build`` in Ansible 2.10 or newer.

.. _trying_collection_locally:

Preparing to publish your collection
====================================

Each time you publish your collection, you must create a :ref:`new version <collection_versions>` on the distribution server. After you publish a version of a collection, you cannot delete or modify that version. To avoid unnecessary extra versions, check your collection for bugs, typos, and other issues locally before publishing:

#. Install the collection locally.
#. Review the locally installed collection before publishing a new version.

Installing your collection locally
----------------------------------

You have two options for installing your collection locally:

  * Install your collection locally from the tarball.
  * Install your collection locally from your git repository.

Installing your collection locally from the tarball
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install your collection locally from the tarball, run ``ansible-galaxy collection install`` and specify the collection tarball. You can optionally specify a location using the ``-p`` flag. For example:

.. code-block:: bash

   collection_dir#> ansible-galaxy collection install my_namespace-my_collection-1.0.0.tar.gz -p ./collections

Install the tarball into a directory configured in :ref:`COLLECTIONS_PATHS` so Ansible can easily find and load the collection. If you do not specify a path value, ``ansible-galaxy collection install`` installs the collection in the first path defined in :ref:`COLLECTIONS_PATHS`.

.. _collections_scm_install:

Installing your collection locally from a git repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install your collection locally from a git repository, specify the repository and the branch you want to install:

.. code-block:: bash

   collection_dir#> ansible-galaxy collection install git+https://github.com/org/repo.git,devel

.. include:: ../shared_snippets/installing_collections_git_repo.txt

Reviewing your collection
-------------------------

Review the collection:

* Run a playbook that uses the modules and plugins in your collection. Verify that new features and functionality work as expected. For examples and more details see :ref:`Using collections <using_collections>`. 
* Check the documentation for typos.
* Check that the version number of your tarball is higher than the latest published version on the distribution server or servers.
* If you find any issues, fix them and rebuild the collection tarball.

.. _collection_versions:

Understanding collection versioning
-----------------------------------

The only way to change a collection is to release a new version. The latest version of a collection (by highest version number) is the version displayed everywhere in Galaxy and Automation Hub. Users can still download older versions.

Follow semantic versioning when setting the version for your collection. In summary:

* Increment the major version number, ``x`` of ``x.y.z``, for an incompatible API change.
* Increment the minor version number, ``y`` of ``x.y.z``, for new functionality in a backwards compatible manner (for example new modules/plugins, parameters, return values).
* Increment the patch version number, ``z`` of ``x.y.z``, for backwards compatible bug fixes.

Read the official `Semantic Versioning <https://semver.org/>`_ documentation for details and examples.

.. _publish_collection:

Publishing your collection
==========================

The last step in distributing your collection is publishing the tarball to Ansible Galaxy, Red Hat Automation Hub, or a privately hosted Automation Hub instance. You can publish your collection in two ways:

* from the command line using the ``ansible-galaxy collection publish`` command
* from the website of the distribution server (Galaxy, Automation Hub) itself

.. _upload_collection_ansible_galaxy:
.. _publish_collection_galaxy_cmd:

Publishing a collection from the command line
---------------------------------------------

To upload the collection tarball from the command line using ``ansible-galaxy``:

.. code-block:: bash

     ansible-galaxy collection publish path/to/my_namespace-my_collection-1.0.0.tar.gz

.. note::

	This ansible-galaxy command assumes you have retrieved and stored your API token in configuration. See :ref:`galaxy_specify_token` for details.

The ``ansible-galaxy collection publish`` command triggers an import process, just as if you uploaded the collection through the Galaxy website. The command waits until the import process completes before reporting the status back. If you want to continue without waiting for the import result, use the ``--no-wait`` argument and manually look at the import progress in your `My Imports <https://galaxy.ansible.com/my-imports/>`_ page.

.. _upload_collection_galaxy:

Publishing a collection from the website
----------------------------------------

To publish your collection directly on the Galaxy website:

#. Go to the `My Content <https://galaxy.ansible.com/my-content/namespaces>`_ page, and click the **Add Content** button on one of your namespaces.
#. From the **Add Content** dialogue, click **Upload New Collection**, and select the collection archive file from your local filesystem.

When you upload a collection, Ansible always uploads the tarball to the namespace specified in the collection metadata in the ``galaxy.yml`` file, no matter which namespace you select on the website. If you are not an owner of the namespace specified in your collection metadata, the upload request fails.

After Galaxy uploads and accepts a collection, the website shows you the **My Imports** page. This page shows import process information. You can review any errors or warnings about your upload there.

.. seealso::

   :ref:`collections`
       Learn how to install and use collections.
   :ref:`collections_galaxy_meta`
       Table of fields used in the :file:`galaxy.yml` file 
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   :ref:`communication_irc`
       How to join Ansible chat channels
