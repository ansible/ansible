
.. _developing_collections:

**********************
Developing collections
**********************

Collections are a distribution format for Ansible content. You can use collections to package and distribute playbooks, roles, modules, and plugins.
You can publish and use collections through `Ansible Galaxy <https://galaxy.ansible.com>`_.

* For details on how to *use* collections see :ref:`collections`.
* For the current development status of Collections and FAQ see `Ansible Collections Overview and FAQ <https://github.com/ansible-collections/overview/blob/main/README.rst>`_.

.. contents::
   :local:
   :depth: 2

.. _collection_structure:

Collection structure
====================

Collections follow a simple data structure. None of the directories are required unless you have specific content that belongs in one of them. A collection does require a ``galaxy.yml`` file at the root level of the collection. This file contains all of the metadata that Galaxy and other tools need in order to package, build and publish the collection::

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

A collection must have a ``galaxy.yml`` file that contains the necessary information to build a collection artifact.
See :ref:`collections_galaxy_meta` for details.

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
------------------

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
    from ansible.module_utils._text import to_text

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

In the PowerShell example the ``module_util`` in question is called ``hyperv`` such that the FCQN is
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

The directory name of the role is used as the role name. Therefore, the directory name must comply with the
above role name rules.
The collection import into Galaxy will fail if a role name does not comply with these rules.

You can migrate 'traditional roles' into a collection but they must follow the rules above. You may need to rename roles if they don't conform. You will have to move or link any role-based plugins to the collection specific directories.

.. note::

    For roles imported into Galaxy directly from a GitHub repository, setting the ``role_name`` value in the role's metadata overrides the role name used by Galaxy. For collections, that value is ignored. When importing a collection, Galaxy uses the role directory as the name of the role and ignores the ``role_name`` metadata value.

playbooks directory
--------------------

TBD.

.. _developing_collections_tests_directory:

tests directory
----------------

Ansible Collections are tested much like Ansible itself, by using the
`ansible-test` utility which is released as part of Ansible, version 2.9.0 and
newer. Because Ansible Collections are tested using the same tooling as Ansible
itself, via `ansible-test`, all Ansible developer documentation for testing is
applicable for authoring Collections Tests with one key concept to keep in mind.

See :ref:`testing_collections` for specific information on how to test collections
with ``ansible-test``.

When reading the :ref:`developing_testing` documentation, there will be content
that applies to running Ansible from source code via a git clone, which is
typical of an Ansible developer. However, it's not always typical for an Ansible
Collection author to be running Ansible from source but instead from a stable
release, and to create Collections it is not necessary to run Ansible from
source. Therefore, when references of dealing with `ansible-test` binary paths,
command completion, or environment variables are presented throughout the
:ref:`developing_testing` documentation; keep in mind that it is not needed for
Ansible Collection Testing because the act of installing the stable release of
Ansible containing `ansible-test` is expected to setup those things for you.

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


.. _creating_collections_skeleton:

Creating a collection skeleton
------------------------------

To start a new collection:

.. code-block:: bash

    collection_dir#> ansible-galaxy collection init my_namespace.my_collection

.. note::

	Both the namespace and collection names use the same strict set of requirements. See `Galaxy namespaces <https://galaxy.ansible.com/docs/contributing/namespaces.html#galaxy-namespaces>`_ on the Galaxy docsite for those requirements.

Once the skeleton exists, you can populate the directories with the content you want inside the collection. See `ansible-collections <https://github.com/ansible-collections/>`_ GitHub Org to get a better idea of what you can place inside a collection.

.. _creating_collections:

Creating collections
======================

To create a collection:

#. Create a collection skeleton with the ``collection init`` command. See :ref:`creating_collections_skeleton` above.
#. Add your content to the collection.
#. Build the collection into a collection artifact with :ref:`ansible-galaxy collection build<building_collections>`.
#. Publish the collection artifact to Galaxy with :ref:`ansible-galaxy collection publish<publishing_collections>`.

