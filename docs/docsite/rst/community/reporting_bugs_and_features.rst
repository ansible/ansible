
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

Ansible practices responsible disclosure - if this is a security-related bug, email `security@ansible.com <mailto:security@ansible.com>`_ instead of filing a ticket or posting to any public groups to receive a prompt response.

Bugs in ansible-core
--------------------

Before reporting a bug, use the bug/issue search to check for already reported issues. Unsure if you found a bug? Report the behavior on the :ref:`mailing list or community chat first <communication>`.

Do not open issues for "how do I do this" type questions. These are great topics for community chat channels or a mailing list, where things are likely to be more of a discussion.

If you are unsure whether a bug is in ansible-core or in a collection, report the behavior on the :ref:`mailing list or community chat channel first <communication>`.

You need a free GitHub account to report a bug to `github.com/ansible/ansible/issues <https://github.com/ansible/ansible/issues>`_ for bugs
- affecting multiple plugins
- a plugin that remained in the ansible/ansible repo
- the overall functioning of Ansible

How to write a good bug report
------------------------------

If you find a bug, open an issue using the `issue template <https://github.com/ansible/ansible/issues/new?assignees=&labels=&template=bug_report.yml>`. Detail what you've tried, why you think this is a bug, and what component to use. Fill it out as completely and as accurately as possible, include:

  * your Ansible version
  * any relevant configurations
  * the exact commands or tasks you are running
  * the expected behavior
  * the steps to reproduce the bug
    * Use minimal reproducible examples, not your entire production playbook. Use comments to describe your case.
    * When sharing YAML in playbooks, preserve formatting using `code blocks  <https://help.github.com/articles/creating-and-highlighting-code-blocks/>`_.
  * the current behavior you got
  * output where possible

For multiple-file content, use gist.github.com, which is more durable than pastebin content.

.. _request_features:

Requesting a feature
====================

Before you request a feature, check what is :ref:`planned for future Ansible Releases <roadmaps>`.
To get your feature into Ansible, to :ref:`submit a pull request <community_pull_requests>`, either against ansible-core or against a collection. See also :ref:`ansible_collection_merge_requirements`.

You can also open an issue in the `ansible/ansible <https://github.com/ansible/ansible/issues>`_ for ``ansible-core`` or in a corresponding collection repository (refer to the :ref:`Bugs in collections<reporting_bugs_in_collections>` section to learn how to find a proper issue tracker).
