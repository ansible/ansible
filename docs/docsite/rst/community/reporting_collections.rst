.. _reporting_bugs_in_collections:

***********************************
Requesting changes to a collection
***********************************

.. contents::
   :local:

Reporting a bug
===============

Security bugs
-------------

Ansible practices responsible disclosure - if this is a security-related bug, email `security@ansible.com <mailto:security@ansible.com>`_ instead of filing a ticket or posting to any public groups, and you will receive a prompt response.


Bugs in collections
-------------------

Many bugs only affect a single module or plugin. If you find a bug that affects a module or plugin hosted in a collection, file the bug in the repository of the :ref:`collection <collections>`:

  #. Find the collection on `Galaxy <https://galaxy.ansible.com>`_.
  #. Click on the Issue Tracker link for that collection.
  #. Follow the contributor guidelines or instructions in the collection repo.

If you are not sure whether a bug is in ansible-core or in a collection, you can report the behavior on the :ref:`mailing list or community chat channel first <communication>`.

Requesting a feature
====================

Before you request a feature, check what is :ref:`planned for future Ansible Releases <roadmaps>`.
The best way to get a feature into an Ansible collection is to :ref:`submit a pull request <community_pull_requests>`, either against ansible-core or against a collection. See also the :ref:`ansible_collection_merge_requirements`.

You can also submit a feature request by opening an issue in the collection repository.
