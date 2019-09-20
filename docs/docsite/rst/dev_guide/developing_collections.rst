
.. _developing_collections:

**********************
Developing collections
**********************


Collections are a distribution format for Ansible content. You can use collections to package and distribute playbooks, roles, modules, and plugins.
You can publish and use collections through `Ansible Galaxy <https://galaxy.ansible.com>`_.

.. contents::
   :local:
   :depth: 2

Collection structure
====================

Collections follow a simple data structure. None of the directories are required unless you have specific content that belongs in one of them. A collection does require a ``galaxy.yml`` file at the root level of the collection. This file contains all of the metadata that Galaxy
and other tools need in order to package, build and publish the collection::

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
    * Ansible only accepts ``.yml`` extensions for galaxy.yml.
    * See the `draft collection <https://github.com/bcoca/collection>`_ for an example of a full collection structure.
    * Not all directories are currently in use. Those are placeholders for future features.


galaxy.yml
----------

A collection must have a ``galaxy.yml`` file that contains the necessary information to build a collection artifact.
See :ref:`collections_galaxy_meta` for details.


docs directory
---------------

Keep general documentation for the collection here. Plugins and modules still keep their specific documentation embedded as Python docstrings. Use the ``docs`` folder to describe how to use the roles and plugins the collection provides, role requirements, and so on. Currently we are looking at Markdown as the standard format for documentation files, but this is subject to change.

Use ``ansible-doc`` to view documentation for plugins inside a collection:

.. code-block:: bash

    ansible-doc -t lookup my_namespace.my_collection.lookup1

The ``ansible-doc`` command requires the fully qualified collection name (FQCN) to display specific plugin documentation. In this example, ``my_namespace`` is the namespace and ``my_collection`` is the collection name within that namespace.

.. note:: The Ansible collection namespace is defined in the ``galaxy.yml`` file and is not equivalent to the GitHub repository name.


plugins directory
------------------

Add a 'per plugin type' specific subdirectory here, including ``module_utils`` which is usable not only by modules, but by any other plugin by using their FQCN. This is a way to distribute modules, lookups, filters, and so on, without having to import a role in every play.

module_utils
^^^^^^^^^^^^

When coding with ``module_utils`` in a collection, the Python ``import`` statement needs to take into account the FQCN along with the ``ansible_collections`` convention. The resulting Python import will look like ``from ansible_collections.{namespace}.{collection}.plugins.module_utils.{util} import {something}``

The following example snippets show a Python and PowerShell module using both default Ansible ``module_utils`` and
those provided by a collection. In this example the namespace is ``ansible_example``, the collection is ``community``.
In the Python example the ``module_util`` in question is called ``qradar`` such that the FQCN is
``ansible_example.community.plugins.module_utils.qradar``:

.. code-block:: python

    from ansible.module_utils.basic import AnsibleModule
    from ansible.module_utils._text import to_text

    from ansible.module_utils.six.moves.urllib.parse import urlencode, quote_plus
    from ansible.module_utils.six.moves.urllib.error import HTTPError
    from ansible_collections.ansible_example.community.plugins.module_utils.qradar import QRadarRequest

    argspec = dict(
        name=dict(required=True, type='str'),
        state=dict(choices=['present', 'absent'], required=True),
    )

    module = AnsibleModule(
        argument_spec=argspec,
        supports_check_mode=True
    )

    qradar_request = QRadarRequest(
        module,
        headers={"Content-Type": "application/json"},
        not_rest_data_keys=['state']
    )


In the PowerShell example the ``module_util`` in question is called ``hyperv`` such that the FCQN is
``ansible_example.community.plugins.module_utils.hyperv``:

.. code-block:: powershell

    #!powershell
    #AnsibleRequires -CSharpUtil Ansible.Basic
    #AnsibleRequires -PowerShell ansible_collections.ansible_example.community.plugins.module_utils.hyperv

    $spec = @{
        name = @{ required = $true; type = "str" }
        state = @{ required = $true; choices = @("present", "absent") }
    }
    $module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

    Invoke-HyperVFunction -Name $module.Params.name

    $module.ExitJson()


roles directory
----------------

Collection roles are mostly the same as existing roles, but with a couple of limitations:

 - Role names are now limited to contain only lowercase alphanumeric characters, plus ``_`` and start with an alpha character.
 - Roles in a collection cannot contain plugins any more. Plugins must live in the collection ``plugins`` directory tree. Each plugin is accessible to all roles in the collection.

The directory name of the role is used as the role name. Therefore, the directory name must comply with the
above role name rules.
The collection import into Galaxy will fail if a role name does not comply with these rules.

You can migrate 'traditional roles' into a collection but they must follow the rules above. You may need to rename roles if they don't conform. You will have to move or link any role-based plugins to the collection specific directories.

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
======================

To create a collection:

