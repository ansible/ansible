.. _base_roadmap_2_10:

=================
Ansible-base 2.10
=================

.. contents::
   :local:

Release Schedule
----------------

Expected
========

PRs must be raised well in advance of the dates below to have a chance of being included in this ansible-base release.

.. note:: There is no Alpha phase in 2.10.
.. note:: Dates subject to change.

- 2020-06-16 Beta 1 **Feature freeze**
  No new functionality (including modules/plugins) to any code

- 2020-07-21 Release Candidate 1 (bumped from 2020-07-14)
- 2020-07-24 Release Candidate 2
- 2020-07-25 Release Candidate 3
- 2020-07-30 Release Candidate 4
- 2020-08-13 Release

Release Manager
---------------

@sivel

Planned work
============

- Migrate non-base plugins and modules from the ``ansible/ansible`` repository to smaller collection repositories
- Add functionality to ease transition to collections, such as automatic redirects from the 2.9 names to the new FQCN of the plugin
- Create new ``ansible-base`` package representing the ``ansible/ansible`` repository

Additional Resources
====================

The 2.10 release of Ansible will fundamentally change the scope of plugins included in the ``ansible/ansible`` repository, by
moving much of the plugins into smaller collection repositories that will be shipped through https://galaxy.ansible.com/

The following links have more information about this process:

- https://groups.google.com/d/msg/ansible-devel/oKqgCeYTs-M/cHrOgMw8CAAJ
- https://github.com/ansible-collections/overview/blob/main/README.rst
