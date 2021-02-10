.. _base_roadmap_2_11:

=================
Ansible-core 2.11
=================

.. contents::
   :local:

Release Schedule
----------------

Expected
========

PRs must be raised well in advance of the dates below to have a chance of being included in this ansible-core release.

.. note:: There is no Alpha phase in 2.11.
.. note:: Dates subject to change.

- 2021-02-12 Feature Freeze
  No new functionality (including modules/plugins) to any code

- 2021-03-02 Beta 1
- 2021-03-15 Beta 2 (if necessary)

- 2021-03-29 Release Candidate 1 (and ``stable-2.11`` branching from ``devel``)
- 2021-04-12 Release Candidate 2 (if necessary)

- 2021-04-26 Release

Release Manager
---------------

 Ansible Core Team

Planned work
============

- Rename ``ansible-base`` to ``ansible-core``.
- Improve UX of ``ansible-galaxy collection`` CLI, specifically as it relates to install and upgrade.
- Add new Role Argument Spec feature that will allow a role to define an argument spec to be used in
  validating variables used by the role.
- Bump the minimum Python version requirement for the controller to Python 3.8. There will be no breaking changes
  to this release, however ``ansible-core`` will only be packaged for Python 3.8+. ``ansible-core==2.12`` will include
  breaking changes requiring at least Python 3.8.
- Introduce split-controller testing in ``ansible-test`` to separate dependencies for the controller from
  dependencies on the target.
