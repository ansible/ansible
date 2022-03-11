
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

Before reporting a bug, use the bug/issue search to check for `already reported issues <https://github.com/ansible/ansible/issues>`. Unsure if you found a bug? Report the behavior on the :ref:`mailing list or community chat first <communication>`.

Also, use the mailing list or chat if you are unsure whether a bug is in ``ansible-core`` or in a collection, and for "how do I do this" type questions to discuss.

You need a free GitHub account to `report bugs <https://github.com/ansible/ansible/issues>`_ that affects
- multiple plugins
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
    * Use a minimal reproducible example and comments describing examples
    * Preserve formatting using `code blocks  <https://help.github.com/articles/creating-and-highlighting-code-blocks/>`_ when sharing YAML in playbooks.
  * the behavior you currently see
  * output where possible
  * ``ansible -vvvv`` (debugging) output

For multiple-file content, use gist.github.com, which is more durable than pastebin content.

.. _request_features:

Requesting a feature
====================

Before you request a feature, check what is :ref:`planned for future Ansible Releases <roadmaps>`.
To get your feature into Ansible,  :ref:`submit a pull request <community_pull_requests>`, either against ansible-core or against a collection. See also :ref:`ansible_collection_merge_requirements`. To check already submitted pull requests, refer to :ref: `existing pull requests tagged with feature <https://github.com/ansible/ansible/issues?q=is%3Aissue+is%3Aopen+label%3Afeature>`.

For ``ansible-core``, you can also open an issue in `ansible/ansible <https://github.com/ansible/ansible/issues>`_  or in a corresponding collection repository (to learn how to find a proper issue tracker, refer to :ref:`Bugs in collections<reporting_bugs_in_collections>` section ).