A user can then install your collection on their systems.

Currently the ``ansible-galaxy collection`` command implements the following sub commands:

* ``init``: Create a basic collection skeleton based on the default template included with Ansible or your own template.
* ``build``: Create a collection artifact that can be uploaded to Galaxy or your own repository.
* ``publish``: Publish a built collection artifact to Galaxy.
* ``install``: Install one or more collections.

To learn more about the ``ansible-galaxy`` command-line tool, see the :ref:`ansible-galaxy` man page.


.. _docfragments_collections:

Using documentation fragments in collections
--------------------------------------------

To include documentation fragments in your collection:

#. Create the documentation fragment: ``plugins/doc_fragments/fragment_name``.

#. Refer to the documentation fragment with its FQCN.

.. code-block:: yaml

   extends_documentation_fragment:
     - community.kubernetes.k8s_name_options
     - community.kubernetes.k8s_auth_options
     - community.kubernetes.k8s_resource_options
     - community.kubernetes.k8s_scale_options

:ref:`module_docs_fragments` covers the basics for documentation fragments. The `kubernetes <https://github.com/ansible-collections/kubernetes>`_ collection includes a complete example.

You can also share documentation fragments across collections with the FQCN.

.. _building_collections:

Building collections
--------------------

To build a collection, run ``ansible-galaxy collection build`` from inside the root directory of the collection:

.. code-block:: bash

    collection_dir#> ansible-galaxy collection build

This creates a tarball of the built collection in the current directory which can be uploaded to Galaxy.::

    my_collection/
    ├── galaxy.yml
    ├── ...
    ├── my_namespace-my_collection-1.0.0.tar.gz
    └── ...

.. note::
   * Certain files and folders are excluded when building the collection artifact. See :ref:`ignoring_files_and_folders_collections`  to exclude other files you would not want to distribute.
   * If you used the now-deprecated ``Mazer`` tool for any of your collections, delete any and all files it added to your :file:`releases/` directory before you build your collection with ``ansible-galaxy``.
   * The current Galaxy maximum tarball size is 2 MB.


This tarball is mainly intended to upload to Galaxy
as a distribution method, but you can use it directly to install the collection on target systems.

.. _ignoring_files_and_folders_collections:

Ignoring files and folders
^^^^^^^^^^^^^^^^^^^^^^^^^^

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


.. _trying_collection_locally:

Trying collections locally
--------------------------

You can try your collection locally by installing it from the tarball. The following will enable an adjacent playbook to
access the collection:

.. code-block:: bash

   ansible-galaxy collection install my_namespace-my_collection-1.0.0.tar.gz -p ./collections


You should use one of the values configured in :ref:`COLLECTIONS_PATHS` for your path. This is also where Ansible itself will
expect to find collections when attempting to use them. If you don't specify a path value, ``ansible-galaxy collection install``
installs the collection in the first path defined in :ref:`COLLECTIONS_PATHS`, which by default is ``~/.ansible/collections``.

Next, try using the local collection inside a playbook. For examples and more details see :ref:`Using collections <using_collections>`

.. _collections_scm_install:

Installing collections from a git repository
--------------------------------------------

You can also test a version of your collection in development by installing it from a git repository.

.. code-block:: bash

   ansible-galaxy collection install git+https://github.com/org/repo.git,devel

.. include:: ../shared_snippets/installing_collections_git_repo.txt

.. _publishing_collections:

Publishing collections
----------------------

You can publish collections to Galaxy using the ``ansible-galaxy collection publish`` command or the Galaxy UI itself. You need a namespace on Galaxy to upload your collection. See `Galaxy namespaces <https://galaxy.ansible.com/docs/contributing/namespaces.html#galaxy-namespaces>`_ on the Galaxy docsite for details.

.. note:: Once you upload a version of a collection, you cannot delete or modify that version. Ensure that everything looks okay before you upload it.

