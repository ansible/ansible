:orphan:

.. _collections:

***********
Collections
***********


Collections are a distribution format for Ansible content. They can be used to
package and distribute playbooks, roles, modules, and plugins.
You can publish and use collections through `Ansible Galaxy <https://galaxy.ansible.com>`_.

.. important::
    This feature is available in Ansible 2.8 as a *Technology Preview* and therefore is not fully supported. It should only be used for testing and should not be deployed in a production environment.
    Future Galaxy or Ansible releases may introduce breaking changes.


.. contents::
   :local:
   :depth: 2

Collection structure
====================

Collections follow a simple data structure. None of the directories are required unless you have specific content that belongs in one of them. A collection does require a ``galaxy.yml`` file at the root level of the collection. This file contains all of the metadata that Galaxy
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
======================

To create a collection:

#. Initialize a collection with :ref:`ansible-galaxy collection init<creating_collections_skeleton>` to create the skeleton directory structure.
#. Add your content to the collection.
#. Build the collection into a collection artifact with :ref:`ansible-galaxy collection build<building_collections>`.
#. Publish the collection artifact to Galaxy with :ref:`ansible-galaxy collection publish<publishing_collections>`.

A user can then install your collection on their systems.

.. note::
    Any references to ``ansible-galaxy`` below will be of a 'working version' that is in development for the 2.9
    release. As such, the command and this documentation section is subject to frequent changes.

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

Collection versions use `Sematic Versioning <https://semver.org/>` for version numbers. Please read the official documentation for details and examples. In summary:

* Increment major (for example: x in `x.y.z`) version number for an incompatible API change.
* Increment minor (for example: y in `x.y.z`) version number for new functionality in a backwards compatible manner.
* Increment patch (for example: z in `x.y.z`) version number for backwards compatible bug fixes.

Migrating Ansible content to a collection
=========================================

You can experiment with migrating existing modules into a collection using the `content_collector tool <https://github.com/ansible/content_collector>`_. The ``content_collector`` is a playbook that helps you migrate content from an Ansible distribution into a collection.

.. warning::

	This tool is in active development and is provided only for experimentation and feedback at this point.

See the `content_collector README <https://github.com/ansible/content_collector>`_ for full details and usage guidelines.

Installing collections
======================

You can use the ``ansible-galaxy collection install`` command to install a collection on your system. You must specify an installation location using the ``-p`` option.

To install a collection hosted in Galaxy:

.. code-block:: bash

   ansible-galaxy collection install my_namespace.my_collection -p /collections


You can also directly use the tarball from your build:

.. code-block:: bash

   ansible-galaxy collection install my_namespace-my_collection-1.0.0.tar.gz -p ./collections

.. note::
    The install command automatically appends the path ``ansible_collections`` to the one specified  with the ``-p`` option unless the
    parent directory is already in a folder called ``ansible_collections``.


You should use one of the values configured in :ref:`COLLECTIONS_PATHS` for your path. This is also where Ansible itself will expect to find collections when attempting to use them.

You can also keep a collection adjacent to the current playbook, under a ``collections/ansible_collections/`` directory structure.

::

    play.yml
    ├── collections/
    │   └── ansible_collections/
    │               └── my_namespace/
    │                   └── my_collection/<collection structure lives here>


Installing an older version of a collection
-------------------------------------------

By default ``ansible-galaxy`` installs the latest collection that is available but you can add a version range
identifier to install a specific version.

To install the 1.0.0 version of the collection:

.. code-block:: bash

   ansible-galaxy collection install my_namespace.my_collection:1.0.0

To install the 1.0.0-beta.1 version of the collection:

.. code-block:: bash

   ansible-galaxy collection install my_namespace.my_collection:==1.0.0-beta.1

To install the collections that are greater than or equal to 1.0.0 or less than 2.0.0:

.. code-block:: bash

   ansible-galaxy collection install my_namespace.my_collection:>=1.0.0,<2.0.0


You can specify multiple range identifiers which are split by ``,``. You can use the following range identifiers:

* ``*``: Any version, this is the default used when no range specified is set.
* ``!=``: Version is not equal to the one specified.
* ``==``: Version must be the one specified.
* ``>=``: Version is greater than or equal to the one specified.
* ``>``: Version is greater than the one specified.
* ``<=``: Version is less than or equal to the one specified.
* ``<``: Version is less than the one specified.

