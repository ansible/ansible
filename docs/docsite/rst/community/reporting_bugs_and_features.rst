.. _reporting_bugs_and_features:

**************************************
Reporting bugs and requesting features
**************************************

.. contents::
   :local:

.. _reporting_bugs:

Reporting a bug
===============

Security bugs
-------------

Ansible practices responsible disclosure - if this is a security-related bug, email `security@ansible.com <mailto:security@ansible.com>`_ instead of filing a ticket or posting to any public groups, and you will receive a prompt response.

Bugs in ansible-core
--------------------

If you find a bug that affects multiple plugins, a plugin that remained in the ansible/ansible repo, or the overall functioning of Ansible, report it to `github.com/ansible/ansible/issues <https://github.com/ansible/ansible/issues>`_. You need a free GitHub account.  Before reporting a bug, use the bug/issue search to see if the issue has already been reported. If you are not sure if something is a bug yet, you can report the behavior on the :ref:`mailing list or community chat first <communication>`.

Do not open issues for "how do I do this" type questions.  These are great topics for community chat channels or a mailing list, where things are likely to be more of a discussion.

If you find a bug, open the issue yourself to ensure we have a record of it. Do not rely on someone else in the community to file the bug report for you. We have created an issue template, which saves time and helps us help everyone with their issues more quickly. Please fill it out as completely and as accurately as possible:

  * Include the Ansible version
  * Include any relevant configuration
  * Include the exact commands or tasks you are running
  * Describe the behavior you expected
  * Provide steps to reproduce the bug
    * Use minimal well-reduced and well-commented examples, not your entire production playbook
    * When sharing YAML in playbooks, preserve the formatting by using `code blocks  <https://help.github.com/articles/creating-and-highlighting-code-blocks/>`_.
  * Document the behavior you got
  * Include output where possible
  * For multiple-file content, use gist.github.com, which is more durable than pastebin content

.. _reporting_bugs_in_collections:

Bugs in collections
-------------------

Many bugs only affect a single module or plugin. If you find a bug that affects a module or plugin hosted in a collection, file the bug in the repository of the :ref:`collection <collections>`:

  #. Find the collection on `Galaxy <https://galaxy.ansible.com>`_.
  #. Click on the Issue Tracker link for that collection.
  #. Follow the contributor guidelines or instructions in the collection repo.

If you are not sure whether a bug is in ansible-core or in a collection, you can report the behavior on the :ref:`mailing list or community chat channel first <communication>`.

.. _request_features:

Requesting a feature
====================

The best way to get a feature into Ansible is to :ref:`submit a pull request <community_pull_requests>`, either against ansible-core or against a collection. See also :ref:`ansible_collection_merge_requirements`.

You can also submit a feature request through opening an issue in the `ansible/ansible <https://github.com/ansible/ansible/issues>`_ for ``ansible-core`` or in a corresponding collection repository (refer to the :ref:`Bugs in collections<reporting_bugs_in_collections>` section to learn how to find a proper issue tracker).
