.. _collection_structure:

********************
Collection structure
********************

A collection is a simple data structure. None of the directories are required unless you have specific content that belongs in one of them. A collection does require a ``galaxy.yml`` file at the root level of the collection. This file contains all of the metadata that Galaxy and other tools need in order to package, build and publish the collection.

.. contents::
   :local:
   :depth: 2

Collection directories and files
================================

A collection can contain these directories and files::

    collection/
    ├── docs/
    ├── galaxy.yml
    ├── meta/
    │   └── runtime.yml
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
    * Ansible only accepts ``.md`` extensions for the :file:`README` file and any files in the :file:`/docs` folder.
    * See the `ansible-collections <https://github.com/ansible-collections/>`_ GitHub Org for examples of collection structure.
    * Not all directories are currently in use. Those are placeholders for future features.

.. _galaxy_yml:

galaxy.yml
----------

A collection must have a ``galaxy.yml`` file that contains the necessary information to build a collection artifact. See :ref:`collections_galaxy_meta` for details.

.. _collections_doc_dir:

docs directory
---------------

Put general documentation for the collection here. Keep the specific documentation for plugins and modules embedded as Python docstrings. Use the ``docs`` folder to describe how to use the roles and plugins the collection provides, role requirements, and so on. Use markdown and do not add subfolders.

Use ``ansible-doc`` to view documentation for plugins inside a collection:

.. code-block:: bash

    ansible-doc -t lookup my_namespace.my_collection.lookup1

The ``ansible-doc`` command requires the fully qualified collection name (FQCN) to display specific plugin documentation. In this example, ``my_namespace`` is the Galaxy namespace and ``my_collection`` is the collection name within that namespace.

.. note:: The Galaxy namespace of an Ansible collection is defined in the ``galaxy.yml`` file. It can be different from the GitHub organization or repository name.

.. _collections_plugin_dir:

plugins directory
-----------------

Add a 'per plugin type' specific subdirectory here, including ``module_utils`` which is usable not only by modules, but by most plugins by using their FQCN. This is a way to distribute modules, lookups, filters, and so on without having to import a role in every play.

Vars plugins are unsupported in collections. Cache plugins may be used in collections for fact caching, but are not supported for inventory plugins.

.. _collection_module_utils:

module_utils
^^^^^^^^^^^^

When coding with ``module_utils`` in a collection, the Python ``import`` statement needs to take into account the FQCN along with the ``ansible_collections`` convention. The resulting Python import will look like ``from ansible_collections.{namespace}.{collection}.plugins.module_utils.{util} import {something}``

The following example snippets show a Python and PowerShell module using both default Ansible ``module_utils`` and
those provided by a collection. In this example the namespace is ``community``, the collection is ``test_collection``.
In the Python example the ``module_util`` in question is called ``qradar`` such that the FQCN is
``community.test_collection.plugins.module_utils.qradar``:

.. code-block:: python

    from ansible.module_utils.basic import AnsibleModule
    from ansible.module_utils.common.text.converters import to_text

    from ansible.module_utils.six.moves.urllib.parse import urlencode, quote_plus
    from ansible.module_utils.six.moves.urllib.error import HTTPError
    from ansible_collections.community.test_collection.plugins.module_utils.qradar import QRadarRequest

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

Note that importing something from an ``__init__.py`` file requires using the file name:

.. code-block:: python

    from ansible_collections.namespace.collection_name.plugins.callback.__init__ import CustomBaseClass

In the PowerShell example the ``module_util`` in question is called ``hyperv`` such that the FQCN is
``community.test_collection.plugins.module_utils.hyperv``:

.. code-block:: powershell

    #!powershell
    #AnsibleRequires -CSharpUtil Ansible.Basic
    #AnsibleRequires -PowerShell ansible_collections.community.test_collection.plugins.module_utils.hyperv

    $spec = @{
        name = @{ required = $true; type = "str" }
        state = @{ required = $true; choices = @("present", "absent") }
    }
    $module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

    Invoke-HyperVFunction -Name $module.Params.name

    $module.ExitJson()

.. _collections_roles_dir:

roles directory
----------------

Collection roles are mostly the same as existing roles, but with a couple of limitations:

 - Role names are now limited to contain only lowercase alphanumeric characters, plus ``_`` and start with an alpha character.
 - Roles in a collection cannot contain plugins any more. Plugins must live in the collection ``plugins`` directory tree. Each plugin is accessible to all roles in the collection.

