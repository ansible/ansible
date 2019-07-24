:orphan:

.. _collections:

***********
Collections
***********


Collections are a distribution format for Ansible content. They can be used to
package and distribute playbooks, roles, modules, and plugins.
You will be able to publish and use collections through `Ansible's Galaxy repository <https://galaxy.ansible.com>`_.

.. important::
    This feature is available in Ansible 2.8 as a *Technology Preview* and therefore is not fully supported. It should only be used for testing  and should not be deployed in a production environment.
    Future Galaxy or Ansible releases may introduce breaking changes.


.. contents::
   :local:

Collection structure
====================

Collections follow a simple data structure. None of the directories are required unless you have specific content that belongs in one of them. They do require a ``galaxy.yml`` file at the root level of the collection. This file contains all of the metadata that Galaxy
and other tools need in order to package, build and publish the collection.::

    collection/
    ├── docs/
    ├── galaxy.yml
    ├── plugins/
    │   ├── modules/
    │   │   └── module1.py
    │   ├── inventory/
    │   └── .../
    ├── README.md
    ├── roles/
    │   ├── role1/
    │   ├── role2/
    │   └── .../
    ├── playbooks/
    │   ├── files/
    │   ├── vars/
    │   ├── templates/
    │   └── tasks/
    └── tests/


.. note::
    * We will only accept ``.yml`` extensions for galaxy.yml.
    * A full structure can be found at `Draft collection <https://github.com/bcoca/collection>`_
    * Not all directories are currently in use. Those are placeholders for future features.


galaxy.yml
----------

A collection must have a ``galaxy.yml`` file that contains the necessary information to build a collection artifact.
See :ref:`collections_galaxy_meta` for details on how this file is structured.


docs directory
---------------

Keep general documentation for the collection here. Plugins and modules will still keep their specific documentation embedded as Python docstrings. Use the ``docs`` folder to describe how to use the roles and plugins the collection provides, role requirements, and so on. Currently we are looking at Markdown as the standard format for documentation files, but this is subject to change.

We are `updating ansible-doc <https://github.com/ansible/ansible/pull/57764>`_ to allow showing documentation for plugins inside a collection::

    ansible-doc -t lookup mycol.myname.lookup1

The ``ansible-doc`` command requires the fully qualified collection name (FQCN) to display specific plugin documentation.


plugins directory
------------------

 Add a 'per plugin type' specific subdirectory here, including ``module_utils`` which is usable not only by modules, but by any other plugin by using their FQCN. This is a way to distribute modules, lookups, filters, and so on, without having to import a role in every play.


roles directory
----------------

Collection roles are mostly the same as existing roles, but with a couple of limitations:

 - Role names are now limited to contain only lowercase alphanumeric characters, plus ``_`` and start with an alpha character.
 - Roles cannot have their own plugins any more. The plugins must live in the collection ``plugins`` directory and will be accessible to the collection roles.

The directory name of the role is used as the role name. Therefore, the directory name must comply with the
above role name rules.
The collection import into Galaxy will fail if a role name does not comply with these rules.

You can migrate 'traditional roles' into a collection but they must follow the rules above. You man need to rename roles if they don't conform. You will have to move or link any role-based plugins to the collection specific directories.

.. note::

    For roles imported into Galaxy directly from a GitHub repository, setting the ``role_name`` value in the role's
    metadata overrides the role name used by Galaxy. For collections, that value is ignored. When importing a
    collection, Galaxy uses the role directory as the name of the role and ignores the ``role_name`` metadata value.

playbooks directory
--------------------

TBD.

tests directory
----------------

TBD. Expect tests for the collection itself to reside here.


.. _creating_collections:

Creating collections
====================

This is currently a work in progress with some basic commands being integrated into the existing ``ansible-galaxy``
command line tool that is included with Ansible.

.. note::
    Any references to ``ansible-galaxy`` below will be of a 'working version' that is in development for the 2.9
    release. As such, the command and this documentation section is subject to frequent changes.

Currently the ``ansible-galaxy collection`` command implements the following sub commands:

* ``init``: Create a basic collection skeleton based on the default template included with Ansible or your own
* ``build``: Create a collection artifact that can be uploaded to Galaxy or your own repository
* ``publish``: Publish a built collection artifact to Galaxy
* ``install``: Install one or multiple collections

You can learn more about the ``ansible-galaxy`` cli tool by read the :ref:`ansible-galaxy` man page._

In the end, to get started with authoring a new collection it should be as simple as:

.. code-block:: bash

    collection_dir#> ansible-galaxy collection init namespace.collection

And then populating the directories with the content you want inside the collection. You can also have a look at
https://github.com/bcoca/collection to get a better idea of what can be placed inside a collection.


.. _building_collections:

Building collections
====================

Collections are built by running ``ansible-galaxy collection build`` from inside the collection's root directory. This
will create a tarball of the built collection in the current directory which can be uploaded to Galaxy.::

    collection/
    ├── galaxy.yml
    ├── ...
    ├── namespace_name-collection_name-1.0.12.tar.gz
    └── ...


.. note::
    Certain files and folders are excluded when building the collection artifact. This is not currently configurable
    and is a work in progress so the collection artifact may contain files you would not wish to distribute.

This tarball itself can be used to install the collection on target systems. It is mainly intended to upload to Galaxy
as a distribution method, but you should be able to use it directly.


Publishing collections
======================

Upload using ansible-galaxy
---------------------------

