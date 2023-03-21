.. _maintainers_workflow:


Backporting and Ansible inclusion
==================================

Each collection community can set its own rules and workflow for managing pull requests, bug reports, documentation issues, and feature requests, as well as adding and replacing maintainers. Maintainers review and merge pull requests following the:

* :ref:`code_of_conduct`
* :ref:`maintainer_requirements`
* :ref:`Committer guidelines <committer_general_rules>`
* :ref:`PR review checklist<review_checklist>`

There can be two kinds of maintainers: :ref:`collection_maintainers` and :ref:`module_maintainers`.

.. _collection_maintainers:

Collection maintainers
----------------------

Collection-scope maintainers are contributors who have the ``write`` or higher access level in a collection. They have commit rights and can merge pull requests, among other permissions.

When a collection maintainer considers a contribution to a file significant enough
(for example, fixing a complex bug, adding a feature, providing regular reviews, and so on),
they can invite the author to become a module maintainer.


.. _module_maintainers:

Module maintainers
------------------

Module-scope maintainers exist in collections that have the `collection bot <https://github.com/ansible-community/collection_bot>`_,
for example, `community.general <https://github.com/ansible-collections/community.general>`_
and `community.network <https://github.com/ansible-collections/community.network>`_.

Being a module maintainer is the stage prior to becoming a collection maintainer. Module maintainers are contributors who are listed in ``.github/BOTMETA.yml``. The scope can be any file (for example, a module or plugin), directory, or repository. Because in most cases the scope is a module or group of modules, we call these contributors module maintainers. The collection bot notifies module maintainers when issues/pull requests related to files they maintain are created.

Module maintainers have indirect commit rights implemented through the `collection bot <https://github.com/ansible-community/collection_bot>`_.
When two module maintainers comment with the keywords ``shipit``, ``LGTM``, or ``+1`` on a pull request
which changes a module they maintain, the collection bot merges the pull request automatically.

For more information about the collection bot and its interface,
see to the `Collection bot overview <https://github.com/ansible-community/collection_bot/blob/main/ISSUE_HELP.md>`_.


Releasing a collection
----------------------

Collection maintainers are responsible for releasing new versions of a collection. Generally, releasing a collection consists of:

#. Planning and announcement.
#. Generating a changelog.
#. Creating a release git tag and pushing it.
#. Automatically publishing the release tarball on `Ansible Galaxy <https://galaxy.ansible.com/>`_ through the `Zuul dashboard <https://dashboard.zuul.ansible.com/t/ansible/builds?pipeline=release>`_.
#. Final announcement.
#. Optionally, `file a request to include a new collection into the Ansible package <https://github.com/ansible-collections/ansible-inclusion>`_.

See :ref:`releasing_collections` for details.

.. _Backporting:

Backporting
------------

Collection maintainers backport merged pull requests to stable branches
following the `semantic versioning <https://semver.org/>`_ and release policies of the collections.

The manual backport process is similar to the :ref:`ansible-core backporting guidelines <backport_process>`.

For convenience, backporting can be implemented automatically using GitHub bots (for example, with the `Patchback app <https://github.com/apps/patchback>`_) and labeling as it is done in `community.general <https://github.com/ansible-collections/community.general>`_ and `community.network <https://github.com/ansible-collections/community.network>`_.


.. _including_collection_ansible:

Including a collection in Ansible
-----------------------------------

If a collection is not included in Ansible (not shipped with Ansible package), maintainers can submit the collection for inclusion by creating a discussion under the `ansible-collections/ansible-inclusion repository <https://github.com/ansible-collections/ansible-inclusion>`_. For more information, see the `repository's README <https://github.com/ansible-collections/ansible-inclusion/blob/main/README.md>`_, and the :ref:`Ansible community package collections requirements <collections_requirements>`.

Stepping down as a collection maintainer
===========================================

Times change, and so may your ability to continue as a collection maintainer. We ask that you do not step down silently.

If you feel you don't have time to maintain your collection anymore, you should:

- Inform other maintainers about it.
- If the collection is under the ``ansible-collections`` organization, also inform relevant :ref:`communication_irc`, the ``community`` chat channels on IRC or matrix, or by email ``ansible-community@redhat.com``.
- Look at active contributors in the collection to find new maintainers among them. Discuss the potential candidates with other maintainers or with the community team.
- If you failed to find a replacement, create a pinned issue in the collection, announcing that the collection needs new maintainers.
- Make the same announcement through the `Bullhorn newsletter <https://github.com/ansible/community/wiki/News#the-bullhorn>`_.
- Please be around to discuss potential candidates found by other maintainers or by the community team.

Remember, this is a community, so you can come back at any time in the future.
