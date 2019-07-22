:orphan:

.. _collections:

Collections
===========

.. contents::
   :local:
   
Collections are a distribution format for Ansible content. They can be used to
package and distribute playbooks, roles, modules, and plugins.
You will be able to publish and use collections through `Ansible's Galaxy repository <http://galaxy.ansible.com>`_.

.. important::
    This feature is available in Ansible 2.8 as a *Technology Preview* and therefore is not fully supported. It should only be used for testing  and should not be deployed in a production environment.
    Future Galaxy or Ansible releases may introduce breaking changes.


Collection Structure
====================

Collections follow a simple data stucture. None of the directories are required unless you have specific content that belongs in one of them. They do require a ``galaxy.yml`` file at the root level of the collection. This file contains all of the metadata that Galaxy
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

This file contains the information about a collection that is necessary for Ansible tools to operate.
``galaxy.yml`` has the following fields (subject to changes and expansion):

.. code-block:: yaml

    namespace: "namespace_name"
    name: "collection_name"
    version: "1.0.12"
    authors:
        - "Author1"
        - "Author2 (http://author2.example.com)"
        - "Author3 <author3@example.com>"
    dependencies:
        "other_namespace.collection1": ">=1.0.0"
        "other_namespace.collection2": ">=2.0.0,<3.0.0"
        "anderson55.my_collection": "*"    # note: "*" selects the highest version available
    license:
        - "MIT"
    tags:
        - demo
        - collection
    repository: "https://www.github.com/my_org/my_collection"


Required Fields:
    - ``namespace``: the namespace that the collection lives under. It must be a valid Python identifier,
        and may only contain alphanumeric characters and underscores. Additionally
        the ``namespace`` cannot start with underscores or numbers and cannot contain consecutive
        underscores.
    - ``name``: the collection's name. Has the same character restrictions as ``namespace``.
    - ``version``: the collection's version. To upload to Galaxy, it must be compatible with semantic versioning.


Optional Fields:
    - ``dependencies``: A dictionary where keys are collections, and values are version
      range 'specifiers <https://python-semanticversion.readthedocs.io/en/latest/#requirement-specification>`_.
      It is good practice to depend on a version range to minimize conflicts, and pin to a
      a major version to protect against breaking changes. For example: ``"user1.collection1": ">=1.2.2,<2.0.0"``
      This field allows  other collections as dependencies, not traditional roles.
    - ``description``: A short summary description of the collection.
    - ``license``: Either a single license or a list of licenses for content inside of a collection.
      Galaxy currently only accepts `SPDX <https://spdx.org/licenses/>`_ licenses.
    - ``tags``: a list of tags. These have the same character requirements as ``namespace`` and ``name``.
    - ``repository``: URL of originating SCM repository.

docs directory
---------------

Keep general documentation for the collection here. Plugins and modules will still keep their specific documentation embedded as Python docstrings. Use the ``docs`` folder to list the roles and plugins the collection provides, role requirements, user guides, and so on. Currently we are looking at Markdown as the standard format for documentation files, but this is subject to change.

We are `updating ansible-doc  <https://github.com/ansible/ansible/pull/57764>`_ to allow showing documentation for plugins inside a collection::

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

TBD. Expect tests for the collection itself, including Molecule files, to reside here.


.. _creating_collections:

Creating Collections
====================

This is currently is a work in progress. We created the `Mazer <https://galaxy.ansible.com/docs/mazer/index.html>`_ command line tool
available at the `Ansible Mazer project <https://github.com/ansible/mazer>`_. as a proof of concept for packaging,
distributing and installing collections.  You can install mazer with ``pip install mazer`` or checkout the code directly.

.. Note::
    All the documentation below that use ``mazer`` might be updated to use another tool in the future as ``mazer`` will not be updated in the future.