You can upload collection artifacts with ``ansible-galaxy``, as shown in the following example:

.. code-block:: bash

     ansible-galaxy collection publish path/to/namespace_name-collection_name-1.0.12.tar.gz --api-key=SECRET

The above command triggers an import process, just as if the collection has been uploaded through the Galaxy website.
The command will wait until the import process has completed before reporting the status back. If you wish to continue
without waiting for the import result, use the ``--no-wait`` argument and manually look at the import progress in your
`My Imports <https://galaxy.ansible.com/my-imports/>`_ page.

The API key is a secret token used by Ansible Galaxy to protect your content. You can find your API key at your
`Galaxy profile preferences <https://galaxy.ansible.com/me/preferences>`_ page.

Upload from the Galaxy website
------------------------------

Go to the `My Content <https://galaxy.ansible.com/my-content/namespaces>`_ page, and click the **Add Content** button on one of your namespaces. From
the **Add Content** dialogue, click **Upload New Collection**, and select the collection archive file from your local
filesystem.

When uploading collections it doesn't matter which namespace you select. The collection will be uploaded to the
namespace specified in the collection metadata in the ``galaxy.yml`` file. If you're not an owner of the
namespace, the upload request will fail.

Once Galaxy uploads and accepts a collection, you will be redirected to the **My Imports** page, which displays output from the
import process, including any errors or warnings about the metadata and content contained in the collection.


Collection versions
-------------------

Once you upload a version of a collection, you cannot delete or modify that version. Ensure that everything looks okay before
uploading. The only way to change a collection is to release a new version. The latest version of a collection (by highest version number)
will be the version displayed everywhere in Galaxy; however, users will still be able to download older versions.


Installing collections
======================

The recommended way to install a collection is:

.. code-block:: bash

   # Will install the collection to /path/ansible_collections/mynamespace/mycollection
   ansible-galaxy collection install mynamespace.mycollection -p /path

assuming the collection is hosted in Galaxy.

You can also use a tarball resulting from your build:

.. code-block:: bash

   # Will install the collection to ./collections/ansible_collections/mynamespace/mycollection
   ansible-galaxy install mynamespace-mycollection-0.1.0.tar.gz -p ./collections/ansible_collections

.. note::
    The install command will automatically append the path ``ansible_collections`` to the one specified unless the
    parent directory is already in a folder called ``ansible_collections``.


As a path you should use one of the values configured in :ref:`COLLECTIONS_PATHS`. This is also where Ansible itself will expect to find collections when attempting to use them.

You can also keep a collection adjacent to the current playbook, under a ``collections/ansible_collections/`` directory structure.

::

    play.yml
    ├── collections/
    │   └── ansbile_collections/
    │               └── myname/
    │                   └── mycol/<collection structure lives here>


By default ``ansible-galaxy`` will install the latest collection that is available but a version range identifier can
be used to filter the version that is installed like so:

.. code-block:: bash

   # Install the collection at 1.0.0
   ansible-galaxy collection install mynamespace.mycollection:1.0.0

   # Install the collection at 1.0.0-beta.1
   ansible-galaxy collection install mynamespace.mycollection:==1.0.0-beta.1

   # Only install the collections that are greater than or equal to 1.0.0 or less than 2.0.0
   ansible-galaxy collection install mynamespace.mycollection:>=1.0.0,<2.0.0


Multiple range identifiers can be specified and are split by ``,``. The following range identifiers can be used:

* ``*``: Any version, this is the default used when no range specified is set.
* ``!=``: Version is not equal to the one specified
* ``==``: Version must be the one specified
* ``>=``: Version is greater than or equal to the one specified
* ``>``: Version is greater than the one specified
* ``<=``: Version is less than or equal to the one specified
* ``<``: Version is less than the one specified

.. note::
    The ansible-galaxy command will ignore any pre-release versions unless the ``==`` range identifier is used to
    explicitly set to that pre-release version.


.. _collection_requirements_file:

Install requirements file
-------------------------

You can also setup a ``requirements.yml`` file to install multiple collections in one command. This file is a YAML file in the format:

.. code-block:: yaml+jinja

   ---
   collections:
   # With just the collection name
   - namespace.collection

   # With the collection name, version, and source options
   - name: namespace.collection
     version: 'version range identifiers (default: ``*``)'
     source: 'The Galaxy URL to pull the collection from (default: ``--api-server`` from cmdline)'

The ``version`` key can take in the same range identifier format documented above.


Using collections
=================

Once installed, you can reference collection content by its FQCN:

.. code-block:: yaml

     - hosts: all
       tasks:
         - myname.mycol.mymodule:
             option1: value

This works for roles or any type of plugin distributed within the collection:

.. code-block:: yaml

     - hosts: all
       tasks:
         - include_role:
             name : myname.mycol.role1
         - myname.mycol.mymodule:
             option1: value

         - debug:
             msg: '{{ lookup("myname.mycol.lookup1", 'param1')| myname.mycol.filter1 }}'


To avoid a lot of typing, you can use the ``collections`` keyword added in Ansbile 2.8:


.. code-block:: yaml

     - hosts: all
       collections:
        - myname.mycol
       tasks:
         - include_role:
             name: role1
         - mymodule:
             option1: value

         - debug:
             msg: '{{ lookup("myname.mycol.lookup1", 'param1')| myname.mycol.filter1 }}'

This keyword creates a 'search path' for non namespaced plugin references. It does not import roles or anything else.
Notice that you still need the FQCN for non-action or module plugins.