#. Initialize a collection with :ref:`ansible-galaxy collection init<creating_collections_skeleton>` to create the skeleton directory structure.
#. Add your content to the collection.
#. Build the collection into a collection artifact with :ref:`ansible-galaxy collection build<building_collections>`.
#. Publish the collection artifact to Galaxy with :ref:`ansible-galaxy collection publish<publishing_collections>`.

A user can then install your collection on their systems.

Currently the ``ansible-galaxy collection`` command implements the following sub commands:

* ``init``: Create a basic collection skeleton based on the default template included with Ansible or your own template.
* ``build``: Create a collection artifact that can be uploaded to Galaxy or your own repository.
* ``publish``: Publish a built collection artifact to Galaxy.
* ``install``: Install one or more collections.

To learn more about the ``ansible-galaxy`` cli tool, see the :ref:`ansible-galaxy` man page.

.. _creating_collections_skeleton:

Creating a collection skeleton
------------------------------

To start a new collection:

.. code-block:: bash

    collection_dir#> ansible-galaxy collection init my_namespace.my_collection

Then you can populate the directories with the content you want inside the collection. See
https://github.com/bcoca/collection to get a better idea of what you can place inside a collection.


.. _building_collections:

Building collections
--------------------

To build a collection, run ``ansible-galaxy collection build`` from inside the root directory of the collection:

.. code-block:: bash

    collection_dir#> ansible-galaxy collection build

This creates
a tarball of the built collection in the current directory which can be uploaded to Galaxy.::

    my_collection/
    ├── galaxy.yml
    ├── ...
    ├── my_namespace-my_collection-1.0.0.tar.gz
    └── ...


.. note::
    Certain files and folders are excluded when building the collection artifact. This is not currently configurable
    and is a work in progress so the collection artifact may contain files you would not wish to distribute.

This tarball is mainly intended to upload to Galaxy
as a distribution method, but you can use it directly to install the collection on target systems.

.. _trying_collection_locally:

Trying collection locally
-------------------------

You can try your collection locally by installing it from the tarball.

.. code-block:: bash

   ansible-galaxy collection install my_namespace-my_collection-1.0.0.tar.gz -p ./collections/ansible_collections

You should use one of the values configured in :ref:`COLLECTIONS_PATHS` for your path. This is also where Ansible itself will expect to find collections when attempting to use them.

Then try to use the local collection inside a playbook, for more details see :ref:`Using collections <using_collections>`

.. _publishing_collections:

Publishing collections
----------------------

You can publish collections to Galaxy using the ``ansible-galaxy collection publish`` command or the Galaxy UI itself.

.. note:: Once you upload a version of a collection, you cannot delete or modify that version. Ensure that everything looks okay before you upload it.

Upload using ansible-galaxy
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To upload the collection artifact with the ``ansible-galaxy`` command:

.. code-block:: bash

     ansible-galaxy collection publish path/to/my_namespace-my_collection-1.0.0.tar.gz --api-key=SECRET

The above command triggers an import process, just as if you uploaded the collection through the Galaxy website.
The command waits until the import process completes before reporting the status back. If you wish to continue
without waiting for the import result, use the ``--no-wait`` argument and manually look at the import progress in your
`My Imports <https://galaxy.ansible.com/my-imports/>`_ page.

The API key is a secret token used by Ansible Galaxy to protect your content. You can find your API key at your
`Galaxy profile preferences <https://galaxy.ansible.com/me/preferences>`_ page.

Upload from the Galaxy website
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To upload your collection artifact directly on Galaxy:

#. Go to the `My Content <https://galaxy.ansible.com/my-content/namespaces>`_ page, and click the **Add Content** button on one of your namespaces.
#. From the **Add Content** dialogue, click **Upload New Collection**, and select the collection archive file from your local filesystem.

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

Collection versions use `Sematic Versioning <https://semver.org/>`_ for version numbers. Please read the official documentation for details and examples. In summary:

* Increment major (for example: x in `x.y.z`) version number for an incompatible API change.
* Increment minor (for example: y in `x.y.z`) version number for new functionality in a backwards compatible manner.
* Increment patch (for example: z in `x.y.z`) version number for backwards compatible bug fixes.

Migrating Ansible content to a collection
=========================================

You can experiment with migrating existing modules into a collection using the `content_collector tool <https://github.com/ansible/content_collector>`_. The ``content_collector`` is a playbook that helps you migrate content from an Ansible distribution into a collection.

.. warning::

	This tool is in active development and is provided only for experimentation and feedback at this point.

See the `content_collector README <https://github.com/ansible/content_collector>`_ for full details and usage guidelines.

.. seealso::

   :ref:`collections`
       Learn how to install and use collections.
   :ref:`collections_galaxy_meta`
       Understand the collections metadata structure.
   :ref:`developing_modules_general`
       Learn about how to write Ansible modules
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
