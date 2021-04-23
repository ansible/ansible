.. _migrate_to_collection:

***************************************************
Migrating Ansible content to a different collection
***************************************************

When you move content from one collection to another, for example to extract a set of related modules out of ``community.general`` to create a more focused collection, you must make sure the transition is easy for users to follow. 
 
.. contents::
   :local:
   :depth: 2

Migrating content
=================

Before you start migrating content from one collection to another, look at `Ansible Collection Checklist <https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst>`_.

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

To implement these changes, you need to create at least three PRs:

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


Updating BOTMETA.yml
--------------------

The ``BOTMETA.yml``, for example in `community.general collection repository <https://github.com/ansible-collections/community.general/blob/main/.github/BOTMETA.yml>`_, is the source of truth for:

* ansibullbot

If the old and/or new collection has ``ansibullbot``, its ``BOTMETA.yml`` must be updated correspondingly.

Ansibulbot will know how to redirect existing issues and PRs to the new repo. The build process for docs.ansible.com will know where to find the module docs.

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

.. seealso::

   :ref:`collections`
       Learn how to install and use collections.
   :ref:`contributing_maintained_collections`
       Guidelines for contributing to selected collections
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