.. note::
    The ``ansible-galaxy`` command ignores any pre-release versions unless the ``==`` range identifier is used to
    explicitly set to that pre-release version.


.. _collection_requirements_file:

Install multiple collections with a requirements file
-----------------------------------------------------

You can also setup a ``requirements.yml`` file to install multiple collections in one command. This file is a YAML file in the format:

.. code-block:: yaml+jinja

   ---
   collections:
   # With just the collection name
   - my_namespace.my_collection

   # With the collection name, version, and source options
   - name: my_namespace.my_other_collection
     version: 'version range identifiers (default: ``*``)'
     source: 'The Galaxy URL to pull the collection from (default: ``--api-server`` from cmdline)'

The ``version`` key can take in the same range identifier format documented above.

Roles can also be specified and placed under the ``roles`` key. The values follow the same format as a requirements
file used in older Ansible releases.

.. note::
    While both roles and collections can be specified in one requirements file, they need to be installed separately.
    The ``ansible-galaxy role install -r requirements.yml`` will only install roles and
    ``ansible-galaxy collection install -r requirements.yml -p ./`` will only install collections.

.. _galaxy_server_config:

Galaxy server configuration list
--------------------------------

By default running ``ansible-galaxy`` will use the :ref:`galaxy_server` config value or the ``--server`` command line
argument when it performs an action against a Galaxy server. The ``ansible-galaxy collection install`` supports
installing collections from multiple servers as defined in the :ref:`ansible_configuration_settings_locations` file
using the :ref:`galaxy_server_list` configuration option. To define multiple Galaxy servers you have to create the
following entries like so:

.. code-block:: ini

    [galaxy]
    server_list = my_org_hub, release_galaxy, test_galaxy

    [galaxy_server.my_org_hub]
    url=https://automation.my_org/
    username=my_user
    password=my_pass

    [galaxy_server.release_galaxy]
    url=https://galaxy.ansible.com/
    token=my_token

    [galaxy_server.test_galaxy]
    url=https://galaxy-dev.ansible.com/
    token=my_token

.. note::
    You can use the ``--server`` command line argument to select an explicit Galaxy server in the ``server_list`` and
    the value of this arg should match the name of the server. If the value of ``--server`` is not a pre-defined server
    in ``ansible.cfg`` then the value specified will be the URL used to access that server and all pre-defined servers
    are ignored. Also the ``--api-key`` argument is not applied to any of the pre-defined servers, it is only applied
    if no server list is defined or a URL was specified by ``--server``.


The :ref:`galaxy_server_list` option is a list of server identifiers in a prioritized order. When searching for a
collection, the install process will search in that order, e.g. ``my_org_hub`` first, then ``release_galaxy``, and
finally ``test_galaxy`` until the collection is found. The actual Galaxy instance is then defined under the section
``[galaxy_server.{{ id }}]`` where ``{{ id }}`` is the server identifier defined in the list. This section can then
define the following keys:

* ``url``: The URL of the galaxy instance to connect to, this is required.
* ``token``: A token key to use for authentication against the Galaxy instance, this is mutually exclusive with ``username``
* ``username``: The username to use for basic authentication against the Galaxy instance, this is mutually exclusive with ``token``
* ``password``: The password to use for basic authentication

As well as being defined in the ``ansible.cfg`` file, these server options can be defined as an environment variable.
The environment variable is in the form ``ANSIBLE_GALAXY_SERVER_{{ id }}_{{ key }}`` where ``{{ id }}`` is the upper
case form of the server identifier and ``{{ key }}`` is the key to define. For example I can define ``token`` for
``release_galaxy`` by setting ``ANSIBLE_GALAXY_SERVER_RELEASE_GALAXY_TOKEN=secret_token``.

For operations where only one Galaxy server is used, i.e. ``publish``, ``info``, ``login`` then the first entry in the
``server_list`` is used unless an explicit server was passed in as a command line argument.

.. note::
    Once a collection is found, any of its requirements are only searched within the same Galaxy instance as the parent
    collection. The install process will not search for a collection requirement in a different Galaxy instance.


.. _using_collections:
 
Using collections
=================

Once installed, you can reference a collection content by its FQCN:

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