.. _galaxy_get_token:

Getting your API token
^^^^^^^^^^^^^^^^^^^^^^

To upload your collection to Galaxy, you must first obtain an API token (``--token`` in the ``ansible-galaxy`` CLI command or ``token`` in the :file:`ansible.cfg` file under the ``galaxy_server`` section). The API token is a secret token used to protect your content.

To get your API token:

* For Galaxy, go to the `Galaxy profile preferences <https://galaxy.ansible.com/me/preferences>`_ page and click :guilabel:`API Key`.
* For Automation Hub, go to https://cloud.redhat.com/ansible/automation-hub/token/ and click :guilabel:`Load token` from the version dropdown.

Storing or using your API token
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once you have retrieved your API token, you can store or use the token for collections in two ways:

* Pass the token to  the ``ansible-galaxy`` command using the ``--token``.
* Specify the token within a Galaxy server list in your :file:`ansible.cfg` file.

Using the ``token`` argument
............................

You can use the ``--token`` argument with the ``ansible-galaxy`` command (in conjunction with the ``--server`` argument or :ref:`GALAXY_SERVER` setting in your :file:`ansible.cfg` file). You cannot use ``apt-key`` with any servers defined in your :ref:`Galaxy server list <galaxy_server_config>`.

.. code-block:: text

    ansible-galaxy collection publish ./geerlingguy-collection-1.2.3.tar.gz --token=<key goes here>


Specify the token within a Galaxy server list
.............................................

With this option, you configure one or more servers for Galaxy in your :file:`ansible.cfg` file under the ``galaxy_server_list`` section. For each server, you also configure the token.


.. code-block:: ini

   [galaxy]
   server_list = release_galaxy

   [galaxy_server.release_galaxy]
   url=https://galaxy.ansible.com/
   token=my_token

See :ref:`galaxy_server_config` for complete details.

.. _upload_collection_ansible_galaxy:

Upload using ansible-galaxy
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::
  By default, ``ansible-galaxy`` uses https://galaxy.ansible.com as the Galaxy server (as listed in the :file:`ansible.cfg` file under :ref:`galaxy_server`). If you are only publishing your collection to Ansible Galaxy, you do not need any further configuration. If you are using Red Hat Automation Hub or any other Galaxy server, see :ref:`Configuring the ansible-galaxy client <galaxy_server_config>`.

To upload the collection artifact with the ``ansible-galaxy`` command:

.. code-block:: bash

     ansible-galaxy collection publish path/to/my_namespace-my_collection-1.0.0.tar.gz

.. note::

	The above command assumes you have retrieved and stored your API token as part of a Galaxy server list. See :ref:`galaxy_get_token` for details.

The ``ansible-galaxy collection publish`` command triggers an import process, just as if you uploaded the collection through the Galaxy website.
The command waits until the import process completes before reporting the status back. If you want to continue
without waiting for the import result, use the ``--no-wait`` argument and manually look at the import progress in your
`My Imports <https://galaxy.ansible.com/my-imports/>`_ page.


.. _upload_collection_galaxy:

Upload a collection from the Galaxy website
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To upload your collection artifact directly on Galaxy:

#. Go to the `My Content <https://galaxy.ansible.com/my-content/namespaces>`_ page, and click the **Add Content** button on one of your namespaces.
#. From the **Add Content** dialogue, click **Upload New Collection**, and select the collection archive file from your local filesystem.

When uploading collections it doesn't matter which namespace you select. The collection will be uploaded to the
namespace specified in the collection metadata in the ``galaxy.yml`` file. If you're not an owner of the
namespace, the upload request will fail.

Once Galaxy uploads and accepts a collection, you will be redirected to the **My Imports** page, which displays output from the
import process, including any errors or warnings about the metadata and content contained in the collection.

.. _collection_versions:

Collection versions
-------------------

