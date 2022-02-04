.. _maintainers_workflow:


Pull requests, issues, and workflow
===================================

Each collection community can set its own rules and workflow for managing pull requests, bug reports, documentation issues, and feature requests, as well as adding and replacing maintainers.

Maintainers review and merge pull requests following the `Ansible Code of Conduct <https://docs.ansible.com/ansible/latest/community/code_of_conduct.html>`_, `Review checklist <review_checklist.rst>`_, and the `Committer guidelines <https://docs.ansible.com/ansible/devel/community/committer_guidelines.html#general-rules>`_.

There can be two kinds of maintainers: :ref:`collection_maintainers` and :ref:`module_maintainers`.

For the both kinds it is worth keeping in mind that “with great power comes great responsibility”.

.. _collection_maintainers:

Collection maintainers
----------------------

Collection-scope maintainers are contributors who have the ``write`` or higher access level in a collection.

They have the commit right and can merge pull requests among other permissions.

If applicable, the collection maintainers expand a pull of module maintainers.

.. _module_maintainers:

Module maintainers
------------------

Module-scope maintainers exist in collections that have the `collection bot <https://github.com/ansible-community/collection_bot>`_,
for example `community.general <https://github.com/ansible-collections/community.general>`_
and `community.network <https://github.com/ansible-collections/community.network>`_.

Being a module maintainer is the stage prior to becoming a collection maintainer.

Module maintainers are contributors who are listed in ``.github/BOTMETA.yml``.

The scope can be any file (for example, a module or plugin), directory, or repository.

Because in most cases the scope is a module or group of modules, we call these contributors as module maintainers.

The collection bot notifies module maintainers when issues / pull requests related to files they maintain are created.

Module maintainers have indirect commit rights implemented through the `collection bot <https://github.com/ansible-community/collection_bot>`_.
When two module maintainers comment with the keywords ``shipit``, ``LGTM``, or ``+1`` on a pull request
which changes a module they maintain, the collection bot will merge the pull request automatically.

For more information about the collection bot and its interface,
refer to the `Collection bot overview <https://github.com/ansible-community/collection_bot/blob/main/ISSUE_HELP.md>`_.

When a collection maintainer considers a contribution to a file significant enough
(it can be, for example, fixing a complex bug, adding a feature, providing regular reviews, and so on),
they can offer the author to become a module maintainer, in other words, to add their GitHub account to ``.github/BOTMETA.yml``.

Module maintainers, as well as collection ones, act in accordance to the `Ansible Code of Conduct <https://docs.ansible.com/ansible/latest/community/code_of_conduct.html>`_, the `Review checklist <review_checklist.rst>`_, and the `Committer guidelines <https://docs.ansible.com/ansible/devel/community/committer_guidelines.html>`_.

.. _Backporting:

Backporting
===========

Collection maintainers backport merged pull requests to stable branches
following the `semantic versioning <https://semver.org/>`_ and release policies of the collections.

For more information about the process, refer to the `Backporting guidelines <https://docs.ansible.com/ansible/devel/community/development_process.html#backporting-merged-prs-in-ansible-core>`_.

For convenience, backporting can be implemented automatically using GitHub bots (for example, with the `Patchback app <https://github.com/apps/patchback>`_) and labeling like it is done in `community.general <https://github.com/ansible-collections/community.general>`_ and `community.network <https://github.com/ansible-collections/community.network>`_.