We are working on integrating this into Ansible itself for 2.9. Currently we have an `ansible-galaxy PR <https://github.com/ansible/ansible/pull/57106>`_ incorporating some of the commands into ``ansible-galaxy``. Currently it is not installable outside ansible, but we hope to land this into development soon so early adopters can test.

.. Note::
    Any references to ``ansbile-galaxy`` below will be of a 'working version' either in this PR or subsequently in development. As such, the command and this documentation section is subject to frequent change.

We also plan to update `Ansible Molecule <https://github.com/ansible/molecule>`_, for a full developer toolkit with integrated testing.

In the end, to get started with authoring a new collection it should be as simple as:

.. code-block:: bash

    collecion_dir#>ansible-galaxy collection init


And then populating the directories with the content you want inside the collection. For now you can optionally clone from  https://github.com//bcoca/collection to get the directory structure (or just create the directories as you need them).

.. _building_collections:

Building Collections
====================

Collections are built by running ``mazer build`` from inside the collection's root directory.
This will create a ``releases`` directory inside the collection with the build artifacts,
which can be uploaded to Galaxy.::

    collection/
    ├── ...
    ├── releases
    │   └── namespace_name-collection_name-1.0.12.tar.gz
    └── ...

.. note::
        Changing the filename of the tarball in the release directory so that it doesn't match
        the data in ``galaxy.yml`` will cause the import to fail.


This tarball itself can be used to install the collection on target systems. It is mainly intended to upload to Galaxy as a distribution method, but you should be able to use directly.

Publishing Collections
======================

We are in the process of updating Ansible Galaxy to manage collections as it manages roles until now.


Upload From the Galaxy Website
------------------------------

Go to the `My Content </my-content/namespaces>`_ page, and click the **Add Content** button on one of your namespaces. From
the **Add Content** dialogue, click **Upload New Collection**, and select the collection archive file from your local
filesystem.

When uploading collections it doesn't  matter which namespace you select. The collection will be uploaded to the
namespace specified in the collection metadata  in the ``galaxy.yml`` file. If you're not an owner of the
namespace, the upload request will fail.

Once Galaxy uploads and accepts a collection, you will be redirected to the **My Imports** page, which displays output from the
import process, including any errors or warnings about the metadata and content contained in the collection.

Upload Using Mazer
------------------

You can upload ollection artefacts with Mazer, as shown in the following example:

.. code-block:: bash

    mazer publish --api-key=SECRET path/to/namespace_name-collection_name-1.0.12.tar.gz

The above command triggers an import process, just as if the collection had been uploaded through the Galaxy website. Use the **My Imports**
page to view the output from the import process.

Your API key can be found on `the preferences page in Galaxy </me/preferences>`_.

To learn more about Mazer, see `Mazer <https://galaxy-dev.ansible.com/docs/mazer/index.html>`.


Collection Versions
-------------------

Once you upload a version of a collection, you cannot delete or modify that version. Ensure that everything looks okay before
uploading. The only way to change a collection is to release a new version. The latest version of a collection (by highest version number)
will be the version displayed everywhere in Galaxy; however, users will still be able to download older versions.


Installing Collections
======================

The recommended way to install a collection is:

.. code-block:: bash

   #> ansible-galaxy collection install  mycollection -p /path

assuming the collection is hosted in Galaxy.

You can also use a tarball resulting from your build:

.. code-block:: bash

   #> ansible-galaxy install  mynamespace.mycollection.0.1.0.tgz -p /path


As a path you should use one of the values configured in `COLLECTINS_PATHS <https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths>`_. This is also where Ansible itself will expect to find collections when attempting to use them.

You can also keep a collection adjacent to the current playbook, under a `collections/ansible_collection/` directory structure.

::

    play.yml
    ├── collections/
    │   └── ansbile_collection/
    │               └── myname/
    │                   └── mycol/< collection structure lives here>




Using Collections
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

         - debug:
             msg: '{{ lookup("lookup1", 'param1')|filter1 }}'

This keyword creates a 'search path' for non namespaced plugin references. It does not import roles or anything else.