Once you upload a version of a collection, you cannot delete or modify that version. Ensure that everything looks okay before
uploading. The only way to change a collection is to release a new version. The latest version of a collection (by highest version number)
will be the version displayed everywhere in Galaxy; however, users will still be able to download older versions.

Collection versions use `Semantic Versioning <https://semver.org/>`_ for version numbers. Please read the official documentation for details and examples. In summary:

* Increment major (for example: x in `x.y.z`) version number for an incompatible API change.
* Increment minor (for example: y in `x.y.z`) version number for new functionality in a backwards compatible manner (for example new modules/plugins, parameters, return values).
* Increment patch (for example: z in `x.y.z`) version number for backwards compatible bug fixes.

.. _migrate_to_collection:

Migrating Ansible content to a different collection
====================================================

First, look at `Ansible Collection Checklist <https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst>`_.

To migrate content from one collection to another, if the collections are parts of `Ansible distribution <https://github.com/ansible-community/ansible-build-data/blob/main/2.10/ansible.in>`_:

#. Copy content from the source (old) collection to the target (new) collection.
#. Deprecate the module/plugin with ``removal_version`` scheduled for the next major version in ``meta/runtime.yml`` of the old collection. The deprecation must be released after the copied content has been included in a release of the new collection.
#. When the next major release of the old collection is prepared:

  * remove the module/plugin from the old collection
  * remove the symlink stored in ``plugin/modules`` directory if appropriate (mainly when removing from ``community.general`` and ``community.network``)
  * remove related unit and integration tests
  * remove specific module utils
  * remove specific documentation fragments if there are any in the old collection
  * add a changelog fragment containing entries for ``removed_features`` and ``breaking_changes``; you can see an example of a changelog fragment in this `pull request <https://github.com/ansible-collections/community.general/pull/1304>`_ 
  * change ``meta/runtime.yml`` in the old collection:

    * add ``redirect`` to the corresponding module/plugin's entry
    * in particular, add ``redirect`` for the removed module utils and documentation fragments if applicable
    * remove ``removal_version`` from there
  * remove related entries from ``tests/sanity/ignore.txt`` files if exist
  * remove changelog fragments for removed content that are not yet part of the changelog (in other words, do not modify `changelogs/changelog.yaml` and do not delete files mentioned in it)
  * remove requirements that are no longer required in ``tests/unit/requirements.txt``, ``tests/requirements.yml`` and ``galaxy.yml``

According to the above, you need to create at least three PRs as follows:

#. Create a PR against the new collection to copy the content.
#. Deprecate the module/plugin in the old collection.
#. Later create a PR against the old collection to remove the content according to the schedule.


Adding the content to the new collection
----------------------------------------

Create a PR in the new collection to:

#. Copy ALL the related files from the old collection.
#. If it is an action plugin, include the corresponding module with documentation.
#. If it is a module, check if it has a corresponding action plugin that should move with it.
#. Check ``meta/`` for relevant updates to ``runtime.yml`` if it exists.
#. Carefully check the moved ``tests/integration`` and ``tests/units`` and update for FQCN.
#. Review ``tests/sanity/ignore-*.txt`` entries in the old collection.
#. Update ``meta/runtime.yml`` in the old collection.


Removing the content from the old collection
--------------------------------------------

Create a PR against the source collection repository to remove the modules, module_utils, plugins, and docs_fragments related to this migration:

#. If you are removing an action plugin, remove the corresponding module that contains the documentation.
#. If you are removing a module, remove any corresponding action plugin that should stay with it.
#. Remove any entries about removed plugins from ``meta/runtime.yml``. Ensure they are added into the new repo.
#. Remove sanity ignore lines from ``tests/sanity/ignore\*.txt``
#. Remove associated integration tests from ``tests/integrations/targets/`` and unit tests from ``tests/units/plugins/``.
#. if you are removing from content from ``community.general`` or ``community.network``, remove entries from ``.github/BOTMETA.yml``.
#. Carefully review ``meta/runtime.yml`` for any entries you may need to remove or update, in particular deprecated entries.
#. Update ``meta/runtime.yml`` to contain redirects for EVERY PLUGIN, pointing to the new collection name.