The directory name of the role is used as the role name. Therefore, the directory name must comply with the above role name rules. The collection import into Galaxy will fail if a role name does not comply with these rules.

You can migrate 'traditional roles' into a collection but they must follow the rules above. You may need to rename roles if they don't conform. You will have to move or link any role-based plugins to the collection specific directories.

.. note::

    For roles imported into Galaxy directly from a GitHub repository, setting the ``role_name`` value in the role's metadata overrides the role name used by Galaxy. For collections, that value is ignored. When importing a collection, Galaxy uses the role directory as the name of the role and ignores the ``role_name`` metadata value.

playbooks directory
--------------------

TBD.

.. _developing_collections_tests_directory:

tests directory
----------------

Ansible Collections are tested much like Ansible itself, by using the `ansible-test` utility which is released as part of Ansible, version 2.9.0 and newer. Because Ansible Collections are tested using the same tooling as Ansible itself, via `ansible-test`, all Ansible developer documentation for testing is applicable for authoring Collections Tests with one key concept to keep in mind.

See :ref:`testing_collections` for specific information on how to test collections with ``ansible-test``.

When reading the :ref:`developing_testing` documentation, there will be content that applies to running Ansible from source code via a git clone, which is typical of an Ansible developer. However, it's not always typical for an Ansible Collection author to be running Ansible from source but instead from a stable release, and to create Collections it is not necessary to run Ansible from source. Therefore, when references of dealing with `ansible-test` binary paths, command completion, or environment variables are presented throughout the :ref:`developing_testing` documentation; keep in mind that it is not needed for Ansible Collection Testing because the act of installing the stable release of Ansible containing `ansible-test` is expected to setup those things for you.

.. _meta_runtime_yml:

meta directory
--------------

A collection can store some additional metadata in a ``runtime.yml`` file in the collection's ``meta`` directory. The ``runtime.yml`` file supports the top level keys:

- *requires_ansible*:

  The version of Ansible required to use the collection. Multiple versions can be separated with a comma.

  .. code:: yaml

     requires_ansible: ">=2.10,<2.11"

  .. note:: although the version is a `PEP440 Version Specifier <https://www.python.org/dev/peps/pep-0440/#version-specifiers>`_ under the hood, Ansible deviates from PEP440 behavior by truncating prerelease segments from the Ansible version. This means that Ansible 2.11.0b1 is compatible with something that ``requires_ansible: ">=2.11"``.

- *plugin_routing*:

  Content in a collection that Ansible needs to load from another location or that has been deprecated/removed.
  The top level keys of ``plugin_routing`` are types of plugins, with individual plugin names as subkeys.
  To define a new location for a plugin, set the ``redirect`` field to another name.
  To deprecate a plugin, use the ``deprecation`` field to provide a custom warning message and the removal version or date. If the plugin has been renamed or moved to a new location, the ``redirect`` field should also be provided. If a plugin is being removed entirely, ``tombstone`` can be used for the fatal error message and removal version or date.

  .. code:: yaml

     plugin_routing:
       inventory:
         kubevirt:
           redirect: community.general.kubevirt
         my_inventory:
           tombstone:
             removal_version: "2.0.0"
             warning_text: my_inventory has been removed. Please use other_inventory instead.
       modules:
         my_module:
           deprecation:
             removal_date: "2021-11-30"
             warning_text: my_module will be removed in a future release of this collection. Use another.collection.new_module instead.
           redirect: another.collection.new_module
         podman_image:
           redirect: containers.podman.podman_image
       module_utils:
         ec2:
           redirect: amazon.aws.ec2
         util_dir.subdir.my_util:
           redirect: namespace.name.my_util

- *import_redirection*

  A mapping of names for Python import statements and their redirected locations.

  .. code:: yaml

     import_redirection:
       ansible.module_utils.old_utility:
         redirect: ansible_collections.namespace_name.collection_name.plugins.module_utils.new_location

.. seealso::

   :ref:`distributing_collections`
        Learn how to package and publish your collection
   :ref:`contributing_maintained_collections`
        Guidelines for contributing to selected collections
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
        The development mailing list
   `irc.libera.chat <https://libera.chat/>`_
        #ansible IRC chat channel