.. warning::

	Maintainers for the old collection have to make sure that the PR is merged in a way that it does not break user experience and semantic versioning:

	#. A new version containing the merged PR must not be released before the collection the content has been moved to has been released again, with that content contained in it. Otherwise the redirects cannot work and users relying on that content will experience breakage.
	#. Once 1.0.0 of the collection from which the content has been removed has been released, such PRs can only be merged for a new **major** version (in other words, 2.0.0, 3.0.0, and so on).


BOTMETA.yml
-----------

The ``BOTMETA.yml``, for example in `community.general collection repository <https://github.com/ansible-collections/community.general/blob/main/.github/BOTMETA.yml>`_, is the source of truth for:

* ansibullbot

If the old and/or new collection has ``ansibullbot``, its ``BOTMETA.yml`` must be updated correspondingly.

Ansibulbot will know how to redirect existing issues and PRs to the new repo.
The build process for docs.ansible.com will know where to find the module docs.

.. code-block:: yaml

   $modules/monitoring/grafana/grafana_plugin.py:
       migrated_to: community.grafana
   $modules/monitoring/grafana/grafana_dashboard.py:
       migrated_to: community.grafana
   $modules/monitoring/grafana/grafana_datasource.py:
       migrated_to: community.grafana
   $plugins/callback/grafana_annotations.py:
       maintainers: $team_grafana
       labels: monitoring grafana
       migrated_to: community.grafana
   $plugins/doc_fragments/grafana.py:
       maintainers: $team_grafana
       labels: monitoring grafana
       migrated_to: community.grafana

`Example PR <https://github.com/ansible/ansible/pull/66981/files>`_

* The ``migrated_to:`` key must be added explicitly for every *file*. You cannot add ``migrated_to`` at the directory level. This is to allow module and plugin webdocs to be redirected to the new collection docs.
* ``migrated_to:`` MUST be added for every:

  * module
  * plugin
  * module_utils
  * contrib/inventory script

* You do NOT need to add ``migrated_to`` for:

  * Unit tests
  * Integration tests
  * ReStructured Text docs (anything under ``docs/docsite/rst/``)
  * Files that never existed in ``ansible/ansible:devel``

.. _testing_collections:

Testing collections
===================

The main tool for testing collections is ``ansible-test``, Ansible's testing tool described in :ref:`developing_testing`. You can run several compile and sanity checks, as well as run unit and integration tests for plugins using ``ansible-test``. When you test collections, test against the ansible-base version(s) you are targeting.

You must always execute ``ansible-test`` from the root directory of a collection. You can run ``ansible-test`` in Docker containers without installing any special requirements. The Ansible team uses this approach in Shippable both in the ansible/ansible GitHub repository and in the large community collections such as `community.general <https://github.com/ansible-collections/community.general/>`_ and `community.network <https://github.com/ansible-collections/community.network/>`_. The examples below demonstrate running tests in Docker containers.

Compile and sanity tests
------------------------

To run all compile and sanity tests::

    ansible-test sanity --docker default -v

See :ref:`testing_compile` and :ref:`testing_sanity` for more information. See the :ref:`full list of sanity tests <all_sanity_tests>` for details on the sanity tests and how to fix identified issues.

Unit tests
----------

You must place unit tests in the appropriate``tests/unit/plugins/`` directory. For example, you would place tests for ``plugins/module_utils/foo/bar.py`` in ``tests/unit/plugins/module_utils/foo/test_bar.py`` or ``tests/unit/plugins/module_utils/foo/bar/test_bar.py``. For examples, see the `unit tests in community.general <https://github.com/ansible-collections/community.general/tree/master/tests/unit/>`_.

To run all unit tests for all supported Python versions::

    ansible-test units --docker default -v

To run all unit tests only for a specific Python version::

    ansible-test units --docker default -v --python 3.6

To run only a specific unit test::

    ansible-test units --docker default -v --python 3.6 tests/unit/plugins/module_utils/foo/test_bar.py

You can specify Python requirements in the ``tests/unit/requirements.txt`` file. See :ref:`testing_units` for more information, especially on fixture files.

Integration tests
-----------------

You must place integration tests in the appropriate ``tests/integration/targets/`` directory. For module integration tests, you can use the module name alone. For example, you would place integration tests for ``plugins/modules/foo.py`` in a directory called ``tests/integration/targets/foo/``. For non-module plugin integration tests, you must add the plugin type to the directory name. For example, you would place integration tests for ``plugins/connections/bar.py`` in a directory called ``tests/integration/targets/connection_bar/``. For lookup plugins, the directory must be called ``lookup_foo``, for inventory plugins, ``inventory_foo``, and so on.

You can write two different kinds of integration tests:

* Ansible role tests run with ``ansible-playbook`` and validate various aspects of the module. They can depend on other integration tests (usually named ``prepare_bar`` or ``setup_bar``, which prepare a service or install a requirement named ``bar`` in order to test module ``foo``) to set-up required resources, such as installing required libraries or setting up server services.
* ``runme.sh`` tests run directly as scripts. They can set up inventory files, and execute ``ansible-playbook`` or ``ansible-inventory`` with various settings.

For examples, see the `integration tests in community.general <https://github.com/ansible-collections/community.general/tree/master/tests/integration/targets/>`_. See also :ref:`testing_integration` for more details.

Since integration tests can install requirements, and set-up, start and stop services, we recommended running them in docker containers or otherwise restricted environments whenever possible. By default, ``ansible-test`` supports Docker images for several operating systems. See the `list of supported docker images <https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_data/completion/docker.txt>`_ for all options. Use the ``default`` image mainly for platform-independent integration tests, such as those for cloud modules. The following examples use the ``centos8`` image.

To execute all integration tests for a collection::

    ansible-test integration --docker centos8 -v

If you want more detailed output, run the command with ``-vvv`` instead of ``-v``. Alternatively, specify ``--retry-on-error`` to automatically re-run failed tests with higher verbosity levels.

To execute only the integration tests in a specific directory::

    ansible-test integration --docker centos8 -v connection_bar

You can specify multiple target names. Each target name is the name of a directory in ``tests/integration/targets/``.

.. _hacking_collections:

Contributing to collections
===========================

If you want to add functionality to an existing collection, modify a collection you are using to fix a bug, or change the behavior of a module in a collection, clone the git repository for that collection and make changes on a branch. You can combine changes to a collection with a local checkout of Ansible (``source hacking/env-setup``).

This section describes the process for `community.general <https://github.com/ansible-collections/community.general/>`_. To contribute to other collections, replace the folder names ``community`` and ``general`` with the namespace and collection name of a different collection.

We assume that you have included ``~/dev/ansible/collections/`` in :ref:`COLLECTIONS_PATHS`, and if that path mentions multiple directories, that you made sure that no other directory earlier in the search path contains a copy of ``community.general``. Create the directory ``~/dev/ansible/collections/ansible_collections/community``, and in it clone `the community.general Git repository <https://github.com/ansible-collections/community.general/>`_ or a fork of it into the folder ``general``::

    mkdir -p ~/dev/ansible/collections/ansible_collections/community
    cd ~/dev/ansible/collections/ansible_collections/community
    git clone git@github.com:ansible-collections/community.general.git general

If you clone a fork, add the original repository as a remote ``upstream``::

    cd ~/dev/ansible/collections/ansible_collections/community/general
    git remote add upstream git@github.com:ansible-collections/community.general.git

Now you can use this checkout of ``community.general`` in playbooks and roles with whichever version of Ansible you have installed locally, including a local checkout of ``ansible/ansible``'s ``devel`` branch.

For collections hosted in the ``ansible_collections`` GitHub org, create a branch and commit your changes on the branch. When you are done (remember to add tests, see :ref:`testing_collections`), push your changes to your fork of the collection and create a Pull Request. For other collections, especially for collections not hosted on GitHub, check the ``README.md`` of the collection for information on contributing to it.

.. _collection_changelogs:

Generating changelogs for a collection
======================================

We recommend that you use the `antsibull-changelog <https://github.com/ansible-community/antsibull-changelog>`_ tool to generate Ansible-compatible changelogs for your collection. The Ansible changelog uses the output of this tool to collate all the collections included in an Ansible release into one combined changelog for the release.

.. note::

	Ansible here refers to the Ansible 2.10 or later release that includes a curated set of collections.

Understanding antsibull-changelog
---------------------------------

The ``antsibull-changelog`` tool allows you to create and update changelogs for Ansible collections that are compatible with the combined Ansible changelogs. This is an update to the changelog generator used in prior Ansible releases. The tool adds three new changelog fragment categories: ``breaking_changes``, ``security_fixes`` and ``trivial``. The tool also generates the ``changelog.yaml`` file that Ansible uses to create the combined ``CHANGELOG.rst`` file and Porting Guide for the release.

See :ref:`changelogs_how_to` and the `antsibull-changelog documentation <https://github.com/ansible-community/antsibull-changelog/tree/main/docs>`_ for complete details.

.. note::

	The collection maintainers set the changelog policy for their collections. See the individual collection contributing guidelines for complete details.

Generating changelogs
---------------------

To initialize changelog generation:

#. Install ``antsibull-changelog``: :code:`pip install antsibull-changelog`.
#. Initialize changelogs for your repository: :code:`antsibull-changelog init <path/to/your/collection>`.
#. Optionally, edit the ``changelogs/config.yaml`` file to customize the location of the generated changelog ``.rst`` file or other options. See `Bootstrapping changelogs for collections <https://github.com/ansible-community/antsibull-changelog/blob/main/docs/changelogs.rst#bootstrapping-changelogs-for-collections>`_ for details.

To generate changelogs from the changelog fragments you created:

#. Optionally, validate your changelog fragments: :code:`antsibull-changelog lint`.
#. Generate the changelog for your release: :code:`antsibull-changelog release [--version version_number]`.

.. note::

  Add the  ``--reload-plugins`` option if you ran the ``antsibull-changelog release`` command previously and the version of the collection has not changed. ``antsibull-changelog`` caches the information on all plugins and does not update its cache until the collection version changes.


Porting Guide entries
----------------------

The following changelog fragment categories are consumed by the Ansible changelog generator into the Ansible Porting Guide:

* ``major_changes``
* ``breaking_changes``
* ``deprecated_features``
* ``removed_features``

Including collection changelogs into Ansible
=============================================


If your collection is part of Ansible, use one of the following three options  to include your changelog into the Ansible release changelog:

* Use the ``antsibull-changelog`` tool.

* If are not using this tool, include the properly formatted ``changelog.yaml`` file  into your collection. See the `changlog.yaml format <https://github.com/ansible-community/antsibull-changelog/blob/main/docs/changelog.yaml-format.md>`_ for details.

* Add a link to own changelogs or release notes in any format by opening an issue at https://github.com/ansible-community/ansible-build-data/ with the HTML link to that information.

.. note::

  For the first two options, Ansible pulls the changelog details from Galaxy so your changelogs must be included in the collection version on Galaxy that is included in the upcoming Ansible release.

.. seealso::

   :ref:`collections`
       Learn how to install and use collections.
   :ref:`collections_galaxy_meta`
       Understand the collections metadata structure.
   :ref:`developing_modules_general`
       Learn about how to write Ansible modules
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   `irc.libera.chat <https://libera.chat>`_
       #ansible IRC chat channel
